import streamlit as st
from ui.theme import C, T, S, R, SH, A

def render_header(
    active_workspace_name: str,
    active_page_name: str,
    notifications_count: int = 0
) -> str:
    """
    Render Header cho giao diện Apex AI.
    Bao gồm Search Bar, Notification center, Workspace Switcher info, và breadcrumb root.
    """
    # Header styling (Light Theme content container, Dark Header top)
    header_html = f"""
    <div style="
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: {S.SP_3} {S.SP_5};
        background: {C.WHITE};
        border-bottom: 1px solid {C.NEUTRAL_200};
        border-radius: {R.LG};
        box-shadow: {SH.SM};
        margin-bottom: {S.SP_4};
    ">
        <!-- Trái: Breadcrumb info -->
        <div style="display: flex; align-items: center; gap: {S.SP_2};">
            <span style="font-size: {T.TEXT_SM}; color: {C.NEUTRAL_500};">Workspace:</span>
            <span style="font-size: {T.TEXT_SM}; font-weight: {T.WEIGHT_BOLD}; color: {C.PRIMARY}; background-color: {C.PRIMARY_50}; padding: 2px 8px; border-radius: {R.SM};">{active_workspace_name}</span>
            <span style="font-size: {T.TEXT_SM}; color: {C.NEUTRAL_300};">/</span>
            <span style="font-size: {T.TEXT_SM}; color: {C.NEUTRAL_700}; font-weight: {T.WEIGHT_SEMIBOLD};">{active_page_name}</span>
        </div>

        <!-- Phải: Search, Notification, Profile -->
        <div style="display: flex; align-items: center; gap: {S.SP_4};">
            <!-- Search field giả lập dạng nút nhấp -->
            <div style="
                display: flex;
                align-items: center;
                gap: {S.SP_2};
                background-color: {C.NEUTRAL_50};
                border: 1px solid {C.NEUTRAL_300};
                border-radius: {R.MD};
                padding: 4px 12px;
                font-size: {T.TEXT_SM};
                color: {C.NEUTRAL_500};
                cursor: pointer;
            ">
                <span>🔍 Search prompt, posts...</span>
            </div>

            <!-- Bell notification badge -->
            <div style="position: relative; cursor: pointer; font-size: 1.25rem;">
                🔔
                {f'<span style="position: absolute; top: -5px; right: -5px; background-color: {C.ERROR}; color: white; border-radius: 50%; font-size: 10px; padding: 2px 5px; font-weight: bold; line-height: 1;">{notifications_count}</span>' if notifications_count > 0 else ""}
            </div>
        </div>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)
