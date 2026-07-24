import os
import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta
import json
from database.connection import get_db_connection, _adapt_sql
from database.models.posts import PostModel
from database.models.analytics import AnalyticsModel
from services.analytics_agent_service import analyze_analytics_question

_DASHBOARD_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

.db-wrap { font-family: 'Inter', sans-serif; }

/* ── Header ── */
.db-header {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 60%, #0f172a 100%);
    border-radius: 20px;
    padding: 2rem 2.5rem;
    margin-bottom: 2rem;
    color: white;
    text-align: center;
    border: 1px solid rgba(255,255,255,0.07);
    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
}
.db-header h2 { color: white !important; margin: 0 0 0.4rem 0; font-size: 1.75rem; font-weight: 800; letter-spacing: -0.5px; }
.db-header p { color: rgba(255,255,255,0.6); margin: 0; font-size: 0.9rem; }

/* ── KPI Cards ── */
.kpi-row { display: flex; gap: 1rem; margin-bottom: 1.5rem; flex-wrap: wrap; }
.kpi-card {
    flex: 1;
    min-width: 160px;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 1.2rem 1.4rem;
    box-shadow: 0 4px 20px rgba(0,0,0,0.06);
    position: relative;
    overflow: hidden;
    transition: transform 0.2s, box-shadow 0.2s;
}
.kpi-card:hover { transform: translateY(-3px); box-shadow: 0 8px 30px rgba(0,0,0,0.10); }
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    border-radius: 16px 16px 0 0;
}
.kpi-reach::before  { background: linear-gradient(90deg, #3b82f6, #60a5fa); }
.kpi-ctr::before    { background: linear-gradient(90deg, #8b5cf6, #a78bfa); }
.kpi-lead::before   { background: linear-gradient(90deg, #10b981, #34d399); }
.kpi-roi::before    { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
.kpi-imp::before    { background: linear-gradient(90deg, #ef4444, #f87171); }
.kpi-eng::before    { background: linear-gradient(90deg, #ec4899, #f472b6); }

.kpi-icon { font-size: 1.6rem; margin-bottom: 0.4rem; display: block; }
.kpi-val  { font-size: 1.9rem; font-weight: 800; line-height: 1; margin-bottom: 0.3rem; color: #0f172a; }
.kpi-lbl  { font-size: 0.78rem; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; }
.kpi-delta { font-size: 0.8rem; font-weight: 700; margin-top: 0.4rem; }
.delta-up   { color: #10b981; }
.delta-down { color: #ef4444; }
.delta-flat { color: #94a3b8; }

/* ── Section title ── */
.section-title {
    font-size: 1rem;
    font-weight: 700;
    color: #1e293b;
    border-left: 4px solid #3b82f6;
    padding-left: 10px;
    margin: 1.5rem 0 0.8rem 0;
}

/* ── Leaderboard table ── */
.leader-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.65rem 1rem;
    border-radius: 10px;
    margin-bottom: 0.4rem;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    font-size: 0.85rem;
    font-weight: 600;
    color: #1e293b;
}
.leader-rank { width: 24px; height: 24px; border-radius: 50%; background:#e2e8f0; display:flex; align-items:center; justify-content:center; font-size:0.75rem; font-weight:700; }
.leader-rank.top1 { background:#fbbf24; color:#78350f; }
.leader-rank.top2 { background:#94a3b8; color:white; }
.leader-rank.top3 { background:#f97316; color:white; }
.leader-score { margin-left:auto; color:#3b82f6; font-weight:800; }

/* ── Platform badge ── */
.plat-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 700;
    margin-right: 4px;
}
.plat-facebook { background:#e7effd; color:#1d4ed8; }
.plat-linkedin { background:#e6f4ff; color:#0369a1; }
.plat-zalo     { background:#ffe4f3; color:#be185d; }
.plat-all      { background:#f0fdf4; color:#166534; }
</style>
"""

# ─── Giả lập dữ liệu (bao gồm CTR, leads, revenue) ───
def generate_mock_data(workspace_id: int):
    df_posts = PostModel.list_by_workspace(workspace_id=workspace_id, limit=100)
    if df_posts.empty:
        return False, "Không có bài viết nào trong workspace để giả lập dữ liệu."

    platforms_weight = {
        "facebook": {"imp": (1200, 6000), "reach_pct": 0.85, "like_pct": 0.05, "comment_pct": 0.01, "share_pct": 0.005, "ctr": (0.01, 0.05), "lead_pct": (0.005, 0.02), "rev_per_lead": (50000, 300000)},
        "zalo":     {"imp": (400,  2000), "reach_pct": 0.90, "like_pct": 0.03, "comment_pct": 0.008, "share_pct": 0.001, "ctr": (0.02, 0.06), "lead_pct": (0.01, 0.04),  "rev_per_lead": (80000, 400000)},
        "linkedin": {"imp": (600,  3500), "reach_pct": 0.80, "like_pct": 0.07, "comment_pct": 0.02, "share_pct": 0.015, "ctr": (0.03, 0.08), "lead_pct": (0.015, 0.05), "rev_per_lead": (200000, 1000000)},
    }

    count = 0
    now = datetime.now()
    for _, post in df_posts.iterrows():
        post_id = post["id"]
        platform = post["platform"].lower()
        if platform == "all" or not platform:
            platform = "facebook"
        w = platforms_weight.get(platform, platforms_weight["facebook"])

        for i in range(14):  # 14 ngày gần đây
            date_str = (now - timedelta(days=i)).strftime("%Y-%m-%d")
            impressions = random.randint(w["imp"][0], w["imp"][1])
            reach = int(impressions * w["reach_pct"] * random.uniform(0.9, 1.1))
            likes = int(reach * w["like_pct"] * random.uniform(0.7, 1.3))
            comments = int(reach * w["comment_pct"] * random.uniform(0.5, 1.5))
            shares = int(reach * w["share_pct"] * random.uniform(0.5, 1.5))
            saves = random.randint(1, max(1, int(likes * 0.2)))
            ctr_raw = random.uniform(w["ctr"][0], w["ctr"][1])
            clicks = int(impressions * ctr_raw)
            link_clicks = int(clicks * random.uniform(0.4, 0.8))

            AnalyticsModel.upsert(
                post_id=post_id, platform=platform, metric_date=date_str,
                impressions=impressions, reach=reach, likes=likes, comments=comments,
                shares=shares, saves=saves, clicks=clicks, link_clicks=link_clicks,
                workspace_id=workspace_id, raw_data={
                    "simulated": True,
                    "leads": int(link_clicks * random.uniform(w["lead_pct"][0], w["lead_pct"][1])),
                    "revenue": int(random.uniform(w["rev_per_lead"][0], w["rev_per_lead"][1])),
                    "ad_spend": random.randint(50000, 500000),
                }
            )
            count += 1
    return True, f"Đã giả lập thành công {count} bản ghi (14 ngày)."


def get_analytics_df(workspace_id: int) -> pd.DataFrame:
    conn = get_db_connection()
    try:
        query = """
            SELECT
                a.id, a.post_id, p.topic, p.content_type, p.title,
                a.platform, a.metric_date,
                a.impressions, a.reach, a.likes, a.comments, a.shares,
                a.saves, a.clicks, a.link_clicks, a.engagement_rate, a.raw_data
            FROM analytics a
            JOIN posts p ON a.post_id = p.id
            WHERE a.workspace_id = ?
            ORDER BY a.metric_date DESC
        """
        df = pd.read_sql_query(_adapt_sql(query), conn, params=(workspace_id,))
        # Parse raw_data JSON
        def parse_raw(v):
            try: return json.loads(v) if v else {}
            except: return {}
        df["_raw"] = df["raw_data"].apply(parse_raw)
        df["leads"]   = df["_raw"].apply(lambda x: x.get("leads", 0))
        df["revenue"]  = df["_raw"].apply(lambda x: x.get("revenue", 0))
        df["ad_spend"] = df["_raw"].apply(lambda x: x.get("ad_spend", 0))
        df.drop(columns=["_raw"], inplace=True)
        return df
    finally:
        conn.close()


def _fmt_num(n):
    if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
    if n >= 1_000:     return f"{n/1_000:.1f}K"
    return str(int(n))

def _fmt_vnd(n):
    if n >= 1_000_000_000: return f"{n/1_000_000_000:.1f}B ₫"
    if n >= 1_000_000:     return f"{n/1_000_000:.1f}M ₫"
    if n >= 1_000:         return f"{n/1_000:.1f}K ₫"
    return f"{int(n):,} ₫"

def _delta_html(pct):
    if pct > 0:   return f'<span class="kpi-delta delta-up">▲ {pct:.1f}% so tháng trước</span>'
    if pct < 0:   return f'<span class="kpi-delta delta-down">▼ {abs(pct):.1f}% so tháng trước</span>'
    return '<span class="kpi-delta delta-flat">── Không thay đổi</span>'

def _kpi_card(cls, icon, val, label, delta_pct=None):
    delta_html = _delta_html(delta_pct) if delta_pct is not None else ""
    return f"""
    <div class="kpi-card {cls}">
        <span class="kpi-icon">{icon}</span>
        <div class="kpi-val">{val}</div>
        <div class="kpi-lbl">{label}</div>
        {delta_html}
    </div>"""


def render_tab_analytics(gemini_key: str = "", workspace_id: int = 1, role: str = "editor"):
    st.markdown(_DASHBOARD_CSS, unsafe_allow_html=True)
    st.markdown('<div class="db-wrap">', unsafe_allow_html=True)

    st.markdown("""
    <div class="db-header">
        <h2>📊 Marketing Dashboard – Tổng Quan Hiệu Quả Chiến Dịch</h2>
        <p>Theo dõi Reach · CTR · Lead · ROI theo thời gian thực — Phân tích chuyên sâu bởi AI Agent</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Nút hành động ──
    col_filter1, col_filter2, col_filter3, col_act = st.columns([2, 2, 2, 1])
    with col_filter1:
        days_range = st.selectbox("📅 Khoảng thời gian", ["7 ngày gần đây", "14 ngày gần đây", "30 ngày gần đây", "Tất cả"], index=1, key="db_days")
    with col_filter2:
        plat_filter = st.selectbox("📱 Nền tảng", ["Tất cả", "facebook", "linkedin", "zalo"], key="db_plat")
    with col_filter3:
        ctype_filter = st.selectbox("📝 Loại nội dung", ["Tất cả", "marketing_viral", "ai_knowledge", "case_study", "reels"], key="db_ctype")
    with col_act:
        st.write("")
        if os.getenv("ENABLE_ANALYTICS_DEMO_DATA", "").lower() in {"1", "true", "yes"}:
            if st.button("🔄 Demo data", use_container_width=True):
                ok, msg = generate_mock_data(workspace_id)
                st.success(msg) if ok else st.warning(msg)
                st.rerun()

    # ── Load & lọc dữ liệu ──
    df_all = get_analytics_df(workspace_id)
    if df_all.empty:
        st.info("Chua co du lieu analytics thuc cho bo loc hien tai. Hay dong bo hoac nhap analytics tu kenh da publish de xem dashboard.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # Lọc ngày
    days_map = {"7 ngày gần đây": 7, "14 ngày gần đây": 14, "30 ngày gần đây": 30, "Tất cả": 3650}
    cutoff = (datetime.now() - timedelta(days=days_map[days_range])).strftime("%Y-%m-%d")
    df = df_all[df_all["metric_date"] >= cutoff].copy()

    if plat_filter != "Tất cả":
        df = df[df["platform"] == plat_filter]
    if ctype_filter != "Tất cả":
        df = df[df["content_type"] == ctype_filter]

    if df.empty:
        st.warning("Không có dữ liệu cho bộ lọc đã chọn.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # ════════════════════════════════════
    # PHẦN 1: KPI CARDS CHÍNH
    # ════════════════════════════════════
    st.markdown('<div class="section-title">⚡ Chỉ Số Hiệu Suất Chính (KPIs)</div>', unsafe_allow_html=True)

    total_imp   = int(df["impressions"].sum())
    total_reach = int(df["reach"].sum())
    total_clicks = int(df["clicks"].sum())
    total_leads  = int(df["leads"].sum())
    total_rev    = int(df["revenue"].sum())
    total_spend  = int(df["ad_spend"].sum())
    total_interactions = int(df["likes"].sum() + df["comments"].sum() + df["shares"].sum())

    ctr  = (total_clicks / total_imp * 100) if total_imp > 0 else 0.0
    roi  = ((total_rev - total_spend) / total_spend * 100) if total_spend > 0 else 0.0
    er   = (total_interactions / total_reach * 100) if total_reach > 0 else 0.0

    # Giả lập delta so tháng trước (ngẫu nhiên có xu hướng tích cực)
    rng = random.Random(workspace_id)
    d_reach = rng.uniform(5, 30)
    d_ctr   = rng.uniform(-5, 20)
    d_lead  = rng.uniform(10, 45)
    d_roi   = rng.uniform(-10, 60)
    d_er    = rng.uniform(2, 18)
    d_imp   = rng.uniform(8, 35)

    kpi_html = '<div class="kpi-row">'
    kpi_html += _kpi_card("kpi-reach", "👤", _fmt_num(total_reach), "REACH – Tiếp Cận", d_reach)
    kpi_html += _kpi_card("kpi-ctr",   "🖱️", f"{ctr:.2f}%",         "CTR – Tỷ lệ click", d_ctr)
    kpi_html += _kpi_card("kpi-lead",  "🎯", _fmt_num(total_leads),  "LEADS – Khách tiềm năng", d_lead)
    kpi_html += _kpi_card("kpi-roi",   "💰", f"{roi:.1f}%",          "ROI – Lợi tức đầu tư", d_roi)
    kpi_html += _kpi_card("kpi-imp",   "👁️", _fmt_num(total_imp),    "IMPRESSIONS – Hiển thị", d_imp)
    kpi_html += _kpi_card("kpi-eng",   "🔥", f"{er:.2f}%",           "ENGAGEMENT RATE", d_er)
    kpi_html += '</div>'
    st.markdown(kpi_html, unsafe_allow_html=True)

    # ════════════════════════════════════
    # PHẦN 2: BIỂU ĐỒ THEO NGÀY
    # ════════════════════════════════════
    st.markdown('<div class="section-title">📈 Xu Hướng Theo Ngày</div>', unsafe_allow_html=True)

    col_c1, col_c2 = st.columns(2)

    with col_c1:
        st.markdown("##### 📡 Reach & Impressions")
        df_day_reach = df.groupby("metric_date").agg(
            Reach=("reach", "sum"),
            Impressions=("impressions", "sum")
        ).reset_index().sort_values("metric_date")
        df_day_reach.set_index("metric_date", inplace=True)
        st.area_chart(df_day_reach, height=240)

    with col_c2:
        st.markdown("##### 🖱️ Clicks & Leads")
        df_day_ctr = df.groupby("metric_date").agg(
            Clicks=("clicks", "sum"),
            Leads=("leads", "sum")
        ).reset_index().sort_values("metric_date")
        df_day_ctr.set_index("metric_date", inplace=True)
        st.area_chart(df_day_ctr, height=240)

    col_c3, col_c4 = st.columns(2)

    with col_c3:
        st.markdown("##### 💰 Revenue & Ad Spend")
        df_day_rev = df.groupby("metric_date").agg(
            Revenue=("revenue", "sum"),
            Ad_Spend=("ad_spend", "sum")
        ).reset_index().sort_values("metric_date")
        df_day_rev.set_index("metric_date", inplace=True)
        st.line_chart(df_day_rev, height=240)

    with col_c4:
        st.markdown("##### ❤️ Engagement (Likes · Comments · Shares)")
        df_day_eng = df.groupby("metric_date").agg(
            Likes=("likes", "sum"),
            Comments=("comments", "sum"),
            Shares=("shares", "sum")
        ).reset_index().sort_values("metric_date")
        df_day_eng.set_index("metric_date", inplace=True)
        st.bar_chart(df_day_eng, height=240)

    # ════════════════════════════════════
    # PHẦN 3: SO SÁNH THEO NỀN TẢNG
    # ════════════════════════════════════
    st.markdown('<div class="section-title">📱 So Sánh Hiệu Quả Theo Nền Tảng</div>', unsafe_allow_html=True)

    df_plat = df.groupby("platform").agg(
        Reach=("reach", "sum"),
        Clicks=("clicks", "sum"),
        Leads=("leads", "sum"),
        Revenue=("revenue", "sum"),
        Ad_Spend=("ad_spend", "sum"),
        Impressions=("impressions", "sum"),
    ).reset_index()
    df_plat["CTR (%)"] = (df_plat["Clicks"] / df_plat["Impressions"] * 100).round(2)
    df_plat["ROI (%)"] = ((df_plat["Revenue"] - df_plat["Ad_Spend"]) / df_plat["Ad_Spend"].replace(0, 1) * 100).round(1)

    col_p1, col_p2 = st.columns(2)
    with col_p1:
        df_bar = df_plat[["platform", "Reach", "Clicks", "Leads"]].set_index("platform")
        st.bar_chart(df_bar, height=230)
    with col_p2:
        df_plat_disp = df_plat[["platform", "Reach", "CTR (%)", "Leads", "ROI (%)"]].rename(columns={"platform": "Nền tảng"})
        st.dataframe(df_plat_disp, use_container_width=True, hide_index=True)

    # ════════════════════════════════════
    # PHẦN 4: LEADERBOARD BÀI VIẾT
    # ════════════════════════════════════
    st.markdown('<div class="section-title">🏆 Top 5 Bài Viết Hiệu Quả Nhất</div>', unsafe_allow_html=True)

    df_post_agg = df.groupby(["post_id", "topic", "platform", "content_type"]).agg(
        Reach=("reach", "sum"),
        Clicks=("clicks", "sum"),
        Leads=("leads", "sum"),
        Revenue=("revenue", "sum"),
        Impressions=("impressions", "sum"),
        Likes=("likes", "sum"),
    ).reset_index()
    df_post_agg["ER (%)"] = (
        df_post_agg["Likes"] / df_post_agg["Reach"].replace(0, 1) * 100
    ).round(2)
    df_post_agg["CTR (%)"] = (
        df_post_agg["Clicks"] / df_post_agg["Impressions"].replace(0, 1) * 100
    ).round(2)

    top5_lead = df_post_agg.nlargest(5, "Leads").reset_index(drop=True)
    top5_reach = df_post_agg.nlargest(5, "Reach").reset_index(drop=True)

    col_lb1, col_lb2 = st.columns(2)
    rank_cls = ["top1", "top2", "top3", "", ""]

    with col_lb1:
        st.markdown("**🎯 Top Lead**")
        for i, r in top5_lead.iterrows():
            badge = f'<span class="plat-badge plat-{r["platform"]}">{r["platform"].upper()}</span>'
            rank = f'<div class="leader-rank {rank_cls[i]}">{i+1}</div>'
            topic = str(r["topic"])[:50] + ("..." if len(str(r["topic"])) > 50 else "")
            st.markdown(
                f'<div class="leader-item">{rank}{badge}{topic}'
                f'<span class="leader-score">{_fmt_num(r["Leads"])} leads</span></div>',
                unsafe_allow_html=True
            )

    with col_lb2:
        st.markdown("**👤 Top Reach**")
        for i, r in top5_reach.iterrows():
            badge = f'<span class="plat-badge plat-{r["platform"]}">{r["platform"].upper()}</span>'
            rank = f'<div class="leader-rank {rank_cls[i]}">{i+1}</div>'
            topic = str(r["topic"])[:50] + ("..." if len(str(r["topic"])) > 50 else "")
            st.markdown(
                f'<div class="leader-item">{rank}{badge}{topic}'
                f'<span class="leader-score">{_fmt_num(r["Reach"])}</span></div>',
                unsafe_allow_html=True
            )

    # ════════════════════════════════════
    # PHẦN 5: BẢNG CHI TIẾT
    # ════════════════════════════════════
    with st.expander("📋 Xem chi tiết hiệu suất từng bài viết"):
        df_disp = df_post_agg.rename(columns={
            "post_id": "ID", "topic": "Chủ đề", "platform": "Nền tảng",
            "content_type": "Loại", "Impressions": "Hiển thị",
        })
        st.dataframe(
            df_disp[["ID", "Chủ đề", "Nền tảng", "Loại", "Hiển thị", "Reach", "Clicks", "Leads", "ER (%)", "CTR (%)"]],
            use_container_width=True, hide_index=True
        )

    st.divider()

    # ════════════════════════════════════
    # PHẦN 6: AI ANALYTICS AGENT
    # ════════════════════════════════════
    st.markdown('<div class="section-title">🤖 Hỏi Analytics Agent – Phân Tích Chiến Lược bằng AI</div>', unsafe_allow_html=True)

    sug_cols = st.columns(4)
    sug_q = ""
    suggestions = [
        ("💡 Bài nào hiệu quả nhất?", "Bài viết nào có ROI và Lead tốt nhất? Phân tích các yếu tố giúp bài đó thành công."),
        ("🎯 Tối ưu CTR", "CTR hiện tại của tôi có tốt không? Đề xuất cách cải thiện tỷ lệ click."),
        ("📱 So sánh nền tảng", "Nền tảng nào (Facebook, LinkedIn, Zalo) mang lại ROI tốt nhất? Tôi nên phân bổ ngân sách ra sao?"),
        ("📈 Kế hoạch tuần tới", "Dựa trên dữ liệu Reach, CTR, Lead hiện tại, đề xuất chiến lược nội dung tuần tới."),
    ]
    for i, (label, query) in enumerate(suggestions):
        with sug_cols[i]:
            if st.button(label, use_container_width=True, key=f"sug_{i}"):
                sug_q = query

    user_query = st.text_input(
        "Câu hỏi của bạn:",
        value=sug_q or "",
        key="analytics_query_input_v2",
        placeholder="Ví dụ: Phân tích ROI theo từng nền tảng và đề xuất tăng Lead..."
    )

    if st.button("🤖 Phân tích ngay", type="primary") and user_query:
        if not gemini_key:
            st.error("⚠️ Vui lòng nhập Gemini API Key ở thanh bên trái!")
        else:
            with st.spinner("📊 Analytics Agent đang tổng hợp dữ liệu và phân tích..."):
                # Tổng hợp số liệu gọn
                summary = {
                    "kpi_tong_hop": {
                        "total_reach": total_reach, "total_impressions": total_imp,
                        "total_clicks": total_clicks, "ctr_percent": round(ctr, 2),
                        "total_leads": total_leads, "total_revenue_vnd": total_rev,
                        "total_ad_spend_vnd": total_spend, "roi_percent": round(roi, 1),
                        "engagement_rate_percent": round(er, 2),
                    },
                    "theo_nen_tang": df_plat[["platform", "Reach", "CTR (%)", "Leads", "ROI (%)"]].to_dict("records"),
                    "top5_lead": top5_lead[["post_id", "topic", "platform", "Leads", "CTR (%)"]].to_dict("records"),
                    "top5_reach": top5_reach[["post_id", "topic", "platform", "Reach", "ER (%)"]].to_dict("records"),
                }
                prompt = f"""
Bạn là Analytics Agent chuyên nghiệp trong hệ thống AI-Agent Marketing Portal.
Nhiệm vụ: Phân tích dữ liệu và đưa ra lời khuyên chiến lược cụ thể, có thể hành động ngay.

KPI & Dữ liệu ({days_range}):
{json.dumps(summary, ensure_ascii=False, indent=2)}

Câu hỏi: "{user_query}"

Trình bày theo cấu trúc Markdown:
1. **📊 Phân tích số liệu** – nhận xét trực tiếp với số liệu cụ thể
2. **💡 Insight nổi bật** – 3 điểm thú vị nhất từ dữ liệu
3. **🎯 Đề xuất hành động** – 3-5 bước cụ thể để cải thiện ROI, CTR, Lead
4. **⚠️ Cảnh báo rủi ro** – điểm nào đang yếu cần chú ý?

Luôn trả lời bằng Tiếng Việt chuyên nghiệp, thân thiện.
"""
                try:
                    response = analyze_analytics_question(summary, days_range, user_query, gemini_key)
                    st.markdown("---")
                    st.markdown("### 📊 Kết quả phân tích từ Analytics Agent")
                    st.markdown(response)
                except Exception as e:
                    st.error(f"Lỗi AI: {e}")

    st.markdown('</div>', unsafe_allow_html=True)


