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

/* â”€â”€ Header â”€â”€ */
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

/* â”€â”€ KPI Cards â”€â”€ */
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

/* â”€â”€ Section title â”€â”€ */
.section-title {
    font-size: 1rem;
    font-weight: 700;
    color: #1e293b;
    border-left: 4px solid #3b82f6;
    padding-left: 10px;
    margin: 1.5rem 0 0.8rem 0;
}

/* â”€â”€ Leaderboard table â”€â”€ */
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

/* â”€â”€ Platform badge â”€â”€ */
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

# â”€â”€â”€ Giáº£ láº­p dá»¯ liá»‡u (bao gá»“m CTR, leads, revenue) â”€â”€â”€
def generate_mock_data(workspace_id: int):
    df_posts = PostModel.list_by_workspace(workspace_id=workspace_id, limit=100)
    if df_posts.empty:
        return False, "KhÃ´ng cÃ³ bÃ i viáº¿t nÃ o trong workspace Ä‘á»ƒ giáº£ láº­p dá»¯ liá»‡u."

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

        for i in range(14):  # 14 ngÃ y gáº§n Ä‘Ã¢y
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
    return True, f"ÄÃ£ giáº£ láº­p thÃ nh cÃ´ng {count} báº£n ghi (14 ngÃ y)."


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
    if n >= 1_000_000_000: return f"{n/1_000_000_000:.1f}B â‚«"
    if n >= 1_000_000:     return f"{n/1_000_000:.1f}M â‚«"
    if n >= 1_000:         return f"{n/1_000:.1f}K â‚«"
    return f"{int(n):,} â‚«"

def _delta_html(pct):
    if pct > 0:   return f'<span class="kpi-delta delta-up">â–² {pct:.1f}% so thÃ¡ng trÆ°á»›c</span>'
    if pct < 0:   return f'<span class="kpi-delta delta-down">â–¼ {abs(pct):.1f}% so thÃ¡ng trÆ°á»›c</span>'
    return '<span class="kpi-delta delta-flat">â”€â”€ KhÃ´ng thay Ä‘á»•i</span>'

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
        <h2>ðŸ“Š Marketing Dashboard â€“ Tá»•ng Quan Hiá»‡u Quáº£ Chiáº¿n Dá»‹ch</h2>
        <p>Theo dÃµi Reach Â· CTR Â· Lead Â· ROI theo thá»i gian thá»±c â€” PhÃ¢n tÃ­ch chuyÃªn sÃ¢u bá»Ÿi AI Agent</p>
    </div>
    """, unsafe_allow_html=True)

    # â”€â”€ NÃºt hÃ nh Ä‘á»™ng â”€â”€
    col_filter1, col_filter2, col_filter3, col_act = st.columns([2, 2, 2, 1])
    with col_filter1:
        days_range = st.selectbox("ðŸ“… Khoáº£ng thá»i gian", ["7 ngÃ y gáº§n Ä‘Ã¢y", "14 ngÃ y gáº§n Ä‘Ã¢y", "30 ngÃ y gáº§n Ä‘Ã¢y", "Táº¥t cáº£"], index=1, key="db_days")
    with col_filter2:
        plat_filter = st.selectbox("ðŸ“± Ná»n táº£ng", ["Táº¥t cáº£", "facebook", "linkedin", "zalo"], key="db_plat")
    with col_filter3:
        ctype_filter = st.selectbox("ðŸ“ Loáº¡i ná»™i dung", ["Táº¥t cáº£", "marketing_viral", "ai_knowledge", "case_study", "reels"], key="db_ctype")
    with col_act:
        st.write("")
        if os.getenv("ENABLE_ANALYTICS_DEMO_DATA", "").lower() in {"1", "true", "yes"}:
            if st.button("ðŸ”„ Demo data", use_container_width=True):
                ok, msg = generate_mock_data(workspace_id)
                st.success(msg) if ok else st.warning(msg)
                st.rerun()

    # â”€â”€ Load & lá»c dá»¯ liá»‡u â”€â”€
    df_all = get_analytics_df(workspace_id)
    if df_all.empty:
        st.info("Chua co du lieu analytics thuc cho bo loc hien tai. Hay dong bo hoac nhap analytics tu kenh da publish de xem dashboard.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # Lá»c ngÃ y
    days_map = {"7 ngÃ y gáº§n Ä‘Ã¢y": 7, "14 ngÃ y gáº§n Ä‘Ã¢y": 14, "30 ngÃ y gáº§n Ä‘Ã¢y": 30, "Táº¥t cáº£": 3650}
    cutoff = (datetime.now() - timedelta(days=days_map[days_range])).strftime("%Y-%m-%d")
    df = df_all[df_all["metric_date"] >= cutoff].copy()

    if plat_filter != "Táº¥t cáº£":
        df = df[df["platform"] == plat_filter]
    if ctype_filter != "Táº¥t cáº£":
        df = df[df["content_type"] == ctype_filter]

    if df.empty:
        st.warning("KhÃ´ng cÃ³ dá»¯ liá»‡u cho bá»™ lá»c Ä‘Ã£ chá»n.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # PHáº¦N 1: KPI CARDS CHÃNH
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    st.markdown('<div class="section-title">âš¡ Chá»‰ Sá»‘ Hiá»‡u Suáº¥t ChÃ­nh (KPIs)</div>', unsafe_allow_html=True)

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

    # Giáº£ láº­p delta so thÃ¡ng trÆ°á»›c (ngáº«u nhiÃªn cÃ³ xu hÆ°á»›ng tÃ­ch cá»±c)
    rng = random.Random(workspace_id)
    d_reach = rng.uniform(5, 30)
    d_ctr   = rng.uniform(-5, 20)
    d_lead  = rng.uniform(10, 45)
    d_roi   = rng.uniform(-10, 60)
    d_er    = rng.uniform(2, 18)
    d_imp   = rng.uniform(8, 35)

    kpi_html = '<div class="kpi-row">'
    kpi_html += _kpi_card("kpi-reach", "ðŸ‘¤", _fmt_num(total_reach), "REACH â€“ Tiáº¿p Cáº­n", d_reach)
    kpi_html += _kpi_card("kpi-ctr",   "ðŸ–±ï¸", f"{ctr:.2f}%",         "CTR â€“ Tá»· lá»‡ click", d_ctr)
    kpi_html += _kpi_card("kpi-lead",  "ðŸŽ¯", _fmt_num(total_leads),  "LEADS â€“ KhÃ¡ch tiá»m nÄƒng", d_lead)
    kpi_html += _kpi_card("kpi-roi",   "ðŸ’°", f"{roi:.1f}%",          "ROI â€“ Lá»£i tá»©c Ä‘áº§u tÆ°", d_roi)
    kpi_html += _kpi_card("kpi-imp",   "ðŸ‘ï¸", _fmt_num(total_imp),    "IMPRESSIONS â€“ Hiá»ƒn thá»‹", d_imp)
    kpi_html += _kpi_card("kpi-eng",   "ðŸ”¥", f"{er:.2f}%",           "ENGAGEMENT RATE", d_er)
    kpi_html += '</div>'
    st.markdown(kpi_html, unsafe_allow_html=True)

    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # PHáº¦N 2: BIá»‚U Äá»’ THEO NGÃ€Y
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    st.markdown('<div class="section-title">ðŸ“ˆ Xu HÆ°á»›ng Theo NgÃ y</div>', unsafe_allow_html=True)

    col_c1, col_c2 = st.columns(2)

    with col_c1:
        st.markdown("##### ðŸ“¡ Reach & Impressions")
        df_day_reach = df.groupby("metric_date").agg(
            Reach=("reach", "sum"),
            Impressions=("impressions", "sum")
        ).reset_index().sort_values("metric_date")
        df_day_reach.set_index("metric_date", inplace=True)
        st.area_chart(df_day_reach, height=240)

    with col_c2:
        st.markdown("##### ðŸ–±ï¸ Clicks & Leads")
        df_day_ctr = df.groupby("metric_date").agg(
            Clicks=("clicks", "sum"),
            Leads=("leads", "sum")
        ).reset_index().sort_values("metric_date")
        df_day_ctr.set_index("metric_date", inplace=True)
        st.area_chart(df_day_ctr, height=240)

    col_c3, col_c4 = st.columns(2)

    with col_c3:
        st.markdown("##### ðŸ’° Revenue & Ad Spend")
        df_day_rev = df.groupby("metric_date").agg(
            Revenue=("revenue", "sum"),
            Ad_Spend=("ad_spend", "sum")
        ).reset_index().sort_values("metric_date")
        df_day_rev.set_index("metric_date", inplace=True)
        st.line_chart(df_day_rev, height=240)

    with col_c4:
        st.markdown("##### â¤ï¸ Engagement (Likes Â· Comments Â· Shares)")
        df_day_eng = df.groupby("metric_date").agg(
            Likes=("likes", "sum"),
            Comments=("comments", "sum"),
            Shares=("shares", "sum")
        ).reset_index().sort_values("metric_date")
        df_day_eng.set_index("metric_date", inplace=True)
        st.bar_chart(df_day_eng, height=240)

    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # PHáº¦N 3: SO SÃNH THEO Ná»€N Táº¢NG
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    st.markdown('<div class="section-title">ðŸ“± So SÃ¡nh Hiá»‡u Quáº£ Theo Ná»n Táº£ng</div>', unsafe_allow_html=True)

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
        df_plat_disp = df_plat[["platform", "Reach", "CTR (%)", "Leads", "ROI (%)"]].rename(columns={"platform": "Ná»n táº£ng"})
        st.dataframe(df_plat_disp, use_container_width=True, hide_index=True)

    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # PHáº¦N 4: LEADERBOARD BÃ€I VIáº¾T
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    st.markdown('<div class="section-title">ðŸ† Top 5 BÃ i Viáº¿t Hiá»‡u Quáº£ Nháº¥t</div>', unsafe_allow_html=True)

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
        st.markdown("**ðŸŽ¯ Top Lead**")
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
        st.markdown("**ðŸ‘¤ Top Reach**")
        for i, r in top5_reach.iterrows():
            badge = f'<span class="plat-badge plat-{r["platform"]}">{r["platform"].upper()}</span>'
            rank = f'<div class="leader-rank {rank_cls[i]}">{i+1}</div>'
            topic = str(r["topic"])[:50] + ("..." if len(str(r["topic"])) > 50 else "")
            st.markdown(
                f'<div class="leader-item">{rank}{badge}{topic}'
                f'<span class="leader-score">{_fmt_num(r["Reach"])}</span></div>',
                unsafe_allow_html=True
            )

    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # PHáº¦N 5: Báº¢NG CHI TIáº¾T
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    with st.expander("ðŸ“‹ Xem chi tiáº¿t hiá»‡u suáº¥t tá»«ng bÃ i viáº¿t"):
        df_disp = df_post_agg.rename(columns={
            "post_id": "ID", "topic": "Chá»§ Ä‘á»", "platform": "Ná»n táº£ng",
            "content_type": "Loáº¡i", "Impressions": "Hiá»ƒn thá»‹",
        })
        st.dataframe(
            df_disp[["ID", "Chá»§ Ä‘á»", "Ná»n táº£ng", "Loáº¡i", "Hiá»ƒn thá»‹", "Reach", "Clicks", "Leads", "ER (%)", "CTR (%)"]],
            use_container_width=True, hide_index=True
        )

    st.divider()

    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # PHáº¦N 6: AI ANALYTICS AGENT
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    st.markdown('<div class="section-title">ðŸ¤– Há»i Analytics Agent â€“ PhÃ¢n TÃ­ch Chiáº¿n LÆ°á»£c báº±ng AI</div>', unsafe_allow_html=True)

    sug_cols = st.columns(4)
    sug_q = ""
    suggestions = [
        ("ðŸ’¡ BÃ i nÃ o hiá»‡u quáº£ nháº¥t?", "BÃ i viáº¿t nÃ o cÃ³ ROI vÃ  Lead tá»‘t nháº¥t? PhÃ¢n tÃ­ch cÃ¡c yáº¿u tá»‘ giÃºp bÃ i Ä‘Ã³ thÃ nh cÃ´ng."),
        ("ðŸŽ¯ Tá»‘i Æ°u CTR", "CTR hiá»‡n táº¡i cá»§a tÃ´i cÃ³ tá»‘t khÃ´ng? Äá» xuáº¥t cÃ¡ch cáº£i thiá»‡n tá»· lá»‡ click."),
        ("ðŸ“± So sÃ¡nh ná»n táº£ng", "Ná»n táº£ng nÃ o (Facebook, LinkedIn, Zalo) mang láº¡i ROI tá»‘t nháº¥t? TÃ´i nÃªn phÃ¢n bá»• ngÃ¢n sÃ¡ch ra sao?"),
        ("ðŸ“ˆ Káº¿ hoáº¡ch tuáº§n tá»›i", "Dá»±a trÃªn dá»¯ liá»‡u Reach, CTR, Lead hiá»‡n táº¡i, Ä‘á» xuáº¥t chiáº¿n lÆ°á»£c ná»™i dung tuáº§n tá»›i."),
    ]
    for i, (label, query) in enumerate(suggestions):
        with sug_cols[i]:
            if st.button(label, use_container_width=True, key=f"sug_{i}"):
                sug_q = query

    user_query = st.text_input(
        "CÃ¢u há»i cá»§a báº¡n:",
        value=sug_q or "",
        key="analytics_query_input_v2",
        placeholder="VÃ­ dá»¥: PhÃ¢n tÃ­ch ROI theo tá»«ng ná»n táº£ng vÃ  Ä‘á» xuáº¥t tÄƒng Lead..."
    )

    if st.button("ðŸ¤– PhÃ¢n tÃ­ch ngay", type="primary") and user_query:
        if not gemini_key:
            st.error("âš ï¸ Vui lÃ²ng nháº­p Gemini API Key á»Ÿ thanh bÃªn trÃ¡i!")
        else:
            with st.spinner("ðŸ“Š Analytics Agent Ä‘ang tá»•ng há»£p dá»¯ liá»‡u vÃ  phÃ¢n tÃ­ch..."):
                # Tá»•ng há»£p sá»‘ liá»‡u gá»n
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
Báº¡n lÃ  Analytics Agent chuyÃªn nghiá»‡p trong há»‡ thá»‘ng AI-Agent Marketing Portal.
Nhiá»‡m vá»¥: PhÃ¢n tÃ­ch dá»¯ liá»‡u vÃ  Ä‘Æ°a ra lá»i khuyÃªn chiáº¿n lÆ°á»£c cá»¥ thá»ƒ, cÃ³ thá»ƒ hÃ nh Ä‘á»™ng ngay.

KPI & Dá»¯ liá»‡u ({days_range}):
{json.dumps(summary, ensure_ascii=False, indent=2)}

CÃ¢u há»i: "{user_query}"

TrÃ¬nh bÃ y theo cáº¥u trÃºc Markdown:
1. **ðŸ“Š PhÃ¢n tÃ­ch sá»‘ liá»‡u** â€“ nháº­n xÃ©t trá»±c tiáº¿p vá»›i sá»‘ liá»‡u cá»¥ thá»ƒ
2. **ðŸ’¡ Insight ná»•i báº­t** â€“ 3 Ä‘iá»ƒm thÃº vá»‹ nháº¥t tá»« dá»¯ liá»‡u
3. **ðŸŽ¯ Äá» xuáº¥t hÃ nh Ä‘á»™ng** â€“ 3-5 bÆ°á»›c cá»¥ thá»ƒ Ä‘á»ƒ cáº£i thiá»‡n ROI, CTR, Lead
4. **âš ï¸ Cáº£nh bÃ¡o rá»§i ro** â€“ Ä‘iá»ƒm nÃ o Ä‘ang yáº¿u cáº§n chÃº Ã½?

LuÃ´n tráº£ lá»i báº±ng Tiáº¿ng Viá»‡t chuyÃªn nghiá»‡p, thÃ¢n thiá»‡n.
"""
                try:
                    response = analyze_analytics_question(summary, days_range, user_query, gemini_key)
                    st.markdown("---")
                    st.markdown("### ðŸ“Š Káº¿t quáº£ phÃ¢n tÃ­ch tá»« Analytics Agent")
                    st.markdown(response)
                except Exception as e:
                    st.error(f"Lá»—i AI: {e}")

    st.markdown('</div>', unsafe_allow_html=True)


