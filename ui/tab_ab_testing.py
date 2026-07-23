import streamlit as st
import json
from datetime import datetime
from database.models.ab_testing import ABTestModel
from services.gemini_client import generate_with_gemini

# ── Đảm bảo bảng đã tồn tại ──
try:
    ABTestModel.ensure_tables()
except Exception:
    pass

# ─────────────────────────────────────────────────────────────
# CSS PREMIUM
# ─────────────────────────────────────────────────────────────
_AB_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

.ab-header {
    background: linear-gradient(135deg, #0d1117 0%, #1a1f35 50%, #0d1117 100%);
    border-radius: 20px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.8rem;
    text-align: center;
    border: 1px solid rgba(139,92,246,0.25);
    box-shadow: 0 20px 60px rgba(139,92,246,0.15);
}
.ab-header h2 { color: white !important; font-size: 1.75rem; font-weight: 800; margin: 0 0 .4rem; }
.ab-header p  { color: rgba(255,255,255,0.6); margin: 0; font-size: 0.9rem; }

/* ── Variant card ── */
.variant-wrap {
    background: #ffffff;
    border: 2px solid #e2e8f0;
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 4px 20px rgba(0,0,0,0.06);
    height: 100%;
    transition: border-color .2s, box-shadow .2s;
}
.variant-wrap:hover { border-color: #818cf8; box-shadow: 0 8px 32px rgba(99,102,241,0.12); }
.variant-wrap.winner { border-color: #10b981; box-shadow: 0 8px 32px rgba(16,185,129,0.2); }
.variant-wrap.winner .v-header { background: linear-gradient(90deg,#059669,#10b981); }

.v-header {
    background: linear-gradient(90deg,#4f46e5,#7c3aed);
    padding: .75rem 1.2rem;
    display: flex; align-items: center; justify-content: space-between;
}
.v-header.b { background: linear-gradient(90deg,#db2777,#be185d); }
.v-header.c { background: linear-gradient(90deg,#ea580c,#dc2626); }
.v-header.d { background: linear-gradient(90deg,#0369a1,#0284c7); }
.v-type-badge {
    font-size: 1.2rem; font-weight: 900; color: white; letter-spacing: 1px;
}
.v-label { color: rgba(255,255,255,.85); font-size: .8rem; font-weight: 600; }
.v-body { padding: 1rem 1.2rem; }
.v-content {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: .8rem;
    font-size: .82rem;
    color: #334155;
    line-height: 1.6;
    min-height: 120px;
    white-space: pre-wrap;
    font-family: 'Inter', sans-serif;
}

/* ── KPI row ── */
.kpi-mini { display: flex; gap: .7rem; flex-wrap: wrap; margin-top: .7rem; }
.kpi-m {
    flex: 1; min-width: 70px;
    background: #f1f5f9;
    border-radius: 8px;
    padding: .5rem .6rem;
    text-align: center;
    font-size: .78rem;
    font-weight: 700;
    color: #1e293b;
}
.kpi-m span { display: block; font-size: .68rem; color: #94a3b8; font-weight: 500; margin-bottom: .1rem; }

/* ── Score bar ── */
.score-bar-wrap { margin-top: .6rem; }
.score-label { font-size: .75rem; font-weight: 600; color: #475569; margin-bottom: .2rem; display: flex; justify-content: space-between; }
.score-bar { height: 8px; border-radius: 4px; background: #e2e8f0; overflow: hidden; }
.score-fill { height: 100%; border-radius: 4px; background: linear-gradient(90deg,#6366f1,#8b5cf6); }
.score-fill.win { background: linear-gradient(90deg,#10b981,#34d399); }

/* ── Winner banner ── */
.winner-banner {
    background: linear-gradient(135deg,#065f46,#059669);
    color: white;
    border-radius: 12px;
    padding: 1rem 1.5rem;
    margin-bottom: 1rem;
    font-weight: 700;
    font-size: 1rem;
    text-align: center;
    box-shadow: 0 4px 20px rgba(16,185,129,.3);
}

/* ── Status badge ── */
.status-pill {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: .72rem;
    font-weight: 700;
}
.s-draft     { background:#f1f5f9; color:#64748b; }
.s-running   { background:#dbeafe; color:#1d4ed8; }
.s-paused    { background:#fef3c7; color:#92400e; }
.s-completed { background:#d1fae5; color:#065f46; }
.s-archived  { background:#f1f5f9; color:#94a3b8; }

/* ── Section title ── */
.ab-section { font-size:1rem; font-weight:700; color:#1e293b; border-left:4px solid #8b5cf6; padding-left:10px; margin:1.5rem 0 .8rem; }

/* ── Test list card ── */
.test-card {
    background: #fff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: .9rem 1.2rem;
    margin-bottom: .6rem;
    cursor: pointer;
    transition: border-color .2s, box-shadow .2s;
}
.test-card:hover { border-color: #818cf8; box-shadow: 0 4px 16px rgba(99,102,241,.1); }
.test-card-name { font-weight: 700; color: #1e293b; font-size: .95rem; }
.test-card-meta { color: #64748b; font-size: .78rem; margin-top: .25rem; }
</style>
"""

# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────
_TYPE_LABELS = {
    "prompt":       ("🎯", "Prompt"),
    "headline":     ("📰", "Headline / Tiêu đề"),
    "cta":          ("🖱️", "CTA – Call to Action"),
    "full_post":    ("📝", "Full Post"),
    "subject_line": ("📧", "Subject Line Email"),
    "angle":        ("🔭", "Góc nhìn / Angle"),
}
_STATUS_CSS = {"draft": "s-draft", "running": "s-running", "paused": "s-paused",
               "completed": "s-completed", "archived": "s-archived"}
_STATUS_LABELS = {"draft": "Nháp", "running": "Đang chạy", "paused": "Tạm dừng",
                  "completed": "Hoàn thành", "archived": "Lưu trữ"}
_VAR_HEADER_CSS = {"A": "", "B": "b", "C": "c", "D": "d"}

def _status_pill(status):
    cls = _STATUS_CSS.get(status, "s-draft")
    lbl = _STATUS_LABELS.get(status, status)
    return f'<span class="status-pill {cls}">{lbl}</span>'

def _score_bar(score, max_score, is_winner=False):
    pct = int(score / max(max_score, 0.01) * 100)
    cls = "score-fill win" if is_winner else "score-fill"
    return f"""
    <div class="score-bar-wrap">
        <div class="score-label"><span>⚡ Điểm tổng hợp</span><span>{score:.2f}</span></div>
        <div class="score-bar"><div class="{cls}" style="width:{pct}%"></div></div>
    </div>"""

def _fmt_k(n):
    return f"{n/1000:.1f}K" if n >= 1000 else str(int(n))

def _variant_card_html(v, max_score, is_winner):
    ctr  = (v['clicks'] / v['impressions'] * 100) if v['impressions'] > 0 else 0
    cvr  = (v['conversions'] / max(v['clicks'],1) * 100) if v['clicks'] > 0 else 0
    vt   = v.get('variant_type', 'A')
    hcss = _VAR_HEADER_CSS.get(vt, "")
    win_css = "winner" if is_winner else ""
    return f"""
    <div class="variant-wrap {win_css}">
        <div class="v-header {hcss}">
            <span class="v-type-badge">{'🏆 ' if is_winner else ''}Variant {vt}</span>
            <span class="v-label">{v.get('label','')}</span>
        </div>
        <div class="v-body">
            <div class="v-content">{v.get('content','')}</div>
            <div class="kpi-mini">
                <div class="kpi-m"><span>Hiển thị</span>{_fmt_k(v['impressions'])}</div>
                <div class="kpi-m"><span>Clicks</span>{_fmt_k(v['clicks'])}</div>
                <div class="kpi-m"><span>CTR</span>{ctr:.1f}%</div>
                <div class="kpi-m"><span>Conv.</span>{_fmt_k(v['conversions'])}</div>
                <div class="kpi-m"><span>Leads</span>{_fmt_k(v['leads'])}</div>
                <div class="kpi-m"><span>CVR</span>{cvr:.1f}%</div>
            </div>
            {_score_bar(v['score'], max_score, is_winner)}
        </div>
    </div>"""

# ─────────────────────────────────────────────────────────────
# AI GENERATE VARIANTS
# ─────────────────────────────────────────────────────────────
def ai_generate_variants(test_type: str, topic: str, platform: str,
                         api_key: str, num_variants: int = 2) -> list:
    """Dùng Gemini tạo N variants khác nhau cho A/B test."""
    type_desc = {
        "prompt":       "Prompt nhắc AI viết bài (system prompt)",
        "headline":     "Tiêu đề bài viết hook (headline/hook đầu bài)",
        "cta":          "Lời kêu gọi hành động (Call to Action)",
        "full_post":    "Bài viết mạng xã hội hoàn chỉnh",
        "subject_line": "Tiêu đề email marketing",
        "angle":        "Góc nhìn / Angle cho bài viết",
    }.get(test_type, test_type)

    prompt = f"""Bạn là chuyên gia Marketing A/B Testing.
Tạo {num_variants} variants KHÁC NHAU HOÀN TOÀN để A/B test.

Thông tin:
- Loại test: {type_desc}
- Chủ đề / Sản phẩm: {topic}
- Nền tảng: {platform or 'Facebook'}
- Số variants: {num_variants}

Yêu cầu: Mỗi variant phải có cách tiếp cận RÕ RÀNG KHÁC NHAU (góc cảm xúc khác, cấu trúc khác, hook khác nhau).

Trả về JSON array (CHỈ JSON THUẦN):
[
  {{"label": "Tên ngắn mô tả chiến lược variant", "content": "Nội dung variant đầy đủ"}},
  ...
]"""
    try:
        raw = generate_with_gemini(prompt, api_key=api_key)
        start, end = raw.find("["), raw.rfind("]") + 1
        if start == -1 or end == 0:
            return []
        return json.loads(raw[start:end])
    except Exception as e:
        st.error(f"AI error: {e}")
        return []


def ai_analyze_winner(test, variants, api_key: str) -> str:
    """Phân tích chuyên sâu để tuyên bố winner và rút ra insights."""
    variants_desc = []
    for v in variants:
        ctr = (v['clicks'] / v['impressions'] * 100) if v['impressions'] > 0 else 0
        cvr = (v['conversions'] / max(v['clicks'],1) * 100) if v['clicks'] > 0 else 0
        variants_desc.append(
            f"Variant {v['variant_type']} - {v['label']}:\n"
            f"  Nội dung: {v['content'][:200]}...\n"
            f"  Impressions: {v['impressions']} | Clicks: {v['clicks']} | CTR: {ctr:.2f}%\n"
            f"  Conversions: {v['conversions']} | CVR: {cvr:.2f}% | Leads: {v['leads']}"
        )

    prompt = f"""Bạn là chuyên gia Marketing A/B Testing. Phân tích kết quả test và đưa ra kết luận chuyên sâu.

TEST: {test.get('name','N/A')} | Loại: {test.get('test_type','').upper()} | Chủ đề: {test.get('topic','')}

KẾT QUẢ CÁC VARIANTS:
{"="*50}
{chr(10).join(variants_desc)}

Hãy phân tích theo Markdown (Tiếng Việt):
## 🏆 Variant Chiến Thắng
- Tuyên bố rõ variant nào thắng và tại sao (số liệu cụ thể)

## 📊 Phân Tích Chi Tiết
- So sánh từng chỉ số giữa các variants
- Giải thích **tại sao** variant thắng hiệu quả hơn (tâm lý học, copywriting, UX)

## 💡 Insights Rút Ra
- 3-4 điểm học được để áp dụng cho các nội dung tương lai

## 🎯 Khuyến Nghị Tiếp Theo
- Bước tiếp theo cụ thể: scale gì, test gì tiếp, áp dụng gì?"""

    return generate_with_gemini(prompt, api_key=api_key)


# ─────────────────────────────────────────────────────────────
# MAIN RENDER
# ─────────────────────────────────────────────────────────────
def render_tab_ab_testing(gemini_key: str = "", workspace_id: int = 1, role: str = "editor"):
    st.markdown(_AB_CSS, unsafe_allow_html=True)

    st.markdown("""
    <div class="ab-header">
        <h2>🧪 A/B Testing Engine – So Sánh & Tối Ưu Nội Dung</h2>
        <p>Tạo variants • Chạy thử nghiệm • Phân tích Prompt · Headline · CTA • AI tuyên bố winner</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Session state ──
    if "ab_selected_test_id" not in st.session_state:
        st.session_state["ab_selected_test_id"] = None
    if "ab_view" not in st.session_state:
        st.session_state["ab_view"] = "list"  # list | detail | create

    # ── Nút tạo mới ──
    top_col1, top_col2, _ = st.columns([1, 1, 4])
    with top_col1:
        if st.button("➕ Tạo A/B Test mới", type="primary", use_container_width=True):
            st.session_state["ab_view"] = "create"
            st.session_state["ab_selected_test_id"] = None
    with top_col2:
        if st.button("📋 Danh sách Tests", use_container_width=True):
            st.session_state["ab_view"] = "list"
            st.session_state["ab_selected_test_id"] = None

    st.divider()

    # ══════════════════════════════════════════════════════════════
    # VIEW: CREATE
    # ══════════════════════════════════════════════════════════════
    if st.session_state["ab_view"] == "create":
        _render_create_view(gemini_key, workspace_id, role)

    # ══════════════════════════════════════════════════════════════
    # VIEW: DETAIL
    # ══════════════════════════════════════════════════════════════
    elif st.session_state["ab_view"] == "detail" and st.session_state["ab_selected_test_id"]:
        _render_detail_view(gemini_key, workspace_id, role)

    # ══════════════════════════════════════════════════════════════
    # VIEW: LIST (mặc định)
    # ══════════════════════════════════════════════════════════════
    else:
        _render_list_view(workspace_id, role)


# ─────────────────────────────────────────────────────────────
def _render_create_view(gemini_key, workspace_id, role):
    st.markdown('<div class="ab-section">⚙️ Cấu hình A/B Test mới</div>', unsafe_allow_html=True)

    with st.form("ab_create_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            test_name = st.text_input("📝 Tên test", placeholder="VD: Test CTA tháng 7 – Facebook")
            test_type = st.selectbox("🔬 Loại test",
                list(_TYPE_LABELS.keys()),
                format_func=lambda x: f"{_TYPE_LABELS[x][0]} {_TYPE_LABELS[x][1]}"
            )
            topic = st.text_input("💡 Chủ đề / Sản phẩm", placeholder="VD: AI-Agent Marketing Portal")
        with col2:
            platform = st.selectbox("📱 Nền tảng", ["Facebook", "LinkedIn", "Zalo OA", "Email", "Tất cả"])
            num_variants = st.slider("📊 Số variants muốn test", 2, 4, 2)
            description = st.text_area("📋 Mô tả mục tiêu test", height=90,
                placeholder="VD: Test xem headline kiểu câu hỏi vs câu khẳng định có CTR cao hơn không")

        st.markdown("---")
        st.markdown("#### ✍️ Nội dung Variants")
        st.caption("Điền thủ công **hoặc** để AI tạo tự động bên dưới")

        variant_contents = []
        variant_labels   = []
        variant_types    = ["A", "B", "C", "D"]
        vcols = st.columns(num_variants)
        for i in range(num_variants):
            with vcols[i]:
                st.markdown(f"**Variant {variant_types[i]}**")
                lbl = st.text_input(f"Tên chiến lược", key=f"v_label_{i}",
                                    placeholder=f"VD: Cảm xúc / Lý trí / Hài hước")
                cnt = st.text_area(f"Nội dung", key=f"v_content_{i}", height=150,
                                   placeholder="Để trống → AI sẽ tự điền khi nhấn Generate")
                variant_labels.append(lbl)
                variant_contents.append(cnt)

        col_sub1, col_sub2 = st.columns(2)
        with col_sub1:
            gen_btn = st.form_submit_button("🤖 AI Generate Variants", use_container_width=True)
        with col_sub2:
            save_btn = st.form_submit_button("💾 Tạo & Lưu Test", type="primary", use_container_width=True)

    # ── AI Generate ──
    if gen_btn:
        if not gemini_key:
            st.error("⚠️ Cần Gemini API Key để AI generate variants!")
        elif not topic:
            st.error("⚠️ Vui lòng nhập chủ đề!")
        else:
            with st.spinner(f"🤖 AI đang tạo {num_variants} variants khác nhau..."):
                ai_results = ai_generate_variants(test_type, topic, platform, gemini_key, num_variants)
            if ai_results:
                st.success(f"✅ AI đã tạo {len(ai_results)} variants! Xem và chỉnh sửa bên dưới:")
                for i, r in enumerate(ai_results[:num_variants]):
                    with st.expander(f"📄 Variant {variant_types[i]}: {r.get('label','')}", expanded=True):
                        st.markdown(f"**Label:** `{r.get('label','')}`")
                        st.markdown(f"**Nội dung:**\n```\n{r.get('content','')}\n```")
                        if st.button(f"✅ Dùng variant {variant_types[i]} này", key=f"use_ai_{i}"):
                            st.session_state[f"v_label_{i}"] = r.get("label", "")
                            st.session_state[f"v_content_{i}"] = r.get("content", "")
                            st.rerun()

    # ── Save ──
    if save_btn:
        if not test_name:
            st.error("⚠️ Vui lòng nhập tên test!")
        else:
            # Kiểm tra ít nhất 2 variants có nội dung
            filled = [(variant_labels[i], variant_contents[i]) for i in range(num_variants)
                      if variant_contents[i].strip()]
            if len(filled) < 2:
                st.error("⚠️ Cần ít nhất 2 variants có nội dung!")
            else:
                test_id = ABTestModel.create_test(
                    workspace_id=workspace_id, name=test_name, test_type=test_type,
                    topic=topic, platform=platform, description=description
                )
                for i in range(num_variants):
                    if variant_contents[i].strip():
                        ABTestModel.add_variant(
                            test_id=test_id,
                            label=variant_labels[i] or f"Variant {variant_types[i]}",
                            content=variant_contents[i],
                            variant_type=variant_types[i],
                        )
                ABTestModel.update_test_status(test_id, "running")
                st.success(f"✅ Đã tạo A/B Test **{test_name}** và bắt đầu chạy!")
                st.session_state["ab_view"] = "detail"
                st.session_state["ab_selected_test_id"] = test_id
                st.rerun()


# ─────────────────────────────────────────────────────────────
def _render_detail_view(gemini_key, workspace_id, role):
    test_id  = st.session_state["ab_selected_test_id"]
    test     = ABTestModel.get_test(test_id)
    variants = ABTestModel.get_variants(test_id)

    if not test:
        st.error("Không tìm thấy test!"); return

    icon, type_lbl = _TYPE_LABELS.get(test["test_type"], ("🔬", test["test_type"]))
    winner_id = test.get("winner_id")
    max_score = max((v["score"] for v in variants), default=0.01)

    # ── Header ──
    col_h1, col_h2, col_h3 = st.columns([4, 1, 1])
    with col_h1:
        st.markdown(f"### {icon} {test['name']}")
        st.markdown(
            f"{_status_pill(test['status'])} "
            f"&nbsp;<span style='color:#94a3b8;font-size:.8rem'>{type_lbl} · {test.get('platform','')} · {test.get('topic','')}</span>",
            unsafe_allow_html=True
        )
    with col_h2:
        if test["status"] == "running":
            if st.button("⏸ Tạm dừng", use_container_width=True):
                ABTestModel.update_test_status(test_id, "paused")
                st.rerun()
        elif test["status"] == "paused":
            if st.button("▶ Tiếp tục", use_container_width=True):
                ABTestModel.update_test_status(test_id, "running")
                st.rerun()
    with col_h3:
        if st.button("🗑️ Xóa test", use_container_width=True):
            ABTestModel.delete_test(test_id)
            st.session_state["ab_view"] = "list"
            st.session_state["ab_selected_test_id"] = None
            st.rerun()

    st.divider()

    # ── Winner banner ──
    if winner_id:
        winner_v = next((v for v in variants if v["id"] == winner_id), None)
        if winner_v:
            st.markdown(
                f'<div class="winner-banner">🏆 WINNER: Variant {winner_v["variant_type"]} — {winner_v["label"]} '
                f'(Score: {winner_v["score"]:.2f})</div>',
                unsafe_allow_html=True
            )

    # ── Hiển thị variants song song ──
    st.markdown('<div class="ab-section">📊 So Sánh Variants</div>', unsafe_allow_html=True)
    cols = st.columns(len(variants))
    for i, v in enumerate(variants):
        is_winner = (v["id"] == winner_id)
        with cols[i]:
            st.markdown(_variant_card_html(v, max_score, is_winner), unsafe_allow_html=True)

    st.divider()

    # ── Nhập kết quả thực tế ──
    st.markdown('<div class="ab-section">📥 Nhập Kết Quả Thực Tế (sau khi chạy test)</div>', unsafe_allow_html=True)

    for v in variants:
        with st.expander(f"✏️ Nhập kết quả – Variant {v['variant_type']}: {v['label']}", expanded=False):
            with st.form(f"metrics_form_{v['id']}"):
                mc1, mc2, mc3, mc4, mc5 = st.columns(5)
                imp  = mc1.number_input("👁 Impressions", min_value=0, value=v.get("impressions",0), step=100, key=f"imp_{v['id']}")
                clk  = mc2.number_input("🖱 Clicks",      min_value=0, value=v.get("clicks",0),      step=10,  key=f"clk_{v['id']}")
                conv = mc3.number_input("✅ Conversions", min_value=0, value=v.get("conversions",0),  step=1,   key=f"conv_{v['id']}")
                leads = mc4.number_input("🎯 Leads",       min_value=0, value=v.get("leads",0),        step=1,   key=f"lead_{v['id']}")
                rev  = mc5.number_input("💰 Revenue (đ)", min_value=0, value=v.get("revenue",0),      step=10000, key=f"rev_{v['id']}")
                notes = st.text_input("Ghi chú", value=v.get("notes",""), key=f"note_{v['id']}")
                if st.form_submit_button("💾 Lưu kết quả", use_container_width=True):
                    ABTestModel.update_variant_metrics(
                        variant_id=v["id"], impressions=imp, clicks=clk,
                        conversions=conv, leads=leads, revenue=rev, notes=notes
                    )
                    st.success(f"✅ Đã lưu kết quả cho Variant {v['variant_type']}!")
                    st.rerun()

    st.divider()

    # ── Tuyên bố winner ──
    st.markdown('<div class="ab-section">🏆 Tuyên Bố Winner</div>', unsafe_allow_html=True)
    col_w1, col_w2 = st.columns([2, 1])
    with col_w1:
        sorted_v = sorted(variants, key=lambda x: x["score"], reverse=True)
        winner_options = {v["id"]: f"Variant {v['variant_type']} – {v['label']} (Score: {v['score']:.2f})"
                          for v in sorted_v}
        default_idx = 0
        if winner_id and winner_id in winner_options:
            default_idx = list(winner_options.keys()).index(winner_id)
        selected_winner = st.selectbox(
            "Chọn Variant thắng cuộc",
            options=list(winner_options.keys()),
            format_func=lambda x: winner_options[x],
            index=default_idx,
            key="winner_select"
        )
    with col_w2:
        st.write("")
        if st.button("🏁 Hoàn thành & Tuyên bố Winner", type="primary", use_container_width=True):
            ABTestModel.update_test_status(test_id, "completed", winner_id=selected_winner)
            st.success("✅ Đã lưu Winner và hoàn thành test!")
            st.rerun()

    # ── AI Analysis ──
    st.markdown('<div class="ab-section">🤖 AI Phân Tích Chuyên Sâu</div>', unsafe_allow_html=True)
    has_data = any(v["impressions"] > 0 for v in variants)

    if not has_data:
        st.info("💡 Nhập kết quả thực tế ở trên trước, sau đó dùng AI phân tích để nhận insights chuyên sâu.")
    else:
        if st.button("🤖 Phân tích winner & rút ra insights bằng AI", type="primary"):
            if not gemini_key:
                st.error("⚠️ Cần Gemini API Key!")
            else:
                with st.spinner("🧠 AI đang phân tích kết quả A/B test..."):
                    analysis = ai_analyze_winner(test, variants, gemini_key)
                st.markdown("---")
                st.markdown("### 📊 Phân Tích Từ AI Expert")
                st.markdown(analysis)

                # Learning Loop: Lưu insight vào learning_insights
                try:
                    from database.models.learning_insights import LearningInsightModel
                    best = max(variants, key=lambda x: x["score"])
                    ctr = (best['clicks'] / best['impressions'] * 100) if best['impressions'] > 0 else 0
                    LearningInsightModel.create(
                        workspace_id=workspace_id,
                        title=f"🧪 A/B Test: {test['name']} → Variant {best['variant_type']} thắng",
                        description=f"Test type: {test['test_type']}. Winner: {best['label']}. CTR: {ctr:.2f}%",
                        recommendation=f"Áp dụng phong cách của Variant {best['variant_type']} cho các bài tương tự: {best['content'][:200]}",
                        insight_type="cta_effectiveness" if test["test_type"] == "cta" else "content_pattern",
                        platform=test.get("platform"),
                        avg_ctr=ctr,
                        avg_leads=best.get("leads", 0),
                        confidence=0.85,
                        sample_size=sum(v["impressions"] for v in variants),
                    )
                    st.success("💡 Đã lưu insight vào **Learning Loop** để AI học cho lần sau!")
                except Exception as e:
                    pass  # Learning loop is optional


# ─────────────────────────────────────────────────────────────
def _render_list_view(workspace_id, role):
    # ── Stats ──
    stats = ABTestModel.get_test_stats(workspace_id)
    total = sum(stats.values())

    if total == 0:
        st.info("💡 Chưa có A/B Test nào. Nhấn **➕ Tạo A/B Test mới** để bắt đầu!")
        return

    # Quick stats pills
    pills_html = '<div style="display:flex;gap:.7rem;flex-wrap:wrap;margin-bottom:1.2rem">'
    pills_html += f'<div style="background:#f1f5f9;border:1px solid #e2e8f0;border-radius:10px;padding:.5rem 1rem;font-size:.82rem;font-weight:700;color:#334155">📋 Tổng: <span style="color:#6366f1">{total}</span></div>'
    for s, cnt in stats.items():
        lbl = _STATUS_LABELS.get(s, s)
        pills_html += f'<div style="background:#f1f5f9;border:1px solid #e2e8f0;border-radius:10px;padding:.5rem 1rem;font-size:.82rem;font-weight:700;color:#334155">{lbl}: <span style="color:#6366f1">{cnt}</span></div>'
    pills_html += '</div>'
    st.markdown(pills_html, unsafe_allow_html=True)

    # ── Filter ──
    col_f1, col_f2 = st.columns([2, 4])
    with col_f1:
        filter_status = st.selectbox("Lọc trạng thái",
            ["Tất cả"] + list(_STATUS_LABELS.keys()),
            format_func=lambda x: _STATUS_LABELS.get(x, "🌐 Tất cả") if x != "Tất cả" else "🌐 Tất cả",
            key="ab_filter_status"
        )

    status_param = None if filter_status == "Tất cả" else filter_status
    tests = ABTestModel.list_tests(workspace_id, status=status_param, limit=50)

    st.markdown(f'<div class="ab-section">📋 Danh sách Tests ({len(tests)})</div>', unsafe_allow_html=True)

    for test in tests:
        icon, type_lbl = _TYPE_LABELS.get(test["test_type"], ("🔬", test["test_type"]))
        variants = ABTestModel.get_variants(test["id"])
        best = max(variants, key=lambda x: x["score"]) if variants else None

        col_t1, col_t2, col_t3 = st.columns([5, 2, 1])
        with col_t1:
            st.markdown(f"""
            <div class="test-card">
                <div class="test-card-name">{icon} {test['name']}</div>
                <div class="test-card-meta">
                    {_status_pill(test['status'])} &nbsp;
                    {type_lbl} · {test.get('platform','')} · {test.get('topic','')[:40]}
                    {f" | 🏅 {len(variants)} variants" if variants else ""}
                    {f" | 🏆 Tốt nhất: Variant {best['variant_type']} ({best['score']:.2f}pt)" if best and best['score']>0 else ""}
                </div>
            </div>""", unsafe_allow_html=True)
        with col_t2:
            created = str(test.get("created_at",""))[:10]
            st.caption(f"📆 {created}")
        with col_t3:
            if st.button("🔍 Xem", key=f"view_test_{test['id']}", use_container_width=True):
                st.session_state["ab_view"] = "detail"
                st.session_state["ab_selected_test_id"] = test["id"]
                st.rerun()
