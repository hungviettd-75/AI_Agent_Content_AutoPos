import streamlit as st
import json
from datetime import datetime
from database.models.learning_insights import LearningInsightModel
from workflow.learning_engine import run_learning_loop, get_insights_as_context

_LEARNING_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

.ll-header {
    background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 50%, #0f172a 100%);
    border-radius: 20px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.8rem;
    color: white;
    text-align: center;
    border: 1px solid rgba(99,179,237,0.2);
    box-shadow: 0 20px 60px rgba(0,0,0,0.35);
}
.ll-header h2 { color: white !important; margin: 0 0 0.4rem; font-size: 1.75rem; font-weight: 800; }
.ll-header p  { color: rgba(255,255,255,0.65); margin: 0; font-size: 0.9rem; }

/* ── Insight Card ── */
.insight-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-left: 5px solid #3b82f6;
    border-radius: 14px;
    padding: 1.2rem 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 4px 20px rgba(0,0,0,0.05);
    transition: transform .2s, box-shadow .2s;
    position: relative;
}
.insight-card:hover { transform: translateY(-2px); box-shadow: 0 8px 30px rgba(0,0,0,0.10); }
.insight-card.type-platform     { border-left-color: #8b5cf6; }
.insight-card.type-content      { border-left-color: #10b981; }
.insight-card.type-timing       { border-left-color: #f59e0b; }
.insight-card.type-topic        { border-left-color: #ef4444; }
.insight-card.type-cta          { border-left-color: #06b6d4; }
.insight-card.type-audience     { border-left-color: #ec4899; }

.insight-title { font-size: 1rem; font-weight: 700; color: #1e293b; margin-bottom: 0.4rem; }
.insight-desc  { font-size: 0.85rem; color: #475569; line-height: 1.55; margin-bottom: 0.6rem; }
.insight-reco  {
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    border-radius: 8px;
    padding: 0.6rem 1rem;
    font-size: 0.82rem;
    color: #14532d;
    font-weight: 600;
    line-height: 1.5;
}
.insight-reco::before { content: "🎯 Khuyến nghị: "; font-weight: 800; }
.insight-meta {
    display: flex;
    gap: 0.6rem;
    margin-top: 0.7rem;
    flex-wrap: wrap;
    align-items: center;
}
.meta-badge {
    font-size: 0.72rem;
    font-weight: 700;
    padding: 2px 9px;
    border-radius: 20px;
    background: #e2e8f0;
    color: #475569;
}
.confidence-bar {
    height: 4px;
    border-radius: 4px;
    background: #e2e8f0;
    margin-top: 0.6rem;
    overflow: hidden;
}
.confidence-fill {
    height: 100%;
    border-radius: 4px;
    background: linear-gradient(90deg, #3b82f6, #10b981);
}

/* ── Status badge ── */
.badge-new       { background: #dbeafe; color: #1d4ed8; }
.badge-applied   { background: #d1fae5; color: #065f46; }
.badge-dismissed { background: #f1f5f9; color: #94a3b8; }

/* ── Section title ── */
.ll-section {
    font-size: 1rem; font-weight: 700; color: #1e293b;
    border-left: 4px solid #6366f1;
    padding-left: 10px;
    margin: 1.5rem 0 0.8rem;
}

/* ── Context box ── */
.context-box {
    background: #fafafa;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1rem 1.2rem;
    font-family: monospace;
    font-size: 0.82rem;
    color: #334155;
    white-space: pre-wrap;
    line-height: 1.6;
}

/* ── Stat pills ── */
.stat-row { display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 1.2rem; }
.stat-pill {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 0.6rem 1.1rem;
    font-size: 0.82rem;
    font-weight: 700;
    color: #334155;
}
.stat-pill span { color: #6366f1; font-size: 1.1rem; }
</style>
"""

_TYPE_LABELS = {
    "content_pattern":   ("📝", "Nội dung",   "type-content"),
    "platform_strategy": ("📱", "Nền tảng",   "type-platform"),
    "timing":            ("📅", "Thời điểm",  "type-timing"),
    "topic_performance": ("🔑", "Chủ đề",     "type-topic"),
    "cta_effectiveness": ("🖱️", "CTA",        "type-cta"),
    "audience":          ("👥", "Đối tượng",  "type-audience"),
}

def _render_insight_card(ins: dict):
    itype = ins.get("insight_type", "content_pattern")
    icon, label, css_cls = _TYPE_LABELS.get(itype, ("💡", itype, ""))
    confidence = float(ins.get("confidence", 0.7))
    conf_pct = int(confidence * 100)
    status = ins.get("status", "new")
    status_cls = f"badge-{status}"

    plat  = ins.get("platform") or ""
    ctype = ins.get("content_type") or ""
    sample = ins.get("sample_size") or 0
    gen_at = str(ins.get("generated_at", ""))[:10]
    ins_id = ins.get("id")

    plat_html  = f'<span class="meta-badge">{plat.upper()}</span>' if plat else ""
    ctype_html = f'<span class="meta-badge">{ctype}</span>' if ctype else ""

    st.markdown(f"""
    <div class="insight-card {css_cls}">
        <div class="insight-title">{ins['title']}</div>
        <div class="insight-desc">{ins.get('description','')}</div>
        <div class="insight-reco">{ins.get('recommendation','')}</div>
        <div class="insight-meta">
            <span class="meta-badge {status_cls}">{'🆕 Mới' if status=='new' else '✅ Đã áp dụng' if status=='applied' else '🚫 Bỏ qua'}</span>
            <span class="meta-badge">{icon} {label}</span>
            {plat_html}{ctype_html}
            <span class="meta-badge">📊 {sample} mẫu</span>
            <span class="meta-badge">📆 {gen_at}</span>
        </div>
        <div class="confidence-bar">
            <div class="confidence-fill" style="width:{conf_pct}%"></div>
        </div>
        <div style="font-size:0.72rem;color:#94a3b8;margin-top:3px;">Độ tin cậy: {conf_pct}%</div>
    </div>
    """, unsafe_allow_html=True)
    return ins_id


def render_tab_learning(gemini_key: str = "", workspace_id: int = 1, role: str = "editor"):
    st.markdown(_LEARNING_CSS, unsafe_allow_html=True)

    st.markdown("""
    <div class="ll-header">
        <h2>🧠 Learning Loop – AI Học Từ Analytics</h2>
        <p>Hệ thống tự động phân tích hiệu quả bài đăng • Học patterns • Cải thiện nội dung tương lai liên tục</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Thanh điều khiển ──
    col_cfg1, col_cfg2, col_cfg3, col_btn = st.columns([2, 2, 2, 1])
    with col_cfg1:
        days = st.selectbox("📅 Phân tích", ["7 ngày", "14 ngày", "30 ngày", "60 ngày"],
                            index=2, key="ll_days")
        days_val = int(days.split()[0])
    with col_cfg2:
        use_ai = st.toggle("🤖 Dùng AI Gemini để phân tích sâu",
                           value=bool(gemini_key), key="ll_use_ai")
    with col_cfg3:
        type_filter = st.selectbox("🔍 Lọc loại insight", 
                                   ["Tất cả"] + list(_TYPE_LABELS.keys()),
                                   format_func=lambda x: f"{_TYPE_LABELS[x][0]} {_TYPE_LABELS[x][1]}" if x != "Tất cả" else "🌐 Tất cả",
                                   key="ll_type")
    with col_btn:
        st.write("")
        run_btn = st.button("🔄 Chạy Learning Loop", use_container_width=True, type="primary")

    # ── Chạy Learning Loop ──
    if run_btn:
        if use_ai and not gemini_key:
            st.warning("⚠️ Chưa có Gemini API Key — sẽ chạy chỉ phân tích thống kê.")
        with st.spinner("🧠 AI đang phân tích dữ liệu analytics và học patterns..."):
            result = run_learning_loop(
                workspace_id=workspace_id,
                days=days_val,
                api_key=gemini_key if use_ai else None,
                use_ai=use_ai and bool(gemini_key),
            )
        total = result["statistical_count"] + result["ai_count"]
        if total > 0:
            st.success(f"✅ Vòng lặp học hoàn tất! Đã sinh **{total} insights** mới "
                       f"({result['statistical_count']} thống kê + {result['ai_count']} AI).")
        else:
            st.warning("Không sinh được insight nào. Hãy đảm bảo có dữ liệu analytics.")
        if result["errors"]:
            with st.expander(f"⚠️ {len(result['errors'])} cảnh báo"):
                for err in result["errors"]:
                    st.caption(f"• {err}")
        st.rerun()

    # ── Load insights ──
    type_param = None if type_filter == "Tất cả" else type_filter
    insights = LearningInsightModel.list_by_workspace(workspace_id=workspace_id, insight_type=type_param, limit=50)
    active_insights = [i for i in insights if i.get("status") == "new"]
    applied_insights = [i for i in insights if i.get("status") == "applied"]

    # ── Thống kê nhanh ──
    by_type = LearningInsightModel.count_by_type(workspace_id)
    total_insights = sum(by_type.values())

    st.markdown('<div class="stat-row">', unsafe_allow_html=True)
    stats_html = ""
    stats_html += f'<div class="stat-pill">🧠 Tổng insights: <span>{total_insights}</span></div>'
    stats_html += f'<div class="stat-pill">🆕 Chờ áp dụng: <span>{len(active_insights)}</span></div>'
    stats_html += f'<div class="stat-pill">✅ Đã áp dụng: <span>{len(applied_insights)}</span></div>'
    for itype, cnt in by_type.items():
        icon = _TYPE_LABELS.get(itype, ("💡", itype, ""))[0]
        lbl  = _TYPE_LABELS.get(itype, ("💡", itype, ""))[1]
        stats_html += f'<div class="stat-pill">{icon} {lbl}: <span>{cnt}</span></div>'
    st.markdown(stats_html + '</div>', unsafe_allow_html=True)

    if not insights:
        st.info("💡 Chưa có insights nào. Nhấn **🔄 Chạy Learning Loop** để bắt đầu phân tích!")
        return

    # ════════════════════════════════════════════
    # PHẦN 1: INSIGHTS MỚI (chưa áp dụng)
    # ════════════════════════════════════════════
    if active_insights:
        st.markdown(f'<div class="ll-section">🆕 Insights Mới Cần Xem Xét ({len(active_insights)})</div>', unsafe_allow_html=True)

        for ins in active_insights:
            ins_id = _render_insight_card(ins)
            col_a, col_b, _ = st.columns([1, 1, 3])
            with col_a:
                if st.button("✅ Áp dụng", key=f"apply_{ins_id}", use_container_width=True):
                    LearningInsightModel.update_status(ins_id, "applied", workspace_id=workspace_id)
                    LearningInsightModel.increment_applied(ins_id, workspace_id=workspace_id)
                    st.success("Đã đánh dấu là áp dụng!")
                    st.rerun()
            with col_b:
                if st.button("🚫 Bỏ qua", key=f"dismiss_{ins_id}", use_container_width=True):
                    LearningInsightModel.update_status(ins_id, "dismissed", workspace_id=workspace_id)
                    st.rerun()

    # ════════════════════════════════════════════
    # PHẦN 2: INSIGHTS ĐÃ ÁP DỤNG
    # ════════════════════════════════════════════
    if applied_insights:
        with st.expander(f"✅ Insights đã áp dụng ({len(applied_insights)})", expanded=False):
            for ins in applied_insights[:10]:
                _render_insight_card(ins)

    # ════════════════════════════════════════════
    # PHẦN 3: CONTEXT NHÚNG VÀO PROMPT
    # ════════════════════════════════════════════
    st.markdown('<div class="ll-section">🔗 Learning Context – Nhúng vào Prompt Tạo Nội Dung</div>', unsafe_allow_html=True)
    st.markdown("Context này được **tự động nhúng vào tất cả các prompt** tạo nội dung (tab Tạo & Đăng, Campaign, Copywriting...) để AI học từ kinh nghiệm thực tế.")

    context_str = get_insights_as_context(workspace_id, max_insights=5)
    if context_str:
        st.markdown(f'<div class="context-box">{context_str}</div>', unsafe_allow_html=True)
    else:
        st.caption("_(Chưa có insights active để nhúng vào context)_")

    # ════════════════════════════════════════════
    # PHẦN 4: DỌN DẸP
    # ════════════════════════════════════════════
    st.markdown('<div class="ll-section">🗑️ Bảo trì</div>', unsafe_allow_html=True)
    col_clean, _ = st.columns([1, 3])
    with col_clean:
        if role in ["manager", "admin", "owner", "super_admin", "ceo"]:
            if st.button("🧹 Xóa insights cũ & hết hạn", use_container_width=True):
                deleted = LearningInsightModel.delete_expired(workspace_id)
                st.success(f"Đã xóa {deleted} insights cũ/hết hạn.")
                st.rerun()
        else:
            st.caption("(Chỉ Manager+ mới có quyền dọn dẹp)")
