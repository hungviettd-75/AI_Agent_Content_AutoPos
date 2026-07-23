"""
ui/components/icons.py
======================
Hệ thống icon cho Apex AI. Hỗ trợ lấy emoji hoặc tên class icon nếu dùng external font.
"""

ICONS = {
    # Nền tảng
    "facebook": "🔵",
    "zalo": "🌸",
    "linkedin": "💼",
    
    # Menu điều hướng
    "dashboard": "📊",
    "planning": "📅",
    "create": "📝",
    "history": "🗒️",
    "brand": "🧠",
    "trends": "🔥",
    "factcheck": "🔍",
    "settings": "⚙️",
    "cost": "💰",
    "billing": "💳",
    "security": "🔐",
    
    # Trạng thái
    "success": "✅",
    "warning": "⚠️",
    "error": "🚨",
    "info": "ℹ️",
    "pending": "⏳",
    "published": "📢",
    
    # Quyền & Roles
    "super_admin": "👑",
    "admin": "🛡️",
    "editor": "✍️",
    "viewer": "👁️",
    "owner": "🔑",
    "marketing": "📢"
}

def get_icon(name: str) -> str:
    """
    Trả về emoji tương ứng với tên icon.
    """
    return ICONS.get(name.lower(), "🔹")
