import streamlit as st
from services.trend_service import analyze_trends, NICHES, TREND_PLATFORMS


# ── CSS nội bộ cho card xu hướng ──────────────────────────────────────────────
_TREND_CSS = """
<style>
/* Card xu hướng */
.trend-card {
    background: linear-gradient(135deg, #ffffff 0%, #f8faff 100%);
    border: 1px solid #e2e8f0;
    border-left: 5px solid #3b82f6;
    border-radius: 16px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1.2rem;
    box-shadow: 0 4px 12px rgba(59,130,246,0.07);
    transition: box-shadow 0.2s, transform 0.2s;
    position: relative;
}
.trend-card:hover {
    box-shadow: 0 8px 24px rgba(59,130,246,0.14);
    transform: translateY(-2px);
}
/* Badge viral score */
.viral-badge {
    display: inline-block;
    padding: 3px 12px;
    border-radius: 99px;
    font-weight: 700;
    font-size: 0.78rem;
    color: #fff;
    margin-bottom: 0.5rem;
}
.viral-hot   { background: linear-gradient(90deg,#ef4444,#f97316); }
.viral-warm  { background: linear-gradient(90deg,#f59e0b,#eab308); }
.viral-cool  { background: linear-gradient(90deg,#22c55e,#16a34a); }
/* Số thứ tự */
.trend-rank {
    position: absolute;
    top: 1rem;
    right: 1.2rem;
    font-size: 2rem;
    font-weight: 900;
    color: #e2e8f0;
    line-height: 1;
}
/* Tiêu đề xu hướng */
.trend-title {
    font-size: 1.08rem;
    font-weight: 700;
    color: #1e3a8a;
    margin: 0.3rem 0 0.5rem 0;
}
/* Mô tả */
.trend-desc {
    font-size: 0.92rem;
    color: #475569;
    margin-bottom: 0.6rem;
    line-height: 1.55;
}
/* Góc content */
.trend-angle {
    background: #eff6ff;
    border-radius: 8px;
    padding: 0.5rem 0.75rem;
    font-size: 0.88rem;
    color: #1d4ed8;
    margin-bottom: 0.7rem;
}
/* Hashtag chips */
.hashtag-wrap { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 0.8rem; }
.hashtag-chip {
    background: #dbeafe;
    color: #1e40af;
    border-radius: 99px;
    padding: 2px 10px;
    font-size: 0.78rem;
    font-weight: 600;
}
/* Header banner */
.trend-header {
    background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 50%, #7c3aed 100%);
    border-radius: 16px;
    padding: 1.5rem 2rem;
    margin-bottom: 1.8rem;
    color: white;
    text-align: center;
}
.trend-header h2 {
    color: white !important;
    margin: 0 0 0.3rem 0;
    font-size: 1.6rem;
}
.trend-header p { color: rgba(255,255,255,0.85); margin: 0; font-size: 0.95rem; }
</style>
"""


def _viral_badge_class(score: int) -> str:
    """Trả về class CSS dựa trên viral score."""
    if score >= 8:
        return "viral-hot"
    elif score >= 6:
        return "viral-warm"
    return "viral-cool"


def _viral_label(score: int) -> str:
    """Nhãn hiển thị viral score."""
    if score >= 9:
        return f"🔥 Cực kỳ viral ({score}/10)"
    elif score >= 8:
        return f"🚀 Rất hot ({score}/10)"
    elif score >= 6:
        return f"📈 Đang trending ({score}/10)"
    return f"💡 Tiềm năng ({score}/10)"


def _render_trend_card(trend: dict, idx: int, gemini_key: str):
    """Render một card xu hướng."""
    score = trend.get("viral_score", 5)
    badge_cls = _viral_badge_class(score)
    badge_lbl = _viral_label(score)

    hashtags_html = "".join(
        f'<span class="hashtag-chip">{h}</span>'
        for h in trend.get("hashtags", [])
    )

    card_html = f"""
    <div class="trend-card">
        <span class="trend-rank">#{idx}</span>
        <span class="viral-badge {badge_cls}">{badge_lbl}</span>
        <div class="trend-title">📌 {trend.get('title','')}</div>
        <div class="trend-desc">{trend.get('description','')}</div>
        <div class="trend-angle">
            ✍️ <b>Góc content gợi ý:</b> {trend.get('content_angle','')}
        </div>
        <div class="hashtag-wrap">{hashtags_html}</div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

    # Nút tạo bài viết
    btn_key = f"use_trend_{idx}_{trend.get('title','')[:20].replace(' ','_')}"
    if st.button("✍️ Tạo bài viết từ xu hướng này", key=btn_key, use_container_width=True):
        st.session_state["trend_topic"] = trend.get("title", "")
        st.session_state["trend_angle"] = trend.get("content_angle", "")
        st.success(
            f"✅ Đã chọn xu hướng: **{trend.get('title','')}**\n\n"
            "👉 Chuyển sang tab **📝 Tạo & Đăng Bài** để tạo nội dung từ xu hướng này!"
        )


def render_tab_trend(gemini_key: str = "", workspace_id: int = 1, role: str = "editor"):
    """Render toàn bộ tab Trend Agent."""
    st.markdown(_TREND_CSS, unsafe_allow_html=True)

    # Header banner
    st.markdown("""
    <div class="trend-header">
        <h2>🔥 Trend Agent – Radar Xu Hướng AI</h2>
        <p>Phân tích xu hướng nội dung đang hot theo thời gian thực bằng Google Search + Gemini AI</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Form cấu hình ──────────────────────────────────────────────────────────
    with st.form("trend_form"):
        c1, c2 = st.columns(2)
        with c1:
            niche = st.selectbox(
                "🏷️ Lĩnh vực / Ngành nghề",
                NICHES,
                help="Chọn lĩnh vực bạn muốn phân tích xu hướng"
            )
        with c2:
            platform = st.selectbox(
                "📱 Nền tảng mạng xã hội",
                TREND_PLATFORMS,
                help="Xu hướng sẽ được tối ưu cho nền tảng bạn chọn"
            )

        num_display = st.slider(
            "📊 Số xu hướng muốn xem",
            min_value=3, max_value=10, value=8, step=1
        )

        submitted = st.form_submit_button(
            "🔍 Phân tích xu hướng ngay",
            use_container_width=True
        )

    # ── Phân tích xu hướng ────────────────────────────────────────────────────
    if submitted:
        if not gemini_key:
            st.error("⚠️ Vui lòng nhập Gemini API Key ở thanh bên trái trước!")
            return

        with st.spinner(f"🌐 Trend Agent đang tìm kiếm xu hướng **{niche}** trên **{platform}**..."):
            try:
                trends = analyze_trends(
                    niche=niche,
                    platform=platform,
                    api_key=gemini_key
                )
                st.session_state["trend_results"] = trends
                st.session_state["trend_niche"] = niche
                st.session_state["trend_platform"] = platform
            except Exception as e:
                st.error(f"❌ Lỗi khi phân tích xu hướng: {e}")
                return

    # ── Hiển thị kết quả ──────────────────────────────────────────────────────
    trends = st.session_state.get("trend_results", [])

    if trends:
        niche_disp    = st.session_state.get("trend_niche", niche)
        platform_disp = st.session_state.get("trend_platform", platform)

        st.markdown(f"""
        <div style='background:#eff6ff;border-radius:12px;padding:0.8rem 1.2rem;margin-bottom:1.2rem;'>
            📊 Tìm thấy <b>{len(trends)}</b> xu hướng đang hot trong lĩnh vực
            <b>{niche_disp}</b> trên <b>{platform_disp}</b>
        </div>
        """, unsafe_allow_html=True)

        # Hiển thị theo số lượng đã chọn
        for i, trend in enumerate(trends[:num_display], start=1):
            _render_trend_card(trend, i, gemini_key)

        st.divider()
        st.caption(
            "💡 Tip: Sau khi chọn xu hướng, chuyển sang tab **📝 Tạo & Đăng Bài** "
            "để tạo nội dung với chủ đề đã được điền sẵn."
        )

    elif not submitted:
        # Placeholder khi chưa phân tích lần nào
        st.markdown("""
        <div style='text-align:center;padding:3rem 1rem;color:#94a3b8;'>
            <div style='font-size:3.5rem;margin-bottom:1rem;'>📡</div>
            <div style='font-size:1.1rem;font-weight:600;color:#64748b;margin-bottom:0.5rem;'>
                Chưa có dữ liệu xu hướng
            </div>
            <div style='font-size:0.9rem;'>
                Chọn lĩnh vực và nền tảng, sau đó nhấn <b>"Phân tích xu hướng ngay"</b> để bắt đầu.
            </div>
        </div>
        """, unsafe_allow_html=True)
