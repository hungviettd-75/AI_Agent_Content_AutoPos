import streamlit as st
import json
import pandas as pd
from services.gemini_client import generate_with_gemini, clean_ai_json_text
from database.models.posts import PostModel

_CAMPAIGN_CSS = """
<style>
.camp-header {
    background: linear-gradient(135deg, #ec4899 0%, #d946ef 50%, #86198f 100%);
    border-radius: 16px;
    padding: 1.5rem 2rem;
    margin-bottom: 1.8rem;
    color: white;
    text-align: center;
}
.camp-header h2 { color: white !important; margin: 0 0 0.3rem 0; font-size: 1.6rem; }
.camp-header p { color: rgba(255,255,255,0.85); margin: 0; font-size: 0.95rem; }

.section-box {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1.2rem;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
}
.email-box {
    background-color: #fdf2f8;
    border-left: 4px solid #db2777;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1rem;
}
</style>
"""

def generate_campaign_assets(prod_name: str, prod_desc: str, target: str, api_key: str):
    """Gọi Gemini để sinh cấu trúc chiến dịch."""
    prompt = f"""
    Bạn là một CMO & Lead Copywriter Agent chuyên nghiệp.
    Hãy lập kế hoạch chiến dịch tiếp thị 360 độ cho sản phẩm sau:
    - Tên sản phẩm/dịch vụ: "{prod_name}"
    - Mô tả sản phẩm: "{prod_desc}"
    - Đối tượng mục tiêu chính: "{target}"
    
    Hãy trả về một chuỗi JSON Object duy nhất chứa các thông tin sau:
    1. "lead_magnet": Chứa "title" (Tiêu đề), "concept" (Ý tưởng cốt lõi), "outline" (Dàn ý chi tiết gồm 3 phần).
    2. "landing_page": Chứa "headline" (Tiêu đề chính), "subheadline" (Tiêu đề phụ), "pain_points" (Mảng 3 nỗi đau của khách hàng), "solution" (Giải pháp sản phẩm đem lại), "cta" (Kêu gọi hành động).
    3. "emails": Mảng gồm 3 email bán hàng. Mỗi email có "subject" (Tiêu đề) và "body_outline" (Dàn ý/nội dung gợi ý email).
    4. "posts": Mảng gồm 30 bài viết mạng xã hội (tóm tắt ý tưởng). Mỗi bài có "day" (1 đến 30), "topic" (Chủ đề bài đăng), "platform" (facebook hoặc linkedin), "hook_angle" (Góc tiếp cận thu hút).
    5. "reels": Mảng gồm 15 kịch bản video ngắn/Reels. Mỗi Reels có "day" (1 đến 15), "title" (Tiêu đề video), "visual_hook" (Hình ảnh gây ấn tượng giây đầu).
    
    Lưu ý: Chỉ trả về chuỗi JSON thuan tuy, không bao gồm markdown block, không giải thích gì thêm.
    """
    
    raw_text = generate_with_gemini(prompt, api_key=api_key)
    clean_json = clean_ai_json_text(raw_text)
    
    try:
        data = json.loads(clean_json)
        return data
    except Exception as e:
        # Fallback repair prompt
        repair_prompt = f"""
        Sửa lỗi chuỗi text dưới đây thành định dạng JSON hợp lệ chứa các khoá: lead_magnet, landing_page, emails, posts, reels.
        
        Nội dung lỗi:
        {clean_json}
        """
        repaired_text = generate_with_gemini(repair_prompt, api_key=api_key)
        repaired = clean_ai_json_text(repaired_text)
        return json.loads(repaired)

def render_tab_campaign(gemini_key: str = "", workspace_id: int = 1, role: str = "editor"):
    st.markdown(_CAMPAIGN_CSS, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="camp-header">
        <h2>📢 Campaign Engine – Bộ Tài Liệu Tiếp Thị 360 Độ</h2>
        <p>Tự động tạo lập bộ tài liệu bán hàng hoàn chỉnh gồm Landing Page, Lead Magnet, Email và Lịch trình nội dung</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Form đầu vào
    with st.form("campaign_engine_form"):
        prod_name = st.text_input("📦 Tên Sản phẩm / Dịch vụ:", placeholder="Ví dụ: Khóa học lập trình Python thực chiến cho người mới")
        prod_desc = st.text_area("📝 Mô tả sản phẩm (Tính năng, lợi ích nổi bật):", placeholder="Ví dụ: Giúp người đi làm học Python từ số 0 để phân tích dữ liệu, tự động hóa công việc văn phòng trong 8 tuần")
        target_audience = st.text_input("🎯 Khách hàng mục tiêu chính:", placeholder="Ví dụ: Nhân viên văn phòng, kế toán, nhân sự muốn nâng cấp kỹ năng làm việc")
        
        btn_submit = st.form_submit_button("🚀 Sinh bộ tài liệu chiến dịch 360 độ", use_container_width=True)
        
    state_key = f"campaign_data_{workspace_id}"
    
    if btn_submit:
        if not prod_name or not prod_desc or not target_audience:
            st.warning("Vui lòng nhập đầy đủ thông tin sản phẩm và khách hàng!")
            return
        if not gemini_key:
            st.error("⚠️ Vui lòng nhập Gemini API Key ở thanh bên trái!")
            return
            
        with st.spinner("Campaign Engine đang thiết lập toàn bộ kế hoạch và sinh tài sản tiếp thị..."):
            try:
                data = generate_campaign_assets(prod_name, prod_desc, target_audience, gemini_key)
                st.session_state[state_key] = data
                st.success("🎉 Đã tạo thành công bộ tài liệu chiến dịch tiếp thị!")
            except Exception as e:
                st.error(f"Lỗi sinh tài liệu chiến dịch: {e}")
                
    campaign_data = st.session_state.get(state_key, None)
    
    if campaign_data:
        # Chia thành các sub-tabs
        sub_tabs = st.tabs([
            "🧲 Lead Magnet & Landing Page",
            "✉️ Email Marketing Sequence",
            "📱 30 Ngày Bài Viết",
            "🎬 15 Kịch Bản Reels"
        ])
        
        # Sub-tab 1: Lead Magnet & Landing Page
        with sub_tabs[0]:
            st.markdown("### 🧲 Tài liệu thu hút Lead (Lead Magnet)")
            lm = campaign_data.get("lead_magnet", {})
            st.markdown(f"""
            <div class="section-box">
                <h4>📌 Ý tưởng Lead Magnet: {lm.get('title', 'N/A')}</h4>
                <p><b>Khái niệm cốt lõi:</b> {lm.get('concept', 'N/A')}</p>
                <p><b>Dàn ý tài liệu đề xuất:</b></p>
                <ul>
                    {"".join(f"<li>{item}</li>" for item in lm.get('outline', []))}
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("### 📄 Nội dung Trang đích (Landing Page Copy)")
            lp = campaign_data.get("landing_page", {})
            
            pains_html = "".join(f"<li>{p}</li>" for p in lp.get('pain_points', []))
            st.markdown(f"""
            <div class="section-box">
                <h4 style="color:#ec4899;">📣 Headline: {lp.get('headline', 'N/A')}</h4>
                <h5>💡 Sub-headline: {lp.get('subheadline', 'N/A')}</h5>
                <p><b>Nỗi đau của khách hàng cần chạm tới:</b></p>
                <ul>{pains_html}</ul>
                <p><b>Giải pháp sản phẩm mang lại:</b> {lp.get('solution', 'N/A')}</p>
                <p><b>Nút kêu gọi hành động (CTA):</b> <span style="background-color:#ec4899; color:white; padding:4px 12px; border-radius:6px; font-weight:700;">{lp.get('cta', 'N/A')}</span></p>
            </div>
            """, unsafe_allow_html=True)
            
        # Sub-tab 2: Email Sequence
        with sub_tabs[1]:
            st.markdown("### ✉️ Chuỗi Email Marketing nuôi dưỡng")
            emails = campaign_data.get("emails", [])
            for idx, email in enumerate(emails, start=1):
                st.markdown(f"""
                <div class="email-box">
                    <h5>📧 Email {idx}: {email.get('subject', 'N/A')}</h5>
                    <p style="white-space: pre-wrap; font-size:0.9rem; color:#475569;">{email.get('body_outline', 'N/A')}</p>
                </div>
                """, unsafe_allow_html=True)
                
        # Sub-tab 3: 30 Bài viết
        with sub_tabs[2]:
            st.markdown("### 📱 Danh mục 30 ngày đăng bài mạng xã hội")
            posts = campaign_data.get("posts", [])
            
            df_posts = pd.DataFrame(posts)
            st.dataframe(df_posts, use_container_width=True, hide_index=True)
            
            st.write("")
            st.markdown("##### 🚀 Sinh nội dung chi tiết bài viết:")
            
            selected_day = st.selectbox("Chọn ngày muốn viết bài:", [f"Ngày {p['day']}: {p['topic']}" for p in posts])
            day_num = int(selected_day.split(":")[0].replace("Ngày ", ""))
            post_item = next(p for p in posts if p["day"] == day_num)
            
            if st.button("✍️ Tạo nội dung chi tiết bài đăng này", key="btn_gen_campaign_post"):
                with st.spinner("AI đang soạn thảo nội dung bài đăng chi tiết..."):
                    prompt = f"""
                    Viết một bài viết chi tiết cho mạng xã hội ({post_item['platform']}) dựa trên chủ đề: "{post_item['topic']}" và góc tiếp cận: "{post_item['hook_angle']}".
                    Hãy viết thật cuốn hút, có cấu trúc tốt, có hook hay và lời kêu gọi hành động (CTA) rõ ràng cho sản phẩm "{prod_name}".
                    """
                    post_content = generate_with_gemini(prompt, api_key=gemini_key)
                    st.session_state["campaign_post_temp"] = post_content
                    
            if "campaign_post_temp" in st.session_state:
                st.text_area("Nội dung bài viết chi tiết:", value=st.session_state["campaign_post_temp"], height=250)
                if st.button("💾 Lưu vào Kho Bản Nháp", key="btn_save_camp_post_db"):
                    # Lưu bài đăng vào database
                    post_id = PostModel.create(
                        content=st.session_state["campaign_post_temp"],
                        platform=post_item["platform"],
                        content_type="marketing_viral",
                        topic=post_item["topic"],
                        title=post_item["topic"][:60],
                        status="draft",
                        workspace_id=workspace_id
                    )
                    st.success(f"🎉 Đã lưu bài viết thành công vào Kho Bản Nháp (Post ID: `#{post_id}`)")
                    del st.session_state["campaign_post_temp"]
                    st.rerun()

        # Sub-tab 4: 15 Kịch bản Reels
        with sub_tabs[3]:
            st.markdown("### 🎬 Kịch bản 15 ngày video ngắn (Reels/TikTok)")
            reels = campaign_data.get("reels", [])
            
            df_reels = pd.DataFrame(reels)
            st.dataframe(df_reels, use_container_width=True, hide_index=True)
            
            st.write("")
            st.markdown("##### 🚀 Sinh kịch bản Reels chi tiết:")
            
            selected_reel = st.selectbox("Chọn ngày muốn viết kịch bản video:", [f"Ngày {r['day']}: {r['title']}" for r in reels])
            reel_num = int(selected_reel.split(":")[0].replace("Ngày ", ""))
            reel_item = next(r for r in reels if r["day"] == reel_num)
            
            if st.button("✍️ Tạo kịch bản chi tiết cho video này", key="btn_gen_campaign_reel"):
                with st.spinner("AI đang soạn thảo kịch bản phân cảnh chi tiết..."):
                    prompt = f"""
                    Viết một kịch bản phân cảnh video ngắn (Reels/TikTok) chi tiết dựa trên chủ đề: "{reel_item['title']}".
                    Khung cảnh mở đầu bắt buộc phải khớp với visual hook: "{reel_item['visual_hook']}".
                    
                    Yêu cầu cấu trúc kịch bản:
                    1. Hook (3 giây đầu): Visual & Audio.
                    2. Body: Gồm 3 phân cảnh chi tiết (Mô tả hình ảnh/Visual + Lời thoại/Voiceover).
                    3. Call to Action (CTA): Lời kêu gọi đăng ký/mua sản phẩm "{prod_name}".
                    """
                    reel_content = generate_with_gemini(prompt, api_key=gemini_key)
                    st.session_state["campaign_reel_temp"] = reel_content
                    
            if "campaign_reel_temp" in st.session_state:
                st.text_area("Kịch bản video chi tiết:", value=st.session_state["campaign_reel_temp"], height=250)
                if st.button("💾 Lưu kịch bản video vào Kho Bản Nháp", key="btn_save_camp_reel_db"):
                    # Lưu bài đăng vào database
                    post_id = PostModel.create(
                        content=st.session_state["campaign_reel_temp"],
                        platform="facebook",
                        content_type="reels",
                        topic=reel_item["title"],
                        title=reel_item["title"][:60],
                        status="draft",
                        workspace_id=workspace_id
                    )
                    st.success(f"🎉 Đã lưu kịch bản video thành công vào Kho Bản Nháp (Post ID: `#{post_id}`)")
                    del st.session_state["campaign_reel_temp"]
                    st.rerun()
    else:
        st.markdown("""
        <div style='text-align:center;padding:3rem 1rem;color:#94a3b8;'>
            <div style='font-size:3.5rem;margin-bottom:1rem;'>📢</div>
            <div style='font-size:1.1rem;font-weight:600;color:#64748b;margin-bottom:0.5rem;'>
                Chưa có chiến dịch tiếp thị nào được tạo
            </div>
            <div style='font-size:0.9rem;'>
                Nhập tên và mô tả sản phẩm của bạn ở biểu mẫu bên trên để bắt đầu sinh trọn bộ tài liệu 360 độ.
            </div>
        </div>
        """, unsafe_allow_html=True)
