import streamlit as st
from ui.theme import C, T, S, R, SH, A

def render_sidebar(
    current_user: dict,
    workspaces: list,
    active_workspace_id: int,
    nav_groups: dict,
    active_nav: str,
    collapsed: bool = False
) -> tuple:
    """
    Render Sidebar với cấu trúc tùy biến nâng cao: hỗ trợ Collapse/Expand,
    Workspace Switcher, User Profile, Quick Action, và thiết kế Dark Sidebar.
    
    Trả về một tuple: (new_active_nav, force_rerun_flag, toggle_collapse_flag)
    """
    selected_nav = active_nav
    rerun = False
    toggle_collapse = False
    
    # ── Sidebar Dark Theme Variables ──
    sb_bg = C.NEUTRAL_900
    text_primary = C.WHITE
    text_muted = C.NEUTRAL_400
    hover_bg = "rgba(255,255,255,0.08)"
    active_bg = f"linear-gradient(135deg, {C.PRIMARY} 0%, {C.PRIMARY_600} 100%)"
    border_color = C.NEUTRAL_800
    
    # Sử dụng cột rộng/hẹp tùy thuộc vào trạng thái collapse
    sidebar_width = "72px" if collapsed else "260px"
    
    # Nhúng CSS tùy chỉnh cho Sidebar cấu trúc động
    sidebar_css = f"""
    <style>
        [data-testid="stSidebar"] {{
            min-width: {sidebar_width} !important;
            max-width: {sidebar_width} !important;
            background-color: {sb_bg} !important;
            border-right: 1px solid {border_color} !important;
            transition: width 0.3s ease !important;
        }}
        .sb-container {{
            display: flex;
            flex-direction: column;
            height: 100vh;
            color: {text_primary};
            font-family: {T.FONT_PRIMARY};
        }}
        .sb-header {{
            padding: {S.SP_4};
            border-bottom: 1px solid {border_color};
            display: flex;
            align-items: center;
            justify-content: {"center" if collapsed else "space-between"};
        }}
        .sb-logo-text {{
            font-weight: {T.WEIGHT_BOLD};
            font-size: {T.TEXT_XL};
            letter-spacing: {T.TRACKING_TIGHT};
            color: {C.PRIMARY_300};
            display: {"none" if collapsed else "block"};
        }}
        .sb-nav-group-title {{
            font-size: {T.TEXT_XS};
            font-weight: {T.WEIGHT_BOLD};
            color: {text_muted};
            text-transform: uppercase;
            letter-spacing: {T.TRACKING_WIDER};
            padding: {S.SP_4} {S.SP_4} {S.SP_1};
            display: {"none" if collapsed else "block"};
        }}
        .sb-profile {{
            padding: {S.SP_4};
            border-top: 1px solid {border_color};
            background-color: {C.NEUTRAL_950};
            display: flex;
            align-items: center;
            gap: {S.SP_3};
        }}
        .sb-profile-avatar {{
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background-color: {C.PRIMARY};
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: {T.WEIGHT_BOLD};
        }}
        .sb-profile-info {{
            display: {"none" if collapsed else "block"};
        }}
        .sb-profile-name {{
            font-size: {T.TEXT_SM};
            font-weight: {T.WEIGHT_SEMIBOLD};
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .sb-profile-role {{
            font-size: {T.TEXT_XS};
            color: {text_muted};
        }}
    </style>
    """
    st.sidebar.markdown(sidebar_css, unsafe_allow_html=True)
    
    # ── 1. Sidebar Header (Logo + Toggle button) ──
    header_cols = st.sidebar.columns([3, 1]) if not collapsed else st.sidebar.columns([1])
    with header_cols[0]:
        if collapsed:
            st.markdown("<div style='text-align: center; font-size: 1.5rem;'>⚡</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='sb-logo-text'>⚡ Apex AI</div>", unsafe_allow_html=True)
            
    if not collapsed:
        with header_cols[1]:
            if st.button("◀", key="sb_btn_collapse", help="Thu gọn sidebar"):
                toggle_collapse = True
    else:
        if st.sidebar.button("▶", key="sb_btn_expand", help="Mở rộng sidebar"):
            toggle_collapse = True

    # ── 2. Workspace Switcher ──
    if not collapsed:
        st.sidebar.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        ws_options = {w["id"]: w["name"] for w in workspaces}
        selected_ws_id = st.sidebar.selectbox(
            "🏢 Workspace Switcher",
            options=list(ws_options.keys()),
            format_func=lambda x: ws_options[x],
            index=list(ws_options.keys()).index(active_workspace_id) if active_workspace_id in ws_options else 0,
            key="sb_ws_switcher"
        )
        if selected_ws_id != active_workspace_id:
            st.session_state['active_workspace_id'] = selected_ws_id
            st.rerun()

    # ── 3. Navigation Links ──
    for group_name, items in nav_groups.items():
        st.sidebar.markdown(f"<div class='sb-nav-group-title'>{group_name}</div>", unsafe_allow_html=True)
        for item in items:
            is_active = active_nav == item
            btn_key = f"sb_nav_btn_{item.replace(' ', '_')}"
            
            # Custom button markup
            if is_active:
                st.sidebar.markdown(
                    f"""<div style='background: {active_bg}; border-radius: {R.MD}; padding: 1px;'>""", 
                    unsafe_allow_html=True
                )
            else:
                st.sidebar.markdown("<div>", unsafe_allow_html=True)
                
            btn_label = item if not collapsed else item[0] # chỉ lấy ký tự đầu/icon nếu collapsed
            if st.sidebar.button(btn_label, key=btn_key, use_container_width=True):
                selected_nav = item
                rerun = True
                
            st.markdown("</div>", unsafe_allow_html=True)

    # ── 4. Quick Actions ──
    if not collapsed:
        st.sidebar.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        st.sidebar.markdown("<div class='sb-nav-group-title'>Quick Action</div>", unsafe_allow_html=True)
        col_qa1, col_qa2 = st.sidebar.columns(2)
        with col_qa1:
            if st.button("📝 Đăng nhanh", key="sb_qa_post", use_container_width=True):
                selected_nav = "📝 Tạo & Đăng Bài"
                st.rerun()
        with col_qa2:
            if st.button("🔥 Trend", key="sb_qa_trend", use_container_width=True):
                selected_nav = "🔥 Trend Agent"
                st.rerun()

    # ── 5. User Profile Footer ──
    profile_html = f"""
    <div class="sb-profile">
        <div class="sb-profile-avatar">
            {current_user.get('username', 'U')[0].upper()}
        </div>
        <div class="sb-profile-info">
            <div class="sb-profile-name">{current_user.get('full_name') or current_user.get('username')}</div>
            <div class="sb-profile-role">{current_user.get('role', 'editor').upper()}</div>
        </div>
    </div>
    """
    st.sidebar.markdown(profile_html, unsafe_allow_html=True)
    
    return selected_nav, rerun, toggle_collapse
