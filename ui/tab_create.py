import streamlit as st
import pandas as pd
from datetime import datetime
from database.repositories import PostRepository, KnowledgeRepository
from social.publishers import post_to_facebook, post_to_zalo_oa, post_to_linkedin
from services.content_service import generate_marketing_or_knowledge_content
from core.doc_exporter import export_post_to_pdf, export_knowledge_to_pdf, export_knowledge_to_docx, export_knowledge_to_csv
from config.config import CONTENT_TYPES, AI_TOOLS, AI_AUDIENCES, AI_DIFFICULTIES, AI_KNOWLEDGE_TYPES
from core.rbac import CAN_AUTO_POST_ROLES, get_role_display, render_role_badge
from core.audit_logger import log_create_post, log_auto_post

def render_tab_create(gemini_key, fb_page_id, fb_access_token, zalo_access_token, linkedin_author_urn, linkedin_access_token, workspace_id, user_id, user_email="", role="editor"):
    role = (role or "editor").lower()
    
    # Xác định quyền hạn dựa theo role (lấy từ core/rbac)
    can_auto_post = role in CAN_AUTO_POST_ROLES
    role_meta = get_role_display(role)
    role_label = f"{role_meta['icon']} {role_meta['label']}"
    role_color = role_meta["color"]

    # Hiển thị badge role
    st.markdown(render_role_badge(role), unsafe_allow_html=True)

    if role == "viewer":
        st.warning("⚠️ Tài khoản của bạn có quyền Người xem (Viewer) tại Workspace này. Bạn không có quyền tạo hoặc đăng bài viết mới.")
        return

    with st.form("content_form"):
        col1, col2 = st.columns(2)
        with col1:
            platform = st.selectbox("Chọn nền tảng muốn đăng", ["Facebook", "Zalo OA", "LinkedIn", "Tất cả"])
            content_type = st.selectbox("Loại nội dung", CONTENT_TYPES)

            # Đọc topic gợi ý từ Trend Agent (nếu có)
            _trend_topic = st.session_state.pop("trend_topic", "")
            if _trend_topic:
                st.info(f"🔥 Chủ đề từ Trend Agent: **{_trend_topic}**")
            topic = st.text_area(
                "Chủ đề bài viết",
                value=_trend_topic,
                placeholder="Ví dụ: Lợi ích của AI-Agent trong bán hàng..."
            )
        with col2:
            target = st.selectbox("Đối tượng mục tiêu (Audience Selection)", [
                "CEO (Chiến lược, Tăng trưởng, Lợi nhuận)",
                "Sales (Chốt sale, Khách hàng, Doanh số)",
                "Chủ Shop (Đơn hàng, Marketing, Quảng cáo)",
                "Freelancer (Thương hiệu cá nhân, Thu nhập, Khách hàng)",
                "Chuyên gia AI (AI Agent, Automation, Công nghệ)",
                "Nhà đầu tư (Xu hướng, ROI, Cơ hội)"
            ])
            angle_selection = st.selectbox("Góc nhìn bài viết (Angle Selection)", [
                "Tự động chọn (Tối ưu nhất)",
                "Góc sai lầm phổ biến",
                "Góc câu chuyện thực tế",
                "Góc trải nghiệm cá nhân",
                "Góc tranh luận",
                "Góc xu hướng",
                "Góc hướng dẫn",
                "Góc case study",
                "Sinh trọn bộ 7 bài (Multi-Angle)"
            ])
            
            if not can_auto_post:
                auto_post = st.checkbox(
                    "Tự động đăng bài sau khi tạo",
                    value=False,
                    disabled=True,
                    help=f"Vai trò **{role_label}** không được phép tự động đăng bài lên mạng xã hội."
                )
            else:
                auto_post = st.checkbox("Tự động đăng bài sau khi tạo", value=False)

        st.markdown("---")
        st.markdown("### AI Knowledge Sharing")
        st.caption("Cấu hình này dùng khi chọn loại nội dung AI Knowledge Sharing.")
        ai_col1, ai_col2 = st.columns(2)
        with ai_col1:
            ai_tool = st.selectbox("AI Tool", AI_TOOLS)
            ai_audience = st.selectbox("Audience", AI_AUDIENCES)
        with ai_col2:
            ai_difficulty = st.selectbox("Difficulty", AI_DIFFICULTIES)
            ai_knowledge_type = st.selectbox("Knowledge Type", AI_KNOWLEDGE_TYPES)
            
        submit = st.form_submit_button("Bắt đầu xử lý ✨")

        # Research Agent toggle (nằm trong form nhưng được render cuối cùng để nổi bật)
        st.markdown("---")
        st.markdown("### 🔍 Research Agent (Tìm kiếm Internet)")
        enable_research = st.checkbox(
            "🌐 Kích hoạt Research Agent (Để AI tự động tìm kiếm dữ liệu thực tế trước khi viết)",
            value=False,
            key="enable_research_checkbox",
            help="Áp dụng Google Search Grounding trực tiếp vào Gemini API. Giúp AI có thông tin mới nhất, số liệu thực tế và xu hướng hiện tại khi tạo nội dung."
        )
        if enable_research:
            st.info("📊 Research Agent đang bật - AI sẽ tự tìm kiếm Google để lấy thông tin mới nhất.")

        if submit and topic:
            st.session_state['last_topic'] = topic
            st.session_state['last_content_type'] = content_type
            if not gemini_key:
                st.error("Vui lòng nhập API Key!")
            else:
                spinner_text = f"🔍 Research Agent đang tìm kiếm & viết nội dung {content_type}..." if enable_research else f"AI đang tạo nội dung {content_type}..."
                with st.spinner(spinner_text):
                    try:
                        # Gọi qua Service Layer
                        result = generate_marketing_or_knowledge_content(
                            platform=platform,
                            content_type=content_type,
                            topic=topic,
                            target=target,
                            angle_selection=angle_selection,
                            ai_tool=ai_tool,
                            ai_audience=ai_audience,
                            ai_difficulty=ai_difficulty,
                            ai_knowledge_type=ai_knowledge_type,
                            api_key=gemini_key,
                            workspace_id=workspace_id,
                            enable_research=enable_research
                        )
                        
                        content = result["content"]
                        st.session_state['current_content'] = content
                        st.session_state['current_image_prompt'] = result["illustration_prompt"]
                        st.session_state['chat_history'] = [
                            {"role": "user", "content": f"Tạo bài viết với chủ đề: {topic}"},
                            {"role": "model", "content": content}
                        ]
                        # ── VIE HOOK: Lưu nội dung bài viết để Thumbnail Studio dùng ──
                        # Tự động điền bài viết vào VIE input của Thumbnail Studio
                        st.session_state['vie_article_cache'] = content
                        st.session_state['vie_article_ready'] = True
                        
                        if content_type == "AI Knowledge Sharing":
                            st.session_state['current_knowledge_metadata'] = {
                                "id": "current",
                                "date": datetime.now().strftime("%d/%m/%Y %H:%M"),
                                "platform": platform,
                                "topic": topic,
                                "audience": ai_audience,
                                "tool_name": ai_tool,
                                "knowledge_type": ai_knowledge_type,
                                "difficulty": ai_difficulty,
                                "summary": result["summary"],
                                "status": "Bản nháp hiện tại",
                                "content": content,
                            }
                            
                        db_status = "Đã tạo bản nháp"
                        
                        # Xử lý tự động đăng bài
                        if auto_post:
                            status_msg = ""
                            success_any = False
                            if platform in ["Facebook", "Tất cả"]:
                                success, msg = post_to_facebook(content, fb_page_id, fb_access_token)
                                status_msg += f"FB: {msg} | "
                                if success: success_any = True
                            if platform in ["Zalo OA", "Tất cả"]:
                                success, msg = post_to_zalo_oa(content, zalo_access_token)
                                status_msg += f"Zalo: {msg} | "
                                if success: success_any = True
                            if platform in ["LinkedIn", "Tất cả"]:
                                success, msg = post_to_linkedin(content, linkedin_author_urn, linkedin_access_token)
                                status_msg += f"LinkedIn: {msg}"
                                if success: success_any = True
                                
                            st.session_state['last_post_status'] = status_msg
                            if success_any:
                                db_status = "Đã đăng"
                                log_auto_post(  # ★ AUDIT
                                    user_id=user_id, user_email=user_email,
                                    workspace_id=workspace_id, platform=platform,
                                    topic=topic, status=status_msg[:120]
                                )
                        else:
                            st.session_state['last_post_status'] = None

                        # Lưu vào cơ sở dữ liệu
                        post_date = datetime.now().strftime("%d/%m/%Y %H:%M")
                        PostRepository.add_post(
                            date=post_date,
                            platform=platform,
                            topic=topic,
                            content=content,
                            status=db_status,
                            content_type=content_type,
                            workspace_id=workspace_id,
                            created_by=user_id
                        )

                        if content_type == "AI Knowledge Sharing":
                            KnowledgeRepository.save_knowledge_post(
                                date=post_date,
                                platform=platform,
                                topic=topic,
                                audience=ai_audience,
                                tool_name=ai_tool,
                                knowledge_type=ai_knowledge_type,
                                difficulty=ai_difficulty,
                                content=content,
                                status=db_status,
                                workspace_id=workspace_id,
                                created_by=user_id
                            )
                        # ★ AUDIT: Ghi log sau khi lưu DB
                        log_create_post(
                            user_id=user_id, user_email=user_email,
                            workspace_id=workspace_id, platform=platform,
                            topic=topic
                        )
                    except Exception as e:
                        if "429" in str(e):
                            st.error("🚫 Hết hạn mức API (Quota Exceeded). Vui lòng thử lại sau vài phút.")
                        else:
                            st.error(f"Lỗi khi xử lý: {e}")

    # Hiển thị kết quả sinh bài viết
    if 'current_content' in st.session_state:
        st.success("✨ Đã tạo nội dung bài đăng xong!")
        st.text_area(
            "Nội dung bài viết đã tạo",
            value=st.session_state['current_content'],
            height=650,
            key="generated_content_output"
        )
        
    if st.session_state.get('current_image_prompt'):
        st.subheader("🎨 Thumbnail AI — Visual Intelligence Engine")
        
        # VIE Ready notification
        if st.session_state.get('vie_article_ready'):
            st.success(
                "✅ **Visual Intelligence Engine đã sẵn sàng!** "
                "Bài viết đã được tự động đưa vào Thumbnail Studio. "
                "Chuyển sang tab **🎨 Thumbnail Studio** → mục **Visual Intelligence** để AI phân tích toàn bài và tạo ảnh chất lượng cao."
            )
            st.info(
                "💡 VIE sẽ:\n"
                "1. Đọc và hiểu toàn bộ nội dung bài viết\n"
                "2. Phân tích Visual Story (theme, emotion, metaphor...)\n"
                "3. Sinh Image Prompt chất lượng cao cho Midjourney / DALL-E / FLUX\n"
                "4. Tự kiểm tra Vision Score và sửa nếu chưa đạt ngưỡng"
            )
        
        # Hiển thị prompt gợi ý cũ (giữ nguyên tính năng cũ)
        with st.expander("📋 Prompt ảnh minh họa đơn giản (classic — tham khảo)"):
            st.caption("Prompt truyền thống từ tiêu đề. Để có prompt chất lượng cao hơn, hãy dùng Visual Intelligence Engine ở Thumbnail Studio.")
            st.text_area(
                "Prompt ảnh minh họa (classic)",
                value=st.session_state['current_image_prompt'],
                height=200,
                key="generated_image_prompt_output"
            )
        
    if 'last_post_status' in st.session_state and st.session_state['last_post_status']:
        st.info(st.session_state['last_post_status'])
        
    if 'current_content' in st.session_state:
        st.divider()
        if st.session_state.get('last_content_type') == "AI Knowledge Sharing":
            from database.connection import build_content_summary
            current_knowledge = st.session_state.get('current_knowledge_metadata', {
                "id": "current",
                "date": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "platform": platform,
                "topic": st.session_state.get('last_topic', 'AI Knowledge'),
                "audience": "",
                "tool_name": "",
                "knowledge_type": "",
                "difficulty": "",
                "summary": build_content_summary(st.session_state['current_content']),
                "status": "Bản nháp hiện tại",
                "content": st.session_state['current_content'],
            })
            col_current_pdf, col_current_docx, col_current_csv = st.columns([1, 1, 1])
            with col_current_pdf:
                current_pdf = export_knowledge_to_pdf(current_knowledge)
                if current_pdf:
                    st.download_button("Tải AI Knowledge PDF", data=current_pdf, file_name="AI_Knowledge_Current.pdf", mime="application/pdf", key="current_ai_knowledge_pdf")
            with col_current_docx:
                current_docx = export_knowledge_to_docx(current_knowledge)
                if current_docx:
                    st.download_button("Tải AI Knowledge DOCX", data=current_docx, file_name="AI_Knowledge_Current.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", key="current_ai_knowledge_docx")
            with col_current_csv:
                current_csv_df = pd.DataFrame([current_knowledge])
                st.download_button("Tải AI Knowledge CSV", data=export_knowledge_to_csv(current_csv_df), file_name="AI_Knowledge_Current.csv", mime="text/csv", key="current_ai_knowledge_csv")
        else:
            pdf_bytes = export_post_to_pdf(
                st.session_state.get('last_topic', 'Bài viết mới'),
                platform,
                st.session_state['current_content'],
                st.session_state.get('current_image_prompt', '')
            )
            if pdf_bytes:
                st.download_button("📩 Tải bài viết này (PDF)", data=pdf_bytes, file_name="Bai_Viet_AI.pdf", mime="application/pdf", key="current_marketing_pdf")

    # --- CONVERSATION MEMORY CHAT PANEL ---
    if 'current_content' in st.session_state:
        st.divider()
        st.subheader("💬 Tinh chỉnh bài viết (Conversation Memory)")
        st.caption("Gõ yêu cầu của bạn bên dưới để trò chuyện và yêu cầu AI chỉnh sửa lại bài viết (ví dụ: 'viết ngắn lại', 'thêm emoji', 'đổi góc nhìn thành...', 'lồng thêm ý X'...)")
        
        # Hiển thị lịch sử chat trong container cuộn được
        chat_container = st.container()
        with chat_container:
            for msg in st.session_state.get('chat_history', []):
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])
                    
        # Nhận tin nhắn mới từ người dùng
        user_input = st.chat_input("Nhập yêu cầu tinh chỉnh bài viết tại đây...", key="brand_voice_chat_input")
        if user_input:
            # Lưu tin nhắn người dùng vào history
            st.session_state['chat_history'].append({"role": "user", "content": user_input})
            
            with st.spinner("Đang tinh chỉnh bài viết theo yêu cầu..."):
                try:
                    from database.models.brand import BrandModel
                    from database.models.companies import CompanyModel
                    from services.chat_service import refine_content_with_history
                    
                    brand_profile = BrandModel.get_by_workspace(workspace_id)
                    company_profile = CompanyModel.get_by_workspace(workspace_id)
                    
                    refined_text = refine_content_with_history(
                        chat_history=st.session_state['chat_history'][:-1],
                        user_instruction=user_input,
                        brand_profile=brand_profile,
                        api_key=gemini_key,
                        company_profile=company_profile
                    )
                    
                    if refined_text:
                        st.session_state['current_content'] = refined_text
                        st.session_state['chat_history'].append({"role": "model", "content": refined_text})
                        
                        # Cập nhật metadata nếu là bài viết tri thức
                        if st.session_state.get('last_content_type') == "AI Knowledge Sharing" and 'current_knowledge_metadata' in st.session_state:
                            st.session_state['current_knowledge_metadata']['content'] = refined_text
                            from database.connection import build_content_summary
                            st.session_state['current_knowledge_metadata']['summary'] = build_content_summary(refined_text)
                            
                        st.rerun()
                except Exception as e:
                    st.error(f"Lỗi khi tinh chỉnh bài viết: {e}")
