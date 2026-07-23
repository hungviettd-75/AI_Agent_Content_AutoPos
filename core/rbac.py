"""core/rbac.py — Định nghĩa tập trung tất cả hằng số RBAC.
Đây là nguồn duy nhất (single source of truth) cho phân quyền.
"""

# Danh sách tất cả vai trò hợp lệ trong Workspace (theo thứ tự quyền giảm dần)
ALL_ROLES = ["owner", "ceo", "manager", "marketing", "editor", "viewer"]

# Metadata hiển thị cho mỗi role (icon, label, màu badge)
ROLE_DISPLAY: dict[str, dict] = {
    "owner":       {"icon": "👑", "label": "Owner",       "color": "#7c3aed"},
    "ceo":         {"icon": "🏢", "label": "CEO",          "color": "#1d4ed8"},
    "manager":     {"icon": "💼", "label": "Manager",      "color": "#0369a1"},
    "marketing":   {"icon": "📣", "label": "Marketing",    "color": "#0891b2"},
    "editor":      {"icon": "✏️",  "label": "Editor",       "color": "#16a34a"},
    "viewer":      {"icon": "👁️", "label": "Viewer",       "color": "#64748b"},
    "admin":       {"icon": "🔧", "label": "Admin",        "color": "#dc2626"},
    "super_admin": {"icon": "⚡", "label": "Super Admin", "color": "#7f1d1d"},
}

# Quyền hạn theo role
# (tạo bài, tự động đăng, quản lý workspace, xem lịch sử)
ROLE_PERMISSIONS: dict[str, dict] = {
    "owner":     {"create_post": True,  "auto_post": True,  "manage_workspace": True,  "view_history": True},
    "ceo":       {"create_post": True,  "auto_post": True,  "manage_workspace": True,  "view_history": True},
    "manager":   {"create_post": True,  "auto_post": True,  "manage_workspace": True,  "view_history": True},
    "marketing": {"create_post": True,  "auto_post": True,  "manage_workspace": False, "view_history": True},
    "editor":    {"create_post": True,  "auto_post": False, "manage_workspace": False, "view_history": True},
    "viewer":    {"create_post": False, "auto_post": False, "manage_workspace": False, "view_history": True},
    "admin":     {"create_post": True,  "auto_post": True,  "manage_workspace": True,  "view_history": True},
}

# Tập các role được phép quản lý Workspace
MANAGER_ROLES: frozenset = frozenset({"owner", "ceo", "manager", "admin"})

# Tập các role được phép tự động đăng bài
CAN_AUTO_POST_ROLES: frozenset = frozenset({"owner", "ceo", "manager", "marketing", "admin"})


def get_role_display(role: str) -> dict:
    """Trả về dict {icon, label, color} cho role, fallback về default."""
    return ROLE_DISPLAY.get(role, {"icon": "🔑", "label": role.title(), "color": "#334155"})


def get_permissions(role: str) -> dict:
    """Trả về dict quyền hạn cho role."""
    return ROLE_PERMISSIONS.get(role, {
        "create_post": False, "auto_post": False,
        "manage_workspace": False, "view_history": False
    })


def has_permission(role: str, permission: str) -> bool:
    """Kiểm tra xem role có quyền cụ thể không."""
    return get_permissions(role).get(permission, False)


def render_role_badge(role: str) -> str:
    """Tạo HTML badge cho role (dùng với unsafe_allow_html=True)."""
    meta = get_role_display(role)
    return (
        f"<div style='display:inline-block;background:{meta['color']};color:#fff;"
        f"padding:2px 12px;border-radius:99px;font-size:0.8rem;font-weight:600;"
        f"margin-bottom:0.8rem'>{meta['icon']} {meta['label']}</div>"
    )


def render_permissions_table(role: str) -> str:
    """Tạo HTML bảng tóm tắt quyền hạn (dùng trong sidebar)."""
    perms = get_permissions(role)
    rows = {
        "Tạo bài viết":      perms.get("create_post", False),
        "Tự động đăng":      perms.get("auto_post", False),
        "Quản lý Workspace": perms.get("manage_workspace", False),
        "Xem lịch sử":       perms.get("view_history", False),
    }
    rows_html = "".join(
        f"<tr><td>{name}</td><td>{'✅' if val else '❌'}</td></tr>"
        for name, val in rows.items()
    )
    return (
        "<details><summary style='font-size:0.8rem;cursor:pointer;color:#3b82f6'>"
        "🔑 Quyền hạn hiện tại</summary>"
        f"<table style='font-size:0.75rem;width:100%;margin-top:6px'>{rows_html}</table>"
        "</details>"
    )
