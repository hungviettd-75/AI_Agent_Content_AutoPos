import streamlit as st
import json
import pandas as pd
from database.models.companies import CompanyModel
from database.repositories import KnowledgeRepository
from database.models.knowledge import KnowledgeModel
from core.audit_logger import log_action
from config.logistics_vertical import LOGISTICS_COMPANY_SEED

_CORP_CSS = """
<style>
.corp-header {
    background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 50%, #1d4ed8 100%);
    border-radius: 16px;
    padding: 1.8rem;
    color: white;
    text-align: center;
    margin-bottom: 2rem;
    box-shadow: 0 10px 25px rgba(29, 78, 216, 0.15);
}
.corp-header h2 { color: white !important; margin: 0 0 0.4rem 0; font-weight: 800; font-size: 1.6rem; }
.corp-header p { color: rgba(255,255,255,0.85); margin: 0; font-size: 0.9rem; }

/* SOP Section styling */
.sop-box {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-left: 5px solid #3b82f6;
    border-radius: 12px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.8rem;
}
.sop-title { font-weight: 700; color: #0f172a; font-size: 0.95rem; }
.sop-meta { font-size: 0.75rem; color: #64748b; margin-top: 0.2rem; }
.sop-desc { font-size: 0.82rem; color: #475569; margin-top: 0.5rem; line-height: 1.5; }
</style>
"""

def render_tab_company_brain(workspace_id: int, user_id: int, user_email: str, role: str):
    st.markdown(_CORP_CSS, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="corp-header">
        <h2>🧠 Company Brain & SOP Center</h2>
        <p>Kho tri thức tích hợp về Sản phẩm · Khách hàng · Dự án · Chiến lược Marketing · Quy trình SOP</p>
    </div>
    """, unsafe_allow_html=True)

    # Đọc dữ liệu Company
    company_data = CompanyModel.get_by_workspace(workspace_id)
    comp_id = company_data.get("id")
    
    # ── PHẦN 1: CẤU HÌNH TÀI NGUYÊN CỦA DOANH NGHIỆP ──
    st.subheader("🏢 Hồ sơ Doanh nghiệp & Sản phẩm")
    
    # Giao diện sửa nếu không phải Viewer
    is_viewer = (role == "viewer")
    if not is_viewer:
        with st.expander("🚚 Logistics Growth Preset", expanded=False):
            st.write("Nạp nhanh hồ sơ ngành Logistics để AI viết đúng về vận chuyển, kho bãi, fulfillment, SLA, ROI và chăm sóc khách B2B/B2C.")
            if st.button("Nạp preset doanh nghiệp Logistics", use_container_width=True, key=f"company_logistics_preset_{workspace_id}"):
                CompanyModel.upsert(
                    workspace_id=workspace_id,
                    name=company_data.get("name", "Logistics Growth Company"),
                    industry=LOGISTICS_COMPANY_SEED["industry"],
                    website=company_data.get("website", ""),
                    size=company_data.get("size", "Medium (11-50)"),
                    description=LOGISTICS_COMPANY_SEED["description"],
                    products=LOGISTICS_COMPANY_SEED["products"],
                    target_customers=LOGISTICS_COMPANY_SEED["target_customers"],
                    marketing_strategy=LOGISTICS_COMPANY_SEED["marketing_strategy"],
                    sales_guideline=LOGISTICS_COMPANY_SEED["sales_guideline"],
                )
                log_action(
                    action="APPLY_LOGISTICS_COMPANY_PRESET",
                    user_id=user_id,
                    user_email=user_email,
                    workspace_id=workspace_id,
                    entity_type="company_brain",
                    entity_id=comp_id,
                    description="Nạp preset ngành Logistics cho Company Brain",
                )
                st.success("Đã nạp preset Logistics vào Company Brain.")
                st.rerun()
    
    with st.form("company_brain_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Tên doanh nghiệp:", value=company_data.get("name", ""), disabled=is_viewer)
            industry = st.text_input("Lĩnh vực hoạt động:", value=company_data.get("industry", ""), disabled=is_viewer)
            website = st.text_input("Địa chỉ website:", value=company_data.get("website", ""), disabled=is_viewer)
            size = st.selectbox("Quy mô nhân sự:", ["Small (1-10)", "Medium (11-50)", "Large (51+)"], index=0, disabled=is_viewer)
        with col2:
            description = st.text_area("Mô tả tổng quan doanh nghiệp:", value=company_data.get("description", ""), height=125, disabled=is_viewer)
            
        st.markdown("---")
        col_p, col_c = st.columns(2)
        with col_p:
            products = st.text_area("📦 Chi tiết Sản phẩm & Dịch vụ (Tính năng, Bảng giá, Lợi thế cạnh tranh):", 
                                    value=company_data.get("products", ""), height=150, disabled=is_viewer,
                                    placeholder="Mô tả cụ thể từng sản phẩm để AI viết bài trích xuất đúng tính năng...")
        with col_c:
            target_customers = st.text_area("👥 Chân dung Khách hàng mục tiêu (Pain Points, Hành vi mua sắm):", 
                                            value=company_data.get("target_customers", ""), height=150, disabled=is_viewer,
                                            placeholder="Khách hàng của bạn gặp khó khăn gì? Họ cần sản phẩm của bạn giải quyết việc gì?")

        st.markdown("---")
        col_m, col_s = st.columns(2)
        with col_m:
            marketing_strategy = st.text_area("📢 Chiến lược Marketing & Kênh truyền thông ưu tiên:", 
                                             value=company_data.get("marketing_strategy", "Kênh ưu tiên: Facebook, LinkedIn, Zalo OA"), height=120, disabled=is_viewer,
                                             placeholder="Ví dụ: Tập trung chia sẻ bài viết dạng AI Knowledge. Tần suất 3 bài/tuần...")
        with col_s:
            sales_guideline = st.text_area("🤝 Cẩm nang Bán hàng (Sales Pitch, Xử lý từ chối, FAQ):", 
                                          value=company_data.get("sales_guideline", "FAQ chính của khách hàng: Hỏi về bảng giá và cách cài đặt."), height=120, disabled=is_viewer,
                                          placeholder="Tập trung nêu các điểm chốt sale chính, giải pháp xử lý khi khách chê đắt...")
                                          
        if not is_viewer:
            btn_save = st.form_submit_button("💾 Cập nhật Company Brain")
            if btn_save:
                # Lưu thông tin
                CompanyModel.upsert(
                    workspace_id=workspace_id,
                    name=name,
                    industry=industry,
                    website=website,
                    size=size,
                    description=description,
                    products=products,
                    target_customers=target_customers,
                    marketing_strategy=marketing_strategy,
                    sales_guideline=sales_guideline
                )
                log_action(
                    action="UPDATE_COMPANY_BRAIN",
                    user_id=user_id,
                    user_email=user_email,
                    workspace_id=workspace_id,
                    entity_type="company_brain",
                    entity_id=comp_id,
                    description="Cập nhật thông tin chi tiết Company Brain"
                )
                st.success("✅ Đã lưu cấu hình Company Brain thành công!")
                st.rerun()

    # ── PHẦN 2: QUY TRÌNH SOP & HƯỚNG DẪN ──
    st.divider()
    st.subheader("📋 Quy trình SOP & Tài liệu vận hành nhóm")
    st.markdown("Quy trình chuẩn (Standard Operating Procedure - SOP) giúp định hình cấu trúc duyệt bài, xuất bản bài và phân phối công việc của Workspace.")
    
    # Lấy tài liệu tri thức thuộc loại SOP hoặc nằm trong Folder "SOP"
    raw_df = KnowledgeRepository.get_knowledge_posts(workspace_id=workspace_id)
    sop_df = pd.DataFrame()
    if not raw_df.empty:
        # Lọc các bài viết có tag 'sop' hoặc loại tài liệu chứa chữ 'sop' / 'quy trình'
        if "folder" in raw_df.columns:
            sop_df = raw_df[(raw_df["folder"].str.lower() == "sop") | (raw_df["knowledge_type"].str.contains("SOP|Quy trình", case=False))]
        else:
            sop_df = raw_df[raw_df["knowledge_type"].str.contains("SOP|Quy trình", case=False)]

    if not sop_df.empty:
        for idx, row in sop_df.iterrows():
            st.markdown(f"""
            <div class="sop-box">
                <div class="sop-title">📑 {row.get('title', row.get('topic'))}</div>
                <div class="sop-meta">Mã ID: #{row['id']} | Loại: {row.get('knowledge_type')} | Cập nhật: {row.get('date')}</div>
                <div class="sop-desc">{row.get('summary', '')}</div>
            </div>
            """, unsafe_allow_html=True)
            with st.expander("🔎 Xem tài liệu SOP đầy đủ"):
                st.text(row["content"])
    else:
        st.info("💡 Chưa có tài liệu quy trình SOP nào được thiết lập. Hãy truy cập tab **🧠 Knowledge Center**, tạo thư mục **SOP** và tải tài liệu quy trình vận hành lên!")

