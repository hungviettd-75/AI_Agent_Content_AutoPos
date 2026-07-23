import streamlit as st
import pandas as pd
from database.models.billing import BillingModel

# Khởi tạo bảng hóa đơn nếu chưa có
try:
    BillingModel.ensure_tables()
except Exception:
    pass


def render_tab_billing(gemini_key: str = "", workspace_id: int = 1, role: str = "editor"):

    # ── HEADER ──
    st.html("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        .bill-hdr {
            background: linear-gradient(135deg, #4f46e5 0%, #312e81 100%);
            border-radius: 16px; padding: 2rem; color: white;
            text-align: center; margin-bottom: 1.5rem;
            box-shadow: 0 10px 25px rgba(79,70,229,0.15);
            font-family: 'Inter', sans-serif;
        }
        .bill-title { color: #ffffff !important; filter: brightness(0) invert(1) !important; }
        .bill-hdr p, .bill-hdr p * { color: rgba(255,255,255,0.95) !important; margin: 0; font-size: 0.9rem; }
    </style>
    <div class="bill-hdr">
        <div style="display: flex; justify-content: center; align-items: center; gap: 8px; margin-bottom: 0.4rem;">
            <span style="font-size: 1.6rem;">💳</span>
            <p class="bill-title" style="font-weight: 800; font-size: 1.6rem; color: #ffffff !important; display: inline-block; margin: 0; filter: brightness(0) invert(1) !important;">Cổng Thanh Toán &amp; Quản Lý Gói Cước</p>
        </div>
        <p>Quản lý hạn mức sử dụng (Quota) · Đăng ký gói cước thành viên · Tải hóa đơn VAT giao dịch</p>
    </div>
    """)

    # Lấy thông tin plan hiện tại
    plan_info = BillingModel.get_workspace_plan_details(workspace_id)
    current_plan = plan_info["plan_code"]

    # ── PHẦN 1: QUOTA LIMIT MONITOR ──
    st.subheader("📊 Hạn Mức Sử Dụng Trong Tháng")
    quota = plan_info["quota"]
    quota_items = list(quota.items())

    # Build toàn bộ quota boxes thành 1 HTML block dùng CSS grid
    quota_html = """
    <style>
        .quota-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-bottom: 1.5rem; font-family: 'Inter', sans-serif; }
        .quota-box-w {
            background: #ffffff; border: 1px solid #e2e8f0;
            border-radius: 12px; padding: 1.2rem;
        }
        .q-lbl { display: flex; justify-content: space-between; font-size: 0.85rem; font-weight: 700; color: #1e293b; margin-bottom: 0.5rem; }
        .q-bg  { height: 8px; border-radius: 4px; background: #f1f5f9; overflow: hidden; margin-bottom: 0.3rem; }
        .q-fill { height: 100%; border-radius: 4px; background: linear-gradient(90deg, #4f46e5, #818cf8); }
        .q-fill.w { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
        .q-fill.d { background: linear-gradient(90deg, #ef4444, #f87171); }
        .q-pct { font-size: 0.72rem; color: #64748b; text-align: right; }
    </style>
    <div class="quota-grid">
    """
    label_map = {"users": "👥 Thành Viên Nhóm", "posts": "📝 Bài Đăng Xuất Bản", "tokens": "🤖 Tokens AI Tiêu Dùng"}
    unit_map  = {"users": "user", "posts": "bài", "tokens": "tokens"}
    for q_key, q_val in quota_items:
        used      = q_val["used"]
        max_limit = q_val["max"]
        pct       = min(1.0, used / max_limit) if max_limit > 0 else 0.0
        cls       = "d" if pct >= 0.9 else ("w" if pct >= 0.7 else "")
        lbl       = label_map.get(q_key, q_key)
        unit      = unit_map.get(q_key, "")
        quota_html += f"""
        <div class="quota-box-w">
            <div class="q-lbl"><span>{lbl}</span><span>{used:,} / {max_limit:,} {unit}</span></div>
            <div class="q-bg"><div class="q-fill {cls}" style="width:{pct*100:.1f}%"></div></div>
            <div class="q-pct">Đã sử dụng {pct*100:.1f}%</div>
        </div>"""
    quota_html += "</div>"
    st.html(quota_html)

    # ── PHẦN 2: CHOOSE PRICING PLAN ──
    st.subheader("💎 Các Gói Cước Dịch Vụ")

    plans_list = [
        ("free",   "Free Plan",   "$0",  ["Tối đa 3 thành viên", "Tối đa 30 bài đăng / tháng", "100K Tokens AI sử dụng", "Mạng xã hội cơ bản", "Hỗ trợ cộng đồng"]),
        ("pro",    "Pro Plan",    "$29", ["Tối đa 10 thành viên", "Tối đa 300 bài đăng / tháng", "2.0M Tokens AI sử dụng", "Kéo thả Workflow chuyên sâu", "A/B Testing & Learning Loop", "Hỗ trợ 24/7"]),
        ("agency", "Agency Plan", "$99", ["Tối đa 50 thành viên", "Lên tới 2000 bài đăng / tháng", "15.0M Tokens AI sử dụng", "Full Automation Webhook/CRM", "Mở khóa toàn bộ Agent cấp cao", "Quản lý nhiều Client / Brand"])
    ]

    # Render plan cards thành 1 HTML block dùng st.html()
    cards_html = """
    <style>
        .plan-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.2rem; margin-bottom: 1rem; font-family: 'Inter', sans-serif; }
        .pc {
            background: #ffffff; border: 1px solid #e2e8f0;
            border-radius: 16px; padding: 1.5rem; text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.04); position: relative;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .pc:hover { transform: translateY(-3px); box-shadow: 0 10px 25px rgba(79,70,229,0.1); border-color: #4f46e5; }
        .pc.active { border: 2px solid #4f46e5; background: #faf5ff; }
        .pc-badge {
            position: absolute; top: 12px; right: 12px;
            background: #4f46e5; color: white;
            font-size: 0.68rem; font-weight: 700;
            padding: 2px 10px; border-radius: 20px;
        }
        .pc-name  { font-size: 1.1rem; font-weight: 800; color: #1e293b; margin-bottom: 0.5rem; }
        .pc-price { font-size: 2.2rem; font-weight: 800; color: #0f172a; margin-bottom: 1rem; line-height: 1; }
        .pc-price span { font-size: 0.85rem; color: #64748b; font-weight: 500; }
        .pc-feats { list-style: none; padding: 0; margin: 1rem 0 0; font-size: 0.83rem; color: #475569; line-height: 1.9; text-align: left; }
        .pc-feats li::before { content: "✓  "; color: #10b981; font-weight: 700; }
    </style>
    <div class="plan-grid">
    """
    for p_code, p_name, p_price, p_feats in plans_list:
        is_active  = (p_code == current_plan)
        active_cls = "active" if is_active else ""
        badge      = '<div class="pc-badge">Gói hiện tại</div>' if is_active else ""
        feats      = "".join(f"<li>{f}</li>" for f in p_feats)
        cards_html += f"""
        <div class="pc {active_cls}">
            {badge}
            <div class="pc-name">{p_name}</div>
            <div class="pc-price">{p_price}<span> / tháng</span></div>
            <ul class="pc-feats">{feats}</ul>
        </div>"""
    cards_html += "</div>"
    st.html(cards_html)

    # Action buttons cho từng gói
    col_p1, col_p2, col_p3 = st.columns(3)
    for idx, (p_code, p_name, p_price, p_feats) in enumerate(plans_list):
        is_active = (p_code == current_plan)
        with [col_p1, col_p2, col_p3][idx]:
            if not is_active:
                if role in ["owner", "admin", "ceo", "super_admin"]:
                    if st.button(f"Nâng cấp lên {p_name}", key=f"btn_plan_{p_code}", use_container_width=True, type="primary"):
                        BillingModel.update_plan(workspace_id, p_code)
                        price_val = float(p_price.replace("$", ""))
                        BillingModel.create_invoice(workspace_id, p_name, price_val)
                        st.success(f"✅ Nâng cấp thành công lên {p_name}!")
                        st.rerun()
                else:
                    st.caption("_(Chỉ quản trị viên mới có quyền nâng cấp gói)_")
            else:
                st.button("Gói cước đang sử dụng 🟢", key=f"btn_plan_act_{p_code}", use_container_width=True, disabled=True)

    # ── PHẦN 3: INVOICE HISTORY ──
    st.subheader("📋 Lịch Sử Hóa Đơn & Thanh Toán")

    col_mock, _ = st.columns([1, 4])
    with col_mock:
        if st.button("🔄 Mock Lịch Sử Hóa Đơn", use_container_width=True):
            BillingModel.generate_mock_invoices(workspace_id, current_plan)
            st.rerun()

    invoices = BillingModel.get_invoices(workspace_id)
    if invoices:
        df_inv = pd.DataFrame(invoices)
        df_inv_disp = df_inv[["invoice_no", "plan", "amount", "payment_method", "billing_date", "status"]].copy()
        df_inv_disp.rename(columns={
            "invoice_no": "Mã hóa đơn", "plan": "Gói cước",
            "amount": "Số tiền ($)", "payment_method": "Phương thức thanh toán",
            "billing_date": "Ngày thanh toán", "status": "Trạng thái"
        }, inplace=True)
        st.dataframe(df_inv_disp, use_container_width=True, hide_index=True)
    else:
        st.info("Chưa có giao dịch hóa đơn nào phát sinh.")
