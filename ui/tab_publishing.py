import io
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from database.models.posts import PostModel
from database.models.assets import AssetModel
from social.publishers import post_to_facebook, post_to_zalo_oa, post_to_linkedin
from core.audit_logger import log_auto_post
from core.rbac import can_perform, normalize_role
from config.config import logger

_PUBLISHING_CSS = """
<style>
.pub-header {
    background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 50%, #1e3a8a 100%);
    border-radius: 16px;
    padding: 1.5rem 2rem;
    margin-bottom: 1.8rem;
    color: white;
    text-align: center;
}
.pub-header h2 { color: white !important; margin: 0 0 0.3rem 0; font-size: 1.6rem; }
.pub-header p { color: rgba(255,255,255,0.85); margin: 0; font-size: 0.95rem; }

.status-badge {
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 0.8rem;
    font-weight: 700;
}
.status-configured   { background-color: #d1fae5; color: #065f46; }
.status-unconfigured { background-color: #fee2e2; color: #991b1b; }

/* Thumbnail queue badges */
.thumb-ready    { background:#dbeafe; color:#1e40af; padding:3px 8px; border-radius:5px; font-size:.78rem; font-weight:700; }
.thumb-approved { background:#d1fae5; color:#065f46; padding:3px 8px; border-radius:5px; font-size:.78rem; font-weight:700; }
.thumb-pending  { background:#fef3c7; color:#92400e; padding:3px 8px; border-radius:5px; font-size:.78rem; font-weight:700; }
.thumb-notset   { background:#f3f4f6; color:#374151; padding:3px 8px; border-radius:5px; font-size:.78rem; font-weight:700; }
.thumb-error    { background:#fee2e2; color:#991b1b; padding:3px 8px; border-radius:5px; font-size:.78rem; font-weight:700; }

.spec-box {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 8px;
    font-size: 0.88rem;
}
.safe-info { color: #16a34a; font-weight: 600; }
.mockup-wrap { border: 2px solid #e2e8f0; border-radius: 10px; padding: 10px; background:#fafafa; }
</style>
"""


def _test_facebook(page_id, token):
    if not page_id or not token:
        return False, "Chưa cấu hình Page ID hoặc Access Token."
    try:
        url = f"https://graph.facebook.com/{page_id}?fields=name&access_token={token}"
        res = requests.get(url, timeout=5)
        data = res.json()
        if "name" in data:
            return True, f"Kết nối OK! Tên Page: {data['name']}"
        return False, f"Lỗi FB: {data.get('error', {}).get('message')}"
    except Exception as e:
        return False, f"Lỗi kết nối: {str(e)}"


def _test_zalo_oa(token):
    if not token:
        return False, "Chưa cấu hình Access Token."
    try:
        url = "https://openapi.zalo.me/v2.0/oa/getoa"
        headers = {"access_token": token}
        res = requests.get(url, headers=headers, timeout=5)
        data = res.json()
        if data.get("error") == 0:
            oa_data = data.get("data", {})
            return True, f"Kết nối OK! Tên OA: {oa_data.get('name', 'N/A')}"
        return False, f"Lỗi Zalo: {data.get('message')}"
    except Exception as e:
        return False, f"Lỗi kết nối: {str(e)}"


def _test_linkedin(urn, token):
    if not urn or not token:
        return False, "Chưa cấu hình Author URN hoặc Access Token."
    try:
        url = "https://api.linkedin.com/v2/me"
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Restli-Protocol-Version": "2.0.0"
        }
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            data = res.json()
            name = f"{data.get('localizedFirstName', '')} {data.get('localizedLastName', '')}".strip()
            return True, f"Kết nối OK! Tên User: {name}"
        return False, f"Lỗi LinkedIn (HTTP {res.status_code}): {res.text[:100]}"
    except Exception as e:
        return False, f"Lỗi kết nối: {str(e)}"


# ============================================================
# THUMBNAIL HELPER FUNCTIONS
# ============================================================

_THUMB_STATUS_MAP = {
    "not_set":          ("➕ Chưa gắn",    "thumb-notset"),
    "pending_approval": ("⏳ Chờ duyệt",   "thumb-pending"),
    "approved":         ("✅ Approved",     "thumb-approved"),
    "ready":            ("🚀 Ready",        "thumb-ready"),
    "error":            ("❌ Lỗi",          "thumb-error"),
}

_LIFECYCLE_COLORS = {
    "draft":     ("📝 Draft",     "#F59E0B"),
    "approved":  ("✅ Approved",  "#10B981"),
    "published": ("🚀 Published", "#3B82F6"),
    "archived":  ("🗄️ Archived", "#6B7280"),
}


def _try_import_service():
    """Import thumbnail service — trả về None nếu Pillow chưa cài."""
    try:
        from services.thumbnail_publishing_service import (
            ThumbnailProcessor, ThumbnailApprovalGate,
            PublishQueue, RetryManager,
            check_publish_readiness, build_platform_mockup_html,
            get_spec, list_post_types, PLATFORM_SPECS,
        )
        return {
            "ThumbnailProcessor":    ThumbnailProcessor,
            "ThumbnailApprovalGate": ThumbnailApprovalGate,
            "PublishQueue":          PublishQueue,
            "RetryManager":          RetryManager,
            "check_publish_readiness": check_publish_readiness,
            "build_platform_mockup_html": build_platform_mockup_html,
            "get_spec":              get_spec,
            "list_post_types":       list_post_types,
            "PLATFORM_SPECS":        PLATFORM_SPECS,
        }
    except ImportError as e:
        logger.warning(f"[Publishing] thumbnail_publishing_service không khả dụng: {e}")
        return None


def _render_spec_panel(platform: str, post_type: str, svc: dict):
    """Hiển thị thông số kỹ thuật thumbnail cho platform + post_type."""
    spec = svc["get_spec"](platform, post_type)
    if not spec:
        return
    st.markdown(
        f"""
        <div class="spec-box">
          <b>📐 {spec.name}</b> &nbsp;
          <code>{spec.width} × {spec.height} px</code> &nbsp;·&nbsp;
          Tỷ lệ <code>{spec.ratio_str}</code> &nbsp;·&nbsp;
          Max <code>{spec.max_mb:.1f} MB</code><br>
          <span class="safe-info">🟢 Safe Zone: {spec.safe_width}×{spec.safe_height}px</span>
          &nbsp;(Margin T:{spec.safe_margin_top} B:{spec.safe_margin_bottom}
          L:{spec.safe_margin_left} R:{spec.safe_margin_right}px)<br>
          <small>📋 {spec.notes}</small>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_thumbnail_manager(
    post_id: int,
    post_content: str,
    platform: str,
    workspace_id: int,
    user_id: int,
    user_role: str,
    svc: dict,
):
    """
    Panel quản lý Thumbnail tích hợp vào luồng đăng bài thủ công.
    Hiển thị: Spec → Thumbnail hiện tại → Safe Zone → Mock-up Preview → Approval Gate.
    Trả về True nếu thumbnail đã sẵn sàng publish.
    """
    ThumbnailApprovalGate = svc["ThumbnailApprovalGate"]
    ThumbnailProcessor    = svc["ThumbnailProcessor"]
    get_spec              = svc["get_spec"]
    list_post_types       = svc["list_post_types"]
    build_mockup          = svc["build_platform_mockup_html"]

    st.markdown("#### 🖼️ Quản lý Thumbnail")

    # ── Chọn loại bài đăng ────────────────────────────────
    types = list_post_types(platform)
    if not types:
        st.caption("Platform không hỗ trợ thumbnail spec.")
        return True   # không chặn publish

    type_key = f"pub_post_type_{post_id}"
    post_type = st.selectbox(
        "Loại bài đăng:",
        options=types,
        key=type_key,
        format_func=lambda t: svc["PLATFORM_SPECS"].get(
            platform.lower(), {}).get(t, type("X", (), {"name": t})()).name
    )
    spec = get_spec(platform, post_type)

    # ── Hiện thông số kỹ thuật ────────────────────────────
    if spec:
        _render_spec_panel(platform, post_type, svc)

    # ── Lấy thumbnail hiện tại ────────────────────────────
    approval_check = ThumbnailApprovalGate.check_thumbnail_approved(post_id, workspace_id)
    thumbnails     = approval_check["thumbnails"]
    thumb          = thumbnails[0] if thumbnails else None

    col_prev, col_act = st.columns([3, 2], gap="medium")

    with col_prev:
        if thumb:
            t_url    = thumb.get("url", "")
            t_status = thumb.get("_status", "draft")
            t_ver    = thumb.get("_lifecycle", {}).get("version", 1)
            label, color = _LIFECYCLE_COLORS.get(t_status, ("❓", "#999"))

            st.markdown(
                f"<span style='background:{color};color:#fff;padding:3px 10px;"
                f"border-radius:5px;font-size:.8rem;font-weight:700'>{label}</span>"
                f"&nbsp;<small>v{t_ver} · <b>{thumb['name']}</b></small>",
                unsafe_allow_html=True,
            )

            if t_url:
                try:
                    st.image(t_url, use_container_width=True,
                             caption=f"{spec.width if spec else '?'}×{spec.height if spec else '?'}px")
                except Exception:
                    st.caption(f"🔗 URL: `{t_url[:70]}...`")
            else:
                st.info("Thumbnail chưa có URL.")
        else:
            st.info("➕ Bài viết chưa có thumbnail.")
            st.caption("Gắn thumbnail từ Media Library hoặc upload mới.")

    with col_act:
        if thumb and spec:
            t_url = thumb.get("url", "")
            t_status = thumb.get("_status", "draft")

            # Approve nhanh (admin+)
            if t_status not in ("approved", "published") and \
               can_perform(user_role, "approve_thumbnail"):
                if st.button("✅ Approve Thumbnail",
                             key=f"qapprove_{post_id}", type="primary",
                             use_container_width=True):
                    ok = ThumbnailApprovalGate.quick_approve(
                        thumb["id"], workspace_id, user_id,
                        "Quick-approve từ Publishing"
                    )
                    st.success("Đã approve!") if ok else st.error("Thất bại.")
                    st.rerun()

            # Reject (admin+)
            if t_status in ("approved",) and can_perform(user_role, "approve_thumbnail"):
                if st.button("❌ Reject Thumbnail",
                             key=f"qreject_{post_id}",
                             use_container_width=True):
                    ThumbnailApprovalGate.reject_thumbnail(
                        thumb["id"], workspace_id, user_id, "Từ chối từ Publishing"
                    )
                    st.warning("Đã reject — thumbnail về Draft.")
                    st.rerun()

            # Validate & Crop
            if t_url:
                if st.button("✂️ Crop & Validate",
                             key=f"crop_{post_id}",
                             use_container_width=True):
                    with st.spinner(f"Đang xử lý cho {spec.name}..."):
                        try:
                            img_bytes, val = ThumbnailProcessor.prepare_for_platform(
                                t_url, spec
                            )
                            if val["ok"]:
                                st.success(
                                    f"✅ Hợp lệ · {val['width']}×{val['height']}px · "
                                    f"{val['size_mb']:.2f}MB"
                                )
                            else:
                                for iss in val["issues"]:
                                    st.error(iss)
                        except Exception as e:
                            st.error(f"Lỗi xử lý ảnh: {e}")

                # Preview Safe Zone
                sz_key = f"sz_bytes_{post_id}"
                if st.button("🔍 Safe Zone Preview",
                             key=f"sz_{post_id}",
                             use_container_width=True):
                    with st.spinner("Đang tạo Safe Zone overlay..."):
                        try:
                            sz_bytes = ThumbnailProcessor.generate_safe_zone_preview_bytes(
                                t_url, spec
                            )
                            st.session_state[sz_key] = sz_bytes
                            st.rerun()
                        except Exception as e:
                            st.error(f"Lỗi: {e}")

                # Hiển thị safe zone nếu đã render
                sz_key = f"sz_bytes_{post_id}"
                if sz_key in st.session_state:
                    st.image(st.session_state[sz_key],
                             caption="Safe Zone Overlay Preview",
                             use_container_width=True)
                    if st.button("✕ Đóng", key=f"closesz_{post_id}"):
                        del st.session_state[sz_key]
                        st.rerun()

        # Gắn thumbnail mới từ assets workspace
        st.divider()
        st.caption("**Gắn thumbnail khác từ Media Library:**")
        all_imgs = AssetModel.list_by_workspace(workspace_id, file_type="image")
        if all_imgs:
            img_opts = {a["id"]: f"{a['name']} (#{a['id']})" for a in all_imgs}
            sel_id = st.selectbox(
                "Chọn asset:",
                options=[None] + list(img_opts.keys()),
                format_func=lambda x: "— chọn —" if x is None else img_opts[x],
                key=f"attach_sel_{post_id}",
            )
            if sel_id and st.button("📌 Gắn vào bài",
                                    key=f"attach_{post_id}",
                                    use_container_width=True,
                                    disabled=not can_perform(user_role, "edit_post")):
                AssetModel.attach_to_post(sel_id, post_id)
                
                # Mark asset as thumbnail in its tags
                try:
                    from services.thumbnail_publishing_service import _write_asset_tags
                    asset_info = AssetModel.get_by_id(sel_id)
                    if asset_info:
                        tags = asset_info.get("tags", {})
                        if "thumbnail" not in tags:
                            tags["thumbnail"] = {}
                        tags["thumbnail"]["is_thumbnail"] = True
                        if "lifecycle" not in tags:
                            tags["lifecycle"] = {"status": "draft"}
                        _write_asset_tags(sel_id, workspace_id, tags)
                except Exception as e:
                    pass
                    
                st.success("Đã gắn thumbnail!")
                st.rerun()

    # ── Platform Mock-up Preview ──────────────────────────
    st.markdown("**🖥️ Preview giao diện bài đăng:**")
    t_url_prev = thumb.get("url") if thumb else None
    mockup_html = build_mockup(platform, post_content, t_url_prev)
    st.markdown(
        f'<div class="mockup-wrap">{mockup_html}</div>',
        unsafe_allow_html=True,
    )

    # ── Approval Gate result ───────────────────────────────
    st.divider()
    if approval_check["ok"]:
        st.success(approval_check["message"])
        return True
    else:
        if can_perform(user_role, "approve_thumbnail"):
            st.warning(approval_check["message"] + "  \n⚙️ Admin có thể bỏ qua và tiếp tục đăng bài.")
            return True   # Admin override
        else:
            st.error(approval_check["message"])
            return False  # Chặn editor


def _render_thumbnail_queue(
    workspace_id: int,
    user_id: int,
    user_role: str,
    svc: dict,
):
    """
    Hiển thị hàng chờ publish được enriched với trạng thái thumbnail.
    Thay thế / bổ sung cho bảng pending_list dạng dataframe cũ.
    """
    PublishQueue  = svc["PublishQueue"]
    RetryManager  = svc["RetryManager"]
    ThumbnailApprovalGate = svc["ThumbnailApprovalGate"]

    st.markdown("##### 🖼️📋 Thumbnail Publish Queue")

    # Summary metrics
    summary = PublishQueue.get_summary(workspace_id)
    mc = st.columns(5)
    mc[0].metric("📦 Tổng",       summary["total"])
    mc[1].metric("🚀 Ready",       summary["ready"] + summary["approved"])
    mc[2].metric("⏳ Chờ duyệt",  summary["pending_approval"])
    mc[3].metric("➕ Chưa gắn",   summary["not_set"])
    mc[4].metric("❌ Lỗi",         summary["error"])

    items = PublishQueue.get_enriched(workspace_id, quick_validate=False)
    if not items:
        st.caption("Hàng chờ trống.")
        return

    for item in items:
        t_label, t_css = _THUMB_STATUS_MAP.get(
            item.thumbnail_status, ("❓", "thumb-notset")
        )
        retry_badge = ""
        if item.retry_count > 0:
            retry_badge = f" · 🔄 Retry {item.retry_count}/{RetryManager.MAX_RETRIES}"

        expander_title = (
            f"Schedule #{item.schedule_id} · Post #{item.post_id} · "
            f"{item.platform.upper()} · {item.scheduled_at[:16]} · "
            f"{t_label}{retry_badge}"
        )
        is_problem = item.thumbnail_status in ("error", "pending_approval", "not_set")

        with st.expander(expander_title, expanded=is_problem):
            left, right = st.columns([2, 1], gap="medium")

            with left:
                # Thumbnail status badge HTML
                st.markdown(
                    f'<span class="{t_css}">{t_label}</span>',
                    unsafe_allow_html=True,
                )
                if item.thumbnail_name:
                    st.caption(f"📎 {item.thumbnail_name}")

                # Preview thumbnail nhỏ
                if item.thumbnail_url:
                    try:
                        st.image(item.thumbnail_url, width=180)
                    except Exception:
                        st.caption(f"🔗 `{item.thumbnail_url[:60]}...`")

                # Validation info
                if item.validation_issues:
                    for iss in item.validation_issues:
                        st.warning(iss)

                # Error message
                if item.error_message:
                    st.error(f"🔴 {item.error_message[:150]}")
                    strategy_label, _ = RetryManager.get_strategy(item.retry_count)
                    st.caption(f"Chiến lược retry tiếp theo: **{strategy_label}**")

            with right:
                # Quick approve (admin)
                if item.thumbnail_status == "pending_approval" and \
                   item.thumbnail_asset_id and \
                   can_perform(user_role, "approve_thumbnail"):
                    if st.button(
                        "✅ Approve",
                        key=f"qa_q_{item.schedule_id}_{item.thumbnail_asset_id}",
                        type="primary",
                        use_container_width=True,
                    ):
                        ok = ThumbnailApprovalGate.quick_approve(
                            item.thumbnail_asset_id, workspace_id, user_id,
                            "Quick-approve từ Publish Queue"
                        )
                        if ok:
                            st.success("Đã approve!")
                            st.rerun()

                # Retry
                if item.status == "failed" and \
                   RetryManager.should_retry(item.retry_count, item.error_message or ""):
                    if st.button(
                        "🔄 Retry",
                        key=f"retry_q_{item.schedule_id}",
                        type="secondary",
                        use_container_width=True,
                    ):
                        ok = RetryManager.mark_for_retry(
                            item.schedule_id, item.error_message or "Manual retry"
                        )
                        if ok:
                            st.success("Đã đặt lịch retry!")
                        else:
                            st.error("Hết số lần retry.")
                        st.rerun()

                # Cancel schedule
                if item.status == "pending" and can_perform(user_role, "cancel_schedule"):
                    if st.button(
                        "❌ Hủy lịch",
                        key=f"cancel_q_{item.schedule_id}",
                        use_container_width=True,
                    ):
                        from database.models.schedules import ScheduleModel
                        if ScheduleModel.cancel(item.schedule_id):
                            PostModel.update_status(item.post_id, "draft")
                            st.success(f"Đã hủy lịch #{item.schedule_id}")
                            st.rerun()


def render_tab_publishing(
    gemini_key: str = "",
    fb_page_id: str = "",
    fb_access_token: str = "",
    zalo_access_token: str = "",
    linkedin_author_urn: str = "",
    linkedin_access_token: str = "",
    workspace_id: int = 1,
    user_id: int = None,
    user_email: str = "",
    role: str = "editor"
):
    role = normalize_role(role, default="viewer")
    can_publish = can_perform(role, "publish_post")
    can_schedule = can_perform(role, "schedule_post")
    can_run_scheduler = can_perform(role, "run_scheduler")
    can_cancel_schedule = can_perform(role, "cancel_schedule")
    st.markdown(_PUBLISHING_CSS, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="pub-header">
        <h2>📢 Publishing Agent – Quản Lý & Đăng Bài</h2>
        <p>Kiểm tra kết nối mạng xã hội thời gian thực và đẩy bài đăng lên các kênh</p>
    </div>
    """, unsafe_allow_html=True)
    
    # ── PHẦN 1: KẾT NỐI API ──────────────────────────────────────────────────
    st.subheader("🔗 Trạng thái cấu hình API")
    
    c_fb, c_zalo, c_li = st.columns(3)
    
    # Facebook Card
    with c_fb:
        st.markdown("### Facebook Page")
        if fb_page_id and fb_access_token:
            st.markdown('<span class="status-badge status-configured">🟢 Đã cấu hình</span>', unsafe_allow_html=True)
            st.caption(f"Page ID: `{fb_page_id[:10]}...`")
            if st.button("🔌 Kiểm tra kết nối FB", key="btn_test_fb"):
                with st.spinner("Đang kết nối Facebook..."):
                    ok, msg = _test_facebook(fb_page_id, fb_access_token)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)
        else:
            st.markdown('<span class="status-badge status-unconfigured">🔴 Chưa cấu hình</span>', unsafe_allow_html=True)
            
    # Zalo OA Card
    with c_zalo:
        st.markdown("### Zalo OA")
        if zalo_access_token:
            st.markdown('<span class="status-badge status-configured">🟢 Đã cấu hình</span>', unsafe_allow_html=True)
            st.caption("Access Token đã nhập")
            if st.button("🔌 Kiểm tra kết nối Zalo", key="btn_test_zalo"):
                with st.spinner("Đang kết nối Zalo OA..."):
                    ok, msg = _test_zalo_oa(zalo_access_token)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)
        else:
            st.markdown('<span class="status-badge status-unconfigured">🔴 Chưa cấu hình</span>', unsafe_allow_html=True)
            
    # LinkedIn Card
    with c_li:
        st.markdown("### LinkedIn Profile")
        if linkedin_author_urn and linkedin_access_token:
            st.markdown('<span class="status-badge status-configured">🟢 Đã cấu hình</span>', unsafe_allow_html=True)
            st.caption(f"URN: `{linkedin_author_urn[:15]}...`")
            if st.button("🔌 Kiểm tra kết nối LinkedIn", key="btn_test_li"):
                with st.spinner("Đang kết nối LinkedIn..."):
                    ok, msg = _test_linkedin(linkedin_author_urn, linkedin_access_token)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)
        else:
            st.markdown('<span class="status-badge status-unconfigured">🔴 Chưa cấu hình</span>', unsafe_allow_html=True)
            
    st.divider()
    
    # ── PHẦN 2: KHO BẢN NHÁP & ĐĂNG BÀI THỦ CÔNG ──────────────────────────────
    st.subheader("📝 Đăng bài thủ công từ Kho nháp")

    # Load thumbnail service (graceful degradation nếu Pillow chưa cài)
    svc = _try_import_service()
    if svc is None:
        st.info(
            "ℹ️ Tính năng Thumbnail Management chưa khả dụng.  "
            "Cài Pillow: `pip install Pillow>=10.0.0`"
        )

    # Load các bài nháp
    df_drafts = PostModel.list_by_workspace(workspace_id=workspace_id, status="draft")

    if df_drafts.empty:
        st.info("💡 Không tìm thấy bài viết nháp nào trong Workspace hiện tại.")
    else:
        post_options = {
            row["id"]: f"#{row['id']} - [{row['platform'].upper()}] {str(row.get('topic',''))[:60]}..."
            for _, row in df_drafts.iterrows()
        }

        selected_post_id = st.selectbox(
            "Chọn bài viết nháp để tiến hành đăng:",
            options=list(post_options.keys()),
            format_func=lambda x: post_options[x],
        )

        post_data = next(
            (row for _, row in df_drafts.iterrows() if row["id"] == selected_post_id),
            None,
        )

        if post_data is not None:
            st.write("")

            # Editor nội dung
            edit_content = st.text_area(
                "Nội dung bài đăng (Có thể chỉnh sửa tại đây):",
                value=str(post_data.get("content", "")),
                height=280,
            )

            # Override platform
            target_platform = st.selectbox(
                "Chọn lại kênh muốn đăng:",
                options=["Facebook", "Zalo OA", "LinkedIn", "Tất cả"],
                index=(["facebook", "zalo", "linkedin", "all"].index(
                    str(post_data.get("platform", "facebook")).lower())
                    if str(post_data.get("platform", "facebook")).lower()
                    in ["facebook", "zalo", "linkedin", "all"] else 0),
            )

            st.divider()

            # ── THUMBNAIL MANAGEMENT ────────────────────────────
            thumb_ok = True
            if svc is not None:
                plat_key = target_platform.lower().replace(" oa", "").replace(" ", "")
                if plat_key == "tấtcả":
                    plat_key = "facebook"   # dùng FB spec làm đại diện
                with st.expander("🖼️ Thumbnail Management", expanded=True):
                    thumb_ok = _render_thumbnail_manager(
                        post_id=int(post_data["id"]),
                        post_content=edit_content,
                        platform=plat_key,
                        workspace_id=workspace_id,
                        user_id=user_id,
                        user_role=role,
                        svc=svc,
                    )

            # ── READINESS CHECK ─────────────────────────────────
            if svc is not None:
                readiness = svc["check_publish_readiness"](
                    post_id=int(post_data["id"]),
                    workspace_id=workspace_id,
                    platform=plat_key if target_platform != "Tất cả" else "facebook",
                    user_role=role,
                    require_thumbnail=True,
                    require_post_approval=False,   # tab này cho phép đăng thủ công
                )
                if readiness["warnings"]:
                    for w in readiness["warnings"]:
                        st.warning(w)

            st.write("")

            # Nút Publish — disabled nếu thumbnail chưa ok và không phải admin
            can_push = can_publish and (thumb_ok or can_perform(role, "approve_thumbnail"))
            btn_publish = st.button(
                "🚀 Bắt đầu đăng lên mạng xã hội ngay",
                use_container_width=True,
                type="primary",
                disabled=not can_push,
            )
            if not can_publish:
                st.caption("Ban khong co quyen dang bai thu cong tu tab Publishing.")
            elif not can_push:
                st.caption("⛔ Cần approve thumbnail trước khi publish.")

            if btn_publish:
                status_msg  = ""
                success_any = False

                with st.spinner("Đang gửi bài viết lên các mạng xã hội..."):
                    if target_platform in ["Facebook", "Tất cả"]:
                        success, msg = post_to_facebook(edit_content, fb_page_id, fb_access_token)
                        status_msg += f"FB: {msg} | "
                        if success:
                            success_any = True

                    if target_platform in ["Zalo OA", "Tất cả"]:
                        success, msg = post_to_zalo_oa(edit_content, zalo_access_token)
                        status_msg += f"Zalo: {msg} | "
                        if success:
                            success_any = True

                    if target_platform in ["LinkedIn", "Tất cả"]:
                        success, msg = post_to_linkedin(
                            edit_content, linkedin_author_urn, linkedin_access_token
                        )
                        status_msg += f"LinkedIn: {msg}"
                        if success:
                            success_any = True

                if success_any:
                    PostModel.update_status(selected_post_id, "published")
                    if edit_content != str(post_data.get("content", "")):
                        PostModel.update(selected_post_id, content=edit_content)
                    log_auto_post(
                        user_id=user_id,
                        user_email=user_email,
                        workspace_id=workspace_id,
                        platform=target_platform,
                        topic=str(post_data.get("topic", "")),
                        status=status_msg[:120],
                    )
                    st.success(f"🎉 Đăng bài thành công! {status_msg}")
                    st.rerun()
                else:
                    st.error(f"❌ Đăng bài thất bại! {status_msg}")

    st.divider()
    
    # ── PHẦN 3: LÊN LỊCH ĐĂNG BÀI TỰ ĐỘNG ────────────────────────────────────
    st.subheader("📅 Lên lịch đăng bài tự động (Scheduler)")
    
    # Load all approved or draft posts to schedule
    df_all_posts = PostModel.list_by_workspace(workspace_id=workspace_id)
    # Filter to only show drafts or approved posts
    if not df_all_posts.empty:
        df_sched_options = df_all_posts[df_all_posts["status"].isin(["draft", "approved"])]
    else:
        df_sched_options = pd.DataFrame()
        
    if df_sched_options.empty:
        st.info("💡 Không có bài viết nháp/phê duyệt nào để lên lịch.")
    else:
        sched_options = {
            row["id"]: f"#{row['id']} - [{row['platform'].upper()}] {row['topic'][:60]}..."
            for _, row in df_sched_options.iterrows()
        }
        
        with st.form("schedule_post_form"):
            selected_sched_post_id = st.selectbox(
                "Chọn bài viết để lên lịch:",
                options=list(sched_options.keys()),
                format_func=lambda x: sched_options[x]
            )
            
            c_date, c_time = st.columns(2)
            with c_date:
                sched_date = st.date_input("Chọn ngày đăng:")
            with c_time:
                sched_time = st.time_input("Chọn giờ đăng:")
                
            sched_platform = st.selectbox(
                "Nền tảng đăng bài:",
                options=["facebook", "zalo", "linkedin", "all"]
            )
            
            btn_schedule = st.form_submit_button("Dat lich dang bai", disabled=not can_schedule)
            if btn_schedule:
                # Gộp ngày và giờ
                sched_dt = datetime.combine(sched_date, sched_time)
                sched_dt_str = sched_dt.isoformat()
                
                from database.models.schedules import ScheduleModel
                sched_id = ScheduleModel.create(
                    post_id=selected_sched_post_id,
                    scheduled_at=sched_dt_str,
                    platform=sched_platform,
                    workspace_id=workspace_id,
                    created_by=user_id
                )
                
                # Cập nhật trạng thái bài viết thành pending_approval hoặc status tương ứng
                PostModel.update_status(selected_sched_post_id, "pending_approval")
                
                st.success(f"🎉 Đã lên lịch đăng bài thành công! ID Lịch: `#{sched_id}` vào lúc {sched_dt_str}")
                st.rerun()

    st.divider()

    # ── PHẦN 4: TRÌNH CHẠY SCHEDULER & HÀNG CHỜ ─────────────────────────────────
    from database.models.schedules import ScheduleModel
    from workflow.scheduler import execute_pending_schedules

    st.subheader("⚙️ Trình chạy Lịch Đăng (Execution Engine)")

    if st.button(
        "⚡ Quét & Đăng các bài viết đến hạn ngay (Run Scheduler)",
        type="primary",
        use_container_width=True,
        disabled=not can_run_scheduler,
    ):
        with st.spinner("Đang chạy Scheduler..."):
            run_results = execute_pending_schedules(
                workspace_id=workspace_id,
                fb_page_id=fb_page_id,
                fb_access_token=fb_access_token,
                zalo_access_token=zalo_access_token,
                linkedin_author_urn=linkedin_author_urn,
                linkedin_access_token=linkedin_access_token,
            )
            if run_results:
                st.success(
                    f"🎉 Scheduler đã chạy xong! "
                    f"Thực hiện thành công {len(run_results)} lịch đăng."
                )
                for res in run_results:
                    st.write(f"- Lịch `#{res['id']}`: {res['status']} - {res['message']}")
                st.rerun()
            else:
                st.info("💡 Không có lịch đăng nào đến hạn cần xử lý tại thời điểm này.")

    st.write("")

    # ── Thumbnail Publish Queue (enriched) ───────────────────────────────────
    if svc is not None:
        _render_thumbnail_queue(
            workspace_id=workspace_id,
            user_id=user_id,
            user_role=role,
            svc=svc,
        )
    else:
        # Fallback: bảng dataframe đơn giản như cũ
        st.markdown("##### ⏳ Hàng chờ xuất bản (Pending Queue)")
        pending_list = ScheduleModel.list_by_workspace(
            workspace_id=workspace_id, status="pending"
        )
        if pending_list:
            df_pending = pd.DataFrame(pending_list)
            cols_show = [c for c in ["id", "post_id", "platform",
                                      "scheduled_at", "status", "retry_count"]
                         if c in df_pending.columns]
            st.dataframe(df_pending[cols_show],
                         use_container_width=True, hide_index=True)

            with st.form("cancel_schedule_form"):
                cancel_id = st.selectbox(
                    "Chọn ID lịch muốn hủy:",
                    options=[p["id"] for p in pending_list],
                )
                if st.form_submit_button("Huy lich dang", disabled=not can_cancel_schedule):
                    if ScheduleModel.cancel(cancel_id):
                        sched_data = ScheduleModel.get_by_id(cancel_id)
                        if sched_data:
                            PostModel.update_status(sched_data["post_id"], "draft")
                        st.success(f"Đã hủy lịch `#{cancel_id}`!")
                        st.rerun()
        else:
            st.caption("Không có bài viết nào đang trong hàng chờ đăng.")

    # ── Lịch sử Scheduler ────────────────────────────────────────────────────
    st.write("")
    st.markdown("##### 🗒️ Lịch sử hoạt động của Scheduler")
    all_schedules = ScheduleModel.list_by_workspace(workspace_id=workspace_id, limit=20)
    history_list  = [s for s in all_schedules if s.get("status") != "pending"]
    if history_list:
        df_history = pd.DataFrame(history_list)
        cols_hist  = [c for c in ["id", "post_id", "platform",
                                    "scheduled_at", "status",
                                    "published_at", "error_message",
                                    "retry_count"]
                      if c in df_history.columns]
        st.dataframe(df_history[cols_hist],
                     use_container_width=True, hide_index=True)
    else:
        st.caption("Chưa có lịch sử hoạt động.")

