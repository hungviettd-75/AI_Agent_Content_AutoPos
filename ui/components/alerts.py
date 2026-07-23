import streamlit as st
from ui.theme import C, T, R, S, SH

def render_alert(message: str, alert_type: str = "info", icon: str = None):
    """
    Hiển thị hộp thoại Alert tùy chỉnh đẹp đẽ thay thế st.info / st.warning / st.error gốc.
    """
    bg = C.INFO_BG
    border = C.INFO_BORDER
    text_color = C.INFO_TEXT
    default_icon = "ℹ️"

    if alert_type == "success":
        bg = C.SUCCESS_BG
        border = C.SUCCESS_BORDER
        text_color = C.SUCCESS_TEXT
        default_icon = "✅"
    elif alert_type == "warning":
        bg = C.WARNING_BG
        border = C.WARNING_BORDER
        text_color = C.WARNING_TEXT
        default_icon = "⚠️"
    elif alert_type == "danger":
        bg = C.ERROR_BG
        border = C.ERROR_BORDER
        text_color = C.ERROR_TEXT
        default_icon = "🚨"

    icon = icon or default_icon

    html = f"""
    <div style="
        background-color: {bg};
        border: 1px solid {border};
        border-radius: {R.LG};
        padding: {S.SP_4};
        display: flex;
        align-items: flex-start;
        gap: {S.SP_3};
        margin-bottom: {S.SP_4};
        box-shadow: {SH.SM};
    ">
        <span style="font-size: 1.25rem; line-height: 1;">{icon}</span>
        <div style="
            font-size: {T.TEXT_BASE};
            color: {text_color};
            font-family: {T.FONT_PRIMARY};
            line-height: {T.LEADING_NORMAL};
        ">
            {message}
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
