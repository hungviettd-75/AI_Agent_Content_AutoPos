import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from database.connection import get_db_connection
from database.models.ai_cost import AICostModel

# Khởi tạo bảng nếu chưa tồn tại
try:
    AICostModel.ensure_table()
except Exception:
    pass

_COST_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

.cost-header {
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    border-radius: 16px;
    padding: 2rem 2.5rem;
    margin-bottom: 2rem;
    color: white;
    text-align: center;
    border: 1px solid rgba(255, 255, 255, 0.05);
    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
}
.cost-header h2 { color: white !important; margin: 0 0 0.4rem 0; font-size: 1.6rem; font-weight: 800; }
.cost-header p { color: rgba(255,255,255,0.7); margin: 0; font-size: 0.9rem; }

/* Dashboard Cards */
.cost-card-row { display: flex; gap: 1rem; margin-bottom: 1.5rem; flex-wrap: wrap; }
.cost-card {
    flex: 1;
    min-width: 150px;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1.1rem 1.3rem;
    box-shadow: 0 2px 10px rgba(0,0,0,0.03);
    position: relative;
    overflow: hidden;
}
.cost-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
}
.c-blue::before   { background: #3b82f6; }
.c-purple::before { background: #8b5cf6; }
.c-green::before  { background: #10b981; }
.c-amber::before  { background: #f59e0b; }

.c-val  { font-size: 1.7rem; font-weight: 800; color: #0f172a; margin-top: 0.3rem; }
.c-lbl  { font-size: 0.75rem; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; }

/* Brand Colors */
.br-gemini   { color: #1a73e8; font-weight: 700; }
.br-claude   { color: #d97706; font-weight: 700; }
.br-gpt      { color: #10b981; font-weight: 700; }
</style>
"""

def render_tab_ai_cost(gemini_key: str = "", workspace_id: int = 1, role: str = "editor"):
    st.markdown(_COST_CSS, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="cost-header">
        <h2>💰 AI Cost Center & Token Monitor</h2>
        <p>Giám sát tổng chi phí thực tế • Lưu lượng Token tiêu thụ • Độ trễ (Latency) theo từng nhà cung cấp</p>
    </div>
    """, unsafe_allow_html=True)

    # Controls
    col_f1, col_f2, col_btn = st.columns([2, 2, 1])
    with col_f1:
        days = st.selectbox("📅 Bộ lọc thời gian", ["7 ngày qua", "15 ngày qua", "30 ngày qua", "Tất cả"], index=2, key="cc_days")
        days_val = {"7 ngày qua": 7, "15 ngày qua": 15, "30 ngày qua": 30, "Tất cả": 3650}[days]
    with col_f2:
        provider_filter = st.selectbox("🤖 Nhà cung cấp", ["Tất cả", "Gemini", "Claude", "GPT"], key="cc_provider")
    with col_btn:
        st.write("")
        if st.button("🔄 Demo Cost Data", use_container_width=True):
            count = AICostModel.generate_mock_data(workspace_id)
            st.success(f"Đã giả lập thành công {count} bản ghi chi phí!")
            st.rerun()

    # Load Logs
    raw_logs = AICostModel.get_summary(workspace_id, days=days_val)
    if not raw_logs:
        st.info("💡 Chưa có ghi nhận sử dụng AI nào trong Database của Workspace này. Hãy nhấn **🔄 Demo Cost Data** để trải nghiệm giao diện!")
        return

    df = pd.DataFrame(raw_logs)
    
    # Filter
    if provider_filter != "Tất cả":
        df = df[df["provider"] == provider_filter]

    if df.empty:
        st.warning("Không tìm thấy dữ liệu phù hợp với bộ lọc.")
        return

    # Tính toán chỉ số
    total_cost = float(df["cost"].sum())
    total_tokens = int(df["total_tokens"].sum())
    avg_latency = float(df["latency_ms"].mean())
    total_calls = len(df)
    
    # Render KPI Cards
    st.markdown('<div class="cost-card-row">', unsafe_allow_html=True)
    st.markdown(f'<div class="cost-card c-green"><div class="c-lbl">Tổng Chi Phí</div><div class="c-val">${total_cost:.4f} USD</div></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="cost-card c-blue"><div class="c-lbl">Tổng Tokens Tiêu Thụ</div><div class="c-val">{total_tokens:,}</div></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="cost-card c-purple"><div class="c-lbl">Độ Trễ Trung Bình</div><div class="c-val">{avg_latency:.0f} ms</div></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="cost-card c-amber"><div class="c-lbl">Số Cuộc Gọi API</div><div class="c-val">{total_calls:,}</div></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Biểu đồ phân tích ──
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.markdown("##### 📈 Chi Phí Tích Lũy Theo Ngày ($ USD)")
        df["date_only"] = df["created_at"].apply(lambda x: x[:10])
        df_date_cost = df.groupby("date_only")["cost"].sum().reset_index().sort_values("date_only")
        df_date_cost.set_index("date_only", inplace=True)
        st.area_chart(df_date_cost, height=220)

    with col_chart2:
        st.markdown("##### ⏱️ Phân Bố Độ Trễ Latency Theo Tính Năng (ms)")
        df_feat_lat = df.groupby("feature")["latency_ms"].mean().reset_index()
        df_feat_lat.set_index("feature", inplace=True)
        st.bar_chart(df_feat_lat, height=220)

    # ── So sánh các Provider ──
    st.markdown("### 📊 So sánh Hiệu Quả & Chi Phí")
    df_prov = df.groupby("provider").agg(
        Calls=("id", "count"),
        Total_Tokens=("total_tokens", "sum"),
        Total_Cost=("cost", "sum"),
        Avg_Latency=("latency_ms", "mean")
    ).reset_index()
    
    df_prov["Chi phí trên 1M Tokens ($)"] = (df_prov["Total_Cost"] / df_prov["Total_Tokens"] * 1_000_000).round(2)
    df_prov["Avg_Latency"] = df_prov["Avg_Latency"].round(0)
    df_prov["Total_Cost"] = df_prov["Total_Cost"].round(4)
    
    col_t1, col_t2 = st.columns([1, 1])
    with col_t1:
        st.markdown("**Bảng tổng hợp theo Provider:**")
        st.dataframe(df_prov, use_container_width=True, hide_index=True)
    with col_t2:
        st.markdown("**Tỷ Lệ Tiêu Thụ Token Giữa Các Hãng:**")
        df_pie = df_prov.set_index("provider")[["Total_Tokens"]]
        st.bar_chart(df_pie, height=180)

    # ── Bảng nhật ký API ──
    with st.expander("📋 Nhật Ký Cuộc Gọi API Chi Tiết (Mới Nhất)"):
        df_disp = df[["created_at", "provider", "model_name", "feature", "prompt_tokens", "completion_tokens", "latency_ms", "cost"]].copy()
        df_disp.rename(columns={
            "created_at": "Thời gian", "provider": "Hãng", "model_name": "Model",
            "feature": "Tính năng", "prompt_tokens": "Prompt Tok", "completion_tokens": "Comp Tok",
            "latency_ms": "Độ trễ (ms)", "cost": "Chi phí ($)"
        }, inplace=True)
        st.dataframe(df_disp, use_container_width=True, hide_index=True)
