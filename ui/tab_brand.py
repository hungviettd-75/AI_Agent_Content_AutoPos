"""ui/tab_brand.py
==================
Giao diện quản lý Brand Brain (Thương hiệu & Doanh nghiệp) của Workspace.
"""

import streamlit as st
import json
from database.models.brand import BrandModel
from database.models.companies import CompanyModel
from core.audit_logger import log_action
from core.rbac import render_role_badge
from config.logistics_vertical import LOGISTICS_BRAND_KEYWORDS, LOGISTICS_DEFAULT_CTA

TONE_OPTIONS = [
    "Chuyên nghiệp & Tin cậy (Professional & Trustworthy)",
    "Thân thiện & Gần gũi (Casual & Friendly)",
    "Hài hước & Dí dỏm (Humorous & Witty)",
    "Trang trọng & Lịch sự (Formal & Polite)",
    "Đột phá & Sáng tạo (Bold & Creative)",
    "Đồng cảm & Chia sẻ (Empathetic & Supportive)",
    "Khác (Tự nhập dưới đây...)"
]

def render_tab_brand(workspace_id: int, user_id: int, user_email: str, role: str):
    st.markdown(render_role_badge(role), unsafe_allow_html=True)
    st.header("🧠 Brand Brain — Bộ não Thương hiệu & Doanh nghiệp")
    st.caption("Cung cấp tri thức nền tảng về doanh nghiệp, sản phẩm, khách hàng mục tiêu và các nguyên tắc nhận diện thương hiệu để AI viết bài chuẩn xác.")

    if role == "viewer":
        st.warning("⚠️ Vai trò Viewer chỉ có quyền xem cấu hình, không thể chỉnh sửa.")
        disabled_fields = True
    else:
        disabled_fields = False

    # Lấy dữ liệu từ Database
    brand_data = BrandModel.get_by_workspace(workspace_id)
    company_data = CompanyModel.get_by_workspace(workspace_id)

    # 1. Chuẩn bị dữ liệu Doanh nghiệp (Company Memory)
    comp_name = company_data.get("name", "Công ty mặc định")
    comp_industry = company_data.get("industry", "")
    comp_website = company_data.get("website", "")
    comp_desc = company_data.get("description", "")
    comp_products = company_data.get("products", "")
    comp_customers = company_data.get("target_customers", "")

    # 2. Chuẩn bị dữ liệu Thương hiệu (Brand Profile)
    current_tone = brand_data.get("tone_of_voice", "Chuyên nghiệp & Tin cậy (Professional & Trustworthy)")
    current_cta = brand_data.get("cta", "")
    current_vision = brand_data.get("vision", "")
    current_mission = brand_data.get("mission", "")
    
    current_keywords_list = brand_data.get("keywords", [])
    if not isinstance(current_keywords_list, list):
        current_keywords_list = []
    current_keywords = ", ".join(current_keywords_list)
    
    current_forbidden_list = brand_data.get("blacklist_words", [])
    if not isinstance(current_forbidden_list, list):
        current_forbidden_list = []
    current_forbidden = ", ".join(current_forbidden_list)

    if not disabled_fields:
        with st.expander("🚚 Logistics Brand Preset", expanded=False):
            st.write("Cấu hình nhanh keyword và CTA cho doanh nghiệp Logistics: vận chuyển, fulfillment, SLA, last-mile, kho bãi và tối ưu chi phí.")
            if st.button("Áp dụng Brand Preset Logistics", use_container_width=True, key=f"brand_logistics_preset_{workspace_id}"):
                BrandModel.upsert(
                    workspace_id=workspace_id,
                    tone_of_voice="Chuyên nghiệp & Tin cậy (Professional & Trustworthy)",
                    cta=LOGISTICS_DEFAULT_CTA,
                    vision=current_vision,
                    mission=current_mission,
                    keywords=LOGISTICS_BRAND_KEYWORDS,
                    blacklist_words=current_forbidden_list,
                )
                log_action(
                    action="APPLY_LOGISTICS_BRAND_PRESET",
                    user_id=user_id,
                    user_email=user_email,
                    workspace_id=workspace_id,
                    entity_type="brand",
                    entity_id=brand_data.get("id"),
                    description="Áp dụng Logistics Brand Preset",
                )
                st.success("Đã áp dụng Brand Preset Logistics.")
                st.rerun()

    # Biểu mẫu chính
    with st.form("brand_brain_unified_form"):
        col_left, col_right = st.columns(2)
        
        # --- CỘT TRÁI: COMPANY MEMORY ---
        with col_left:
            st.markdown("### 🏢 Company Memory (Thông tin Doanh nghiệp)")
            
            c_name = st.text_input(
                "Tên doanh nghiệp:",
                value=comp_name,
                placeholder="Ví dụ: Công ty Công nghệ Hùng Việt AI",
                disabled=disabled_fields
            )
            
            c_industry = st.text_input(
                "Lĩnh vực hoạt động:",
                value=comp_industry,
                placeholder="Ví dụ: Cung cấp giải pháp phần mềm tự động hóa marketing",
                disabled=disabled_fields
            )
            
            c_website = st.text_input(
                "Địa chỉ Website:",
                value=comp_website,
                placeholder="Ví dụ: hungvietai.com",
                disabled=disabled_fields
            )
            
            c_desc = st.text_area(
                "Mô tả chi tiết về Doanh nghiệp:",
                value=comp_desc,
                placeholder="Ví dụ: Hùng Việt AI chuyên nghiên cứu ứng dụng AI vào tự động hóa bán hàng...",
                height=100,
                disabled=disabled_fields
            )
            
            c_products = st.text_area(
                "📦 Sản phẩm & Dịch vụ cốt lõi (Sản phẩm):",
                value=comp_products,
                placeholder="Ví dụ: \n- AI-Agent Content Auto-Post: Tự động lên lịch và tạo bài đăng lên MXH.\n- Chatbot chăm sóc khách hàng tự động.",
                height=120,
                disabled=disabled_fields,
                help="Liệt kê các sản phẩm chính và đặc điểm nổi bật để AI lồng ghép vào nội dung."
            )
            
            c_customers = st.text_area(
                "👥 Khách hàng mục tiêu (Khách hàng):",
                value=comp_customers,
                placeholder="Ví dụ: Các CEO doanh nghiệp vừa và nhỏ, Trưởng phòng Marketing, chủ cửa hàng online bán hàng đa kênh...",
                height=120,
                disabled=disabled_fields,
                help="Mô tả nhóm đối tượng khách hàng mục tiêu để AI hướng bài viết tới chính xác nhu cầu của họ."
            )

        # --- CỘT PHẢI: BRAND PROFILE ---
        with col_right:
            st.markdown("### 🎭 Brand Profile (Nhận diện Thương hiệu)")
            
            # Tone of Voice
            default_tone_idx = 0
            if current_tone in TONE_OPTIONS:
                default_tone_idx = TONE_OPTIONS.index(current_tone)
            else:
                if current_tone:
                    default_tone_idx = len(TONE_OPTIONS) - 1
                    
            selected_tone_opt = st.selectbox(
                "Giọng điệu thương hiệu (Tone of Voice):",
                options=TONE_OPTIONS,
                index=default_tone_idx,
                disabled=disabled_fields
            )
            
            if selected_tone_opt == "Khác (Tự nhập dưới đây...)":
                tone_val = st.text_input(
                    "Nhập giọng điệu tùy chỉnh:",
                    value=current_tone if current_tone not in TONE_OPTIONS else "",
                    placeholder="Ví dụ: Năng động, trẻ trung, dùng nhiều thuật ngữ công nghệ...",
                    disabled=disabled_fields
                )
            else:
                tone_val = selected_tone_opt

            vision = st.text_area(
                "👁️ Tầm nhìn (Vision):",
                value=current_vision,
                placeholder="Ví dụ: Trở thành cổng tự động hóa marketing AI tin cậy nhất...",
                height=80,
                disabled=disabled_fields
            )
            
            mission = st.text_area(
                "🚀 Sứ mệnh (Mission):",
                value=current_mission,
                placeholder="Ví dụ: Giải phóng thời gian sáng tạo nội dung cho nhà kinh doanh...",
                height=80,
                disabled=disabled_fields
            )
            
            cta = st.text_area(
                "📢 Lời kêu gọi hành động mặc định (CTA):",
                value=current_cta,
                placeholder="Ví dụ: Nhắn tin cho chúng tôi ngay hôm nay để nhận tư vấn giải pháp AI miễn phí!",
                height=110,
                disabled=disabled_fields
            )

            keywords_input = st.text_input(
                "🔑 Từ khóa khuyên dùng (Keywords):",
                value=current_keywords,
                placeholder="Ví dụ: AI Agent, tự động hóa, tăng trưởng doanh thu",
                disabled=disabled_fields,
                help="Phân cách bằng dấu phẩy."
            )
            
            forbidden_input = st.text_input(
                "🚫 Từ ngữ cấm sử dụng (Forbidden Words):",
                value=current_forbidden,
                placeholder="Ví dụ: cam đoan 100%, lừa đảo, duy nhất",
                disabled=disabled_fields,
                help="Phân cách bằng dấu phẩy."
            )

        st.markdown("<br>", unsafe_allow_html=True)
        
        # --- NÚT LƯU ---
        if not disabled_fields:
            btn_save = st.form_submit_button("💾 Lưu cấu hình Thương hiệu & Doanh nghiệp")
            if btn_save:
                # 1. Lưu Company Memory
                CompanyModel.upsert(
                    workspace_id=workspace_id,
                    name=c_name,
                    industry=c_industry,
                    website=c_website,
                    description=c_desc,
                    products=c_products,
                    target_customers=c_customers
                )

                # 2. Lưu Brand Profile
                keywords_list = [k.strip() for k in keywords_input.split(",") if k.strip()]
                forbidden_list = [f.strip() for f in forbidden_input.split(",") if f.strip()]
                
                brand_id = BrandModel.upsert(
                    workspace_id=workspace_id,
                    tone_of_voice=tone_val,
                    cta=cta,
                    vision=vision,
                    mission=mission,
                    keywords=keywords_list,
                    blacklist_words=forbidden_list
                )
                
                # Ghi Audit log
                log_action(
                    action="UPDATE_BRAND_UNIFIED",
                    user_id=user_id,
                    user_email=user_email,
                    workspace_id=workspace_id,
                    entity_type="brand_and_company",
                    entity_id=brand_id,
                    description="Cập nhật cấu hình hợp nhất Brand Brain và Company Memory.",
                    new_value={
                        "company": {
                            "name": c_name,
                            "industry": c_industry,
                            "website": c_website,
                            "description": c_desc,
                            "products": c_products,
                            "target_customers": c_customers
                        },
                        "brand": {
                            "tone_of_voice": tone_val,
                            "cta": cta,
                            "vision": vision,
                            "mission": mission,
                            "keywords": keywords_list,
                            "blacklist_words": forbidden_list
                        }
                    }
                )
                
                st.success("✅ Đã cập nhật cấu hình Thương hiệu & Doanh nghiệp thành công!")
                st.rerun()
        else:
            st.info("ℹ️ Bạn chỉ có quyền xem cấu hình.")

