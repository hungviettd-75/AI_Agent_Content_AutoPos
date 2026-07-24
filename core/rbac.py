"""core/rbac.py - Dinh nghia tap trung tat ca hang so RBAC.
Day la nguon duy nhat (single source of truth) cho phan quyen UI va thao tac.
"""

# Danh sach tat ca vai tro hop le trong Workspace (theo thu tu quyen giam dan)
ALL_ROLES = ["owner", "ceo", "manager", "marketing", "editor", "viewer"]

SYSTEM_ROLES = {"admin", "super_admin"}
VALID_ROLES = set(ALL_ROLES) | SYSTEM_ROLES


def normalize_role(role: str, default: str = "editor") -> str:
    """Return the canonical lowercase role used by RBAC checks."""
    normalized = (role or "").strip().lower()
    return normalized if normalized in VALID_ROLES else default


# Metadata hien thi cho moi role (icon, label, mau badge)
ROLE_DISPLAY: dict[str, dict] = {
    "owner":       {"icon": "\U0001f451", "label": "Owner",       "color": "#7c3aed"},
    "ceo":         {"icon": "\U0001f3e2", "label": "CEO",         "color": "#1d4ed8"},
    "manager":     {"icon": "\U0001f4bc", "label": "Manager",     "color": "#0369a1"},
    "marketing":   {"icon": "\U0001f4e3", "label": "Marketing",   "color": "#0891b2"},
    "editor":      {"icon": "\u270f\ufe0f", "label": "Editor",      "color": "#16a34a"},
    "viewer":      {"icon": "\U0001f441\ufe0f", "label": "Viewer",      "color": "#64748b"},
    "admin":       {"icon": "\U0001f527", "label": "Admin",       "color": "#dc2626"},
    "super_admin": {"icon": "\u26a1", "label": "Super Admin", "color": "#7f1d1d"},
}


# Quyen han theo role. Cac tab chi nen kiem tra qua has_permission/can_perform.
ROLE_PERMISSIONS: dict[str, dict[str, bool]] = {
    "owner": {
        "create_post": True, "auto_post": True, "manage_workspace": True,
        "view_history": True, "export_data": True, "manage_knowledge": True,
        "approve_thumbnail": False,
    },
    "ceo": {
        "create_post": True, "auto_post": True, "manage_workspace": True,
        "view_history": True, "export_data": True, "manage_knowledge": True,
        "approve_thumbnail": False,
    },
    "manager": {
        "create_post": True, "auto_post": True, "manage_workspace": True,
        "view_history": True, "export_data": True, "manage_knowledge": True,
        "approve_thumbnail": False,
    },
    "marketing": {
        "create_post": True, "auto_post": True, "manage_workspace": False,
        "view_history": True, "export_data": True, "manage_knowledge": True,
        "approve_thumbnail": False,
    },
    "editor": {
        "create_post": True, "auto_post": False, "manage_workspace": False,
        "view_history": True, "export_data": False, "manage_knowledge": True,
        "approve_thumbnail": False,
    },
    "viewer": {
        "create_post": False, "auto_post": False, "manage_workspace": False,
        "view_history": True, "export_data": False, "manage_knowledge": False,
        "approve_thumbnail": False,
    },
    "admin": {
        "create_post": True, "auto_post": True, "manage_workspace": True,
        "view_history": True, "export_data": True, "manage_knowledge": True,
        "approve_thumbnail": True,
    },
    "super_admin": {
        "create_post": True, "auto_post": True, "manage_workspace": True,
        "view_history": True, "export_data": True, "manage_knowledge": True,
        "approve_thumbnail": True,
    },
}


# Tap cac role duoc phep quan ly Workspace
MANAGER_ROLES: frozenset = frozenset({"owner", "ceo", "manager", "admin", "super_admin"})

# Tap cac role duoc phep tu dong dang bai / thao tac publishing queue
CAN_AUTO_POST_ROLES: frozenset = frozenset({"owner", "ceo", "manager", "marketing", "admin", "super_admin"})


ACTION_PERMISSION_MAP: dict[str, str] = {
    "create_post": "create_post",
    "edit_post": "create_post",
    "submit_approval": "create_post",
    "publish_post": "auto_post",
    "schedule_post": "auto_post",
    "run_scheduler": "auto_post",
    "cancel_schedule": "auto_post",
    "manage_workspace": "manage_workspace",
    "view_history": "view_history",
    "export_data": "export_data",
    "manage_knowledge": "manage_knowledge",
    "approve_thumbnail": "approve_thumbnail",
}


def get_role_display(role: str) -> dict:
    """Tra ve dict {icon, label, color} cho role, fallback ve default."""
    normalized = normalize_role(role, default="viewer")
    return ROLE_DISPLAY.get(normalized, {"icon": "\U0001f511", "label": normalized.title(), "color": "#334155"})


def get_permissions(role: str) -> dict:
    """Tra ve dict quyen han cho role."""
    return ROLE_PERMISSIONS.get(normalize_role(role, default="viewer"), {
        "create_post": False,
        "auto_post": False,
        "manage_workspace": False,
        "view_history": False,
        "export_data": False,
        "manage_knowledge": False,
        "approve_thumbnail": False,
    })


def has_permission(role: str, permission: str) -> bool:
    """Kiem tra xem role co quyen cu the khong."""
    return get_permissions(role).get(permission, False)


def can_perform(role: str, action: str) -> bool:
    """Kiem tra role co duoc thuc hien mot thao tac UI/app-level khong."""
    permission = ACTION_PERMISSION_MAP.get(action, action)
    return has_permission(role, permission)


def render_role_badge(role: str) -> str:
    """Tao HTML badge cho role (dung voi unsafe_allow_html=True)."""
    meta = get_role_display(role)
    return (
        f"<div style='display:inline-block;background:{meta['color']};color:#fff;"
        f"padding:2px 12px;border-radius:99px;font-size:0.8rem;font-weight:600;"
        f"margin-bottom:0.8rem'>{meta['icon']} {meta['label']}</div>"
    )


def render_permissions_table(role: str) -> str:
    """Tao HTML bang tom tat quyen han (dung trong sidebar)."""
    perms = get_permissions(role)
    rows = {
        "T\u1ea1o b\u00e0i vi\u1ebft": perms.get("create_post", False),
        "\u0110\u0103ng / l\u00ean l\u1ecbch": perms.get("auto_post", False),
        "Qu\u1ea3n l\u00fd Workspace": perms.get("manage_workspace", False),
        "Xem l\u1ecbch s\u1eed": perms.get("view_history", False),
        "Xu\u1ea5t d\u1eef li\u1ec7u": perms.get("export_data", False),
        "Qu\u1ea3n l\u00fd tri th\u1ee9c": perms.get("manage_knowledge", False),
    }
    rows_html = "".join(
        f"<tr>"
        f"<td style='color:#edf0ff;padding:4px 8px 4px 0;font-weight:500;'>{name}</td>"
        f"<td style='color:#edf0ff;padding:4px 0;text-align:right;'>{'&#9989;' if val else '&#10060;'}</td>"
        f"</tr>"
        for name, val in rows.items()
    )
    return (
        "<details><summary style='font-size:0.8rem;cursor:pointer;color:#3b82f6'>"
        "&#128273; Quy\u1ec1n h\u1ea1n hi\u1ec7n t\u1ea1i</summary>"
        f"<table style='font-size:0.78rem;width:100%;margin-top:8px;border-collapse:collapse;'>{rows_html}</table>"
        "</details>"
    )
