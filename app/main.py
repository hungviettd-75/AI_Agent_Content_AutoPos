import streamlit as st
import os
import sys
import json
from datetime import datetime

# Dam bao Python uu tien import cac package noi bo cua du an tren Streamlit Cloud
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config import settings
from database.connection import init_db
from database.models.users import UserModel
from database.models.workspaces import WorkspaceModel
from core.auth import encode_jwt, decode_jwt
from core.rbac import MANAGER_ROLES, get_role_display, normalize_role, render_permissions_table, ALL_ROLES
from core.audit_logger import (
    log_login, log_login_failed, log_logout, log_register,
    log_create_workspace, log_add_member, log_remove_member, log_change_role
)

# Khá»Ÿi táº¡o giao diá»‡n trang
st.set_page_config(page_title="Apex AI Logistics - Sales & Marketing Growth", layout="wide", page_icon="🚀")

@st.cache_resource(show_spinner=False)
def ensure_database_ready():
    """Run schema setup once per Streamlit process instead of every rerun."""
    init_db()
    return True

ensure_database_ready()

# NhÃºng Custom CSS cho giao diá»‡n chuyÃªn nghiá»‡p cá»§a Apex AI
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* ============================
       APEX AI â€” CORE SYSTEM
       ============================ */

    /* Font & Canvas ná»n */
    html, body, [class*="css"], .stApp {
        font-family: 'Inter', sans-serif !important;
        background-color: #f9f9ff !important;
        color: #141b2b !important;
    }

    /* ============================
       SIDEBAR â€” Slate Dark Anchor
       ============================ */
    [data-testid="stSidebar"] {
        background-color: #1e293b !important;
        border-right: 1px solid #293040 !important;
    }

    /* Chá»‰ nháº¯m vÃ o text thuáº§n â€” KHÃ”NG Ä‘á»¥ng span (trÃ¡nh lá»—i icon Material) */
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] .stMarkdown li,
    [data-testid="stSidebar"] label {
        color: #edf0ff !important;
    }

    /* Input trong sidebar */
    [data-testid="stSidebar"] input {
        background-color: #293040 !important;
        color: #edf0ff !important;
        border: 1px solid #434655 !important;
        border-radius: 8px !important;
    }

    /* Divider trong sidebar */
    [data-testid="stSidebar"] hr {
        border-color: #293040 !important;
    }

    /* Sidebar heading labels */
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #b4c5ff !important;
        font-size: 0.78rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.08em !important;
        text-transform: uppercase !important;
    }

    /* Sidebar selectbox */
    [data-testid="stSidebar"] .stSelectbox > div > div {
        background-color: #293040 !important;
        border: 1px solid #434655 !important;
        color: #edf0ff !important;
        border-radius: 8px !important;
    }

    /* Sidebar expander header */
    [data-testid="stSidebar"] details > summary {
        background-color: #293040 !important;
        border: 1px solid #434655 !important;
        border-radius: 8px !important;
        color: #edf0ff !important;
        padding: 8px 12px !important;
    }

    /* Sidebar button (Ä‘Äƒng xuáº¥t) */
    [data-testid="stSidebar"] .stButton > button {
        background: #293040 !important;
        border: 1px solid #434655 !important;
        color: #edf0ff !important;
        width: 100%;
        border-radius: 8px !important;
        font-size: 0.85rem !important;
        transition: all 0.2s ease-in-out !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: #ba1a1a !important;
        border-color: #ba1a1a !important;
        color: #ffffff !important;
    }

    /* Khá»‘i ná»™i dung chÃ­nh (Glassmorphism tinh táº¿) */

    .block-container {
        background: #ffffff;
        border-radius: 16px;
        padding: 2.5rem !important;
        margin-top: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05), 0 10px 15px -3px rgba(0,0,0,0.02);
        border: 1px solid #e1e8fd;
    }
    
    /* Cáº¥u trÃºc Header & Typography */
    h1 {
        color: #004ac6 !important; /* Primary color */
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        font-size: 32px !important;
        letter-spacing: -0.02em !important;
        margin-bottom: 0.5rem !important;
    }
    h2 {
        color: #712ae2 !important; /* Secondary color (AI accent) */
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        font-size: 24px !important;
        letter-spacing: -0.01em !important;
    }
    h3 {
        color: #005a82 !important; /* Tertiary color */
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        font-size: 20px !important;
    }
    
    /* CÃ¡c tháº» text vÃ  body â€” KHÃ”NG bao gá»“m span Ä‘á»ƒ trÃ¡nh lá»—i icon Material */
    p, label {
        font-family: 'Inter', sans-serif !important;
        line-height: 1.6 !important;
    }

    /* Custom Streamlit Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #004ac6 0%, #0053db 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.6rem 1.2rem !important;
        font-weight: 600 !important;
        transition: all 0.2s ease-in-out !important;
        box-shadow: 0 4px 6px -1px rgba(0, 74, 198, 0.15) !important;
    }
    .stButton>button:hover {
        transform: scale(0.98) !important; /* Hiá»‡u á»©ng click váº­t lÃ½ */
        background: linear-gradient(135deg, #0053db 0%, #003ea8 100%) !important;
        box-shadow: 0 6px 12px -2px rgba(0, 74, 198, 0.25) !important;
    }
    
    /* Input Fields */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div>div {
        border: 1px solid #c3c6d7 !important;
        border-radius: 8px !important;
        background-color: #ffffff !important;
        color: #141b2b !important;
        transition: all 0.2s ease-in-out !important;
    }
    .stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {
        border-color: #2563eb !important;
        box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.15) !important;
    }

    /* Container Card Forms */
    [data-testid="stForm"] {
        background-color: #ffffff !important;
        border: 1px solid #e1e8fd !important;
        border-radius: 16px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
        padding: 24px !important; /* Strict 8pt spacing grid */
    }
    
    /* Style cho cÃ¡c Tab Äiá»u HÆ°á»›ng */
    .stTabs [role="tablist"],
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.4rem !important;
        flex-wrap: wrap !important;
        overflow: visible !important;
        background-color: #f1f3ff !important;
        padding: 6px !important;
        border-radius: 12px !important;
        border: 1px solid #c3c6d7 !important;
    }
    .stTabs [role="tab"],
    .stTabs [data-baseweb="tab"] {
        height: auto !important;
        min-height: 36px !important;
        white-space: nowrap !important;
        background-color: #ffffff !important;
        border: 1px solid #c3c6d7 !important;
        border-radius: 8px !important;
        padding: 6px 12px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        color: #434655 !important;
        transition: all 0.2s ease-in-out !important;
        margin: 2px !important;
    }
    .stTabs [role="tab"]:hover,
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #e9edff !important;
        color: #141b2b !important;
        border-color: #737686 !important;
    }
    .stTabs [role="tab"][aria-selected="true"],
    .stTabs [aria-selected="true"] {
        color: #ffffff !important;
        background: linear-gradient(135deg, #004ac6 0%, #2563eb 100%) !important;
        border: 1px solid #004ac6 !important;
        box-shadow: 0 4px 6px -1px rgba(0, 74, 198, 0.15) !important;
    }
    .stTabs [data-baseweb="tab-highlight-block"],
    .stTabs [data-testid="stTabHighlight"] {
        display: none !important;
    }
    
    /* DataFrame tables */
    [data-testid="stDataFrame"] {
        border: 1px solid #e1e8fd;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.03);
        background: #ffffff;
    }
</style>


""", unsafe_allow_html=True)

# --- KHá»žI Táº O STATE XÃC THá»°C & JWT ---
from streamlit_cookies_controller import CookieController
cookie_controller = CookieController()

# Äá»c token tá»« cookie náº¿u session_state chÆ°a cÃ³
stored_token = cookie_controller.get('jwt_token')
if stored_token and ('jwt_token' not in st.session_state or not st.session_state['jwt_token']):
    st.session_state['jwt_token'] = stored_token
    payload = decode_jwt(stored_token)
    if payload:
        st.session_state['current_user'] = UserModel.get_by_email(payload["email"])

if 'jwt_token' not in st.session_state:
    st.session_state['jwt_token'] = None
if 'current_user' not in st.session_state:
    st.session_state['current_user'] = None

# Giáº£i mÃ£ token hiá»‡n táº¡i Ä‘á»ƒ xÃ¡c Ä‘á»‹nh phiÃªn Ä‘Äƒng nháº­p
user_payload = None
if st.session_state['jwt_token']:
    user_payload = decode_jwt(st.session_state['jwt_token'])
if not user_payload:
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"], [data-testid="stHeader"] { display: none; }
        .block-container { padding: 0 !important; max-width: 100% !important; }
        .appview-container .main .block-container { padding-top: 0 !important; }
        .login-wrap {
            min-height: 100vh;
            background: #f6f8fc;
            color: #10213f;
        }
        .login-left {
            min-height: 100vh;
            padding: 34px 42px;
            background:
                radial-gradient(circle at 12% 18%, rgba(0, 224, 255, 0.20), transparent 24%),
                radial-gradient(circle at 86% 12%, rgba(255, 199, 0, 0.18), transparent 22%),
                linear-gradient(145deg, #042e7d 0%, #0758d8 45%, #2331b8 100%);
            color: #fff;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        .login-logo {
            display: flex;
            align-items: center;
            gap: 12px;
            font-weight: 900;
            font-size: 23px;
        }
        .login-logo-mark {
            width: 42px;
            height: 42px;
            border-radius: 10px;
            display: grid;
            place-items: center;
            background: rgba(255,255,255,0.14);
            border: 1px solid rgba(255,255,255,0.20);
            font-size: 24px;
        }
        .login-hero h1 {
            margin: 58px 0 16px;
            font-size: clamp(36px, 5vw, 64px);
            line-height: 1.02;
            letter-spacing: 0;
            font-weight: 900;
        }
        .login-hero p {
            max-width: 760px;
            color: rgba(255,255,255,0.84);
            font-size: 17px;
            line-height: 1.7;
        }
        .login-feature-list {
            margin-top: 42px;
            display: grid;
            gap: 16px;
            max-width: 760px;
        }
        .login-feature {
            display: flex;
            gap: 14px;
            align-items: flex-start;
            color: rgba(255,255,255,0.92);
            font-size: 15px;
            line-height: 1.5;
        }
        .login-feature span:first-child {
            width: 38px;
            height: 38px;
            flex: 0 0 38px;
            border-radius: 10px;
            display: grid;
            place-items: center;
            background: rgba(255,255,255,0.16);
            border: 1px solid rgba(255,255,255,0.18);
        }
        .login-badges {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 40px;
        }
        .login-badge {
            padding: 8px 12px;
            border-radius: 999px;
            background: rgba(255,255,255,0.14);
            border: 1px solid rgba(255,255,255,0.16);
            color: rgba(255,255,255,0.94);
            font-size: 12px;
            font-weight: 700;
        }
        .login-footer {
            margin-top: 22px;
            color: rgba(255,255,255,0.62);
            font-size: 12px;
        }
        .login-card {
            padding: clamp(56px, 8vh, 96px) clamp(34px, 7vw, 86px) 10px;
            background: #ffffff;
        }
        .login-card-inner {
            width: min(100%, 760px);
            margin: 0 auto;
        }
        .login-kicker {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 12px;
            border-radius: 999px;
            background: #eef5ff;
            color: #0758d8;
            font-weight: 800;
            font-size: 12px;
            margin-bottom: 18px;
        }
        .login-card h2 {
            font-size: clamp(30px, 4vw, 46px);
            line-height: 1.08;
            margin: 0 0 12px;
            font-weight: 900;
            color: #0f2144;
            letter-spacing: 0;
        }
        .login-card p {
            margin: 0 0 18px;
            color: #647084;
            font-size: 15px;
            line-height: 1.7;
        }
        div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(2) div[data-testid="stRadio"],
        div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(2) div[data-testid="stForm"] {
            width: min(100%, 760px);
            margin-left: auto;
            margin-right: auto;
        }
        div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(2) div[data-testid="stRadio"] {
            margin-top: 8px;
            margin-bottom: 14px;
        }
        div[data-testid="stRadio"] label { font-weight: 700; }
        .stTextInput input, .stSelectbox div[data-baseweb="select"] > div {
            border-radius: 10px !important;
            min-height: 46px;
        }
        .stButton > button {
            min-height: 48px;
            border-radius: 10px;
            border: 0;
            background: linear-gradient(90deg, #0758d8 0%, #00a6d6 100%);
            color: #fff;
            font-weight: 800;
        }
        .stButton > button:hover {
            color: #fff;
            border: 0;
            filter: brightness(0.98);
        }
        @media (max-width: 900px) {
            .login-left { min-height: auto; padding: 28px 24px; }
            .login-card { padding: 30px 24px 8px; }
            .login-hero h1 { margin-top: 34px; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    col_left, col_right = st.columns([0.95, 1.05], gap="small")
    with col_left:
        st.markdown(
            """
            <div class="login-left">
                <div>
                    <div class="login-logo">
                        <div class="login-logo-mark">&#128666;</div>
                        <div class="login-logo-text">Apex AI Logistics</div>
                    </div>
                    <div class="login-hero">
                        <h1>AI Sales &amp; Marketing Growth Platform cho Logistics</h1>
                        <p>Lập kế hoạch nội dung 365 ngày, quản lý lead pipeline, chấm điểm cơ hội bán hàng, tạo campaign funnel và kịch bản chăm sóc khách trên Facebook, LinkedIn, Zalo.</p>
                    </div>
                    <div class="login-feature-list">
                        <div class="login-feature"><span>&#127919;</span><div><b>Logistics Growth Center</b> - Lead pipeline, lead scoring, next best action và sales scripts.</div></div>
                        <div class="login-feature"><span>&#128197;</span><div><b>Content Planning 365</b> - Chủ đề SLA, fulfillment, kho bãi, chi phí vận chuyển, ROI và case study.</div></div>
                        <div class="login-feature"><span>&#9997;</span><div><b>AI Content Studio</b> - Tạo bài Facebook, LinkedIn, Zalo theo đúng Brand Brain và Company Brain.</div></div>
                        <div class="login-feature"><span>&#128200;</span><div><b>Analytics &amp; Learning Loop</b> - Theo dõi hiệu quả nội dung và tối ưu chiến dịch theo dữ liệu.</div></div>
                    </div>
                </div>
                <div>
                    <div class="login-badges">
                        <span class="login-badge">Logistics Ready</span>
                        <span class="login-badge">Sales Pipeline</span>
                        <span class="login-badge">Marketing Automation</span>
                        <span class="login-badge">AI-Powered</span>
                    </div>
                    <div class="login-footer">&copy; 2026 Apex AI Logistics &middot; Powered by Gemini</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_right:
        st.markdown(
            """
            <div class="login-card">
                <div class="login-card-inner">
                    <div class="login-kicker">AI Growth Workspace</div>
                    <h2>Đăng nhập để vận hành tăng trưởng Logistics</h2>
                    <p>Một nơi làm việc tập trung cho team sales và marketing: từ ý tưởng nội dung, lịch đăng, kịch bản tư vấn đến đo lường hiệu quả chiến dịch.</p>
            """,
            unsafe_allow_html=True,
        )
        login_label = "Đăng nhập"
        register_label = "Tạo tài khoản mới"
        auth_mode = st.radio("Chế độ:", [login_label, register_label], horizontal=True, label_visibility="collapsed")
        if auth_mode == login_label:
            with st.form("login_form", clear_on_submit=False):
                email = st.text_input("Email", placeholder="sales@logistics-company.com")
                password = st.text_input("Mật khẩu", type="password", placeholder="********")
                submitted = st.form_submit_button("Vào Growth Platform ->", use_container_width=True)
                if submitted:
                    user = UserModel.authenticate(email, password)
                    if user:
                        token = encode_jwt({"user_id": user["id"], "email": user["email"], "role": user["role"]})
                        st.session_state['jwt_token'] = token
                        st.session_state['current_user'] = user
                        cookie_controller.set('jwt_token', token)
                        log_login(user["id"], email)
                        st.success("Đăng nhập thành công. Đang tải workspace...")
                        st.rerun()
                    else:
                        log_login_failed(email)
                        st.error("Email hoặc mật khẩu chưa đúng.")
        else:
            with st.form("register_form", clear_on_submit=False):
                reg_username = st.text_input("Tên đăng nhập", placeholder="logistics_growth_admin")
                reg_fullname = st.text_input("Họ và tên", placeholder="Nguyễn Văn A")
                reg_email = st.text_input("Email công ty", placeholder="growth@company.com")
                reg_password = st.text_input("Mật khẩu", type="password", placeholder="Tối thiểu 6 ký tự")
                public_user_role = "viewer"
                initial_workspace_role = "owner"
                st.caption("T\u00e0i kho\u1ea3n m\u1edbi s\u1ebd l\u00e0 Owner c\u1ee7a workspace v\u1eeba t\u1ea1o. Quy\u1ec1n Admin/Super Admin ch\u1ec9 \u0111\u01b0\u1ee3c c\u1ea5p trong khu v\u1ef1c qu\u1ea3n tr\u1ecb n\u1ed9i b\u1ed9.")
                submitted_reg = st.form_submit_button("Tạo workspace Logistics ->", use_container_width=True)
                if submitted_reg:
                    try:
                        new_user_id = UserModel.create(
                            reg_email.strip(),
                            reg_username.strip(),
                            reg_password,
                            full_name=reg_fullname.strip(),
                            role=public_user_role,
                        )
                        log_register(new_user_id, reg_email, public_user_role)
                        ws_name = f"Logistics Growth Workspace - {reg_fullname.strip() or reg_username.strip()}"
                        ws_id = WorkspaceModel.create(ws_name, new_user_id, "free")
                        WorkspaceModel.add_member(ws_id, new_user_id, initial_workspace_role)
                        log_create_workspace(new_user_id, reg_email, ws_id, ws_name)
                        st.success("Tao tai khoan thanh cong. Hay dang nhap de bat dau.")
                    except Exception as exc:
                        st.error(f"Không tạo được tài khoản: {exc}")
        st.markdown("</div></div></div>", unsafe_allow_html=True)
    st.stop()

# Load only the shared shell modules up front. Page modules are imported lazily
# after navigation is resolved so switching tabs on Streamlit Cloud does less work.
from importlib import import_module

from ui.nav_config import DEFAULT_NAV, get_nav_groups
from ui.top_navigation_tabs import render_top_navigation_tabs


def _load_view(module_name: str, function_name: str):
    return getattr(import_module(module_name), function_name)


def _clear_content_strategy_session_state() -> None:
    clear_fn = _load_view("ui.tab_content_planning_wizard", "clear_content_strategy_session_state")
    clear_fn()

# --- Náº¾U ÄÃƒ ÄÄ‚NG NHáº¬P THÃ€NH CÃ”NG ---
current_user = st.session_state['current_user']
user_id = current_user["id"]
user_role = normalize_role(user_payload.get("role", "editor"))

# Láº¥y danh sÃ¡ch workspace mÃ  user thuá»™c vá»
workspaces = WorkspaceModel.list_by_user(user_id)

if not workspaces:
    # Náº¿u chÆ°a cÃ³ workspace nÃ o, tá»± Ä‘á»™ng táº¡o 1 cÃ¡i máº·c Ä‘á»‹nh
    default_ws_id = WorkspaceModel.create(name=f"Workspace cá»§a {current_user.get('full_name') or current_user['username']}", owner_id=user_id, plan="free")
    WorkspaceModel.add_member(workspace_id=default_ws_id, user_id=user_id, role="owner")
    workspaces = WorkspaceModel.list_by_user(user_id)

# LÆ°u active workspace trong session state
if 'active_workspace_id' not in st.session_state or st.session_state['active_workspace_id'] not in [w["id"] for w in workspaces]:
    st.session_state['active_workspace_id'] = workspaces[0]["id"]

# Láº¥y role cá»§a thÃ nh viÃªn trong Workspace hiá»‡n táº¡i
active_ws_info = next((w for w in workspaces if w["id"] == st.session_state['active_workspace_id']), workspaces[0])
active_ws_role = normalize_role(active_ws_info.get("member_role", "editor"))

# Quyá»n háº¡n tá»‘i cao náº¿u lÃ  super_admin há»‡ thá»‘ng
if user_role == "super_admin":
    active_ws_role = "admin"

ws_meta  = get_role_display(active_ws_role)
sys_meta = get_role_display(user_role)

# --- SIDEBAR: THONG TIN TAI KHOAN, CHON TENANT/WORKSPACE & SETTINGS ---
st.sidebar.markdown(
    f"""
    <div style='padding: 8px 0 4px;'>
        <div style='font-size:1rem; font-weight:700; color:#edf0ff; letter-spacing:-0.01em;'>👤 {current_user.get('full_name') or current_user['username']}</div>
        <div style='font-size:0.72rem; color:#b4c5ff; margin-top:4px;'>{current_user.get('email','')}</div>
    </div>
    <div style='margin-top:8px; font-size:0.78rem; color:#b4c5ff;'>⏩ Hệ thống: <span style='background:{sys_meta['color']};color:#fff;padding:2px 8px;border-radius:99px;font-weight:600;'>{sys_meta['icon']} {sys_meta['label']}</span></div>
    <div style='margin-top:4px; font-size:0.78rem; color:#b4c5ff;'>⏩ Workspace: <span style='background:{ws_meta['color']};color:#fff;padding:2px 8px;border-radius:99px;font-weight:600;'>{ws_meta['icon']} {ws_meta['label']}</span></div>
    """,
    unsafe_allow_html=True
)
st.sidebar.markdown(render_permissions_table(active_ws_role), unsafe_allow_html=True)
st.sidebar.markdown("---")

# Selector chon Workspace (Multi-Tenant Isolation)
ws_options = {w["id"]: w["name"] for w in workspaces}
selected_ws_id = st.sidebar.selectbox(
    "🏢 Chọn Workspace (Tenant):",
    options=list(ws_options.keys()),
    format_func=lambda x: ws_options[x],
    index=list(ws_options.keys()).index(st.session_state['active_workspace_id'])
)

if selected_ws_id != st.session_state['active_workspace_id']:
    _clear_content_strategy_session_state()
    st.session_state['active_workspace_id'] = selected_ws_id
    st.rerun()

if st.sidebar.button("🔓 Đăng xuất"):
    log_logout(user_id, current_user.get("email", ""))
    st.session_state['jwt_token'] = None
    st.session_state['current_user'] = None
    cookie_controller.remove('jwt_token')
    st.rerun()

st.sidebar.divider()
st.sidebar.header("🔑 Cấu hình API")
can_manage_api_keys = (active_ws_role in MANAGER_ROLES) or (user_role == "super_admin")

if can_manage_api_keys:
    gemini_key = st.sidebar.text_input(
        "Gemini API Key:",
        value=settings.GEMINI_API_KEY,
        type="password",
        help="Chỉ quản trị viên mới thấy và chỉnh sửa khóa API trong phiên làm việc này."
    )
else:
    gemini_key = settings.GEMINI_API_KEY
    if gemini_key:
        st.sidebar.success("Gemini API đã được cấu hình.")
    else:
        st.sidebar.warning("Gemini API chưa được cấu hình. Vui lòng liên hệ quản trị viên.")

with st.sidebar.expander("🌐 Cấu hình Facebook API"):
    fb_page_id = st.text_input("Facebook Page ID", value=settings.FB_PAGE_ID)
    fb_access_token = st.text_input("Facebook Access Token", value=settings.FB_ACCESS_TOKEN, type="password")

with st.sidebar.expander("💬 Cấu hình Zalo OA API"):
    zalo_oa_id = st.text_input("Zalo OA ID", value=settings.ZALO_OA_ID)
    zalo_access_token = st.text_input("Zalo Access Token", value=settings.ZALO_ACCESS_TOKEN, type="password")

with st.sidebar.expander("💼 Cấu hình LinkedIn API"):
    linkedin_author_urn = st.text_input("LinkedIn Author URN (VD: urn:li:person:123...)", value=settings.LINKEDIN_AUTHOR_URN, placeholder="urn:li:person:...")
    linkedin_access_token = st.text_input("LinkedIn Access Token", value=settings.LINKEDIN_ACCESS_TOKEN, type="password")

# Khá»Ÿi táº¡o navigation state
if 'active_nav' not in st.session_state:
    st.session_state['active_nav'] = DEFAULT_NAV

# Äá»‹nh nghÄ©a quyá»n xem Tab Admin
show_admin_tab = (active_ws_role in MANAGER_ROLES) or (user_role == "super_admin")

# Láº¥y nav_groups tá»« nguá»“n dá»¯ liá»‡u dÃ¹ng chung (ui/nav_config.py)
nav_groups = get_nav_groups(show_admin=show_admin_tab)

# --- HEADER TRANG ---
st.markdown(
    f"""
    <div style='display:flex; align-items:center; gap:16px; margin-bottom:8px;'>
        <div>
            <h1 style='margin:0; font-size:2rem; font-weight:700; color:#004ac6; letter-spacing:-0.02em;'>&#128666; Apex AI Logistics</h1>
            <p style='margin:4px 0 0; font-size:0.95rem; color:#434655;'>AI Sales & Marketing Growth Platform for Logistics | Workspace: <b style='color:#004ac6;'>{ws_options[st.session_state['active_workspace_id']]}</b></p>
        </div>
    </div>
    <hr style='border:none; border-top:1px solid #e1e8fd; margin:0 0 0.5rem;'/>
    """,
    unsafe_allow_html=True
)

# --- TOP NAVIGATION TABS (Ä‘áº·t phÃ­a dÆ°á»›i tiÃªu Ä‘á» Apex AI) ---
render_top_navigation_tabs(show_admin=show_admin_tab)
active_page = st.session_state['active_nav']

# TiÃªu Ä‘á» trang hiá»‡n táº¡i
st.markdown(
    f"<h2 style='font-size:1.4rem;font-weight:700;color:#004ac6;margin-bottom:1.5rem;'>{active_page}</h2>",
    unsafe_allow_html=True
)


# --- RENDER Ná»˜I DUNG THEO TRANG ÄANG CHá»ŒN ---
ws_id = st.session_state['active_workspace_id']

if active_page == "🚀 Logistics Growth Center":
    _load_view("ui.tab_logistics_growth", "render_tab_logistics_growth")(gemini_key=gemini_key, workspace_id=ws_id, role=active_ws_role, user_id=user_id)

elif active_page == "🗓️ Content Planning (Wizard)":
    _load_view("ui.tab_content_planning_wizard", "render_tab_content_planning_wizard")(gemini_key, workspace_id=ws_id, role=active_ws_role, user_id=user_id, user_email=current_user.get("email", ""))

elif active_page == "🎨 Content Studio Workspace":
    _load_view("ui.tab_content_studio_workspace", "render_tab_content_studio_workspace")(
        gemini_key, workspace_id=ws_id, user_id=user_id,
        user_email=current_user.get("email", ""), role=active_ws_role
    )

elif active_page == "🧠 Knowledge Center":
    _load_view("ui.tab_knowledge", "render_tab_knowledge")(
        workspace_id=ws_id, user_id=user_id,
        user_email=current_user.get("email", ""), role=active_ws_role
    )

elif active_page == "🏢 Company Brain":
    _load_view("ui.tab_company_brain", "render_tab_company_brain")(
        workspace_id=ws_id, user_id=user_id,
        user_email=current_user.get("email", ""), role=active_ws_role
    )

elif active_page == "🎗️ Brand Identity":
    _load_view("ui.tab_brand", "render_tab_brand")(
        workspace_id=ws_id, user_id=user_id,
        user_email=current_user.get("email", ""), role=active_ws_role
    )

elif active_page == "🔍 Fact Check":
    _load_view("ui.tab_factcheck", "render_tab_factcheck")(gemini_key=gemini_key, workspace_id=ws_id, role=active_ws_role)

elif active_page == "🎨 Thumbnail Studio":
    _load_view("ui.tab_thumbnail_studio", "render_tab_thumbnail_studio")(workspace_id=ws_id, user_id=user_id, user_email=current_user.get("email", ""), role=active_ws_role, api_key=gemini_key)

elif active_page == "📢 Publishing Agent":
    _load_view("ui.tab_publishing", "render_tab_publishing")(
        gemini_key=gemini_key, fb_page_id=fb_page_id, fb_access_token=fb_access_token,
        zalo_access_token=zalo_access_token, linkedin_author_urn=linkedin_author_urn,
        linkedin_access_token=linkedin_access_token, workspace_id=ws_id,
        user_id=user_id, user_email=current_user.get("email", ""), role=active_ws_role
    )

elif active_page == "⛓️ Workflow Engine":
    _load_view("ui.tab_workflow", "render_tab_workflow")(gemini_key=gemini_key, workspace_id=ws_id, role=active_ws_role)

elif active_page == "⚖️ Quy trình phê duyệt":
    _load_view("ui.tab_approval", "render_tab_approval")(gemini_key=gemini_key, workspace_id=ws_id, role=active_ws_role)

elif active_page == "📈 Analytics Agent":
    _load_view("ui.tab_analytics", "render_tab_analytics")(gemini_key=gemini_key, workspace_id=ws_id, role=active_ws_role)

elif active_page == "📊 Thumbnail Analytics":
    _load_view("ui.tab_thumbnail_analytics", "render_tab_thumbnail_analytics")(workspace_id=ws_id, user_id=user_id, user_email=current_user.get("email", ""), role=active_ws_role)

elif active_page == "🧠 Learning Loop":
    _load_view("ui.tab_learning", "render_tab_learning")(gemini_key=gemini_key, workspace_id=ws_id, role=active_ws_role)

elif active_page == "🧪 A/B Testing":
    _load_view("ui.tab_ab_testing", "render_tab_ab_testing")(gemini_key=gemini_key, workspace_id=ws_id, role=active_ws_role)

elif active_page == "💰 AI Cost Center":
    _load_view("ui.tab_ai_cost", "render_tab_ai_cost")(gemini_key=gemini_key, workspace_id=ws_id, role=active_ws_role)

elif active_page == "💳 Billing & Quota":
    _load_view("ui.tab_billing", "render_tab_billing")(gemini_key=gemini_key, workspace_id=ws_id, role=active_ws_role)

elif active_page == "🖥️ System Monitor":
    _load_view("ui.tab_monitoring", "render_tab_monitoring")(gemini_key=gemini_key, workspace_id=ws_id, role=active_ws_role)

elif active_page == "⚙️ Quản lý Workspace" and show_admin_tab:
    st.header("⚙️ Quản lý thành viên & Cài đặt Workspace")
    ws_name_active = ws_options[st.session_state['active_workspace_id']]

    with st.expander("🏢 Tạo Workspace mới", expanded=False):
        with st.form("create_workspace_form"):
            new_ws_name = st.text_input("Tên Workspace mới:")
            btn_create_ws = st.form_submit_button("Tạo Workspace ➕")
            if btn_create_ws and new_ws_name:
                try:
                    new_ws_id = WorkspaceModel.create(name=new_ws_name, owner_id=user_id, plan="free")
                    WorkspaceModel.add_member(workspace_id=new_ws_id, user_id=user_id, role="owner")
                    log_create_workspace(user_id, current_user.get("email",""), new_ws_id, new_ws_name)
                    st.success(f"Đã tạo thành công Workspace '**{new_ws_name}**'!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Lỗi: {e}")

    st.divider()
    st.subheader(f"👥 Thành viên của '{ws_name_active}'")
    members = WorkspaceModel.get_members(st.session_state['active_workspace_id'])

    if members:
        members_data = []
        for m in members:
            rm = get_role_display(m["role"])
            members_data.append({
                "ID":              m["id"],
                "Tên đăng nhập":   m["username"] or "",
                "Họ tên":          m["full_name"] or "",
                "Email":           m["email"],
                "Vai trò":         f"{rm['icon']} {rm['label']}",
                "Ngày gia nhập":  m["joined_at"][:10] if m["joined_at"] else "",
            })
        st.dataframe(members_data, use_container_width=True, hide_index=True)
        st.divider()

        st.subheader("🔄 Cập nhật vai trò thành viên")
        member_options = {m["id"]: f"{m['full_name'] or m['username']} ({m['email']})" for m in members if m["id"] != user_id}
        if member_options:
            with st.form("change_role_form"):
                c1, c2 = st.columns(2)
                selected_member_id = c1.selectbox("Chọn thành viên:", options=list(member_options.keys()), format_func=lambda x: member_options[x])
                new_role = c2.selectbox("Vai trò mới:", options=ALL_ROLES, format_func=lambda r: f"{get_role_display(r)['icon']} {get_role_display(r)['label']}")
                btn_change = st.form_submit_button("🔄 Cập nhật vai trò")
                if btn_change:
                    old_member = next((m for m in members if m["id"] == selected_member_id), {})
                    old_role = old_member.get("role", "")
                    target_email_change = old_member.get("email", "")
                    ok = WorkspaceModel.update_member_role(workspace_id=st.session_state['active_workspace_id'], user_id=selected_member_id, new_role=new_role)
                    if ok:
                        log_change_role(actor_id=user_id, actor_email=current_user.get("email",""), workspace_id=st.session_state['active_workspace_id'], target_email=target_email_change, old_role=old_role, new_role=new_role)
                        st.success("Đã cập nhật vai trò thành công!")
                        st.rerun()
                    else:
                        st.error("Đổi vai trò thất bại.")
        else:
            st.info("Không có thành viên nào khác.")

        st.divider()
        if active_ws_role in {"owner", "ceo", "admin"} or user_role == "super_admin":
            st.subheader("🗑️ Xóa thành viên khỏi Workspace")
            removable = [m for m in members if m["id"] != user_id]
            if removable:
                with st.form("remove_member_form"):
                    removable_opts = {m["id"]: f"{m['full_name'] or m['username']} ({m['email']})" for m in removable}
                    remove_id = st.selectbox("Chọn thành viên cần xóa:", options=list(removable_opts.keys()), format_func=lambda x: removable_opts[x])
                    btn_remove = st.form_submit_button("❌ Xóa khỏi Workspace", type="primary")
                    if btn_remove:
                        removed_member = next((m for m in removable if m["id"] == remove_id), {})
                        removed_email = removed_member.get("email", "")
                        ok = WorkspaceModel.remove_member(workspace_id=st.session_state['active_workspace_id'], user_id=remove_id)
                        if ok:
                            log_remove_member(actor_id=user_id, actor_email=current_user.get("email",""), workspace_id=st.session_state['active_workspace_id'], target_email=removed_email)
                            st.success("Xóa thành viên thành công!")
                            st.rerun()
                        else:
                            st.error("Xóa thất bại.")
            else:
                st.info("Không có thành viên nào khác để xóa.")
    else:
        st.info("⚠️ Workspace này chưa có thành viên.")

    st.divider()
    st.subheader("➕ Thêm thành viên vào Workspace")
    with st.form("add_member_form"):
        target_email = st.text_input("Nhập Email của thành viên mới:")
        target_role = st.selectbox("Vai trò trong Workspace:", options=ALL_ROLES, format_func=lambda r: f"{get_role_display(r)['icon']} {get_role_display(r)['label']}")
        btn_add_member = st.form_submit_button("Thêm thành viên 👤")
        if btn_add_member:
            if not target_email:
                st.error("Vui lòng nhập Email!")
            else:
                target_user = UserModel.get_by_email(target_email)
                if not target_user:
                    st.error("Không tìm thấy người dùng có Email này.")
                else:
                    is_member = any(m["id"] == target_user["id"] for m in (members or []))
                    if is_member:
                        st.warning("Người dùng này đã là thành viên rồi.")
                    else:
                        ok = WorkspaceModel.add_member(workspace_id=st.session_state['active_workspace_id'], user_id=target_user["id"], role=target_role)
                        if ok:
                            rm = get_role_display(target_role)
                            log_add_member(actor_id=user_id, actor_email=current_user.get("email",""), workspace_id=st.session_state['active_workspace_id'], target_email=target_email, role=target_role)
                            st.success(f"Đã thêm **{target_user['full_name'] or target_user['username']}** với vai trò {rm['icon']} **{rm['label']}**!")
                            st.rerun()
                        else:
                            st.error("Có lỗi xảy ra khi thêm thành viên.")
elif active_page == "🗒️ Audit Log" and show_admin_tab:
    _load_view("ui.tab_audit", "render_tab_audit")(workspace_id=ws_id, role=active_ws_role)











