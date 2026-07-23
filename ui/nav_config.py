# ============================================================
# ui/nav_config.py
# Nguồn dữ liệu navigation dùng chung (Single Source of Truth)
#
# Mọi component (Sidebar, TopNav, Layout...) đều import từ đây.
# KHÔNG định nghĩa danh sách tab ở bất kỳ nơi nào khác.
# ============================================================

# Tab mặc định khi khởi động ứng dụng
DEFAULT_NAV = "🚀 Logistics Growth Center"

# Các nhóm navigation cốt lõi (không phụ thuộc vào quyền hạn)
# Key: tên nhóm hiển thị, Value: danh sách tên tab trong nhóm đó
NAV_GROUPS_BASE: dict[str, list[str]] = {

    "🚀 Growth Platform": [
        "🚀 Logistics Growth Center",
        "🗓️ Content Planning (Wizard)",
    ],

    "🎨 Content Studio Workspace": [
        "🎨 Content Studio Workspace",
        "🧠 Knowledge Center",
        "🏢 Company Brain",
        "🎗️ Brand Identity",
        "🎨 Thumbnail Studio",
        "🔍 Fact Check",
        "📢 Publishing Agent",
    ],

    "🧠 Intelligence": [
        "🧠 Learning Loop",
    ],

    "⚙️ Automation Engine": [
        "⛓️ Workflow Engine",
        "⚖️ Quy trình phê duyệt",
        "🧪 A/B Testing",
    ],

    "📊 Data & Analytics": [
        "📈 Analytics Agent",
        "📊 Thumbnail Analytics",
        "💰 AI Cost Center",
        "💳 Billing & Quota",
    ],

    "🖥️ System": [
        "🖥️ System Monitor",
    ],
}

# Nhóm Admin — chỉ dùng khi show_admin_tab=True
NAV_GROUP_ADMIN: dict[str, list[str]] = {
    "🔐 Admin": [
        "⚙️ Quản lý Workspace",
        "🗒️ Audit Log",
    ]
}


def get_nav_groups(show_admin: bool = False) -> dict[str, list[str]]:
    """
    Trả về dict nav_groups đầy đủ dựa trên quyền hạn của user.

    Args:
        show_admin: True nếu user có quyền xem tab Admin.

    Returns:
        dict mapping tên nhóm -> danh sách tên tab.
    """
    groups = dict(NAV_GROUPS_BASE)  # shallow copy để không ảnh hưởng bản gốc
    if show_admin:
        groups.update(NAV_GROUP_ADMIN)
    return groups


def get_all_tab_names(show_admin: bool = False) -> list[str]:
    """
    Trả về danh sách phẳng tất cả tên tab (dùng cho validation, routing...).

    Args:
        show_admin: True nếu user có quyền xem tab Admin.

    Returns:
        list tên tất cả các tab.
    """
    groups = get_nav_groups(show_admin)
    return [tab for tabs in groups.values() for tab in tabs]


