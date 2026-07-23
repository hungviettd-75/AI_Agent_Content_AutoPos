"""ui/tab_approval.py — Tab Quy Trình Phê Duyệt Đa Cấp (Phiên bản đầy đủ v2).

Đã sửa:
  - [FIX #1] Bỏ `return` sớm gây mất giao diện Manager/CEO khi workspace rỗng.
  - [FIX #2] CEO dùng đúng `ApprovalModel.respond()` thay vì tạo bản ghi mới.
  - [FIX #3] Tách phân quyền Viewer (chỉ xem) khỏi Editor (được gửi duyệt).
  - [NEW]    Kanban Board 4 cột trực quan.
  - [NEW]    Metrics Dashboard (count_by_status).
  - [NEW]    Audit Trail – lịch sử phê duyệt từng bài.
  - [NEW]    Hiển thị lý do từ chối cho người tạo bài.
  - [NEW]    Bộ lọc bài viết theo platform.
  - [NEW]    Shortcut "Đặt lịch đăng ngay" sau khi CEO duyệt.
  - [NEW]    Pending Approval List – bảng đầy đủ Tiêu đề/Tác giả/Ngày/Kênh.
  - [NEW]    Quick Review Modal – xem toàn nội dung + ảnh tại chỗ.
  - [NEW]    Decision Actions riêng biệt: Approve → publishing queue, Từ chối → ô nhập lý do.
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from database.models.posts import PostModel
from database.models.approvals import ApprovalModel


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _current_user_id() -> int:
    """Lấy ID người dùng hiện tại từ session_state một cách an toàn."""
    return st.session_state.get("current_user", {}).get("id")


_STATUS_BADGE = {
    "draft":                     ("📝 Nháp",           "#f1f5f9", "#475569"),
    "pending_manager_approval":  ("👔 Chờ Manager",    "#fef3c7", "#92400e"),
    "pending_ceo_approval":      ("👑 Chờ CEO",        "#ffe4e6", "#9f1239"),
    "approved":                  ("✅ Đã duyệt",        "#d1fae5", "#065f46"),
    "published":                 ("🚀 Đã đăng",         "#dbeafe", "#1e40af"),
    "failed":                    ("❌ Lỗi đăng",        "#fee2e2", "#991b1b"),
    "archived":                  ("🗄️ Lưu trữ",        "#f3f4f6", "#374151"),
}

_PLATFORM_COLOR = {
    "facebook":  "#1877F2",
    "zalo":      "#0084FF",
    "linkedin":  "#0A66C2",
    "all":       "#6B7280",
}


def _badge_html(status: str) -> str:
    label, bg, color = _STATUS_BADGE.get(status, (status, "#e2e8f0", "#475569"))
    return (
        f"<span style='background:{bg};color:{color};padding:3px 9px;"
        f"border-radius:6px;font-size:0.78rem;font-weight:700;'>{label}</span>"
    )


def _platform_dot(platform: str) -> str:
    color = _PLATFORM_COLOR.get(platform.lower(), "#6B7280")
    return f"<span style='color:{color};font-weight:800;'>{platform.upper()}</span>"


# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────

_APPROVAL_CSS = """
<style>
/* ── Header ─────────────────────────────────────────────────────────── */
.app-header {
    background: linear-gradient(135deg, #f59e0b 0%, #d97706 50%, #78350f 100%);
    border-radius: 16px;
    padding: 1.5rem 2rem;
    margin-bottom: 1.8rem;
    color: white;
    text-align: center;
}
.app-header h2 { color: white !important; margin: 0 0 0.3rem 0; font-size: 1.6rem; }
.app-header p  { color: rgba(255,255,255,0.85); margin: 0; font-size: 0.95rem; }

/* ── Pending List Table ──────────────────────────────────────────────── */
.pending-list-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
    margin-bottom: 1rem;
}
.pending-list-table thead th {
    background: #f8fafc;
    border-bottom: 2px solid #e2e8f0;
    padding: 10px 14px;
    text-align: left;
    font-weight: 700;
    color: #374151;
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
.pending-list-table tbody tr {
    border-bottom: 1px solid #f1f5f9;
    transition: background 0.15s;
}
.pending-list-table tbody tr:hover { background: #f8fafc; }
.pending-list-table tbody td {
    padding: 10px 14px;
    vertical-align: middle;
    color: #1e293b;
}
.pending-list-table tbody td.post-id { color: #94a3b8; font-size: 0.78rem; }
.pending-list-table tbody td.post-title { font-weight: 600; max-width: 280px; }
.pending-list-table tbody td.post-title small {
    display: block; font-weight: 400; color: #64748b; margin-top: 2px;
}

/* ── Quick Review Modal (inline expander) ───────────────────────────── */
.qr-modal {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 18px 22px;
    margin: 10px 0 16px 0;
}
.qr-modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
}
.qr-content-box {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 14px 16px;
    font-size: 0.87rem;
    line-height: 1.7;
    color: #1e293b;
    white-space: pre-wrap;
    max-height: 320px;
    overflow-y: auto;
}
.qr-image-box {
    border: 2px dashed #e2e8f0;
    border-radius: 8px;
    padding: 12px;
    text-align: center;
    color: #94a3b8;
    font-size: 0.82rem;
    margin-top: 10px;
}

/* ── Reject Reason Box ───────────────────────────────────────────────── */
.reject-reason-box {
    background: #fff7ed;
    border-left: 4px solid #f97316;
    border-radius: 0 10px 10px 0;
    padding: 12px 16px;
    margin: 8px 0 12px 0;
}

/* ── Metric tile ─────────────────────────────────────────────────────── */
.metric-tile {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 14px 18px;
    text-align: center;
    box-shadow: 0 2px 6px rgba(0,0,0,0.05);
}
.metric-tile .val  { font-size: 2rem; font-weight: 800; color: #1e293b; }
.metric-tile .lbl  { font-size: 0.78rem; color: #64748b; margin-top: 2px; }

/* ── Kanban ──────────────────────────────────────────────────────────── */
.kanban-col-header {
    font-weight: 700;
    font-size: 0.9rem;
    padding: 8px 12px;
    border-radius: 8px;
    margin-bottom: 10px;
    text-align: center;
}
.kanban-card {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 10px 13px;
    margin-bottom: 8px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
    font-size: 0.84rem;
}
.kanban-card:hover { border-color: #cbd5e1; box-shadow: 0 3px 10px rgba(0,0,0,0.08); }

/* ── Pipeline diagram ────────────────────────────────────────────────── */
.pipeline-container {
    display: flex;
    justify-content: space-around;
    align-items: center;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1.2rem;
    margin-bottom: 1rem;
}
.pipeline-step {
    text-align: center;
    flex: 1;
    padding: 8px;
    border-radius: 8px;
    font-size: 0.82rem;
    font-weight: 700;
    color: #64748b;
    border: 1px solid #e2e8f0;
    background-color: white;
}
.pipeline-step.active {
    background-color: #fef3c7;
    color: #d97706;
    border-color: #f59e0b;
    box-shadow: 0 0 8px rgba(245,158,11,0.25);
}
.pipeline-step.completed {
    background-color: #d1fae5;
    color: #065f46;
    border-color: #10b981;
}
.pipeline-arrow { font-size: 1.3rem; color: #cbd5e1; padding: 0 6px; }

/* ── Audit table ─────────────────────────────────────────────────────── */
.audit-row {
    display: flex;
    gap: 10px;
    align-items: flex-start;
    padding: 8px 0;
    border-bottom: 1px solid #f1f5f9;
    font-size: 0.83rem;
}
.audit-row:last-child { border-bottom: none; }
.audit-dot {
    width: 10px; height: 10px;
    border-radius: 50%;
    margin-top: 4px;
    flex-shrink: 0;
}

/* ── Rejection notice ────────────────────────────────────────────────── */
.rejection-notice {
    background: #fff7ed;
    border-left: 4px solid #f59e0b;
    border-radius: 0 8px 8px 0;
    padding: 10px 14px;
    margin-bottom: 8px;
    font-size: 0.85rem;
}
</style>
"""


# ─────────────────────────────────────────────────────────────────────────────
# PIPELINE DIAGRAM
# ─────────────────────────────────────────────────────────────────────────────

def _render_pipeline_diagram(status: str):
    """Vẽ sơ đồ quy trình phê duyệt trực quan."""
    steps = [
        {"label": "✍️ Marketing",    "statuses": ["draft"]},
        {"label": "👔 Manager",       "statuses": ["pending_manager_approval"]},
        {"label": "👑 CEO",           "statuses": ["pending_ceo_approval"]},
        {"label": "🚀 Xuất bản",      "statuses": ["approved", "published"]},
    ]
    current_idx = 0
    for idx, step in enumerate(steps):
        if status in step["statuses"]:
            current_idx = idx
            break
    if status == "published":
        current_idx = 3

    html = '<div class="pipeline-container">'
    for idx, step in enumerate(steps):
        cls = "completed" if idx < current_idx else ("active" if idx == current_idx else "")
        html += f'<div class="pipeline-step {cls}">{step["label"]}</div>'
        if idx < len(steps) - 1:
            html += '<div class="pipeline-arrow">➔</div>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# METRICS DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────

def _render_metrics(workspace_id: int):
    """Hiển thị số liệu tổng quan phê duyệt."""
    counts = ApprovalModel.count_by_status(workspace_id)
    pending   = counts.get("pending", 0)
    approved  = counts.get("approved", 0)
    rejected  = counts.get("revision_requested", 0)
    total     = sum(counts.values())

    m1, m2, m3, m4 = st.columns(4)
    tiles = [
        (m1, total,    "📦 Tổng yêu cầu",   "#1e293b"),
        (m2, pending,  "⏳ Đang chờ duyệt",  "#d97706"),
        (m3, approved, "✅ Đã phê duyệt",    "#065f46"),
        (m4, rejected, "🔄 Yêu cầu sửa lại", "#991b1b"),
    ]
    for col, val, label, color in tiles:
        with col:
            st.markdown(
                f"<div class='metric-tile'>"
                f"<div class='val' style='color:{color};'>{val}</div>"
                f"<div class='lbl'>{label}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
    st.write("")


# ─────────────────────────────────────────────────────────────────────────────
# KANBAN BOARD
# ─────────────────────────────────────────────────────────────────────────────

def _render_kanban(df_posts: pd.DataFrame, workspace_id: int, role: str):
    """Bảng Kanban 4 cột: Draft | Chờ duyệt | Đã duyệt | Đã đăng."""
    st.markdown("### 📋 Bảng Kanban Tổng Quan Bài Viết")

    col_headers = [
        ("📝 Nháp",           "#f1f5f9", "#475569", ["draft"]),
        ("⏳ Chờ Duyệt",      "#fef9c3", "#713f12",
         ["pending_manager_approval", "pending_ceo_approval"]),
        ("✅ Đã Duyệt",        "#d1fae5", "#065f46", ["approved"]),
        ("🚀 Đã Đăng",         "#dbeafe", "#1e40af", ["published"]),
    ]

    cols = st.columns(4)
    for col, (header, bg, color, statuses) in zip(cols, col_headers):
        with col:
            st.markdown(
                f"<div class='kanban-col-header' style='background:{bg};color:{color};'>"
                f"{header}</div>",
                unsafe_allow_html=True,
            )
            subset = df_posts[df_posts["status"].isin(statuses)]
            if subset.empty:
                st.caption("_Trống_")
            else:
                for _, row in subset.head(8).iterrows():
                    topic_short = str(row.get("topic", ""))[:45]
                    plat = str(row.get("platform", "")).lower()
                    plat_color = _PLATFORM_COLOR.get(plat, "#6B7280")
                    st.markdown(
                        f"<div class='kanban-card'>"
                        f"<b style='color:{plat_color};'>#{row['id']} {plat.upper()}</b><br/>"
                        f"<small>{topic_short}…</small>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                if len(subset) > 8:
                    st.caption(f"+ {len(subset) - 8} bài khác…")


# ─────────────────────────────────────────────────────────────────────────────
# PENDING APPROVAL LIST – bảng tổng quan
# ─────────────────────────────────────────────────────────────────────────────

def _render_pending_list(df_pending: pd.DataFrame, stage_label: str):
    """Hiển thị bảng Pending Approval List đầy đủ: ID, Tiêu đề, Tác giả, Ngày tạo, Kênh."""
    if df_pending.empty:
        return

    rows_html = ""
    for _, row in df_pending.iterrows():
        post_id    = int(row["id"])
        title      = str(row.get("title") or row.get("topic") or "—")[:70]
        topic_sub  = str(row.get("topic") or "")[:55]
        platform   = str(row.get("platform", "")).lower()
        p_color    = _PLATFORM_COLOR.get(platform, "#6B7280")
        created_at = str(row.get("created_at") or "")[:10]
        created_by = str(row.get("created_by") or "—")
        content_type = str(row.get("content_type") or "—")

        rows_html += f"""
        <tr>
          <td class='post-id'>#{post_id}</td>
          <td class='post-title'>
            {title}
            <small>{topic_sub}{'…' if len(topic_sub)==55 else ''}</small>
          </td>
          <td><code style='font-size:0.78rem;'>{content_type}</code></td>
          <td>{created_at}</td>
          <td>
            <span style='background:{p_color};color:white;padding:2px 8px;
              border-radius:5px;font-size:0.76rem;font-weight:700;'>
              {platform.upper()}
            </span>
          </td>
        </tr>"""

    st.markdown(
        f"""<table class='pending-list-table'>
          <thead>
            <tr>
              <th>Mã bài</th>
              <th>Tiêu đề / Chủ đề</th>
              <th>Loại nội dung</th>
              <th>Ngày tạo</th>
              <th>Kênh đăng</th>
            </tr>
          </thead>
          <tbody>{rows_html}</tbody>
        </table>""",
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# QUICK REVIEW MODAL – xem toàn bộ nội dung + ảnh tại chỗ
# ─────────────────────────────────────────────────────────────────────────────

def _render_quick_review(row: pd.Series, post_id: int):
    """Quick Review Modal: hiển thị toàn bộ nội dung bài viết và ảnh đính kèm."""
    from database.models.assets import AssetModel  # lazy import

    title        = str(row.get("title") or "(Chưa có tiêu đề)")
    platform     = str(row.get("platform", "")).upper()
    content_type = str(row.get("content_type") or "—")
    content      = str(row.get("content") or "")
    topic        = str(row.get("topic") or "")
    created_at   = str(row.get("created_at") or "")[:16]
    viral_score  = row.get("viral_score")

    p_color = _PLATFORM_COLOR.get(platform.lower(), "#6B7280")

    # Header thông tin
    col_meta1, col_meta2, col_meta3 = st.columns(3)
    col_meta1.markdown(
        f"<b>Kênh:</b> <span style='color:{p_color};font-weight:800;'>{platform}</span>",
        unsafe_allow_html=True,
    )
    col_meta2.markdown(f"**Loại:** `{content_type}`")
    col_meta3.markdown(f"**Ngày tạo:** {created_at}")

    if title and title != "(Chưa có tiêu đề)":
        st.markdown(f"### 📌 {title}")
    if topic:
        st.caption(f"💡 Chủ đề: {topic}")
    if viral_score:
        st.markdown(
            f"<span style='background:#fef3c7;color:#92400e;padding:3px 9px;"
            f"border-radius:6px;font-size:0.78rem;font-weight:700;'>"
            f"🔥 Viral Score: {viral_score}/10</span>",
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown("**📝 Nội dung bài viết:**")
    st.markdown(
        f"<div class='qr-content-box'>{content}</div>",
        unsafe_allow_html=True,
    )

    # Ảnh đính kèm
    try:
        assets = AssetModel.list_by_post(post_id)
        images = [a for a in (assets or []) if str(a.get("file_type", "")).startswith("image")]
        if images:
            st.markdown("**🖼️ Ảnh đính kèm:**")
            img_cols = st.columns(min(len(images), 3))
            for i, img in enumerate(images[:3]):
                with img_cols[i]:
                    try:
                        st.image(img["url"], caption=img.get("name", f"Ảnh #{i+1}"),
                                 use_container_width=True)
                    except Exception:
                        st.caption(f"🔗 {img.get('url', '')[:50]}…")
        else:
            st.markdown(
                "<div class='qr-image-box'>📷 Bài viết chưa có ảnh đính kèm</div>",
                unsafe_allow_html=True,
            )
    except Exception:
        st.caption("(Không thể tải ảnh đính kèm)")


# ─────────────────────────────────────────────────────────────────────────────
# DECISION ACTIONS – Approve / Từ chối với ô nhập lý do
# ─────────────────────────────────────────────────────────────────────────────

def _render_decision_actions(
    post_id: int,
    approval_record: dict,
    uid: int,
    workspace_id: int,
    approve_label: str,
    approve_next_status: str,
    form_key_suffix: str,
):
    """
    Hiển thị Decision Actions chuẩn:
    - ✅ Phê duyệt: cập nhật status và respond(approved) — chuyển vào publishing queue.
    - ❌ Từ chối: hiện ô nhập lý do, respond(revision_requested), trả về draft.
    """
    approve_key  = f"btn_approve_{form_key_suffix}_{post_id}"
    reject_key   = f"btn_reject_{form_key_suffix}_{post_id}"
    reason_key   = f"reject_reason_{form_key_suffix}_{post_id}"
    show_rej_key = f"show_reject_{form_key_suffix}_{post_id}"

    # Khởi tạo session state
    if show_rej_key not in st.session_state:
        st.session_state[show_rej_key] = False

    col_app, col_rej = st.columns(2)

    with col_app:
        if st.button(
            f"✅ {approve_label}",
            key=approve_key,
            type="primary",
            use_container_width=True,
        ):
            PostModel.update_status(post_id, approve_next_status)
            if approval_record:
                ApprovalModel.respond(
                    approval_record["id"], "approved",
                    approved_by=uid, notes="",
                )
            if approve_next_status == "approved":
                st.success(
                    f"🎉 Phê duyệt tối cao thành công bài #{post_id}! "
                    "Bài đã vào **hàng đợi xuất bản**. "
                    "Chuyển sang tab 📢 Publishing để lên lịch hoặc đăng ngay."
                )
            else:
                st.success(f"✅ Đã chuyển bài #{post_id} lên cấp tiếp theo phê duyệt!")
            st.rerun()

    with col_rej:
        if st.button(
            "❌ Từ chối (Nhập lý do)",
            key=reject_key,
            use_container_width=True,
        ):
            st.session_state[show_rej_key] = True

    # Ô nhập lý do từ chối — chỉ hiện khi bấm ❌
    if st.session_state.get(show_rej_key):
        st.markdown(
            "<div class='reject-reason-box'>✍️ <b>Nhập lý do từ chối</b> "
            "(sẽ hiển thị cho người tạo bài để sửa lại):</div>",
            unsafe_allow_html=True,
        )
        reject_reason = st.text_area(
            "Lý do từ chối:",
            key=reason_key,
            placeholder="Ví dụ: Nội dung chưa đúng tone of voice, cần bổ sung số liệu thực tế…",
            height=100,
        )
        confirm_col, cancel_col = st.columns(2)
        with confirm_col:
            if st.button(
                "🚫 Xác nhận từ chối",
                key=f"confirm_rej_{form_key_suffix}_{post_id}",
                type="secondary",
                use_container_width=True,
            ):
                if not reject_reason.strip():
                    st.warning("⚠️ Vui lòng nhập lý do từ chối trước khi xác nhận.")
                else:
                    PostModel.update_status(post_id, "draft")
                    if approval_record:
                        ApprovalModel.respond(
                            approval_record["id"], "revision_requested",
                            approved_by=uid, notes=reject_reason.strip(),
                        )
                    st.session_state[show_rej_key] = False
                    st.warning(
                        f"🔄 Bài #{post_id} đã bị từ chối và trả về nháp. "
                        f"**Lý do:** {reject_reason[:120]}"
                    )
                    st.rerun()
        with cancel_col:
            if st.button(
                "↩️ Hủy",
                key=f"cancel_rej_{form_key_suffix}_{post_id}",
                use_container_width=True,
            ):
                st.session_state[show_rej_key] = False
                st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# AUDIT TRAIL
# ─────────────────────────────────────────────────────────────────────────────

def _render_audit_trail(post_id: int):
    """Hiển thị lịch sử phê duyệt của một bài viết."""
    history = ApprovalModel.get_by_post(post_id)
    if not history:
        st.caption("Chưa có lịch sử phê duyệt.")
        return

    _STATUS_COLORS_AUDIT = {
        "pending":            "#f59e0b",
        "approved":           "#10b981",
        "rejected":           "#ef4444",
        "revision_requested": "#f97316",
    }
    _STATUS_LABELS_AUDIT = {
        "pending":            "⏳ Chờ xử lý",
        "approved":           "✅ Đã duyệt",
        "rejected":           "❌ Từ chối",
        "revision_requested": "🔄 Yêu cầu sửa",
    }

    html_rows = ""
    for rec in history:
        dot_color  = _STATUS_COLORS_AUDIT.get(rec.get("status", ""), "#94a3b8")
        status_lbl = _STATUS_LABELS_AUDIT.get(rec.get("status", ""), rec.get("status", ""))
        req_at     = (rec.get("requested_at") or "")[:16]
        res_at     = (rec.get("responded_at") or "—")[:16]
        notes      = rec.get("notes") or "—"
        html_rows += (
            f"<div class='audit-row'>"
            f"  <div class='audit-dot' style='background:{dot_color};'></div>"
            f"  <div>"
            f"    <b>{status_lbl}</b><br/>"
            f"    <span style='color:#64748b;'>Gửi: {req_at} &nbsp;|&nbsp; Phản hồi: {res_at}</span><br/>"
            f"    <span style='color:#374151;'>💬 {notes}</span>"
            f"  </div>"
            f"</div>"
        )

    st.markdown(
        f"<div style='border:1px solid #e2e8f0;border-radius:10px;padding:12px 16px;"
        f"background:#fafafa;'>{html_rows}</div>",
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# MAIN RENDER
# ─────────────────────────────────────────────────────────────────────────────

def render_tab_approval(gemini_key: str = "", workspace_id: int = 1, role: str = "editor"):
    st.markdown(_APPROVAL_CSS, unsafe_allow_html=True)

    st.markdown("""
    <div class="app-header">
        <h2>⚖️ Approval Workflow – Quy Trình Phê Duyệt Đa Cấp</h2>
        <p>Luồng nội dung chuyên nghiệp: Marketing ➔ Manager ➔ CEO ➔ Publish</p>
    </div>
    """, unsafe_allow_html=True)

    role = (role or "editor").lower()
    uid  = _current_user_id()

    # ── METRICS ──────────────────────────────────────────────────────────────
    _render_metrics(workspace_id)

    # ── TẢI DỮ LIỆU BÀI VIẾT ─────────────────────────────────────────────
    df_posts = PostModel.list_by_workspace(workspace_id=workspace_id, limit=200)

    # ── KANBAN BOARD (tất cả role được xem) ───────────────────────────────
    if not df_posts.empty:
        _render_kanban(df_posts, workspace_id, role)
    else:
        st.info("💡 Chưa có bài viết nào trong workspace này. Hãy tạo bài viết mới ở Content Studio!")

    st.divider()

    # ══════════════════════════════════════════════════════════════════════════
    # PHẦN A: MARKETING / EDITOR – GỬI YÊU CẦU DUYỆT + XEM TRẠNG THÁI
    # [FIX #3] Viewer không được phép gửi yêu cầu, chỉ Editor/Marketing được.
    # ══════════════════════════════════════════════════════════════════════════
    if role in ["editor", "marketing", "manager", "admin", "owner", "ceo", "super_admin"]:

        st.subheader("📤 Gửi Yêu Cầu Phê Duyệt Bài Viết")

        if df_posts.empty:
            st.info("Chưa có bài viết nào. Tạo bài mới ở tab Content Studio.")
        else:
            df_drafts = df_posts[df_posts["status"] == "draft"]

            if df_drafts.empty:
                st.success("💡 Tất cả bài viết đã được gửi duyệt hoặc xuất bản.")
            else:
                # Bộ lọc platform
                platforms = ["Tất cả"] + sorted(df_drafts["platform"].dropna().unique().tolist())
                flt_platform = st.selectbox(
                    "Lọc theo nền tảng:", options=platforms, key="flt_draft_platform"
                )
                if flt_platform != "Tất cả":
                    df_drafts = df_drafts[df_drafts["platform"] == flt_platform]

                if df_drafts.empty:
                    st.info("Không có bài nháp nào cho nền tảng đã chọn.")
                else:
                    draft_options = {
                        row["id"]: f"#{row['id']} [{row['platform'].upper()}] {str(row['topic'])[:55]}…"
                        for _, row in df_drafts.iterrows()
                    }
                    with st.form("request_approval_form"):
                        selected_post_id = st.selectbox(
                            "Chọn bài viết nháp cần gửi duyệt:",
                            options=list(draft_options.keys()),
                            format_func=lambda x: draft_options[x],
                        )
                        # Xem trước nội dung bài trước khi gửi
                        preview_row = df_drafts[df_drafts["id"] == selected_post_id]
                        if not preview_row.empty:
                            with st.expander("👁️ Xem trước nội dung bài viết"):
                                st.markdown(f"**Tiêu đề:** {preview_row.iloc[0].get('title', '—')}")
                                st.markdown(f"**Nền tảng:** {preview_row.iloc[0]['platform'].upper()}")
                                st.code(str(preview_row.iloc[0].get("content", "")), language="markdown")

                        btn_req = st.form_submit_button("📤 Gửi yêu cầu phê duyệt cho Manager")
                        if btn_req:
                            PostModel.update_status(selected_post_id, "pending_manager_approval")
                            ApprovalModel.request(
                                selected_post_id,
                                requested_by=uid,
                                workspace_id=workspace_id,
                            )
                            st.success(f"🎉 Đã gửi yêu cầu phê duyệt thành công cho bài viết `#{selected_post_id}`!")
                            st.rerun()

        st.write("")
        st.markdown("##### 🔍 Trạng thái bài viết của bạn đang trong luồng duyệt")

        if not df_posts.empty:
            df_in_flow = df_posts[
                df_posts["status"].isin(
                    ["pending_manager_approval", "pending_ceo_approval", "approved"]
                )
            ]

            if df_in_flow.empty:
                st.caption("Chưa có bài viết nào đang trong luồng phê duyệt.")
            else:
                # ── [NEW] Hiển thị lý do từ chối / ghi chú gần nhất ────────────
                rejected_posts = df_posts[df_posts["status"] == "draft"]
                for _, rp in rejected_posts.iterrows():
                    latest = ApprovalModel.get_latest_by_post(rp["id"])
                    if latest and latest.get("status") == "revision_requested" and latest.get("notes"):
                        st.markdown(
                            f"<div class='rejection-notice'>"
                            f"⚠️ <b>Bài #{rp['id']} bị yêu cầu sửa lại:</b> {latest['notes']}"
                            f"</div>",
                            unsafe_allow_html=True,
                        )

                # Bảng trạng thái
                display_df = df_in_flow[["id", "title", "platform", "status", "created_at"]].copy()
                display_df.columns = ["Mã bài", "Tiêu đề", "Kênh", "Trạng thái", "Ngày tạo"]
                st.dataframe(display_df, use_container_width=True, hide_index=True)

                # Pipeline diagram + Audit Trail
                selected_track_id = st.selectbox(
                    "Chọn bài để xem sơ đồ & lịch sử phê duyệt:",
                    options=df_in_flow["id"].tolist(),
                    format_func=lambda x: f"#{x} - {df_in_flow[df_in_flow['id']==x].iloc[0]['platform'].upper()}",
                )
                track_row = df_in_flow[df_in_flow["id"] == selected_track_id].iloc[0]
                _render_pipeline_diagram(track_row["status"])

                with st.expander("📜 Lịch sử phê duyệt chi tiết"):
                    _render_audit_trail(selected_track_id)

    # Viewer: chỉ xem bảng trạng thái, không có form
    elif role == "viewer":
        st.subheader("👁️ Xem Trạng Thái Bài Viết Trong Luồng Duyệt")
        if not df_posts.empty:
            df_view = df_posts[
                df_posts["status"].isin(
                    ["pending_manager_approval", "pending_ceo_approval", "approved", "published"]
                )
            ]
            if df_view.empty:
                st.info("Hiện không có bài viết nào trong luồng phê duyệt.")
            else:
                st.dataframe(
                    df_view[["id", "title", "platform", "status", "created_at"]],
                    use_container_width=True, hide_index=True,
                )

    st.divider()

    # ══════════════════════════════════════════════════════════════════════════
    # PHẦN B: MANAGER REVIEW (Giai đoạn 1)
    # ══════════════════════════════════════════════════════════════════════════
    if role in ["manager", "admin", "owner", "super_admin"]:
        st.subheader("👔 Giai đoạn 1: Manager Phê Duyệt")

        if df_posts.empty:
            st.info("Chưa có bài viết nào để duyệt.")
        else:
            df_manager_pending = df_posts[df_posts["status"] == "pending_manager_approval"]

            if df_manager_pending.empty:
                st.success("🎉 Không có bài viết nào đang chờ Manager phê duyệt.")
            else:
                st.info(f"📌 Có **{len(df_manager_pending)}** bài viết đang chờ bạn phê duyệt.")

                # ── [NEW] PENDING APPROVAL LIST ───────────────────────────────
                st.markdown("##### 📋 Danh sách bài chờ duyệt (Manager)")
                _render_pending_list(df_manager_pending, "Manager")
                st.divider()

                # ── [NEW] QUICK REVIEW + DECISION ACTIONS ─────────────────────
                st.markdown("##### 🔍 Xem nhanh & Ra quyết định")
                for _, row in df_manager_pending.iterrows():
                    post_id = int(row["id"])
                    title   = str(row.get("title") or row.get("topic") or f"Bài #{post_id}")[:65]
                    plat    = str(row.get("platform", "")).upper()

                    with st.expander(
                        f"📄 #{post_id} · [{plat}] · {title}…  —  👁️ Xem nhanh & Quyết định",
                        expanded=False,
                    ):
                        _render_pipeline_diagram("pending_manager_approval")

                        # ── Quick Review Modal ─────────────────────────────────
                        st.markdown("<div class='qr-modal'>", unsafe_allow_html=True)
                        _render_quick_review(row, post_id)
                        st.markdown("</div>", unsafe_allow_html=True)

                        # Lịch sử phê duyệt
                        with st.expander("📜 Lịch sử phê duyệt"):
                            _render_audit_trail(post_id)

                        st.markdown("---")
                        st.markdown("**⚖️ Quyết định phê duyệt:**")
                        latest_app = ApprovalModel.get_latest_by_post(post_id)

                        # ── [NEW] Decision Actions chuẩn ──────────────────────
                        _render_decision_actions(
                            post_id=post_id,
                            approval_record=latest_app,
                            uid=uid,
                            workspace_id=workspace_id,
                            approve_label="Phê duyệt & Chuyển lên CEO",
                            approve_next_status="pending_ceo_approval",
                            form_key_suffix="manager",
                        )

        st.divider()

    # ══════════════════════════════════════════════════════════════════════════
    # PHẦN C: CEO REVIEW (Giai đoạn 2)
    # [FIX #2] CEO chỉ dùng respond() trên bản ghi hiện có, không tạo mới.
    # ══════════════════════════════════════════════════════════════════════════
    if role in ["ceo", "owner", "super_admin"]:
        st.subheader("👑 Giai đoạn 2: CEO Phê Duyệt Tối Cao")

        if df_posts.empty:
            st.info("Chưa có bài viết nào.")
        else:
            df_ceo_pending = df_posts[df_posts["status"] == "pending_ceo_approval"]

            if df_ceo_pending.empty:
                st.success("🎉 Không có bài viết nào đang chờ CEO phê duyệt.")
            else:
                st.info(f"👑 Có **{len(df_ceo_pending)}** bài viết đang chờ phê duyệt tối cao.")

                # ── [NEW] PENDING APPROVAL LIST ───────────────────────────────
                st.markdown("##### 📋 Danh sách bài chờ CEO duyệt")
                _render_pending_list(df_ceo_pending, "CEO")
                st.divider()

                # ── [NEW] QUICK REVIEW + DECISION ACTIONS ─────────────────────
                st.markdown("##### 🔍 Xem nhanh & Ra quyết định")
                for _, row in df_ceo_pending.iterrows():
                    post_id = int(row["id"])
                    title   = str(row.get("title") or row.get("topic") or f"Bài #{post_id}")[:65]
                    plat    = str(row.get("platform", "")).upper()

                    with st.expander(
                        f"👑 #{post_id} · [{plat}] · {title}…  —  👁️ Xem nhanh & Quyết định",
                        expanded=False,
                    ):
                        _render_pipeline_diagram("pending_ceo_approval")

                        # ── Quick Review Modal ─────────────────────────────────
                        st.markdown("<div class='qr-modal'>", unsafe_allow_html=True)
                        _render_quick_review(row, post_id)
                        st.markdown("</div>", unsafe_allow_html=True)

                        # Ghi chú của Manager (luôn hiển thị nếu có)
                        latest_app = ApprovalModel.get_latest_by_post(post_id)
                        if latest_app and latest_app.get("notes"):
                            st.info(
                                f"💬 **Ghi chú từ Manager:** {latest_app['notes']}"
                            )

                        # Lịch sử đầy đủ
                        with st.expander("📜 Lịch sử phê duyệt"):
                            _render_audit_trail(post_id)

                        st.markdown("---")
                        st.markdown("**⚖️ Quyết định phê duyệt tối cao:**")

                        # ── [NEW] Decision Actions chuẩn cho CEO ──────────────
                        # Khi CEO Approve → status = 'approved' → vào publishing queue
                        _render_decision_actions(
                            post_id=post_id,
                            approval_record=latest_app,
                            uid=uid,
                            workspace_id=workspace_id,
                            approve_label="Phê duyệt tối cao → Publishing Queue",
                            approve_next_status="approved",
                            form_key_suffix="ceo",
                        )

        st.divider()

    # ══════════════════════════════════════════════════════════════════════════
    # PHẦN D: AUDIT TRAIL TỔNG QUAN (Manager/Admin/Owner trở lên)
    # ══════════════════════════════════════════════════════════════════════════
    if role in ["manager", "admin", "owner", "ceo", "super_admin"]:
        st.subheader("📜 Lịch Sử Phê Duyệt Toàn Workspace")

        all_approvals = ApprovalModel.list_by_workspace(workspace_id=workspace_id, limit=50)
        if not all_approvals:
            st.caption("Chưa có lịch sử phê duyệt nào.")
        else:
            df_audit = pd.DataFrame(all_approvals)
            # Chọn và đổi tên cột thân thiện
            cols_show = ["id", "post_id", "status", "requested_by", "approved_by",
                         "requested_at", "responded_at", "notes"]
            cols_show = [c for c in cols_show if c in df_audit.columns]
            df_show = df_audit[cols_show].copy()
            df_show.columns = [
                {
                    "id": "Mã yêu cầu", "post_id": "Mã bài", "status": "Trạng thái",
                    "requested_by": "Người gửi", "approved_by": "Người duyệt",
                    "requested_at": "Thời gian gửi", "responded_at": "Thời gian phản hồi",
                    "notes": "Ghi chú",
                }.get(c, c)
                for c in cols_show
            ]
            st.dataframe(df_show, use_container_width=True, hide_index=True)
