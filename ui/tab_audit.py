"""ui/tab_audit.py
==================
Tab xem Audit Log — chỉ hiển thị với Manager / CEO / Owner / Admin.
Hiển thị: ai làm, lúc nào, làm gì — có thể lọc và export.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from database.repositories import AuditRepository
from core.rbac import render_role_badge, get_role_display
from core.audit_logger import AuditAction


# Map action → icon + label tiếng Việt
ACTION_LABELS = {
    AuditAction.LOGIN:            ("🔓", "Đăng nhập"),
    AuditAction.LOGOUT:           ("🔒", "Đăng xuất"),
    AuditAction.REGISTER:         ("✨", "Đăng ký"),
    AuditAction.LOGIN_FAILED:     ("⚠️", "Đăng nhập thất bại"),
    AuditAction.CREATE_POST:      ("📝", "Tạo bài viết"),
    AuditAction.AUTO_POST:        ("📤", "Tự động đăng"),
    AuditAction.DELETE_POST:      ("🗑️", "Xóa bài"),
    AuditAction.CREATE_PLAN:      ("📅", "Tạo kế hoạch"),
    AuditAction.CREATE_KNOWLEDGE: ("🧠", "Tạo AI Knowledge"),
    AuditAction.CREATE_WORKSPACE: ("🏢", "Tạo Workspace"),
    AuditAction.ADD_MEMBER:       ("👤➕", "Thêm thành viên"),
    AuditAction.REMOVE_MEMBER:    ("👤❌", "Xóa thành viên"),
    AuditAction.CHANGE_ROLE:      ("🔄", "Đổi vai trò"),
    AuditAction.SYSTEM:           ("⚙️", "Hệ thống"),
}

ENTITY_LABELS = {
    "auth":      "🔐 Xác thực",
    "post":      "📝 Bài viết",
    "plan":      "📅 Kế hoạch",
    "knowledge": "🧠 Knowledge",
    "member":    "👥 Thành viên",
    "workspace": "🏢 Workspace",
}


def _fmt_timestamp(ts: str) -> str:
    """Chuyển ISO timestamp → DD/MM/YYYY HH:MM:SS."""
    try:
        dt = datetime.fromisoformat(str(ts))
        return dt.strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        return str(ts)


def _fmt_action(action: str) -> str:
    icon, label = ACTION_LABELS.get(action, ("🔹", action))
    return f"{icon} {label}"


def render_tab_audit(workspace_id: int | None = None, role: str = "manager"):
    """
    Render tab Audit Log.
    Chỉ gọi khi role là manager / ceo / owner / admin / super_admin.
    """
    st.markdown(render_role_badge(role), unsafe_allow_html=True)
    st.header("🗒️ Audit Log — Nhật ký hoạt động hệ thống")
    st.caption("Ghi lại toàn bộ hành động quan trọng: ai làm, lúc nào, làm gì.")

    # ─── Bộ lọc ──────────────────────────────────────────────────────────
    with st.expander("🔍 Bộ lọc / Tìm kiếm", expanded=True):
        f_col1, f_col2, f_col3 = st.columns(3)
        filter_email = f_col1.text_input("🔎 Lọc theo Email:", placeholder="user@example.com")
        filter_action = f_col2.selectbox(
            "📋 Loại hành động:",
            options=["Tất cả"] + list(ACTION_LABELS.keys()),
            format_func=lambda a: "Tất cả" if a == "Tất cả" else _fmt_action(a)
        )
        filter_entity = f_col3.selectbox(
            "🏷️ Đối tượng:",
            options=["Tất cả"] + list(ENTITY_LABELS.keys()),
            format_func=lambda e: "Tất cả" if e == "Tất cả" else ENTITY_LABELS.get(e, e)
        )
        limit = st.slider("📊 Số bản ghi hiển thị:", min_value=20, max_value=500, value=100, step=20)

    # ─── Lấy dữ liệu từ Repository ──────────────────────────────────────
    df = AuditRepository.get_logs(
        workspace_id=workspace_id,
        user_email=filter_email.strip() if filter_email.strip() else None,
        action=filter_action if filter_action != "Tất cả" else None,
        entity_type=filter_entity if filter_entity != "Tất cả" else None,
        limit=limit
    )

    # ─── Thống kê tóm tắt ────────────────────────────────────────────────
    summary = AuditRepository.get_summary(workspace_id=workspace_id)
    if summary:
        st.subheader("📊 Thống kê nhanh")
        metric_cols = st.columns(min(len(summary), 5))
        for i, (action, count) in enumerate(list(summary.items())[:5]):
            icon, label = ACTION_LABELS.get(action, ("🔹", action))
            metric_cols[i].metric(f"{icon} {label}", count)
        st.markdown("---")

    # ─── Bảng dữ liệu chính ──────────────────────────────────────────────
    if df.empty:
        st.info("📭 Chưa có bản ghi audit log nào phù hợp với điều kiện lọc.")
        return

    st.markdown(f"**Tìm thấy {len(df)} bản ghi** (mới nhất trước)")

    # Format để hiển thị đẹp
    display_df = df.copy()
    display_df["Thời gian"]    = display_df["timestamp"].apply(_fmt_timestamp)
    display_df["Người thực hiện"] = display_df["user_email"].fillna("—")
    display_df["Hành động"]   = display_df["action"].apply(_fmt_action)
    display_df["Đối tượng"]   = display_df["entity_type"].apply(
        lambda e: ENTITY_LABELS.get(e, e) if pd.notna(e) and e else "—"
    )
    display_df["Mô tả"]       = display_df["description"].fillna("—")
    display_df["Workspace"]   = display_df["workspace_id"].apply(
        lambda v: f"WS#{int(v)}" if pd.notna(v) else "Toàn cục"
    )

    show_cols = ["Thời gian", "Người thực hiện", "Hành động", "Đối tượng", "Mô tả", "Workspace"]
    display_df = display_df[show_cols]

    # Cho chọn dòng để xem chi tiết
    selection = st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row"
    )

    selected_rows = selection.get("selection", {}).get("rows", [])
    if selected_rows:
        idx = selected_rows[0]
        raw_row = df.iloc[idx]
        st.markdown("---")
        st.subheader("🔍 Chi tiết bản ghi")
        det_col1, det_col2 = st.columns(2)
        det_col1.markdown(f"**⏰ Thời gian:** {_fmt_timestamp(raw_row['timestamp'])}")
        det_col1.markdown(f"**👤 Người thực hiện:** `{raw_row.get('user_email', '—')}`")
        det_col1.markdown(f"**🔹 Hành động:** {_fmt_action(str(raw_row['action']))}")
        det_col1.markdown(f"**🏷️ Đối tượng:** {ENTITY_LABELS.get(str(raw_row.get('entity_type', '')), raw_row.get('entity_type', '—'))}")
        det_col1.markdown(f"**🆔 Entity ID:** {raw_row.get('entity_id', '—')}")
        det_col2.markdown(f"**📝 Mô tả:**\n\n> {raw_row.get('description', '—')}")

        old_val = raw_row.get("old_value")
        new_val = raw_row.get("new_value")
        if old_val and str(old_val) != "None":
            det_col2.markdown(f"**🔴 Giá trị cũ:**")
            det_col2.code(old_val, language="json")
        if new_val and str(new_val) != "None":
            det_col2.markdown(f"**🟢 Giá trị mới:**")
            det_col2.code(new_val, language="json")

    # ─── Export ──────────────────────────────────────────────────────────
    st.markdown("---")
    exp_col1, exp_col2, _ = st.columns([1, 1, 3])
    with exp_col1:
        csv_data = display_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "📥 Xuất CSV",
            data=csv_data,
            file_name=f"audit_log_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )
    with exp_col2:
        # Export raw với old/new value đầy đủ
        raw_csv = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "📥 Xuất CSV (đầy đủ)",
            data=raw_csv,
            file_name=f"audit_log_raw_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )
