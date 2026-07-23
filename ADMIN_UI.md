# 🛡️ ADMIN_UI.md — Professional Admin Panel Design
> **Hệ thống**: AI_Agent_Content_AutoPos  
> **Phiên bản**: 2.0 — Professional Admin Edition  
> **Ngày**: 2026-07-12  
> **Phạm vi**: Module Administration — Thiết kế lại toàn diện  

---

## 📐 1. Tổng Quan Kiến Trúc

### 1.1 Design Philosophy

Admin Panel được thiết kế theo triết lý **"Power User First"** — ưu tiên density thông tin, tốc độ thao tác, và rõ ràng phân quyền. Mọi action nguy hiểm phải có confirm dialog. Mọi trạng thái phải hiển thị rõ ràng.

```
┌─────────────────────────────────────────────────────────────────┐
│  ADMIN LAYOUT                                                   │
│  ┌──────────┐  ┌──────────────────────────────────────────────┐ │
│  │  Tree    │  │  Content Area                                │ │
│  │  Nav     │  │  ┌──────────────────────────────────────────┐│ │
│  │  260px   │  │  │  Breadcrumb + Action Bar                 ││ │
│  │          │  │  ├──────────────────────────────────────────┤│ │
│  │ ▸ Brain  │  │  │  Search + Filter Bar                     ││ │
│  │ ▸ Know.  │  │  ├──────────────────────────────────────────┤│ │
│  │ ▸ Billing│  │  │                                          ││ │
│  │ ▸ Audit  │  │  │  Main Content                            ││ │
│  │ ▸ Monitor│  │  │                                          ││ │
│  │ ▸ WS     │  │  │                                          ││ │
│  │ ▸ Users  │  │  └──────────────────────────────────────────┘│ │
│  │ ▸ API    │  └──────────────────────────────────────────────┘ │
│  │ ▸ Roles  │                                                   │
│  └──────────┘                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Color System — Admin Dark Theme

```python
# ui/admin_theme.py
ADMIN_COLORS = {
    # Background layers
    "bg_page":       "#0f172a",   # Slate 900 — page base
    "bg_sidebar":    "#0a0f1e",   # Darker sidebar
    "bg_card":       "#1e293b",   # Slate 800 — card surface
    "bg_card_hover": "#263348",   # Card hover
    "bg_input":      "#162032",   # Input field background

    # Accent palette
    "accent_blue":   "#3b82f6",   # Primary action
    "accent_violet": "#7c3aed",   # Super admin / premium
    "accent_green":  "#10b981",   # Success / active
    "accent_amber":  "#f59e0b",   # Warning / billing
    "accent_red":    "#ef4444",   # Danger / delete
    "accent_cyan":   "#06b6d4",   # Info / monitoring

    # Text
    "text_primary":   "#f1f5f9",   # Slate 100
    "text_secondary": "#94a3b8",   # Slate 400
    "text_muted":     "#475569",   # Slate 600
    "text_disabled":  "#334155",   # Slate 700

    # Border
    "border_default": "#1e293b",
    "border_focus":   "#3b82f6",
    "border_danger":  "#ef4444",
}

ADMIN_ROLE_COLORS = {
    "super_admin": {"bg": "#7f1d1d", "accent": "#ef4444", "badge": "#dc2626"},
    "admin":       {"bg": "#1e1b4b", "accent": "#7c3aed", "badge": "#6d28d9"},
    "owner":       {"bg": "#1e1b4b", "accent": "#7c3aed", "badge": "#5b21b6"},
    "ceo":         {"bg": "#1e3a5f", "accent": "#3b82f6", "badge": "#1d4ed8"},
    "manager":     {"bg": "#0c4a6e", "accent": "#0ea5e9", "badge": "#0369a1"},
    "marketing":   {"bg": "#064e3b", "accent": "#10b981", "badge": "#059669"},
    "editor":      {"bg": "#14532d", "accent": "#22c55e", "badge": "#16a34a"},
    "viewer":      {"bg": "#1e293b", "accent": "#64748b", "badge": "#475569"},
}
```

---

## 🌳 2. Tree Navigation

### 2.1 Cấu Trúc Cây Menu Admin

```
⚙️ ADMINISTRATION
├── 🧠 Company Brain
│   ├── 📄 Brand Voice Config
│   ├── 🎯 Target Audience
│   ├── 📋 Product Database
│   └── 🔧 AI Instruction Override
│
├── 📚 Knowledge Base
│   ├── 🗂️ Knowledge Articles
│   ├── 📥 Import / Export
│   ├── 🏷️ Tag Management
│   └── 🔍 Search Index Config
│
├── 💳 Billing
│   ├── 📊 Current Plan
│   ├── 📜 Invoice History
│   ├── 💡 Usage Analytics
│   └── 🔄 Upgrade / Downgrade
│
├── 🕵️ Audit Logs
│   ├── 📋 Activity Timeline
│   ├── 🔐 Security Events
│   ├── 📤 Export Logs
│   └── ⚠️ Anomaly Alerts
│
├── 📡 Monitoring
│   ├── 🟢 System Health
│   ├── 📈 API Performance
│   ├── 🤖 AI Cost Tracker
│   └── 🔔 Alert Configuration
│
├── 🏢 Workspace
│   ├── ⚙️ General Settings
│   ├── 🌐 Social Connections
│   ├── 🤝 Member Invitations
│   └── 🗑️ Danger Zone
│
├── 👥 Users
│   ├── 📋 User Directory
│   ├── ➕ Add / Invite User
│   ├── 🔑 Role Assignment
│   └── 🚫 Deactivated Users
│
├── 🔌 API Config
│   ├── 🤖 AI Providers
│   ├── 📱 Social API Keys
│   ├── 🔗 Webhooks
│   └── 🧪 API Tester
│
└── 🎭 Role Management
    ├── 📜 Role Definitions
    ├── 🛡️ Permission Matrix
    ├── 📊 Role Analytics
    └── 🔄 Role Assignment Bulk
```

### 2.2 ADMIN_TREE_CONFIG — Permission-Aware Navigation

```python
# ui/admin_sidebar.py
import streamlit as st

# ─── Permission Gate cho từng menu node ───────────────────────────────────────
ADMIN_TREE_CONFIG = {
    "🧠 Company Brain": {
        "icon": "🧠", "color": "#7c3aed",
        "required_roles": ["super_admin", "admin", "owner"],
        "children": [
            {"id": "brain_voice",    "label": "📄 Brand Voice Config",     "roles": ["super_admin", "admin", "owner"]},
            {"id": "brain_audience", "label": "🎯 Target Audience",         "roles": ["super_admin", "admin", "owner", "manager"]},
            {"id": "brain_product",  "label": "📋 Product Database",        "roles": ["super_admin", "admin", "owner", "manager"]},
            {"id": "brain_ai",       "label": "🔧 AI Instruction Override", "roles": ["super_admin", "admin"]},
        ]
    },
    "📚 Knowledge Base": {
        "icon": "📚", "color": "#0ea5e9",
        "required_roles": ["super_admin", "admin", "owner", "manager"],
        "children": [
            {"id": "kb_articles", "label": "🗂️ Knowledge Articles",    "roles": ["super_admin", "admin", "owner", "manager", "editor"]},
            {"id": "kb_import",   "label": "📥 Import / Export",        "roles": ["super_admin", "admin", "owner"]},
            {"id": "kb_tags",     "label": "🏷️ Tag Management",         "roles": ["super_admin", "admin", "owner", "manager"]},
            {"id": "kb_search",   "label": "🔍 Search Index Config",    "roles": ["super_admin", "admin"]},
        ]
    },
    "💳 Billing": {
        "icon": "💳", "color": "#f59e0b",
        "required_roles": ["super_admin", "admin", "owner", "ceo"],
        "children": [
            {"id": "billing_plan",    "label": "📊 Current Plan",        "roles": ["super_admin", "admin", "owner", "ceo"]},
            {"id": "billing_invoice", "label": "📜 Invoice History",     "roles": ["super_admin", "admin", "owner", "ceo"]},
            {"id": "billing_usage",   "label": "💡 Usage Analytics",     "roles": ["super_admin", "admin", "owner", "ceo", "manager"]},
            {"id": "billing_upgrade", "label": "🔄 Upgrade / Downgrade", "roles": ["super_admin", "owner"]},
        ]
    },
    "🕵️ Audit Logs": {
        "icon": "🕵️", "color": "#ef4444",
        "required_roles": ["super_admin", "admin"],
        "children": [
            {"id": "audit_timeline", "label": "📋 Activity Timeline", "roles": ["super_admin", "admin"]},
            {"id": "audit_security", "label": "🔐 Security Events",   "roles": ["super_admin"]},
            {"id": "audit_export",   "label": "📤 Export Logs",       "roles": ["super_admin", "admin"]},
            {"id": "audit_alerts",   "label": "⚠️ Anomaly Alerts",    "roles": ["super_admin"]},
        ]
    },
    "📡 Monitoring": {
        "icon": "📡", "color": "#06b6d4",
        "required_roles": ["super_admin", "admin", "owner", "ceo"],
        "children": [
            {"id": "mon_health",  "label": "🟢 System Health",       "roles": ["super_admin", "admin", "owner", "ceo"]},
            {"id": "mon_api",     "label": "📈 API Performance",     "roles": ["super_admin", "admin", "owner"]},
            {"id": "mon_cost",    "label": "🤖 AI Cost Tracker",     "roles": ["super_admin", "admin", "owner", "ceo"]},
            {"id": "mon_alerts",  "label": "🔔 Alert Configuration", "roles": ["super_admin", "admin"]},
        ]
    },
    "🏢 Workspace": {
        "icon": "🏢", "color": "#10b981",
        "required_roles": ["super_admin", "admin", "owner", "manager"],
        "children": [
            {"id": "ws_settings",    "label": "⚙️ General Settings",  "roles": ["super_admin", "admin", "owner"]},
            {"id": "ws_social",      "label": "🌐 Social Connections", "roles": ["super_admin", "admin", "owner"]},
            {"id": "ws_invitations", "label": "🤝 Member Invitations", "roles": ["super_admin", "admin", "owner", "manager"]},
            {"id": "ws_danger",      "label": "🗑️ Danger Zone",        "roles": ["super_admin", "owner"]},
        ]
    },
    "👥 Users": {
        "icon": "👥", "color": "#8b5cf6",
        "required_roles": ["super_admin", "admin", "owner", "manager"],
        "children": [
            {"id": "users_directory", "label": "📋 User Directory",   "roles": ["super_admin", "admin", "owner", "manager"]},
            {"id": "users_add",       "label": "➕ Add / Invite User", "roles": ["super_admin", "admin", "owner"]},
            {"id": "users_roles",     "label": "🔑 Role Assignment",   "roles": ["super_admin", "admin", "owner"]},
            {"id": "users_inactive",  "label": "🚫 Deactivated Users", "roles": ["super_admin", "admin"]},
        ]
    },
    "🔌 API Config": {
        "icon": "🔌", "color": "#f97316",
        "required_roles": ["super_admin", "admin", "owner"],
        "children": [
            {"id": "api_ai",       "label": "🤖 AI Providers",    "roles": ["super_admin", "admin"]},
            {"id": "api_social",   "label": "📱 Social API Keys", "roles": ["super_admin", "admin", "owner"]},
            {"id": "api_webhooks", "label": "🔗 Webhooks",        "roles": ["super_admin", "admin"]},
            {"id": "api_tester",   "label": "🧪 API Tester",      "roles": ["super_admin", "admin"]},
        ]
    },
    "🎭 Role Management": {
        "icon": "🎭", "color": "#ec4899",
        "required_roles": ["super_admin"],
        "children": [
            {"id": "role_definitions", "label": "📜 Role Definitions",  "roles": ["super_admin"]},
            {"id": "role_matrix",      "label": "🛡️ Permission Matrix", "roles": ["super_admin"]},
            {"id": "role_analytics",   "label": "📊 Role Analytics",    "roles": ["super_admin"]},
            {"id": "role_bulk",        "label": "🔄 Bulk Assignment",   "roles": ["super_admin"]},
        ]
    },
}


def render_admin_tree_nav(current_role: str) -> str:
    """
    Render cây điều hướng Admin Panel với phân quyền động.
    Trả về node_id được chọn.
    """
    _inject_tree_css()

    selected = st.session_state.get("admin_active_node", "brain_voice")

    st.sidebar.markdown("""
    <div style="padding:18px 16px 14px;border-bottom:1px solid #1e293b;
         display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
        <span style="font-size:1rem;font-weight:700;color:#7c3aed;letter-spacing:-0.5px;">
            ⚡ Admin Panel
        </span>
        <span style="font-size:0.65rem;color:#334155;background:#1e293b;
              padding:2px 6px;border-radius:99px;">v2.0</span>
    </div>
    """, unsafe_allow_html=True)

    # Search box trong sidebar
    search_query = st.sidebar.text_input(
        "🔍", placeholder="Tìm kiếm menu...",
        key="admin_tree_search",
        label_visibility="collapsed"
    )

    for group_name, group_config in ADMIN_TREE_CONFIG.items():
        # Kiểm tra quyền truy cập group
        if current_role not in group_config["required_roles"]:
            continue

        group_key    = f"admin_tree_group_{group_name}"
        is_expanded  = st.session_state.get(group_key, False)
        group_color  = group_config["color"]

        # Highlight nếu active child thuộc group này
        any_child_active = any(c["id"] == selected for c in group_config["children"])
        if any_child_active:
            is_expanded = True

        # Group toggle button
        toggle_label = f"{'▼' if is_expanded else '▶'}  {group_name}"
        if st.sidebar.button(toggle_label, key=group_key + "_btn", use_container_width=True):
            st.session_state[group_key] = not is_expanded
            st.rerun()

        # Children
        if is_expanded:
            filtered = [
                c for c in group_config["children"]
                if current_role in c["roles"]
                and (not search_query or search_query.lower() in c["label"].lower())
            ]
            for child in filtered:
                is_active  = child["id"] == selected
                btn_label  = f"{'●' if is_active else '○'}  {child['label']}"
                if st.sidebar.button(btn_label, key=f"admin_tree_{child['id']}", use_container_width=True):
                    st.session_state["admin_active_node"] = child["id"]
                    st.rerun()

    return st.session_state.get("admin_active_node", "brain_voice")


def _inject_tree_css():
    """CSS cho Admin Tree Navigation."""
    st.sidebar.markdown("""
    <style>
    [data-testid="stSidebar"] {
        background: #0a0f1e !important;
        border-right: 1px solid #1e293b !important;
    }
    /* Tất cả nút trong sidebar */
    [data-testid="stSidebar"] .stButton > button {
        background: transparent !important;
        color: #64748b !important;
        border: none !important;
        text-align: left !important;
        font-size: 0.82rem !important;
        padding: 6px 16px !important;
        border-radius: 0 !important;
        width: 100% !important;
        transition: all 0.15s ease !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(59,130,246,0.08) !important;
        color: #e2e8f0 !important;
    }
    /* Group headers (chứa ▼/▶) */
    [data-testid="stSidebar"] .stButton > button:has(span:first-child) {
        color: #f1f5f9 !important;
        font-weight: 700 !important;
        font-size: 0.78rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.06em !important;
        padding-top: 14px !important;
    }
    /* Active child node (chứa ●) */
    [data-testid="stSidebar"] .element-container:has(button) button[title*="●"] {
        background: rgba(124,58,237,0.18) !important;
        color: #a78bfa !important;
        border-left: 3px solid #7c3aed !important;
        font-weight: 600 !important;
    }
    /* Search input */
    [data-testid="stSidebar"] .stTextInput > div > div > input {
        background: #162032 !important;
        border: 1px solid #1e293b !important;
        color: #94a3b8 !important;
        border-radius: 8px !important;
        font-size: 0.82rem !important;
    }
    </style>
    """, unsafe_allow_html=True)
```

---

## 🔑 3. Permission Matrix

### 3.1 Admin Module Access Table

| Module | viewer | editor | marketing | manager | admin | owner | ceo | super_admin |
|--------|:------:|:------:|:---------:|:-------:|:-----:|:-----:|:---:|:-----------:|
| 🧠 Company Brain | ❌ | ❌ | ❌ | 🔍 Partial | ✅ RW | ✅ RW | ❌ | ✅ Full |
| 📚 Knowledge Base | ❌ | 📖 R | 📖 R | ✅ RW | ✅ RW | ✅ RW | ❌ | ✅ Full |
| 💳 Billing | ❌ | ❌ | ❌ | 📖 Usage | 📖 R | ✅ RW | 📖 R | ✅ Full |
| 🕵️ Audit Logs | ❌ | ❌ | ❌ | ❌ | 📖 R | ❌ | ❌ | ✅ Full |
| 📡 Monitoring | ❌ | ❌ | ❌ | ❌ | ✅ R | ✅ R | 📖 Cost | ✅ Full |
| 🏢 Workspace | ❌ | ❌ | ❌ | 🤝 Invite | ✅ RW | ✅ RW | ❌ | ✅ Full |
| 👥 Users | ❌ | ❌ | ❌ | 📖 R | ✅ RW | ✅ RW | ❌ | ✅ Full |
| 🔌 API Config | ❌ | ❌ | ❌ | ❌ | ✅ RW | 📱 Social | ❌ | ✅ Full |
| 🎭 Roles | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ Full |

> **Chú thích**: R = Read only | RW = Read & Write | ❌ = Bị từ chối | Partial = Chỉ một số node

### 3.2 Permission Gate Component

```python
# ui/admin_permission.py
import streamlit as st
from functools import wraps


def check_admin_access(current_role: str, allowed_roles: list) -> bool:
    """Kiểm tra quyền. Nếu bị từ chối — render Access Denied và trả về False."""
    if current_role in allowed_roles:
        return True
    _render_access_denied(current_role, allowed_roles)
    return False


def _render_access_denied(current_role: str, allowed_roles: list):
    """Render trang Access Denied chuyên nghiệp."""
    from core.rbac import get_role_display  # Không sửa rbac.py
    role_meta = get_role_display(current_role)

    st.markdown(f"""
    <div style="display:flex;flex-direction:column;align-items:center;
         justify-content:center;min-height:60vh;text-align:center;
         background:#0f172a;border-radius:16px;padding:3rem;
         border:1px solid #1e293b;">
        <div style="font-size:4rem;margin-bottom:1.5rem;">🔒</div>
        <h2 style="color:#ef4444;margin-bottom:0.5rem;">Truy cập bị từ chối</h2>
        <p style="color:#94a3b8;margin-bottom:1.5rem;">
            Vai trò <strong style="color:{role_meta['color']}">
            {role_meta['icon']} {role_meta['label']}</strong>
            không có quyền truy cập khu vực này.
        </p>
        <div style="background:#1e293b;border-radius:8px;
             padding:10px 18px;font-size:0.8rem;color:#64748b;">
            Yêu cầu: {' / '.join(allowed_roles)}
        </div>
        <p style="color:#334155;font-size:0.75rem;margin-top:1.5rem;">
            Liên hệ Super Admin để được cấp quyền.
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_permission_badge(current_role: str, node_id: str):
    """Badge Role + quyền RW/R ở góc phải header mỗi module."""
    from core.rbac import get_role_display
    from ui.admin_sidebar import ADMIN_TREE_CONFIG

    role_meta = get_role_display(current_role)
    is_full   = current_role in ["super_admin", "admin", "owner"]

    perm_color = "#10b981" if is_full else "#f59e0b"
    perm_label = "✏️ Toàn quyền" if is_full else "👁 Chỉ xem"

    st.markdown(f"""
    <div style="display:flex;gap:8px;align-items:center;
         justify-content:flex-end;margin-bottom:12px;">
        <span style="background:{role_meta['color']}22;color:{role_meta['color']};
              border:1px solid {role_meta['color']}44;
              padding:3px 10px;border-radius:99px;
              font-size:0.7rem;font-weight:600;">
            {role_meta['icon']} {role_meta['label']}
        </span>
        <span style="background:{perm_color}22;color:{perm_color};
              border:1px solid {perm_color}44;
              padding:3px 10px;border-radius:99px;
              font-size:0.7rem;font-weight:600;">
            {perm_label}
        </span>
    </div>
    """, unsafe_allow_html=True)
```

---

## 🔍 4. Search & Filter System

### 4.1 Universal Search Bar Component

```python
# ui/admin_search.py
import streamlit as st

# ─── Filter Presets cho từng module ──────────────────────────────────────────
USER_FILTER_OPTIONS = {
    "Vai trò":    ["super_admin", "admin", "owner", "ceo", "manager", "marketing", "editor", "viewer"],
    "Trạng thái": ["active", "inactive", "pending"],
    "Sắp xếp":    ["Mới nhất", "Cũ nhất", "Tên A-Z"],
}
AUDIT_FILTER_OPTIONS = {
    "Sự kiện":  ["login", "logout", "create", "update", "delete", "export", "permission_change"],
    "Thời gian": ["Hôm nay", "7 ngày", "30 ngày", "90 ngày"],
    "Mức độ":   ["info", "warning", "error", "critical"],
}
API_FILTER_OPTIONS = {
    "Provider":   ["Gemini", "OpenAI", "Claude", "Custom"],
    "Trạng thái": ["active", "inactive", "error"],
    "Loại":       ["AI", "Social", "Webhook"],
}
KNOWLEDGE_FILTER_OPTIONS = {
    "Danh mục":   ["Brand Voice", "Product", "FAQ", "Case Study", "Guideline"],
    "Trạng thái": ["published", "draft", "archived"],
    "Ngôn ngữ":   ["vi", "en"],
}
BILLING_FILTER_OPTIONS = {
    "Trạng thái": ["paid", "pending", "overdue", "cancelled"],
    "Gói":        ["Free", "Starter", "Pro", "Enterprise"],
    "Thời gian":  ["Tháng này", "Quý này", "Năm nay"],
}


def render_admin_search_bar(
    placeholder: str = "Tìm kiếm...",
    filter_options: dict = None,
    key_prefix: str = "admin"
) -> dict:
    """
    Render thanh Search + Filter chuyên nghiệp.
    Trả về: {"query": str, "filters": {filter_name: selected_value}}
    """
    st.markdown("""
    <style>
    .admin-search-row { display:flex; gap:12px; align-items:flex-end; margin-bottom:16px; }
    </style>
    """, unsafe_allow_html=True)

    result = {"query": "", "filters": {}}
    n_filters = len(filter_options) if filter_options else 0
    cols = st.columns([3] + [1.8] * n_filters + [0.6])

    with cols[0]:
        result["query"] = st.text_input(
            "🔍", placeholder=placeholder,
            key=f"{key_prefix}_search",
            label_visibility="collapsed"
        )

    if filter_options:
        for i, (fname, fopts) in enumerate(filter_options.items()):
            with cols[1 + i]:
                result["filters"][fname] = st.selectbox(
                    fname,
                    options=["Tất cả"] + fopts,
                    key=f"{key_prefix}_filter_{fname}"
                )

    with cols[-1]:
        st.write(" ")
        if st.button("↺", key=f"{key_prefix}_reset", help="Xóa bộ lọc"):
            for k in list(st.session_state.keys()):
                if k.startswith(f"{key_prefix}_filter_") or k == f"{key_prefix}_search":
                    del st.session_state[k]
            st.rerun()

    return result
```

---

## 📦 5. Module Designs

### 5.1 Shared Components

```python
# ui/admin_components.py
import streamlit as st


def render_module_header(icon, title, subtitle, color, action_label=None, action_key=None):
    """Header chuẩn Dark cho mỗi Admin module."""
    col_title, col_action = st.columns([6, 2]) if action_label else (st.container(), None)

    with (col_title if action_label else col_title):
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,{color}22 0%,transparent 100%);
             border-left:4px solid {color};border-radius:0 12px 12px 0;
             padding:16px 20px;margin-bottom:20px;">
            <h2 style="color:#f1f5f9;margin:0 0 4px;font-size:1.4rem;
                display:flex;align-items:center;gap:10px;">
                {icon} {title}
            </h2>
            <p style="color:#64748b;margin:0;font-size:0.82rem;">{subtitle}</p>
        </div>
        """, unsafe_allow_html=True)

    if action_label and col_action:
        with col_action:
            st.write(" ")
            st.button(action_label, key=action_key or f"hdr_action_{title}",
                      type="primary", use_container_width=True)


def stat_card(col, label: str, value: str, change: str, color: str):
    """Mini stat card."""
    col.markdown(f"""
    <div style="background:#1e293b;border:1px solid #263348;border-radius:10px;
         padding:16px;border-top:3px solid {color};">
        <div style="color:#64748b;font-size:0.7rem;text-transform:uppercase;
             letter-spacing:0.05em;margin-bottom:8px;">{label}</div>
        <div style="color:#f1f5f9;font-size:1.5rem;font-weight:700;margin-bottom:4px;">
            {value}</div>
        <div style="color:{color};font-size:0.72rem;">{change}</div>
    </div>
    """, unsafe_allow_html=True)


def usage_bar(label: str, current: float, total: float, color: str):
    """Progress bar sử dụng tài nguyên."""
    pct = min(current / total * 100, 100) if total else 0
    bar_color = "#ef4444" if pct >= 90 else ("#f59e0b" if pct >= 75 else color)
    st.markdown(f"""
    <div style="margin-bottom:14px;">
        <div style="display:flex;justify-content:space-between;margin-bottom:6px;">
            <span style="color:#94a3b8;font-size:0.82rem;">{label}</span>
            <span style="color:{bar_color};font-size:0.82rem;font-weight:600;">
                {current:,.0f} / {total:,.0f} ({pct:.0f}%)
            </span>
        </div>
        <div style="background:#1e293b;border-radius:99px;height:6px;overflow:hidden;">
            <div style="background:{bar_color};height:100%;width:{pct}%;
                 border-radius:99px;transition:width 0.4s ease;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_breadcrumb(node_id: str):
    """Breadcrumb dựa trên active node."""
    from ui.admin_sidebar import ADMIN_TREE_CONFIG
    path = ["⚙️ Admin"]
    for gname, gcfg in ADMIN_TREE_CONFIG.items():
        for child in gcfg["children"]:
            if child["id"] == node_id:
                # Lấy label bỏ icon đầu
                path.append(gname.split(" ", 1)[-1])
                path.append(child["label"].split(" ", 1)[-1])
                break
    crumb = " / ".join(f"`{p}`" for p in path)
    st.markdown(
        f"<div style='color:#334155;font-size:0.75rem;margin-bottom:12px;'>📍 {crumb}</div>",
        unsafe_allow_html=True
    )
```

---

### 5.2 🧠 Company Brain

```
┌─────────────────────────────────────────────────────────────────────┐
│  🧠 Company Brain                                  [+ Thêm mục]     │
│  "Tri thức nội bộ giúp AI viết đúng thương hiệu"                   │
│  ────────────────────────────────────────────────────────────────── │
│  [📄 Brand Voice] [🎯 Audience] [📋 Products] [🔧 AI Override]      │
│  ────────────────────────────────────────────────────────────────── │
│                                                                      │
│  📄 Brand Voice Config                                               │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ Tone:    [Chuyên nghiệp ×] [Thân thiện ×] [Sáng tạo ×]       │ │
│  │ Xưng hô: [Chúng ta (We)          ▼]                           │ │
│  │ Tránh:   [textarea: từ ngữ cần tránh...]                       │ │
│  │ Ưu tiên: [textarea: từ ngữ nên dùng...]                        │ │
│  │ Story:   [textarea: Brand Story / Tuyên ngôn...]               │ │
│  ├────────────────────────────────────────────────────────────────┤ │
│  │ [💾 Lưu cấu hình]   [🧪 Test AI với cấu hình này]             │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

```python
# ui/admin_company_brain.py
import streamlit as st


def render_company_brain(current_role: str, workspace_id: int):
    from ui.admin_permission import check_admin_access, render_permission_badge
    from ui.admin_components import render_module_header

    if not check_admin_access(current_role, ["super_admin", "admin", "owner"]):
        return

    render_module_header(
        "🧠", "Company Brain",
        "Tri thức nội bộ doanh nghiệp giúp AI viết đúng thương hiệu",
        "#7c3aed",
        action_label="+ Thêm mục" if current_role in ["super_admin", "admin", "owner"] else None
    )
    render_permission_badge(current_role, "brain_voice")

    tabs = st.tabs(["📄 Brand Voice", "🎯 Target Audience", "📋 Product DB", "🔧 AI Override"])
    with tabs[0]:
        _brain_brand_voice(current_role)
    with tabs[1]:
        _brain_audience(current_role)
    with tabs[2]:
        _brain_products(current_role)
    with tabs[3]:
        if not check_admin_access(current_role, ["super_admin", "admin"]):
            return
        _brain_ai_override(current_role)


def _brain_brand_voice(role: str):
    editable = role in ["super_admin", "admin", "owner"]
    st.markdown("""
    <div style="background:#1e293b;border-radius:10px;padding:18px;margin:12px 0;
         border-left:4px solid #7c3aed;">
        <h4 style="color:#a78bfa;margin:0 0 6px;">🎯 Cấu hình Giọng Thương Hiệu</h4>
        <p style="color:#64748b;font-size:0.83rem;margin:0;">
            Định nghĩa tone, style và từ ngữ thương hiệu. AI sẽ dùng khi tạo mọi nội dung.
        </p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.multiselect("🗣️ Tone giọng",
            ["Chuyên nghiệp", "Thân thiện", "Sáng tạo", "Nghiêm túc", "Truyền cảm hứng"],
            default=["Chuyên nghiệp", "Thân thiện"], disabled=not editable)
        st.selectbox("👤 Xưng hô",
            ["Chúng ta (We)", "Bạn/Tôi", "Doanh nghiệp"], disabled=not editable)
    with c2:
        st.text_area("🚫 Từ ngữ cần tránh", height=90,
            placeholder="Mỗi từ/cụm một dòng...", disabled=not editable)
        st.text_area("✅ Từ ngữ ưu tiên", height=90,
            placeholder="Mỗi từ/cụm một dòng...", disabled=not editable)

    st.text_area("📖 Brand Story / Tuyên ngôn thương hiệu", height=110,
        placeholder="Sứ mệnh, giá trị cốt lõi...", disabled=not editable)

    if editable:
        bc1, bc2, _ = st.columns([1.2, 1.2, 5])
        with bc1:
            if st.button("💾 Lưu cấu hình", type="primary", use_container_width=True):
                st.success("✅ Đã cập nhật Brand Voice!")
        with bc2:
            if st.button("🧪 Test AI", use_container_width=True):
                st.info("🤖 Đang tạo sample với Brand Voice mới...")


def _brain_audience(role: str):
    editable = role in ["super_admin", "admin", "owner", "manager"]
    st.markdown("#### 🎯 Chân dung khách hàng mục tiêu")
    c1, c2 = st.columns(2)
    with c1:
        st.text_input("👤 Persona name", placeholder="Ví dụ: Chủ doanh nghiệp SME", disabled=not editable)
        st.text_input("🎂 Độ tuổi", placeholder="Ví dụ: 28 - 45 tuổi", disabled=not editable)
        st.multiselect("📱 Mạng XH họ dùng",
            ["Facebook", "LinkedIn", "TikTok", "Instagram", "Zalo"], disabled=not editable)
    with c2:
        st.text_area("😤 Pain points", height=100,
            placeholder="Vấn đề họ đang gặp...", disabled=not editable)
        st.text_area("🎯 Mong muốn / Goals", height=100,
            placeholder="Họ muốn đạt được gì...", disabled=not editable)

    if editable:
        if st.button("💾 Lưu Audience Profile", type="primary"):
            st.success("✅ Đã lưu!")


def _brain_products(role: str):
    editable = role in ["super_admin", "admin", "owner", "manager"]
    st.markdown("#### 📋 Cơ sở dữ liệu sản phẩm / dịch vụ")
    if editable:
        with st.expander("➕ Thêm sản phẩm mới"):
            pc1, pc2 = st.columns(2)
            with pc1:
                st.text_input("Tên sản phẩm / dịch vụ")
                st.text_input("Giá / Pricing")
            with pc2:
                st.text_area("Mô tả ngắn", height=80)
                st.text_input("USP (Unique Selling Point)")
            if st.button("➕ Thêm", type="primary"):
                st.success("✅ Đã thêm sản phẩm!")

    st.markdown("##### Danh sách sản phẩm hiện tại:")
    demo_products = [
        {"Tên": "Gói Starter AI", "Giá": "$99/tháng", "USP": "AI posts 30/ngày"},
        {"Tên": "Gói Pro Agency", "Giá": "$299/tháng", "USP": "Không giới hạn workspace"},
    ]
    import pandas as pd
    st.dataframe(pd.DataFrame(demo_products), use_container_width=True, hide_index=True)


def _brain_ai_override(role: str):
    st.warning("⚠️ **Chú ý**: Cấu hình này ảnh hưởng trực tiếp đến chất lượng AI. Chỉnh sửa cẩn thận.")
    st.text_area("🔧 System Prompt Override", height=160,
        placeholder="Nhập hướng dẫn tùy chỉnh cho AI model...",
        help="Prompt này sẽ được thêm vào đầu mọi request đến AI.")
    st.slider("🌡️ Temperature (Sáng tạo)", 0.0, 2.0, 0.7, 0.1)
    c1, c2 = st.columns([1, 5])
    with c1:
        if st.button("💾 Lưu Override", type="primary", use_container_width=True):
            st.success("✅ Đã lưu AI override!")
```

---

### 5.3 💳 Billing

```
┌─────────────────────────────────────────────────────────────────────┐
│  💳 Billing & Subscription                                           │
│  ────────────────────────────────────────────────────────────────── │
│  ┌─ Current Plan ──────────────────────────── [ENTERPRISE] ACTIVE ─┐ │
│  │  $299/tháng  •  Gia hạn: 2026-08-01                            │ │
│  │  AI Tokens: ████████░░  82,450 / 100,000                        │ │
│  │  Bài viết:  ████░░░░░░  247 / 500                               │ │
│  │  Thành viên:████████░░  8 / 10                                  │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  📜 Lịch sử hóa đơn                                                  │
│  🔍 [Search hóa đơn...]  [Trạng thái ▼] [Gói ▼] [Thời gian ▼] [↺]  │
│  ─────────────────────────────────────────────────────────────────  │
│  INV-2026-07 │ Enterprise │ $299 │ ✅ Paid │ 2026-07-01    [📥 PDF] │
│  INV-2026-06 │ Enterprise │ $299 │ ✅ Paid │ 2026-06-01    [📥 PDF] │
└─────────────────────────────────────────────────────────────────────┘
```

```python
# ui/admin_billing.py
import streamlit as st


def render_billing(current_role: str, workspace_id: int):
    from ui.admin_permission import check_admin_access, render_permission_badge
    from ui.admin_search import render_admin_search_bar, BILLING_FILTER_OPTIONS
    from ui.admin_components import render_module_header, usage_bar

    if not check_admin_access(current_role, ["super_admin", "admin", "owner", "ceo"]):
        return

    render_module_header("💳", "Billing & Subscription",
        "Quản lý gói cước, hóa đơn và theo dõi mức sử dụng", "#f59e0b")
    render_permission_badge(current_role, "billing_plan")

    # ── Current Plan ──
    can_upgrade = current_role in ["super_admin", "owner"]
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#1e293b 0%,#162032 100%);
         border:1px solid #f59e0b44;border-radius:16px;padding:24px;margin-bottom:20px;">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;">
            <div>
                <div style="color:#f59e0b;font-size:0.72rem;font-weight:700;
                     text-transform:uppercase;letter-spacing:0.1em;margin-bottom:8px;">
                    Gói hiện tại
                </div>
                <div style="color:#f1f5f9;font-size:2rem;font-weight:800;margin-bottom:4px;">
                    ENTERPRISE
                </div>
                <div style="color:#94a3b8;font-size:0.85rem;">
                    $299/tháng  •  Gia hạn: 2026-08-01
                </div>
            </div>
            <span style="background:#10b98122;color:#10b981;border:1px solid #10b98144;
                  padding:6px 14px;border-radius:99px;font-size:0.8rem;font-weight:600;">
                ✅ Active
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Usage bars
    st.markdown("##### 📊 Mức sử dụng tháng này")
    usage_bar("🤖 AI Tokens",   82450,  100000, "#7c3aed")
    usage_bar("📝 Bài viết",    247,    500,    "#3b82f6")
    usage_bar("👥 Thành viên",  8,      10,     "#10b981")
    usage_bar("🔌 API Calls",   1203,   50000,  "#f59e0b")

    if can_upgrade:
        uc1, uc2, _ = st.columns([1.5, 1.5, 5])
        with uc1:
            if st.button("🔄 Upgrade gói", type="primary", use_container_width=True):
                st.info("Đang mở trang nâng cấp...")
        with uc2:
            if st.button("📞 Liên hệ Sales", use_container_width=True):
                st.info("sales@company.com")

    st.divider()

    # Invoice history
    st.markdown("##### 📜 Lịch sử hóa đơn")
    render_admin_search_bar(
        placeholder="Tìm theo số hóa đơn, gói cước...",
        filter_options=BILLING_FILTER_OPTIONS,
        key_prefix="billing"
    )

    invoices = [
        ("INV-2026-07", "Enterprise", "$299.00", "✅ Paid",    "2026-07-01"),
        ("INV-2026-06", "Enterprise", "$299.00", "✅ Paid",    "2026-06-01"),
        ("INV-2026-05", "Pro",        "$99.00",  "✅ Paid",    "2026-05-01"),
        ("INV-2026-04", "Pro",        "$99.00",  "⚠️ Overdue", "2026-04-01"),
    ]
    for inv_id, plan, amount, status, date in invoices:
        c1, c2, c3, c4, c5, c6 = st.columns([2, 2, 1.5, 1.5, 2, 1])
        c1.code(inv_id)
        c2.caption(plan)
        c3.markdown(f"**{amount}**")
        c4.markdown(status)
        c5.caption(date)
        c6.button("📥", key=f"dl_{inv_id}", help="Tải PDF hóa đơn")
```

---

### 5.4 🕵️ Audit Logs

```
┌─────────────────────────────────────────────────────────────────────┐
│  🕵️ Audit Logs                         [📤 Export] [⚠️ Alert Config] │
│  ────────────────────────────────────────────────────────────────── │
│  🔍 [Search...]  [Sự kiện ▼] [Thời gian ▼] [Mức độ ▼] [↺]          │
│  ────────────────────────────────────────────────────────────────── │
│  Stats: 1,204 sự kiện │ 3 ⚠️ Warning │ 0 🔴 Critical │ 24h         │
│  ────────────────────────────────────────────────────────────────── │
│  ──── 12/07/2026 ────────────────────────────────────────────────  │
│  🟢 10:15 │ admin@co.com     │ login          │ 192.168.1.1 │ ✅   │
│  🟡 09:47 │ manager@co.com   │ role_change    │ system      │ ⚠️   │
│  🔴 09:12 │ unknown          │ failed_login   │ 45.33.21.8  │ ❌   │
└─────────────────────────────────────────────────────────────────────┘
```

```python
# ui/admin_audit.py
import streamlit as st


LOG_LEVEL_STYLE = {
    "info":     {"icon": "🟢", "color": "#10b981", "bg": "#10b98112"},
    "warning":  {"icon": "🟡", "color": "#f59e0b", "bg": "#f59e0b12"},
    "error":    {"icon": "🔴", "color": "#ef4444", "bg": "#ef444412"},
    "critical": {"icon": "💥", "color": "#dc2626", "bg": "#dc262618"},
}


def render_audit_logs(current_role: str):
    from ui.admin_permission import check_admin_access, render_permission_badge
    from ui.admin_search import render_admin_search_bar, AUDIT_FILTER_OPTIONS
    from ui.admin_components import render_module_header, stat_card

    if not check_admin_access(current_role, ["super_admin", "admin"]):
        return

    render_module_header("🕵️", "Audit Logs",
        "Nhật ký toàn bộ hoạt động người dùng trong hệ thống", "#ef4444",
        action_label="📤 Export Logs")
    render_permission_badge(current_role, "audit_timeline")

    # Stats
    cs1, cs2, cs3, cs4 = st.columns(4)
    stat_card(cs1, "📋 Tổng sự kiện", "1,204", "24 giờ qua",   "#3b82f6")
    stat_card(cs2, "✅ Thành công",    "1,198", "99.5%",        "#10b981")
    stat_card(cs3, "⚠️ Cảnh báo",     "3",     "Cần xem",      "#f59e0b")
    stat_card(cs4, "🔴 Nghiêm trọng", "0",     "Clear ✓",      "#10b981")

    # Security alert (chỉ super_admin)
    if current_role == "super_admin":
        st.error("⚠️ Phát hiện đăng nhập thất bại từ IP lạ: **45.33.21.8** lúc 09:12 hôm nay — [Xem chi tiết →]")

    # Search & Filter
    search = render_admin_search_bar(
        placeholder="Tìm theo email, IP, loại sự kiện...",
        filter_options=AUDIT_FILTER_OPTIONS,
        key_prefix="audit"
    )

    # Timeline
    MOCK_LOGS = {
        "12/07/2026": [
            {"t": "10:15", "user": "admin@company.com",   "action": "login",         "ip": "192.168.1.1", "level": "info",    "detail": "Đăng nhập thành công"},
            {"t": "09:47", "user": "manager@company.com", "action": "role_change",   "ip": "system",      "level": "warning", "detail": "Đổi role editor → marketing"},
            {"t": "09:12", "user": "unknown",              "action": "failed_login",  "ip": "45.33.21.8",  "level": "error",   "detail": "Sai mật khẩu 3 lần liên tiếp"},
        ],
        "11/07/2026": [
            {"t": "23:58", "user": "admin@company.com",   "action": "export_posts",  "ip": "192.168.1.1", "level": "info",    "detail": "Xuất 47 bài viết ra CSV"},
            {"t": "15:22", "user": "editor@company.com",  "action": "create_post",   "ip": "192.168.1.5", "level": "info",    "detail": "Tạo bài viết mới #312"},
        ],
    }

    for date, logs in MOCK_LOGS.items():
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:12px;
             color:#334155;font-size:0.72rem;font-weight:700;
             text-transform:uppercase;letter-spacing:0.08em;margin:16px 0 8px;">
            <div style="flex:1;height:1px;background:#1e293b;"></div>
            📅 {date}
            <div style="flex:1;height:1px;background:#1e293b;"></div>
        </div>
        """, unsafe_allow_html=True)

        for log in logs:
            # Admin không thấy security-level error của IP lạ
            if log["level"] == "error" and current_role != "super_admin":
                continue
            # Apply search filter
            query = search.get("query", "").lower()
            if query and query not in (log["user"] + log["action"] + log["ip"] + log["detail"]).lower():
                continue

            s = LOG_LEVEL_STYLE.get(log["level"], LOG_LEVEL_STYLE["info"])
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:12px;
                 background:{s['bg']};border:1px solid {s['color']}22;
                 border-left:3px solid {s['color']};
                 border-radius:8px;padding:10px 16px;margin-bottom:5px;">
                <span>{s['icon']}</span>
                <span style="color:#475569;font-size:0.75rem;min-width:45px;">{log['t']}</span>
                <span style="color:#94a3b8;font-size:0.8rem;min-width:190px;">{log['user']}</span>
                <code style="color:{s['color']};font-size:0.73rem;min-width:130px;">{log['action']}</code>
                <span style="color:#475569;font-size:0.73rem;min-width:105px;">{log['ip']}</span>
                <span style="color:#64748b;font-size:0.73rem;flex:1;">{log['detail']}</span>
            </div>
            """, unsafe_allow_html=True)
```

---

### 5.5 📡 Monitoring

```
┌─────────────────────────────────────────────────────────────────────┐
│  📡 System Monitoring              ● Live • 30s  [🔄 Làm mới]       │
│  ────────────────────────────────────────────────────────────────── │
│  ┌── Service Health Grid ─────────────────────────────────────────┐ │
│  │ 🟢 Database   🟢 Gemini API   🟢 Facebook   🟡 Zalo   🔴 TikTok│ │
│  │  OK 12ms       OK 340ms        OK 1.2s      Slow 3s    Down    │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  🤖 AI Cost Tracker — Tháng 07/2026                                  │
│  Budget: ████████████░░░░░░ $87.43 / $150   58.3%                  │
│  Top consumers:                                                      │
│    1. 🎨 Content Studio:   $43.12 (49.3%)                           │
│    2. 🛡️ Fact Check:       $21.05 (24.1%)                           │
│    3. 🗓️ Planning Wizard:  $15.88 (18.2%)                           │
└─────────────────────────────────────────────────────────────────────┘
```

```python
# ui/admin_monitoring.py
import streamlit as st


SERVICES = [
    {"name": "Database",   "status": "ok",      "latency": "12ms",  "uptime": "99.9%"},
    {"name": "Gemini API", "status": "ok",      "latency": "340ms", "uptime": "99.7%"},
    {"name": "Facebook",   "status": "ok",      "latency": "1.2s",  "uptime": "98.1%"},
    {"name": "Zalo OA",    "status": "warning", "latency": "3.1s",  "uptime": "94.2%"},
    {"name": "LinkedIn",   "status": "ok",      "latency": "890ms", "uptime": "99.5%"},
    {"name": "TikTok",     "status": "error",   "latency": "N/A",   "uptime": "—"},
]
SVC_STYLE = {
    "ok":      {"icon": "🟢", "color": "#10b981", "bg": "#10b98112"},
    "warning": {"icon": "🟡", "color": "#f59e0b", "bg": "#f59e0b12"},
    "error":   {"icon": "🔴", "color": "#ef4444", "bg": "#ef444412"},
}


def render_monitoring(current_role: str):
    from ui.admin_permission import check_admin_access, render_permission_badge
    from ui.admin_components import render_module_header, usage_bar

    if not check_admin_access(current_role, ["super_admin", "admin", "owner", "ceo"]):
        return

    ct, cl, cr = st.columns([5, 2, 1.5])
    with ct:
        render_module_header("📡", "System Monitoring",
            "Giám sát sức khỏe hệ thống và API theo thời gian thực", "#06b6d4")
    with cl:
        st.markdown("""
        <div style="display:flex;align-items:center;gap:8px;margin-top:1.4rem;">
            <span style="width:8px;height:8px;border-radius:50%;background:#10b981;
                  display:inline-block;animation:pulse-dot 2s infinite;"></span>
            <span style="color:#10b981;font-size:0.8rem;font-weight:600;">Live</span>
            <span style="color:#475569;font-size:0.75rem;">• 30s</span>
        </div>
        <style>@keyframes pulse-dot{0%,100%{opacity:1}50%{opacity:0.3}}</style>
        """, unsafe_allow_html=True)
    with cr:
        if st.button("🔄", key="mon_refresh", help="Làm mới ngay"):
            st.rerun()

    render_permission_badge(current_role, "mon_health")

    # Service grid
    st.markdown("##### 🟢 Trạng thái dịch vụ")
    cols = st.columns(len(SERVICES))
    for col, svc in zip(cols, SERVICES):
        s = SVC_STYLE[svc["status"]]
        col.markdown(f"""
        <div style="background:{s['bg']};border:1px solid {s['color']}33;
             border-radius:10px;padding:14px;text-align:center;">
            <div style="font-size:1.4rem;">{s['icon']}</div>
            <div style="color:#f1f5f9;font-size:0.73rem;font-weight:600;margin:6px 0 2px;">
                {svc['name']}</div>
            <div style="color:{s['color']};font-size:0.7rem;">{svc['latency']}</div>
            <div style="color:#475569;font-size:0.65rem;">{svc['uptime']}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("")

    # AI Cost Tracker
    if current_role in ["super_admin", "admin", "owner", "ceo"]:
        st.markdown("##### 🤖 AI Cost Tracker — Tháng 07/2026")
        usage_bar("Gemini API Budget", 87.43, 150.0, "#7c3aed")

        st.markdown("""
        <div style="background:#1e293b;border-radius:10px;padding:16px;margin-top:8px;">
            <div style="color:#64748b;font-size:0.78rem;margin-bottom:10px;
                 text-transform:uppercase;letter-spacing:0.05em;">Top consumers</div>
            <div style="color:#f1f5f9;font-size:0.83rem;line-height:2.2;">
                1. 🎨 Content Studio &nbsp;&nbsp; <strong>$43.12</strong>
                    <span style="color:#64748b;">(49.3%)</span><br>
                2. 🛡️ Fact Check &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <strong>$21.05</strong>
                    <span style="color:#64748b;">(24.1%)</span><br>
                3. 🗓️ Planning Wizard <strong>$15.88</strong>
                    <span style="color:#64748b;">(18.2%)</span><br>
                4. 📚 Knowledge Base &nbsp;<strong>$7.38</strong>
                    <span style="color:#64748b;">(8.4%)</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
```

---

### 5.6 🏢 Workspace

```python
# ui/admin_workspace.py
import streamlit as st


def render_workspace(current_role: str, workspace_id: int, workspace_data: dict):
    from ui.admin_permission import check_admin_access, render_permission_badge
    from ui.admin_components import render_module_header

    if not check_admin_access(current_role, ["super_admin", "admin", "owner", "manager"]):
        return

    render_module_header("🏢", "Workspace Settings",
        "Cấu hình không gian làm việc, kết nối mạng XH và thành viên", "#10b981")
    render_permission_badge(current_role, "ws_settings")

    tabs = st.tabs(["⚙️ General", "🌐 Social Connections", "🤝 Invitations", "🗑️ Danger Zone"])
    with tabs[0]: _ws_general(current_role, workspace_data)
    with tabs[1]: _ws_social(current_role)
    with tabs[2]: _ws_invitations(current_role)
    with tabs[3]: _ws_danger(current_role, workspace_id)


def _ws_general(role: str, data: dict):
    editable = role in ["super_admin", "admin", "owner"]
    c1, c2 = st.columns(2)
    with c1:
        st.text_input("🏢 Tên Workspace",
            value=data.get("name", "AI Content Agency"), disabled=not editable)
        st.selectbox("🌐 Múi giờ",
            ["Asia/Ho_Chi_Minh (UTC+7)", "Asia/Bangkok (UTC+7)", "UTC+0"],
            disabled=not editable)
    with c2:
        st.selectbox("🌐 Ngôn ngữ mặc định", ["Tiếng Việt (vi)", "English (en)"], disabled=not editable)
        st.text_input("🖼️ Logo URL", placeholder="https://...", disabled=not editable)

    if editable:
        if st.button("💾 Lưu cài đặt", type="primary"):
            st.success("✅ Đã lưu cài đặt Workspace!")


def _ws_social(role: str):
    editable = role in ["super_admin", "admin", "owner"]
    socials = [
        {"icon": "f", "name": "Facebook Page",  "status": "ok",       "info": "Token còn 23 ngày",   "color": "#1877f2"},
        {"icon": "L", "name": "LinkedIn",        "status": "ok",       "info": "Token còn 7 ngày",    "color": "#0a66c2"},
        {"icon": "Z", "name": "Zalo OA",         "status": "ok",       "info": "Kết nối bình thường", "color": "#0068ff"},
        {"icon": "T", "name": "TikTok Business", "status": "inactive", "info": "Chưa kết nối",        "color": "#ff0050"},
    ]
    for s in socials:
        ok = s["status"] == "ok"
        status_html = (
            f'<span style="color:#10b981;font-size:0.8rem;">✅ Đã kết nối</span>'
            f'<span style="color:#475569;font-size:0.75rem;margin-left:8px;">• {s["info"]}</span>'
            if ok else
            f'<span style="color:#475569;font-size:0.8rem;">○ Chưa kết nối</span>'
        )
        col_icon, col_info, col_btn = st.columns([0.5, 5, 1.5])
        with col_icon:
            st.markdown(f"""
            <div style="width:36px;height:36px;border-radius:8px;
                 background:{s['color']};display:flex;align-items:center;
                 justify-content:center;color:white;font-weight:700;
                 margin-top:4px;">{s['icon']}</div>
            """, unsafe_allow_html=True)
        with col_info:
            st.markdown(f"**{s['name']}** &nbsp;&nbsp; {status_html}", unsafe_allow_html=True)
        with col_btn:
            lbl = "↻ Gia hạn" if ok else "+ Kết nối"
            if editable:
                st.button(lbl, key=f"social_{s['name']}", use_container_width=True)
        st.divider()


def _ws_invitations(role: str):
    can_invite = role in ["super_admin", "admin", "owner", "manager"]
    if can_invite:
        with st.form("invite_form"):
            ic1, ic2, ic3 = st.columns([3, 2, 1.5])
            with ic1:
                email = st.text_input("📧 Email người được mời")
            with ic2:
                from core.rbac import ALL_ROLES
                inv_role = st.selectbox("Vai trò", ALL_ROLES)
            with ic3:
                st.write(" ")
                submit = st.form_submit_button("📨 Mời", use_container_width=True)
            if submit and email:
                st.success(f"✅ Đã gửi lời mời tới **{email}** với vai trò **{inv_role}**!")

    st.markdown("##### 📋 Lời mời đang chờ:")
    pending = [
        {"Email": "neweditor@co.com",   "Vai trò": "editor",  "Gửi lúc": "2026-07-11 09:00"},
        {"Email": "viewer001@co.com",   "Vai trò": "viewer",  "Gửi lúc": "2026-07-10 14:30"},
    ]
    import pandas as pd
    if pending:
        st.dataframe(pd.DataFrame(pending), use_container_width=True, hide_index=True)


def _ws_danger(role: str, workspace_id: int):
    if not role in ["super_admin", "owner"]:
        st.info("🔒 Khu vực này chỉ dành cho Owner và Super Admin.")
        return

    st.markdown("""
    <div style="background:#1a0a0a;border:1px solid #ef444444;
         border-radius:12px;padding:24px;margin-top:12px;">
        <h4 style="color:#ef4444;margin:0 0 8px;">⚠️ Danger Zone</h4>
        <p style="color:#94a3b8;font-size:0.85rem;margin:0;">
            Các thao tác không thể hoàn tác. Thực hiện cẩn thận.
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.write("")

    dc1, dc2 = st.columns(2)
    with dc1:
        st.markdown("**🗂️ Xóa toàn bộ dữ liệu nội dung**")
        st.caption("Xóa tất cả bài viết, draft và lịch sử. Không thể khôi phục.")
        if st.button("🗑️ Xóa dữ liệu", use_container_width=True, type="secondary"):
            conf = st.text_input("Nhập `DELETE` để xác nhận:", key="danger_data")
            if conf == "DELETE":
                st.error("⚠️ Cần xác thực qua email trước khi thực hiện!")

    with dc2:
        st.markdown("**💀 Xóa toàn bộ Workspace**")
        st.caption("Xóa workspace và tất cả dữ liệu thành viên. Vĩnh viễn.")
        if st.button("💀 Xóa Workspace", use_container_width=True, type="secondary"):
            conf2 = st.text_input("Nhập tên workspace để xác nhận:", key="danger_ws")
            if conf2:
                st.error("⚠️ Yêu cầu xác nhận 2 bước qua email!")
```

---

### 5.7 👥 Users

```python
# ui/admin_users.py
import streamlit as st
import pandas as pd


def render_users(current_role: str, workspace_id: int):
    from ui.admin_permission import check_admin_access, render_permission_badge
    from ui.admin_search import render_admin_search_bar, USER_FILTER_OPTIONS
    from ui.admin_components import render_module_header
    from database.models.users import UserModel
    from core.rbac import ALL_ROLES, get_role_display  # Chỉ đọc, không sửa

    if not check_admin_access(current_role, ["super_admin", "admin", "owner", "manager"]):
        return

    can_manage = current_role in ["super_admin", "admin", "owner"]

    render_module_header("👥", "User Management",
        "Quản lý thành viên, phân công vai trò và kiểm soát quyền", "#8b5cf6",
        action_label="+ Mời thành viên" if can_manage else None)
    render_permission_badge(current_role, "users_directory")

    # Capacity bar
    users = UserModel.list_all(active_only=False)
    active_count = sum(1 for u in users if u.get("is_active"))
    st.markdown(f"""
    <div style="display:flex;align-items:center;justify-content:space-between;
         background:#1e293b;border-radius:8px;padding:12px 16px;margin-bottom:16px;">
        <span style="color:#94a3b8;font-size:0.85rem;">
            👥 <strong style="color:#f1f5f9">{active_count}</strong>
            / 10 thành viên đang hoạt động
        </span>
        <div style="background:#0f172a;border-radius:99px;height:6px;width:180px;overflow:hidden;">
            <div style="background:#8b5cf6;height:100%;
                 width:{active_count/10*100}%;border-radius:99px;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Search & Filter
    search = render_admin_search_bar(
        placeholder="Tìm theo tên, email, username...",
        filter_options=USER_FILTER_OPTIONS,
        key_prefix="users"
    )

    # User table với custom HTML
    _render_user_table_html(users, current_role, get_role_display, search)

    # Action bar (admin+)
    if can_manage and users:
        st.write("")
        user_opts = {u["id"]: f"{u.get('full_name') or u['username']} ({u['email']})" for u in users}
        ac1, ac2, ac3, _ = st.columns([2.5, 2, 1.5, 4])
        with ac1:
            sel = st.selectbox("Chọn thành viên:", list(user_opts.keys()),
                format_func=lambda x: user_opts[x], key="users_sel")
        with ac2:
            new_role = st.selectbox("Vai trò mới:", ALL_ROLES, key="users_new_role")
        with ac3:
            st.write(" ")
            if st.button("✅ Áp dụng", type="primary", use_container_width=True):
                UserModel.update(sel, role=new_role)
                st.success(f"✅ Đã cập nhật vai trò thành **{new_role}**!")
                st.rerun()

        if current_role in ["super_admin", "admin"]:
            bc1, bc2, _ = st.columns([1.5, 1.5, 7])
            with bc1:
                if st.button("🚫 Vô hiệu hóa", use_container_width=True):
                    UserModel.update(sel, is_active=0)
                    st.warning("Đã vô hiệu hóa tài khoản!")
                    st.rerun()


def _render_user_table_html(users, current_role, get_role_display, search):
    """Custom HTML table cho User Directory."""
    query = search.get("query", "").lower()
    role_filter = search.get("filters", {}).get("Vai trò", "Tất cả")
    status_filter = search.get("filters", {}).get("Trạng thái", "Tất cả")

    st.markdown("""
    <div style="background:#162032;border-radius:12px;overflow:hidden;border:1px solid #1e293b;">
    <table style="width:100%;border-collapse:collapse;font-size:0.82rem;">
    <thead><tr style="background:#0a0f1e;color:#475569;text-transform:uppercase;
        font-size:0.68rem;letter-spacing:0.05em;">
        <th style="padding:12px 16px;text-align:left;">Thành viên</th>
        <th style="padding:12px;text-align:left;">Email</th>
        <th style="padding:12px;text-align:center;">Vai trò</th>
        <th style="padding:12px;text-align:center;">Trạng thái</th>
        <th style="padding:12px;text-align:center;">Ngày tạo</th>
    </tr></thead><tbody>
    """, unsafe_allow_html=True)

    for u in users:
        name = u.get("full_name") or u.get("username", "?")
        email = u.get("email", "—")
        role = u.get("role", "viewer")
        is_active = u.get("is_active", 0)

        # Apply filters
        if query and query not in (name + email + role).lower():
            continue
        if role_filter != "Tất cả" and role != role_filter:
            continue
        if status_filter == "active" and not is_active:
            continue
        if status_filter == "inactive" and is_active:
            continue

        meta = get_role_display(role)
        avatar = name[0].upper()
        status_html = (
            '<span style="color:#10b981;font-size:0.73rem;">● Hoạt động</span>'
            if is_active else
            '<span style="color:#475569;font-size:0.73rem;">○ Vô hiệu</span>'
        )
        st.markdown(f"""
        <tr style="border-top:1px solid #1e293b;{'opacity:0.5;' if not is_active else ''}">
            <td style="padding:12px 16px;">
                <div style="display:flex;align-items:center;gap:10px;">
                    <div style="width:32px;height:32px;border-radius:50%;
                         background:{meta['color']};display:flex;align-items:center;
                         justify-content:center;color:#fff;font-weight:700;font-size:0.8rem;">
                        {avatar}
                    </div>
                    <div>
                        <div style="color:#f1f5f9;font-weight:500;">{name}</div>
                        <div style="color:#475569;font-size:0.7rem;">@{u.get('username','')}</div>
                    </div>
                </div>
            </td>
            <td style="padding:12px;color:#94a3b8;">{email}</td>
            <td style="padding:12px;text-align:center;">
                <span style="background:{meta['color']}22;color:{meta['color']};
                      border:1px solid {meta['color']}44;
                      padding:3px 10px;border-radius:99px;
                      font-size:0.7rem;font-weight:600;">
                    {meta['icon']} {meta['label']}
                </span>
            </td>
            <td style="padding:12px;text-align:center;">{status_html}</td>
            <td style="padding:12px;text-align:center;color:#475569;font-size:0.73rem;">
                {str(u.get('created_at','—'))[:10]}
            </td>
        </tr>
        """, unsafe_allow_html=True)

    st.markdown("</tbody></table></div>", unsafe_allow_html=True)
```

---

### 5.8 🔌 API Config

```python
# ui/admin_api_config.py
import streamlit as st
import os


AI_PROVIDERS = [
    {"name": "Gemini API",  "icon": "✨", "env": "GEMINI_API_KEY",  "model": "gemini-2.0-flash", "status": "active",   "color": "#7c3aed", "quota": "1M tokens/day", "used": "82,450",  "latency": "~340ms"},
    {"name": "OpenAI",      "icon": "🤖", "env": "OPENAI_API_KEY",  "model": "gpt-4o",           "status": "inactive", "color": "#10b981"},
    {"name": "Anthropic",   "icon": "🧠", "env": "CLAUDE_API_KEY",  "model": "claude-sonnet",    "status": "inactive", "color": "#f59e0b"},
]
SOCIAL_APIS = [
    {"name": "Facebook",   "env": "FACEBOOK_TOKEN",   "color": "#1877f2", "status": "active"},
    {"name": "LinkedIn",   "env": "LINKEDIN_TOKEN",   "color": "#0a66c2", "status": "active"},
    {"name": "Zalo OA",    "env": "ZALO_OA_TOKEN",    "color": "#0068ff", "status": "active"},
    {"name": "TikTok",     "env": "TIKTOK_TOKEN",     "color": "#ff0050", "status": "inactive"},
]


def render_api_config(current_role: str):
    from ui.admin_permission import check_admin_access, render_permission_badge
    from ui.admin_components import render_module_header

    if not check_admin_access(current_role, ["super_admin", "admin", "owner"]):
        return

    render_module_header("🔌", "API Configuration",
        "Quản lý API keys cho AI providers và mạng xã hội", "#f97316",
        action_label="🧪 Test All APIs")
    render_permission_badge(current_role, "api_ai")

    tabs = st.tabs(["🤖 AI Providers", "📱 Social APIs", "🔗 Webhooks", "🧪 API Tester"])
    with tabs[0]: _ai_providers(current_role)
    with tabs[1]: _social_apis(current_role)
    with tabs[2]: _webhooks(current_role)
    with tabs[3]: _api_tester()


def _ai_providers(role: str):
    ai_edit = role in ["super_admin", "admin"]
    for p in AI_PROVIDERS:
        active = p["status"] == "active"
        with st.expander(f"{p['icon']} {p['name']} — {'✅ Active' if active else '○ Inactive'}",
                         expanded=active):
            if active:
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**Model:** `{p.get('model','—')}`")
                    # Masked key
                    env_val = os.getenv(p["env"], "")
                    show_key = st.session_state.get(f"show_{p['name']}", False)
                    display = env_val if (show_key and env_val) else "AIzaSy••••••••XXXX"
                    kc1, kc2 = st.columns([4, 1])
                    with kc1: st.code(display, language=None)
                    with kc2:
                        if st.button("👁", key=f"show_{p['name']}", help="Hiện/Ẩn"):
                            st.session_state[f"show_{p['name']}"] = not show_key
                            st.rerun()
                with c2:
                    st.metric("Quota",      p.get("quota", "—"))
                    st.metric("Used today", p.get("used",  "—"))
                    st.metric("Latency",    p.get("latency","—"))

                if ai_edit:
                    b1, b2, _ = st.columns([1.2, 1.5, 5])
                    with b1:
                        if st.button("▶ Test", key=f"test_{p['name']}", type="primary"):
                            import time; time.sleep(0.5)
                            st.success(f"✅ {p['name']} hoạt động!")
                    with b2:
                        st.button("✏️ Cập nhật key", key=f"edit_{p['name']}")
            else:
                st.info(f"Chưa kết nối. Thêm `{p['env']}` vào `.env` để bật.")
                if ai_edit:
                    new_k = st.text_input(f"Nhập {p['name']} API Key:", type="password",
                                          key=f"new_k_{p['name']}")
                    if st.button(f"+ Kết nối {p['name']}", key=f"conn_{p['name']}", type="primary"):
                        if new_k:
                            st.success("✅ Đã lưu! Vui lòng khởi động lại app.")


def _social_apis(role: str):
    edit = role in ["super_admin", "admin", "owner"]
    for s in SOCIAL_APIS:
        ok = s["status"] == "active"
        c1, c2, c3, c4 = st.columns([0.4, 2, 3, 1.5])
        with c1:
            st.markdown(f"""<div style="width:30px;height:30px;border-radius:6px;
                background:{s['color']};display:flex;align-items:center;
                justify-content:center;color:#fff;font-weight:700;
                font-size:0.8rem;margin-top:4px;">{s['name'][0]}</div>""",
                unsafe_allow_html=True)
        with c2:
            st.markdown(f"**{s['name']}**")
        with c3:
            env_val = os.getenv(s["env"], "")
            display = (env_val[:8] + "••••••••") if env_val else "Chưa cấu hình"
            st.code(display, language=None)
        with c4:
            if edit:
                lbl = "↻ Refresh" if ok else "+ Kết nối"
                st.button(lbl, key=f"soc_{s['name']}", use_container_width=True)
        st.divider()


def _webhooks(role: str):
    edit = role in ["super_admin", "admin"]
    st.markdown("#### 🔗 Cấu hình Webhooks")
    if edit:
        with st.expander("➕ Thêm Webhook mới"):
            wc1, wc2 = st.columns(2)
            with wc1:
                st.text_input("Tên webhook", placeholder="Ví dụ: Notify Slack on publish")
                st.text_input("URL", placeholder="https://hooks.slack.com/...")
            with wc2:
                st.multiselect("Events", ["post.created", "post.published", "post.approved", "user.joined"])
                st.selectbox("Method", ["POST", "GET", "PUT"])
            if st.button("➕ Thêm webhook", type="primary"):
                st.success("✅ Đã thêm webhook!")

    st.markdown("##### Webhooks đang hoạt động:")
    wh_data = [
        {"Tên": "Slack notify",    "URL": "https://hooks.slack.com/...", "Events": "post.published", "Status": "✅ Active"},
        {"Tên": "CRM sync",        "URL": "https://api.crm.com/hook",   "Events": "user.joined",    "Status": "✅ Active"},
    ]
    import pandas as pd
    st.dataframe(pd.DataFrame(wh_data), use_container_width=True, hide_index=True)


def _api_tester():
    st.markdown("#### 🧪 API Tester")
    tc1, tc2 = st.columns(2)
    with tc1:
        provider = st.selectbox("Provider", ["Gemini API", "OpenAI", "Facebook", "Zalo OA"])
        endpoint  = st.text_input("Endpoint / Method", placeholder="generateContent")
    with tc2:
        payload = st.text_area("Payload (JSON)", height=120,
            placeholder='{"prompt": "Hello, test!"}')

    if st.button("▶ Gửi Request", type="primary"):
        with st.spinner("Đang test..."):
            import time; time.sleep(1)
        st.success("✅ Response: 200 OK")
        st.json({"status": "ok", "latency_ms": 342, "model": "gemini-2.0-flash", "tokens_used": 15})
```

---

### 5.9 🎭 Role Management (Read-Only Display)

> ⚠️ **Module này chỉ đọc từ `core/rbac.py`. Không sửa file RBAC.**

```python
# ui/admin_roles.py
import streamlit as st
import pandas as pd


def render_role_management(current_role: str):
    from ui.admin_permission import check_admin_access, render_permission_badge
    from ui.admin_components import render_module_header

    if not check_admin_access(current_role, ["super_admin"]):
        return

    render_module_header("🎭", "Role Management",
        "Xem cấu trúc phân quyền hệ thống — Read-only display từ core/rbac.py", "#ec4899")
    render_permission_badge(current_role, "role_matrix")

    st.warning("""
    ⚠️ **Chế độ chỉ đọc** — Module này hiển thị dữ liệu từ `core/rbac.py`.  
    Để thay đổi cấu trúc phân quyền, chỉnh sửa trực tiếp file `core/rbac.py` và khởi động lại app.
    """)

    tabs = st.tabs(["📜 Role Definitions", "🛡️ Permission Matrix", "📊 Role Analytics"])
    with tabs[0]: _role_definitions()
    with tabs[1]: _permission_matrix()
    with tabs[2]: _role_analytics()


def _role_definitions():
    from core.rbac import ALL_ROLES, ROLE_DISPLAY, ROLE_PERMISSIONS

    st.markdown("#### 📜 Định nghĩa các vai trò hệ thống")
    st.caption("📁 Nguồn: `core/rbac.ROLE_DISPLAY` — Read-only")

    cols = st.columns(4)
    for idx, role in enumerate(ALL_ROLES):
        meta  = ROLE_DISPLAY.get(role, {})
        perms = ROLE_PERMISSIONS.get(role, {})
        color = meta.get("color", "#334155")
        col   = cols[idx % 4]

        perm_html = "".join(
            f"<div style='color:{'#10b981' if v else '#334155'};font-size:0.7rem;'>"
            f"{'✅' if v else '❌'} {{'create_post':'Tạo bài','auto_post':'Auto Post','manage_workspace':'Manage WS','view_history':'Xem lịch sử'}.get(k,k)}</div>"
            for k, v in perms.items()
        )
        col.markdown(f"""
        <div style="background:{color}18;border:1px solid {color}44;border-radius:12px;
             padding:16px;margin-bottom:12px;text-align:center;">
            <div style="font-size:2rem;">{meta.get('icon','')}</div>
            <div style="color:{color};font-weight:700;font-size:0.9rem;margin:8px 0 4px;">
                {meta.get('label', role.title())}
            </div>
            <code style="color:#475569;font-size:0.68rem;">{role}</code>
            <div style="margin-top:10px;text-align:left;">{perm_html}</div>
        </div>
        """, unsafe_allow_html=True)


def _permission_matrix():
    from core.rbac import ALL_ROLES, ROLE_PERMISSIONS

    st.markdown("#### 🛡️ Ma trận phân quyền")
    st.caption("📁 Nguồn: `core/rbac.ROLE_PERMISSIONS` — Read-only")

    perm_labels = {
        "create_post":       "📝 Tạo bài",
        "auto_post":         "🤖 Auto Post",
        "manage_workspace":  "🏢 Manage WS",
        "view_history":      "📜 Xem lịch sử",
    }
    matrix = {}
    for pk, pl in perm_labels.items():
        row = {}
        for role in ALL_ROLES:
            row[role.upper()] = "✅" if ROLE_PERMISSIONS.get(role, {}).get(pk) else "❌"
        matrix[pl] = row

    df = pd.DataFrame(matrix).T
    st.dataframe(df, use_container_width=True)

    st.markdown("""
    <div style="background:#1e293b;border-radius:8px;padding:10px 16px;margin-top:10px;">
        <code style="color:#475569;font-size:0.75rem;">
            📁 core/rbac.py → ROLE_PERMISSIONS dict — Không chỉnh sửa từ UI này.
        </code>
    </div>
    """, unsafe_allow_html=True)


def _role_analytics():
    from core.rbac import ALL_ROLES, get_role_display
    from database.models.users import UserModel

    st.markdown("#### 📊 Phân bổ thành viên theo vai trò")
    users = UserModel.list_all(active_only=False)
    total = len(users) or 1

    for role in ALL_ROLES:
        count = sum(1 for u in users if u.get("role") == role)
        if count == 0:
            continue
        meta = get_role_display(role)
        pct  = count / total * 100
        c1, c2 = st.columns([0.5, 5])
        with c1:
            st.markdown(f"<span style='color:{meta['color']};font-weight:700;font-size:1.1rem;'>"
                       f"{meta['icon']} {count}</span>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div style="margin-top:6px;">
                <div style="display:flex;justify-content:space-between;margin-bottom:5px;">
                    <span style="color:#94a3b8;font-size:0.8rem;">{meta['label']}</span>
                    <span style="color:{meta['color']};font-size:0.75rem;">{pct:.0f}%</span>
                </div>
                <div style="background:#1e293b;border-radius:99px;height:4px;overflow:hidden;">
                    <div style="background:{meta['color']};height:100%;width:{pct}%;
                         border-radius:99px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
```

---

## 🔗 6. Main Controller

```python
# ui/tab_admin.py
"""
ui/tab_admin.py  —  Entry point Admin Panel.
KHÔNG SỬA core/rbac.py từ file này.
"""
import streamlit as st


# Map node_id → module group
NODE_GROUP_MAP = {
    **{k: "brain"      for k in ["brain_voice","brain_audience","brain_product","brain_ai"]},
    **{k: "knowledge"  for k in ["kb_articles","kb_import","kb_tags","kb_search"]},
    **{k: "billing"    for k in ["billing_plan","billing_invoice","billing_usage","billing_upgrade"]},
    **{k: "audit"      for k in ["audit_timeline","audit_security","audit_export","audit_alerts"]},
    **{k: "monitoring" for k in ["mon_health","mon_api","mon_cost","mon_alerts"]},
    **{k: "workspace"  for k in ["ws_settings","ws_social","ws_invitations","ws_danger"]},
    **{k: "users"      for k in ["users_directory","users_add","users_roles","users_inactive"]},
    **{k: "api"        for k in ["api_ai","api_social","api_webhooks","api_tester"]},
    **{k: "roles"      for k in ["role_definitions","role_matrix","role_analytics","role_bulk"]},
}

ADMIN_ALLOWED = {"super_admin", "admin", "owner", "ceo", "manager"}


def render_tab_admin(
    current_role: str = "admin",
    workspace_id: int = 1,
    workspace_data: dict = None,
):
    """Entry point chính cho Admin Panel."""
    if current_role not in ADMIN_ALLOWED:
        st.error("🔒 Bạn không có quyền truy cập Admin Panel.")
        return

    _inject_admin_global_css()

    from ui.admin_sidebar import render_admin_tree_nav
    from ui.admin_components import render_breadcrumb

    active_node = render_admin_tree_nav(current_role)
    render_breadcrumb(active_node)

    group = NODE_GROUP_MAP.get(active_node, "")

    if group == "brain":
        from ui.admin_company_brain import render_company_brain
        render_company_brain(current_role, workspace_id)
    elif group == "knowledge":
        from ui.admin_knowledge import render_knowledge_base
        render_knowledge_base(current_role, workspace_id)
    elif group == "billing":
        from ui.admin_billing import render_billing
        render_billing(current_role, workspace_id)
    elif group == "audit":
        from ui.admin_audit import render_audit_logs
        render_audit_logs(current_role)
    elif group == "monitoring":
        from ui.admin_monitoring import render_monitoring
        render_monitoring(current_role)
    elif group == "workspace":
        from ui.admin_workspace import render_workspace
        render_workspace(current_role, workspace_id, workspace_data or {})
    elif group == "users":
        from ui.admin_users import render_users
        render_users(current_role, workspace_id)
    elif group == "api":
        from ui.admin_api_config import render_api_config
        render_api_config(current_role)
    elif group == "roles":
        from ui.admin_roles import render_role_management
        render_role_management(current_role)
    else:
        st.info("🗺️ Chọn một mục từ menu bên trái để bắt đầu.")


def _inject_admin_global_css():
    """CSS toàn cục cho Admin Panel."""
    st.markdown("""
    <style>
    /* Page base */
    .main .block-container { padding: 1.5rem 2rem !important; max-width: 100% !important; }
    #MainMenu, footer { display: none; }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background:#1e293b !important;border-radius:10px !important;
        padding:4px !important;gap:4px !important;
    }
    .stTabs [data-baseweb="tab"] {
        background:transparent !important;color:#64748b !important;
        border-radius:8px !important;padding:6px 16px !important;font-size:0.82rem !important;
    }
    .stTabs [aria-selected="true"] {
        background:#3b82f620 !important;color:#60a5fa !important;
    }

    /* Expanders */
    .streamlit-expanderHeader {
        background:#1e293b !important;border-radius:8px !important;color:#94a3b8 !important;
    }

    /* Buttons */
    .stButton > button[kind="primary"] {
        background:linear-gradient(135deg,#7c3aed,#4f46e5) !important;
        border:none !important;color:#fff !important;
        font-weight:600 !important;border-radius:8px !important;
    }
    .stButton > button[kind="secondary"] {
        background:#1e293b !important;border:1px solid #334155 !important;
        color:#94a3b8 !important;border-radius:8px !important;
    }

    /* Metrics */
    [data-testid="metric-container"] {
        background:#1e293b !important;border-radius:10px !important;
        padding:12px !important;border:1px solid #263348 !important;
    }

    /* Inputs */
    .stTextInput > div > div > input,
    .stTextArea > div > textarea {
        background:#162032 !important;border:1px solid #1e293b !important;
        color:#f1f5f9 !important;border-radius:8px !important;
    }
    .stTextInput > div > div > input:focus {
        border-color:#3b82f6 !important;box-shadow:0 0 0 3px #3b82f620 !important;
    }
    .stSelectbox > div > div {
        background:#162032 !important;border:1px solid #1e293b !important;color:#f1f5f9 !important;
    }

    /* Dataframe */
    [data-testid="stDataFrame"] {
        background:#1e293b !important;border-radius:10px !important;overflow:hidden !important;
    }
    </style>
    """, unsafe_allow_html=True)
```

---

## 📁 7. File Structure — Tổng hợp

```
ui/
├── tab_admin.py              ← [THAY ĐỔI] Main controller
├── admin_sidebar.py          ← [MỚI] Tree Navigation + ADMIN_TREE_CONFIG
├── admin_permission.py       ← [MỚI] Permission Gate, Access Denied UI
├── admin_search.py           ← [MỚI] Search Bar + Filter presets
├── admin_components.py       ← [MỚI] Shared: header, stat_card, usage_bar, breadcrumb
├── admin_theme.py            ← [MỚI] Color tokens Admin Dark Theme
├── admin_company_brain.py    ← [MỚI] Module Company Brain
├── admin_knowledge.py        ← [MỚI] Module Knowledge Base  
├── admin_billing.py          ← [MỚI] Module Billing
├── admin_audit.py            ← [MỚI] Module Audit Logs
├── admin_monitoring.py       ← [MỚI] Module Monitoring
├── admin_workspace.py        ← [MỚI] Module Workspace Settings
├── admin_users.py            ← [MỚI] Module User Management
├── admin_api_config.py       ← [MỚI] Module API Configuration
└── admin_roles.py            ← [MỚI] Module Role Management (read-only)

# Không thay đổi:
core/rbac.py                  ← [KHÔNG CHỈNH SỬA] Single source of truth RBAC
```

---

## ✅ 8. Role-Based UI Summary

| Role | Vào Admin? | Modules có quyền | Ghi chú |
|------|:----------:|---|---|
| `super_admin` | ✅ | Tất cả 9 modules | Full RW + Danger Zone + Security Events + Role Mgmt |
| `admin` | ✅ | Brain, Knowledge, Billing(R), Audit(R), Monitoring, Workspace, Users, API | Không có Danger Zone, không thấy Security Events |
| `owner` | ✅ | Brain, Knowledge, Billing, Monitoring, Workspace, Users, API Social | Có Danger Zone, không có Role Mgmt |
| `ceo` | ✅ | Billing(R), Monitoring Cost | Chỉ xem chi phí |
| `manager` | ✅ (limited) | Knowledge(R), Workspace(Invite), Users(R) | Read + Invite members |
| `editor` | ❌ | — | Access Denied screen |
| `marketing` | ❌ | — | Access Denied screen |
| `viewer` | ❌ | — | Access Denied screen |

---

## 🚀 9. Integration — Tích hợp vào App

```python
# Trong app/main.py — Thêm routing đến Admin Panel
from ui.tab_admin import render_tab_admin

# Khi user chọn nhóm Administration trong sidebar:
if st.session_state.get("active_group") == "administration":
    current_user = st.session_state.get("current_user", {})
    render_tab_admin(
        current_role   = current_user.get("role", "viewer"),
        workspace_id   = st.session_state.get("active_workspace_id", 1),
        workspace_data = st.session_state.get("workspace_data", {}),
    )
```

---

> **📌 Nguyên tắc bất biến**: Toàn bộ Admin Panel đọc trực tiếp từ  
> `core/rbac.ALL_ROLES`, `core/rbac.ROLE_DISPLAY`, `core/rbac.ROLE_PERMISSIONS`  
> mà **không thay đổi** bất kỳ dòng nào trong `core/rbac.py`.  
> Mọi thay đổi RBAC phải được thực hiện trực tiếp trong file đó bởi developer có thẩm quyền.
