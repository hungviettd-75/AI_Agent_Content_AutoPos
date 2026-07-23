import streamlit as st
import pandas as pd
import json
from datetime import datetime
from database.repositories import PostRepository, KnowledgeRepository
from database.models.posts import PostModel
from database.models.assets import AssetModel
from database.models.brand import BrandModel
from database.models.companies import CompanyModel
from database.models.approvals import ApprovalModel
from services.content_service import generate_marketing_or_knowledge_content
from services.copywriting_service import generate_copy
from services.gemini_client import generate_with_gemini
from ui.components.badge import render_status_badge
from agents.copywriting_prompts import COPY_FRAMEWORKS, COPY_TYPES, COPY_TONES
from agents.prompt_templates import get_creative_concept_prompt, get_single_concept_prompt
from config.config import CONTENT_TYPES
from config.logistics_vertical import LOGISTICS_ANGLES, LOGISTICS_TARGETS

STUDIO_CSS = """
<style>
.studio-title {
    font-size: 1.8rem;
    font-weight: 700;
    color: #004ac6;
    margin-bottom: 0.5rem;
}
.concept-card {
    background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%);
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1.25rem;
    position: relative;
    overflow: hidden;
    transition: box-shadow 0.2s ease;
}
.concept-card:hover {
    box-shadow: 0 8px 32px rgba(0, 74, 198, 0.10);
}
.concept-badge-1 {
    background: linear-gradient(135deg, #004ac6 0%, #2563eb 100%);
    color: white;
    border-radius: 8px;
    padding: 4px 12px;
    font-size: 0.78rem;
    font-weight: 700;
    display: inline-block;
    margin-bottom: 0.75rem;
    letter-spacing: 0.5px;
}
.concept-badge-2 {
    background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%);
    color: white;
    border-radius: 8px;
    padding: 4px 12px;
    font-size: 0.78rem;
    font-weight: 700;
    display: inline-block;
    margin-bottom: 0.75rem;
    letter-spacing: 0.5px;
}
.concept-badge-3 {
    background: linear-gradient(135deg, #059669 0%, #10b981 100%);
    color: white;
    border-radius: 8px;
    padding: 4px 12px;
    font-size: 0.78rem;
    font-weight: 700;
    display: inline-block;
    margin-bottom: 0.75rem;
    letter-spacing: 0.5px;
}
.concept-stripe-1 {
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    background: linear-gradient(90deg, #004ac6, #2563eb);
    border-radius: 16px 16px 0 0;
}
.concept-stripe-2 {
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    background: linear-gradient(90deg, #7c3aed, #a855f7);
    border-radius: 16px 16px 0 0;
}
.concept-stripe-3 {
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    background: linear-gradient(90deg, #059669, #10b981);
    border-radius: 16px 16px 0 0;
}
.concept-engine-banner {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    border-radius: 12px;
    padding: 1rem 1.25rem;
    margin-bottom: 1rem;
    border-left: 4px solid #f59e0b;
}
.concept-engine-banner-title {
    color: #f59e0b;
    font-size: 0.85rem;
    font-weight: 700;
    margin-bottom: 2px;
}
.concept-engine-banner-sub {
    color: #94a3b8;
    font-size: 0.78rem;
}
.studio-container {
    background: #ffffff;
    border-radius: 16px;
    padding: 1.5rem;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03);
    border: 1px solid #e2e8f0;
}
.autosave-indicator {
    font-size: 0.8rem;
    color: #10b981;
    font-weight: 600;
    text-align: right;
    margin-bottom: 0.5rem;
}
.mockup-container {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1.25rem;
    margin-top: 1rem;
}
.mockup-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 1rem;
    border-bottom: 1px solid #e2e8f0;
    padding-bottom: 0.75rem;
}
.mockup-avatar {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: linear-gradient(135deg, #004ac6 0%, #2563eb 100%);
    color: white;
    font-weight: bold;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.9rem;
}
.mockup-meta {
    font-size: 0.82rem;
    color: #64748b;
}
.mockup-content {
    font-size: 0.92rem;
    white-space: pre-wrap;
    line-height: 1.6;
    color: #0f172a;
}
.media-card {
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 8px;
    background: white;
    text-align: center;
}
.media-img {
    max-height: 100px;
    object-fit: cover;
    border-radius: 4px;
    margin-bottom: 6px;
}
</style>
"""

def render_tab_content_studio_workspace(gemini_key, workspace_id: int = None, user_id: int = 1, user_email="", role="editor"):
    st.markdown(STUDIO_CSS, unsafe_allow_html=True)
    role = (role or "editor").lower()
    
    # State Keys
    editor_content_key = f"studio_editor_content_{workspace_id}"
    editor_title_key = f"studio_editor_title_{workspace_id}"
    editor_platform_key = f"studio_editor_platform_{workspace_id}"
    versions_key = f"studio_versions_{workspace_id}"
    media_attached_key = f"studio_media_attached_{workspace_id}"
    media_attached_id_key = f"studio_media_attached_id_{workspace_id}"
    original_content_key = f"studio_original_content_{workspace_id}"
    ai_suggestions_key = f"studio_ai_suggestions_{workspace_id}"

    # Initialize State
    if editor_content_key not in st.session_state:
        st.session_state[editor_content_key] = ""
    if "studio_workspace_textarea" not in st.session_state:
        st.session_state["studio_workspace_textarea"] = ""
    if editor_title_key not in st.session_state:
        st.session_state[editor_title_key] = "Bài viết mới"
    if editor_platform_key not in st.session_state:
        st.session_state[editor_platform_key] = "Facebook"
    if versions_key not in st.session_state:
        st.session_state[versions_key] = []
        # Nếu khởi tạo mà editor đã có sẵn nội dung (ví dụ vừa reload), lưu làm bản ghi đầu tiên
        if st.session_state[editor_content_key]:
            st.session_state[versions_key].append({
                "time": datetime.now().strftime("%H:%M:%S"),
                "content": st.session_state[editor_content_key]
            })
    if media_attached_key not in st.session_state:
        st.session_state[media_attached_key] = None
    if media_attached_id_key not in st.session_state:
        st.session_state[media_attached_id_key] = None
    if original_content_key not in st.session_state:
        st.session_state[original_content_key] = ""
    if ai_suggestions_key not in st.session_state:
        st.session_state[ai_suggestions_key] = []
        
    # Callback function to update editor state safely (prevents StreamlitAPIException)
    def update_editor_state(content, title=None, platform=None, success_msg=None):
        st.session_state[editor_content_key] = content
        st.session_state["studio_workspace_textarea"] = content
        if title is not None:
            st.session_state[editor_title_key] = title
        if platform is not None:
            st.session_state[editor_platform_key] = platform
        if success_msg:
            st.session_state["editor_success_msg"] = success_msg
            
        # Tự động ghi nhận vào lịch sử phiên bản nếu có sự thay đổi nội dung
        if versions_key in st.session_state:
            v_list = st.session_state[versions_key]
            if len(v_list) == 0 or v_list[-1]["content"] != content:
                st.session_state[versions_key].append({
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "content": content
                })

    # Hiển thị thông báo thành công từ callback nếu có
    if "editor_success_msg" in st.session_state and st.session_state["editor_success_msg"]:
        st.success(st.session_state["editor_success_msg"])
        st.session_state["editor_success_msg"] = ""
    
    # State cho Creative Concept Engine
    creative_concepts_key = f"studio_creative_concepts_{workspace_id}"
    creative_concepts_loading_key = f"studio_creative_concepts_loading_{workspace_id}"
    if creative_concepts_key not in st.session_state:
        st.session_state[creative_concepts_key] = ""
    if creative_concepts_loading_key not in st.session_state:
        st.session_state[creative_concepts_loading_key] = False

    # UI Split Screen Layout
    col_editor, col_preview = st.columns([1, 1], gap="large")

    # ==========================================
    # CỘT TRÁI: EDITOR CHUYÊN NGHIỆP & CONTROL PANEL
    # ==========================================
    with col_editor:
        st.markdown("### 📝 Professional Workspace Editor")
        
        # Load Cấu hình Brand & Company
        brand_profile = BrandModel.get_by_workspace(workspace_id)
        company_profile = CompanyModel.get_by_workspace(workspace_id)

        # Tab tạo ý tưởng hoặc Copywriting framework
        creation_mode = st.tabs(["✨ AI Create", "✍️ Copywriting Framework", "📂 Brand Brain Profile", "📂 Mở bài viết (Load)"])
        
        # 1. AI Create Tab
        with creation_mode[0]:
            st.caption("Sinh nội dung tự động dựa trên chủ đề")
            create_col1, create_col2 = st.columns(2)
            with create_col1:
                platform_sel = st.selectbox("Nền tảng mục tiêu", ["Facebook", "LinkedIn", "Zalo OA"], key="studio_create_platform")
                content_type_sel = st.selectbox("Loại bài viết", CONTENT_TYPES, key="studio_create_type")
            with create_col2:
                target_options = ["CEO", "Chủ doanh nghiệp", "Marketer", "Developer", "Sales", "Freelancer", *LOGISTICS_TARGETS]
                target_sel = st.selectbox("Khách hàng mục tiêu", target_options, key="studio_create_target")
                angle_options = ["Tự động chọn", "Sai lầm thường gặp", "Case study", "Câu chuyện thực tế", *LOGISTICS_ANGLES]
                angle_sel = st.selectbox("Góc tiếp cận", angle_options, key="studio_create_angle")
                
            logistics_topics = [
                "Giảm chi phí vận chuyển cho doanh nghiệp thương mại điện tử",
                "Cam kết SLA giao hàng và tác động đến tỷ lệ mua lại",
                "Case study giảm tỷ lệ giao thất bại trong 60 ngày",
                "Fulfillment giúp chủ shop online xử lý đơn mùa cao điểm",
                "Dashboard realtime cho CEO Logistics",
                "So sánh tự vận hành giao hàng và thuê 3PL",
            ]
            selected_logistics_topic = st.selectbox("Gợi ý nhanh cho Logistics", ["Tự nhập chủ đề", *logistics_topics], key="studio_logistics_topic_suggestion")
            default_topic = "" if selected_logistics_topic == "Tự nhập chủ đề" else selected_logistics_topic
            create_topic = st.text_area("Chủ đề cụ thể:", value=default_topic, placeholder="Nhập chủ đề cho bài đăng của bạn...", key="studio_create_topic")
            research_mode = st.checkbox("🌐 Bật Research Agent (Google Search Grounding)", value=False, key="studio_create_research")
            
            if st.button("🚀 Sinh bài viết bằng AI", use_container_width=True, key="studio_create_btn"):
                if not create_topic:
                    st.warning("Vui lòng điền chủ đề!")
                elif not gemini_key:
                    st.error("Vui lòng nhập API Key!")
                else:
                    with st.spinner("AI đang sáng tạo bài viết..."):
                        try:
                            result = generate_marketing_or_knowledge_content(
                                platform=platform_sel,
                                content_type=content_type_sel,
                                topic=create_topic,
                                target=target_sel,
                                angle_selection=angle_sel,
                                api_key=gemini_key,
                                workspace_id=workspace_id,
                                enable_research=research_mode
                            )
                            # Cập nhật nội dung Editor
                            st.session_state[editor_content_key] = result["content"]
                            st.session_state["studio_workspace_textarea"] = result["content"]
                            st.session_state[editor_title_key] = create_topic[:50]
                            st.session_state[editor_platform_key] = platform_sel
                            
                            # ✅ Lưu bản gốc chưa chỉnh sửa để có thể khôi phục bất kỳ lúc nào
                            st.session_state[original_content_key] = result["content"]
                            
                            # Tự động lưu bản nháp vào Database đề phòng mất session khi reload trang
                            post_id = PostModel.create(
                                content=result["content"],
                                platform=platform_sel.lower(),
                                topic=create_topic,
                                title=create_topic[:50],
                                status="draft",
                                workspace_id=workspace_id
                            )
                            
                            # Lưu vào lịch sử phiên bản (đây là bản #1 - bản gốc)
                            st.session_state[versions_key] = [{
                                "time": datetime.now().strftime("%H:%M:%S"),
                                "content": result["content"],
                                "label": "🤖 Bản gốc AI"
                            }]
                            # === AUTO TRIGGER: Creative Concept Engine ===
                            st.session_state[creative_concepts_key] = ""  # Reset concept cũ
                            st.session_state[creative_concepts_loading_key] = True
                            st.success(f"✨ Đã tạo nội dung và tự động lưu nháp vào Database (ID: `#{post_id}`)!")
                            st.info("🎨 Creative Concept Engine đang phân tích bài viết... Vui lòng chuyển sang tab **Creative Concepts**.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Lỗi: {e}")

        # 2. Copywriting Framework Tab
        with creation_mode[1]:
            st.caption("Áp dụng các mô hình bán hàng kinh điển (AIDA/PAS/BAB)")
            copy_col1, copy_col2 = st.columns(2)
            with copy_col1:
                copy_prod = st.text_input("Tên sản phẩm:", key="studio_copy_prod")
                copy_framework = st.selectbox("Framework", COPY_FRAMEWORKS, key="studio_copy_fw")
            with copy_col2:
                copy_target = st.text_input("Đối tượng:", key="studio_copy_target")
                copy_tone = st.selectbox("Giọng điệu", COPY_TONES, key="studio_copy_tone")
            
            copy_benefit = st.text_area("USP / Lợi ích sản phẩm:", key="studio_copy_benefit")
            
            if st.button("🚀 Tạo Copy thuyết phục", use_container_width=True, key="studio_copy_btn"):
                if not copy_prod or not copy_benefit:
                    st.warning("Vui lòng điền đủ sản phẩm và USP!")
                elif not gemini_key:
                    st.error("Vui lòng nhập API Key!")
                else:
                    with st.spinner("AI đang tạo Copy..."):
                        try:
                            result = generate_copy(
                                product=copy_prod,
                                benefit=copy_benefit,
                                target=copy_target,
                                framework=copy_framework,
                                copy_type="Marketing Copy",
                                tone=copy_tone,
                                api_key=gemini_key,
                                workspace_id=workspace_id,
                                enable_research=False,
                                enable_ab=False
                            )
                            st.session_state[editor_content_key] = result["copy"]
                            st.session_state["studio_workspace_textarea"] = result["copy"]
                            st.session_state[editor_title_key] = f"Copy Bán Hàng - {copy_prod[:30]}"
                            
                            # ✅ Lưu bản gốc chưa chỉnh sửa để có thể khôi phục bất kỳ lúc nào
                            st.session_state[original_content_key] = result["copy"]
                            
                            # Tự động lưu bản nháp vào Database đề phòng mất session khi reload trang
                            post_id = PostModel.create(
                                content=result["copy"],
                                platform="facebook",
                                topic=f"Copy Bán Hàng - {copy_prod[:30]}",
                                title=f"Copy Bán Hàng - {copy_prod[:30]}",
                                status="draft",
                                workspace_id=workspace_id
                            )
                            
                            # Lưu vào lịch sử phiên bản (đây là bản #1 - bản gốc)
                            st.session_state[versions_key] = [{
                                "time": datetime.now().strftime("%H:%M:%S"),
                                "content": result["copy"],
                                "label": "✍️ Bản gốc Copy"
                            }]
                            # === AUTO TRIGGER: Creative Concept Engine (Copy Framework) ===
                            st.session_state[creative_concepts_key] = ""
                            st.session_state[creative_concepts_loading_key] = True
                            st.success(f"✨ Đã áp dụng framework Copy vào Editor và tự động lưu nháp vào Database (ID: `#{post_id}`)!")
                            st.info("🎨 Creative Concept Engine đang phân tích bài viết... Vui lòng chuyển sang tab **Creative Concepts**.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Lỗi: {e}")

        # 3. Brand Brain Profile Tab
        with creation_mode[2]:
            st.caption("Tri thức nền tảng đang áp dụng từ Brand Brain")
            st.write(f"🏢 **Doanh nghiệp:** {company_profile.get('name', 'N/A')}")
            st.write(f"🎭 **Tone of Voice:** {brand_profile.get('tone_of_voice', 'Casual')}")
            st.write(f"📢 **CTA Mặc định:** {brand_profile.get('cta', 'N/A')}")

        # 4. Mở bài viết (Load)
        with creation_mode[3]:
            st.caption("Tải bài viết cũ hoặc bài nháp đã lưu vào trình soạn thảo để tiếp tục chỉnh sửa")
            df_all_posts = PostModel.list_by_workspace(workspace_id=workspace_id, limit=100)
            if df_all_posts.empty:
                st.info("Chưa có bài viết nào được lưu trong Workspace này.")
            else:
                post_options = {
                    row["id"]: f"#{row['id']} [{row['platform'].upper()}] - {str(row.get('title') or row.get('topic') or '')[:40]}... ({row['status']})"
                    for _, row in df_all_posts.iterrows()
                }
                selected_load_id = st.selectbox(
                    "Chọn bài viết cần mở lại:",
                    options=list(post_options.keys()),
                    format_func=lambda x: post_options[x],
                    key="studio_load_post_select"
                )
                
                if st.button("📂 Tải vào Editor", use_container_width=True, key="studio_load_post_btn"):
                    post_row = df_all_posts[df_all_posts["id"] == selected_load_id].iloc[0]
                    content_to_load = post_row.get("content", "")
                    title_to_load = post_row.get("title") or post_row.get("topic") or "Bài viết mới"
                    platform_to_load = str(post_row.get("platform", "facebook")).lower().strip()
                    if "facebook" in platform_to_load:
                        platform_to_load = "Facebook"
                    elif "linkedin" in platform_to_load:
                        platform_to_load = "LinkedIn"
                    elif "zalo" in platform_to_load:
                        platform_to_load = "Zalo OA"
                    else:
                        platform_to_load = "Facebook"
                        
                    # Tải thông tin ảnh đã đính kèm (nếu có)
                    assets_list = AssetModel.list_by_post(selected_load_id)
                    attached_url = None
                    attached_id = None
                    if assets_list:
                        # Lọc lấy file ảnh đầu tiên
                        images_only = [a for a in assets_list if str(a.get("file_type", "")).startswith("image")]
                        if images_only:
                            attached_url = images_only[0]["url"]
                            attached_id = images_only[0]["id"]
                            
                    st.session_state[media_attached_key] = attached_url
                    st.session_state[media_attached_id_key] = attached_id
                    
                    # ✅ Lưu bản gốc khi mở bài viết từ DB để có thể khôi phục về trạng thái ban đầu
                    st.session_state[original_content_key] = content_to_load
                    
                    # Reset lịch sử và khởi tạo phiên bản đầu tiên là bản vừa load
                    st.session_state[versions_key] = [{
                        "time": datetime.now().strftime("%H:%M:%S"),
                        "content": content_to_load,
                        "label": f"📂 Bản gốc từ DB (#{selected_load_id})"
                    }]
                    
                    update_editor_state(
                        content=content_to_load,
                        title=title_to_load,
                        platform=platform_to_load,
                        success_msg=f"📂 Đã tải thành công bài viết #{selected_load_id} vào Trình soạn thảo!"
                    )
                    st.rerun()

        st.divider()

        # Editor Area
        st.markdown("#### Trình soạn thảo văn bản")
        
        # Auto-Save status indicator
        st.markdown("<div class='autosave-indicator'>🟢 Auto-Save Active</div>", unsafe_allow_html=True)
        
        ed_title = st.text_input("Tiêu đề bài viết:", value=st.session_state[editor_title_key])
        if ed_title != st.session_state[editor_title_key]:
            st.session_state[editor_title_key] = ed_title
            
        platform_options = ["Facebook", "LinkedIn", "Zalo OA"]
        current_platform = st.session_state[editor_platform_key]
        if current_platform not in platform_options:
            # Fallback an toàn nếu có lệch giá trị
            current_platform = "Facebook"
            st.session_state[editor_platform_key] = current_platform
            
        ed_platform = st.selectbox(
            "Nền tảng:",
            platform_options,
            index=platform_options.index(current_platform)
        )
        if ed_platform != st.session_state[editor_platform_key]:
            st.session_state[editor_platform_key] = ed_platform

        ed_content = st.text_area(
            "Nội dung (Hỗ trợ Markdown):",
            value=st.session_state[editor_content_key],
            height=450
        )
        
        # Auto Save Logic
        if ed_content != st.session_state[editor_content_key]:
            st.session_state[editor_content_key] = ed_content
            # Lưu vết thay đổi
            if len(st.session_state[versions_key]) == 0 or st.session_state[versions_key][-1]["content"] != ed_content:
                st.session_state[versions_key].append({
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "content": ed_content
                })

        # Actions Panel (Save Draft, Knowledge, Post)
        act_col1, act_col2, act_col3 = st.columns(3)
        with act_col1:
            if st.button("💾 Lưu bản nháp (Draft)", use_container_width=True):
                post_id = PostModel.create(
                    content=st.session_state[editor_content_key],
                    platform=st.session_state[editor_platform_key].lower(),
                    topic=st.session_state[editor_title_key],
                    title=st.session_state[editor_title_key],
                    status="draft",
                    workspace_id=workspace_id
                )
                if st.session_state.get(media_attached_id_key):
                    AssetModel.attach_to_post(st.session_state[media_attached_id_key], post_id)
                st.success(f"💾 Đã lưu bài đăng nháp (ID: `#{post_id}`)")
        with act_col2:
            if st.button("🧠 Lưu vào Tri thức", use_container_width=True):
                k_id = KnowledgeRepository.save_knowledge_post(
                    date=datetime.now().strftime("%d/%m/%Y %H:%M"),
                    platform="knowledge_center",
                    topic=st.session_state[editor_title_key],
                    audience="Khách hàng",
                    tool_name="Studio Editor",
                    knowledge_type="Tài liệu hướng dẫn",
                    difficulty="Medium",
                    content=st.session_state[editor_content_key],
                    summary=st.session_state[editor_content_key][:100],
                    status="Active",
                    workspace_id=workspace_id,
                    created_by=user_id
                )
                st.success(f"🧠 Đã đồng bộ vào Knowledge Center (ID: `#{k_id}`)")
        with act_col3:
            if st.button("🚀 Gửi phê duyệt", type="primary", use_container_width=True):
                post_id = PostModel.create(
                    content=st.session_state[editor_content_key],
                    platform=st.session_state[editor_platform_key].lower(),
                    topic=st.session_state[editor_title_key],
                    title=st.session_state[editor_title_key],
                    status="pending_manager_approval",
                    workspace_id=workspace_id
                )
                # Đính kèm ảnh vào bài viết trong cơ sở dữ liệu nếu có
                if st.session_state.get(media_attached_id_key):
                    AssetModel.attach_to_post(st.session_state[media_attached_id_key], post_id)
                # Đăng ký yêu cầu phê duyệt để hiển thị trong tab Quy trình phê duyệt
                ApprovalModel.request(
                    post_id,
                    requested_by=user_id,
                    workspace_id=workspace_id
                )
                st.success(f"🚀 Đã tạo yêu cầu phê duyệt thành công! (ID: `#{post_id}`)")

    # ==========================================
    # CỘT PHẢI: LIVE PREVIEW & ASSETS (MEDIA)
    # ==========================================
    with col_preview:
        st.markdown("### 👁️ Live Preview & Assets")
        
        preview_tabs = st.tabs(["📱 Live Preview Mockup", "🎨 Creative Concepts", "🖼️ Media Manager", "🔄 Version History", "💡 AI Suggestions"])
        
        # 1. Live Preview Mockup
        with preview_tabs[0]:
            with st.container():
                st.caption("Trực quan hóa hiển thị bài viết trên thiết bị di động")
                
                # Chọn nền tảng hiển thị
                preview_platform = st.session_state[editor_platform_key]
                
                st.markdown(f"""
                <div class="mockup-container">
                    <div class="mockup-header">
                        <div class="mockup-avatar">{company_profile.get('name', 'AP')[:2].upper()}</div>
                        <div class="mockup-meta">
                            <b>{company_profile.get('name', 'Apex Brand Owner')}</b><br>
                            <span>Sponsored &middot; {preview_platform}</span>
                        </div>
                    </div>
                    <div class="mockup-content">{st.session_state[editor_content_key] if st.session_state[editor_content_key] else 'Nội dung đang soạn thảo sẽ hiển thị trực quan ở đây...'}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Hiển thị hình ảnh đính kèm nếu có
                img_container = st.container()
                if st.session_state[media_attached_key]:
                    img_url = st.session_state[media_attached_key]
                    import os
                    if isinstance(img_url, str) and not img_url.startswith("http") and not os.path.exists(img_url):
                        img_container.warning(f"⚠️ Không thể hiển thị ảnh (File không tồn tại trên hệ thống: {img_url})")
                    else:
                        try:
                            img_container.image(img_url, caption="Ảnh minh họa đã đính kèm", use_container_width=True)
                        except Exception as img_err:
                            img_container.warning(f"⚠️ Lỗi hiển thị ảnh: {img_err}")

        # 2. Creative Concept Engine Tab
        with preview_tabs[1]:
            with st.container():
                # Banner thông báo
                st.markdown("""
                <div class="concept-engine-banner">
                    <div class="concept-engine-banner-title">🎨 Creative Concept Engine</div>
                    <div class="concept-engine-banner-sub">AI phân tích TOÀN BỘ bài viết → Sinh 03 Creative Concept cho Thumbnail</div>
                </div>
                """, unsafe_allow_html=True)

                current_content = st.session_state[editor_content_key]

                if not current_content:
                    st.info("⬅️ Vui lòng tạo bài viết bằng AI trước. Creative Concept Engine sẽ tự động kích hoạt sau khi bài viết hoàn thành.")
                else:
                    # Hiển thị nút sinh concept thủ công (hoặc auto kích hoạt)
                    col_cc1, col_cc2 = st.columns([3, 1])
                    with col_cc1:
                        st.caption(f"📄 Bài viết hiện tại: **{len(current_content)} ký tự** — AI sẽ phân tích toàn bộ nội dung")
                    with col_cc2:
                        if st.button("🔄 Làm mới", key="studio_cc_refresh", use_container_width=True):
                            st.session_state[creative_concepts_loading_key] = True
                            st.session_state[creative_concepts_key] = ""
                                     # Tự động sinh concept nếu được trigger
                    if st.session_state.get(creative_concepts_loading_key, False) and not st.session_state.get(creative_concepts_key, ""):
                        if gemini_key and current_content:
                            with st.spinner("🎨 Creative Concept Engine đang phân tích TOÀN BỘ bài viết và sinh 03 Concept..."):
                                try:
                                    cc_prompt = get_creative_concept_prompt(
                                        full_article_content=current_content
                                    )
                                    cc_result = generate_with_gemini(cc_prompt, api_key=gemini_key)
                                    st.session_state[creative_concepts_key] = cc_result
                                    
                                    # Tự động phân tách và lưu dữ liệu cho 3 concepts
                                    lines = cc_result.split("\n")
                                    concept1_lines, concept2_lines, concept3_lines = [], [], []
                                    current_section = "header"
                                    for line in lines:
                                        line_stripped = line.strip()
                                        if "CONCEPT 1" in line_stripped.upper() and "BUSINESS" in line_stripped.upper():
                                            current_section = "c1"
                                        elif "CONCEPT 2" in line_stripped.upper() and ("CINEMATIC" in line_stripped.upper() or "STORY" in line_stripped.upper()):
                                            current_section = "c2"
                                        elif "CONCEPT 3" in line_stripped.upper() and ("INFOGRAPHIC" in line_stripped.upper() or "DATA" in line_stripped.upper()):
                                            current_section = "c3"
                                        
                                        if current_section == "c1":
                                            concept1_lines.append(line)
                                        elif current_section == "c2":
                                            concept2_lines.append(line)
                                        elif current_section == "c3":
                                            concept3_lines.append(line)
                                            
                                    # Parser bóc tách từng Concept
                                    def parse_single_concept(lines_list):
                                        data = {
                                            "name": "",
                                            "marketing_goal": "",
                                            "visual_story": "",
                                            "headline": "",
                                            "short_description": "",
                                            "business_value": "",
                                            "preview_prompt": ""
                                        }
                                        current_key = None
                                        acc = []
                                        key_mapping = {
                                            "CONCEPT NAME": "name",
                                            "MARKETING GOAL": "marketing_goal",
                                            "VISUAL STORY": "visual_story",
                                            "HEADLINE SUGGESTION": "headline",
                                            "MAIN MESSAGE": "short_description",
                                            "BUSINESS VALUE": "business_value",
                                            "PREVIEW PROMPT": "preview_prompt"
                                        }
                                        for line in lines_list:
                                            matched = False
                                            for prefix, target_key in key_mapping.items():
                                                if line.strip().upper().startswith(f"**{prefix}**") or line.strip().upper().startswith(f"{prefix}:") or line.strip().upper().startswith(prefix):
                                                    if current_key:
                                                        data[current_key] = "\n".join(acc).strip()
                                                    current_key = target_key
                                                    parts = line.split(":", 1)
                                                    val = parts[1].strip() if len(parts) > 1 else ""
                                                    val = val.strip("* ").strip("[").strip("]")
                                                    acc = [val]
                                                    matched = True
                                                    break
                                            if not matched and current_key:
                                                acc.append(line)
                                        if current_key:
                                            data[current_key] = "\n".join(acc).strip().strip("* ").strip("[").strip("]")
                                        
                                        # Fallbacks
                                        if not data["name"]:
                                            data["name"] = "Concept Spec"
                                        return data
                                    
                                    st.session_state[f"c1_data_{workspace_id}"] = parse_single_concept(concept1_lines)
                                    st.session_state[f"c2_data_{workspace_id}"] = parse_single_concept(concept2_lines)
                                    st.session_state[f"c3_data_{workspace_id}"] = parse_single_concept(concept3_lines)
                                    
                                    st.session_state[creative_concepts_loading_key] = False
                                    st.rerun()
                                except Exception as cc_err:
                                    st.error(f"Lỗi sinh Creative Concept: {cc_err}")
                                    st.session_state[creative_concepts_loading_key] = False

                    # Hiển thị kết quả 3 Creative Concepts
                    cc_output = st.session_state.get(creative_concepts_key, "")
                    if cc_output:
                        st.success("✅ Đã sinh 03 Creative Concept và Prompt tạo ảnh từ phân tích bài viết!")
                        st.divider()

                        # Định nghĩa UI Render cho 1 Card
                        def render_concept_ui_card(concept_num, label, style_class, stripe_class):
                            data_key = f"c{concept_num}_data_{workspace_id}"
                            img_key = f"c{concept_num}_img_preview_{workspace_id}"
                            
                            if data_key not in st.session_state:
                                return
                            
                            concept_data = st.session_state[data_key]
                            
                            st.markdown(f"""
                            <div class="concept-card">
                                <div class="{stripe_class}"></div>
                                <div style="padding-top: 6px;">
                                    <span class="{style_class}">{label} — {concept_data.get('name', 'N/A')}</span>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            st.markdown(f"**🎯 Marketing Goal:** {concept_data.get('marketing_goal', 'N/A')}")
                            st.markdown(f"**🖼️ Visual Story:** {concept_data.get('visual_story', 'N/A')}")
                            
                            headline = concept_data.get('headline', 'N/A')
                            st.markdown(f"""
                            <div class="concept-headline-box">
                                "{headline}"
                            </div>
                            """, unsafe_allow_html=True)
                            
                            st.markdown(f"**📝 Mô tả ngắn:** {concept_data.get('short_description', 'N/A')}")
                            
                            biz_val = concept_data.get('business_value', 'N/A')
                            st.markdown(f"""
                            <div class="concept-value-box">
                                💡 <b>Business Value:</b> {biz_val}
                            </div>
                            """, unsafe_allow_html=True)
                            
                            preview_prompt = concept_data.get('preview_prompt', '')
                            with st.expander("👁️ Xem Prompt tạo ảnh chi tiết"):
                                st.code(preview_prompt, language="text")
                            
                            # Hiển thị ảnh nếu đã sinh
                            img_preview_container = st.container()
                            if img_key in st.session_state and st.session_state[img_key]:
                                img_preview_container.image(st.session_state[img_key], caption=f"Ảnh minh họa cho Concept {concept_num}", use_container_width=True)
                                
                            # Nút bấm hành động
                            col_btn1, col_btn2, col_btn3, col_btn4 = st.columns([1.5, 1.2, 1.2, 1.2])
                            with col_btn1:
                                if st.button(f"🖼️ Generate Image", key=f"gen_img_btn_{concept_num}_{workspace_id}", type="primary"):
                                    with st.spinner("AI đang sinh ảnh minh họa..."):
                                        import time, random
                                        time.sleep(1.5)  # Giả lập thời gian sinh ảnh
                                        seed = random.randint(1, 9999)
                                        st.session_state[img_key] = f"https://picsum.photos/seed/{seed}/800/600"
                                        st.rerun()
                            with col_btn2:
                                if st.button(f"📋 Copy Prompt", key=f"copy_p_btn_{concept_num}_{workspace_id}"):
                                    st.code(preview_prompt, language="text")
                                    st.success("Đã lấy prompt!")
                            with col_btn3:
                                if st.button(f"🔄 Regenerate", key=f"regen_btn_{concept_num}_{workspace_id}"):
                                    with st.spinner(f"Đang sinh lại Concept {concept_num}..."):
                                        try:
                                            single_prompt = get_single_concept_prompt(
                                                full_article_content=current_content,
                                                concept_name=f"CONCEPT {concept_num}"
                                            )
                                            single_res = generate_with_gemini(single_prompt, api_key=gemini_key)
                                            
                                            # Parser cục bộ
                                            def parse_single_concept(text_block):
                                                lines_list = text_block.split("\n")
                                                data = {
                                                    "name": "",
                                                    "marketing_goal": "",
                                                    "visual_story": "",
                                                    "headline": "",
                                                    "short_description": "",
                                                    "business_value": "",
                                                    "preview_prompt": ""
                                                }
                                                current_key = None
                                                acc = []
                                                key_mapping = {
                                                    "CONCEPT NAME": "name",
                                                    "MARKETING GOAL": "marketing_goal",
                                                    "VISUAL STORY": "visual_story",
                                                    "HEADLINE SUGGESTION": "headline",
                                                    "MAIN MESSAGE": "short_description",
                                                    "BUSINESS VALUE": "business_value",
                                                    "PREVIEW PROMPT": "preview_prompt"
                                                }
                                                for line in lines_list:
                                                    matched = False
                                                    for prefix, target_key in key_mapping.items():
                                                        if line.strip().upper().startswith(f"**{prefix}**") or line.strip().upper().startswith(f"{prefix}:") or line.strip().upper().startswith(prefix):
                                                            if current_key:
                                                                data[current_key] = "\n".join(acc).strip()
                                                            current_key = target_key
                                                            parts = line.split(":", 1)
                                                            val = parts[1].strip() if len(parts) > 1 else ""
                                                            val = val.strip("* ").strip("[").strip("]")
                                                            acc = [val]
                                                            matched = True
                                                            break
                                                    if not matched and current_key:
                                                        acc.append(line)
                                                if current_key:
                                                    data[current_key] = "\n".join(acc).strip().strip("* ").strip("[").strip("]")
                                                return data
                                            
                                            st.session_state[data_key] = parse_single_concept(single_res)
                                            # Reset ảnh cũ khi regen
                                            if img_key in st.session_state:
                                                st.session_state[img_key] = None
                                            st.success(f"Đã làm mới Concept {concept_num}!")
                                            st.rerun()
                                        except Exception as single_err:
                                            st.error(f"Lỗi làm mới Concept: {single_err}")
                            with col_btn4:
                                if st.button(f"👁️ Xem Prompt", key=f"view_prompt_btn_{concept_num}_{workspace_id}"):
                                    st.info(preview_prompt)
                            st.markdown("<br>", unsafe_allow_html=True)
                            st.divider()

                        # Render 3 Concepts
                        render_concept_ui_card(1, "🏢 CONCEPT 1", "concept-badge-1", "concept-stripe-1")
                        render_concept_ui_card(2, "🎬 CONCEPT 2", "concept-badge-2", "concept-stripe-2")
                        render_concept_ui_card(3, "📊 CONCEPT 3", "concept-badge-3", "concept-stripe-3")

        # 3. Media Manager (Assets)
        with preview_tabs[2]:
            with st.container():
                st.caption("Quản lý tài nguyên media của Workspace")
                
                # Upload ảnh mới
                uploaded_img = st.file_uploader("Tải lên hình ảnh mới cho bài đăng:", type=["png", "jpg", "jpeg"])
                if uploaded_img is not None:
                    if st.button("Lưu ảnh vào thư viện", key="save_uploaded_img_studio"):
                        import os
                        upload_dir = os.path.join(os.getcwd(), "uploads")
                        if not os.path.exists(upload_dir):
                            os.makedirs(upload_dir)
                        
                        file_path = os.path.join(upload_dir, uploaded_img.name)
                        with open(file_path, "wb") as f:
                            f.write(uploaded_img.getbuffer())
                            
                        AssetModel.create(
                            workspace_id=workspace_id,
                            name=uploaded_img.name,
                            url=file_path,
                            file_type="image",
                            size_bytes=uploaded_img.size
                        )
                        st.success("🖼️ Đã lưu hình ảnh vào Media Assets!")
                        st.rerun()

                # Hiển thị kho ảnh có sẵn
                st.write("##### Kho ảnh của Workspace")
                assets = AssetModel.list_by_workspace(workspace_id=workspace_id, file_type="image")
                
                if assets:
                    # Chia lưới ảnh
                    cols_assets = st.columns(3)
                    for idx, asset in enumerate(assets):
                        with cols_assets[idx % 3]:
                            st.markdown(f"""
                            <div class="media-card">
                                <div style="font-size:0.8rem;font-weight:bold;margin-bottom:4px;">{asset['name'][:12]}...</div>
                            </div>
                            """, unsafe_allow_html=True)
                            if st.button("Đính kèm", key=f"attach_img_{asset['id']}"):
                                st.session_state[media_attached_key] = asset['url']
                                st.session_state[media_attached_id_key] = asset['id']
                                st.success("🖼️ Đã đính kèm ảnh thành công vào bản xem trước!")
                                st.rerun()
                else:
                    st.info("Chưa có hình ảnh nào trong kho lưu trữ.")

        # 4. Version History
        with preview_tabs[3]:
            with st.container():
                st.caption("Quản lý các phiên bản chỉnh sửa của phiên làm việc hiện tại")
                v_list = st.session_state[versions_key]
                
                # --- Nút quay về bản gốc chưa chỉnh sửa ---
                original_content = st.session_state.get(original_content_key, "")
                if original_content:
                    st.info("📌 Bạn có thể quay lại nội dung gốc chưa chỉnh sửa bất kỳ lúc nào bằng nút bên dưới.")
                    col_orig_preview, col_orig_btn = st.columns([3, 1])
                    with col_orig_preview:
                        st.markdown("**🔒 Bản gốc (chưa chỉnh sửa)**")
                        st.caption(f"{original_content[:80]}...")
                    with col_orig_btn:
                        st.button(
                            "↩️ Về bản gốc",
                            key="restore_original_content",
                            type="primary",
                            use_container_width=True,
                            on_click=update_editor_state,
                            args=(original_content, None, None, "↩️ Đã khôi phục về nội dung gốc chưa chỉnh sửa!")
                        )
                    st.divider()
                
                if v_list:
                    st.markdown(f"**📋 Lịch sử chỉnh sửa** ({len(v_list)} phiên bản)")
                    for idx, v in enumerate(reversed(v_list)):
                        version_index = len(v_list) - idx
                        label = v.get('label', f'Phiên bản #{version_index}')
                        col_v_info, col_v_action = st.columns([3, 1])
                        with col_v_info:
                            st.markdown(f"**{label}** — *{v['time']}*")
                            preview_text = v['content'][:60] + '...' if len(v['content']) > 60 else v['content']
                            st.caption(preview_text)
                        with col_v_action:
                            st.button(
                                "Khôi phục",
                                key=f"restore_version_{version_index}_{workspace_id}",
                                use_container_width=True,
                                on_click=update_editor_state,
                                args=(v['content'], None, None, f"🔄 Đã khôi phục về {label}!")
                            )
                else:
                    if not original_content:
                        st.info("Chưa có lịch sử thay đổi phiên bản nào. Hãy sinh bài viết bằng AI hoặc tải một bài viết để bắt đầu.")

        # 5. AI Suggestions
        with preview_tabs[4]:
            with st.container():
                st.caption("AI phân tích nội dung hiện tại và gợi ý nâng cao")
                
                if st.button("💡 Phân tích & Gợi ý (Hashtags, CTA, Điểm Viral)", use_container_width=True, key="studio_ai_suggest_btn"):
                    if not st.session_state[editor_content_key]:
                        st.warning("Vui lòng điền nội dung vào Editor trước khi gợi ý!")
                    elif not gemini_key:
                        st.error("Vui lòng nhập API Key!")
                    else:
                        with st.spinner("AI đang phân tích..."):
                            prompt = f"""
                            Hãy phân tích nội dung bài đăng dưới đây và đưa ra:
                            1. 5 hashtag tối ưu cho {preview_platform}.
                            2. 3 tiêu đề/hook cuốn hút thay thế.
                            3. Nhận xét ngắn về điểm viral và mức độ thu hút.
                            
                            Bài đăng:
                            "{st.session_state[editor_content_key]}"
                            """
                            ai_res = generate_with_gemini(prompt, api_key=gemini_key)
                            st.session_state[ai_suggestions_key] = ai_res
                            st.rerun()
                
                if st.session_state[ai_suggestions_key]:
                    st.markdown("##### Gợi ý từ AI:")
                    st.write(st.session_state[ai_suggestions_key])

        # Lịch sử bài đăng cũ của Workspace
        st.divider()
        st.markdown("#### 📂 Lịch sử bài viết Workspace")
        df_hist = PostRepository.get_all_posts(workspace_id=workspace_id)
        if not df_hist.empty:
            st.dataframe(df_hist[['id', 'title', 'platform', 'status']], use_container_width=True, hide_index=True)
            selected_hist_idx = st.selectbox(
                "Chọn bài viết cũ để nạp lại vào Editor:",
                range(len(df_hist)),
                format_func=lambda x: f"ID {df_hist.iloc[x]['id']}: {df_hist.iloc[x]['title'][:40]}"
            )
            hist_row = df_hist.iloc[selected_hist_idx]
            st.button(
                "📥 Nạp lại bài viết này",
                use_container_width=True,
                on_click=update_editor_state,
                args=(hist_row['content'], hist_row['title'], hist_row['platform'].capitalize(), "📥 Đã nạp lại bài viết cũ vào Editor!")
            )
        else:
            st.caption("Chưa có lịch sử bài viết nào.")

