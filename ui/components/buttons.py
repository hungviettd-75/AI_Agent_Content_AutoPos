import streamlit as st
from ui.theme import C, T, R, SH, A

def render_button(label: str, action_type: str = "primary", key: str = None, use_container_width: bool = False) -> bool:
    """
    Render một nút bấm với các style tùy chỉnh: primary, secondary, danger, success.
    Sử dụng raw HTML/CSS và Streamlit st.button để bắt sự kiện.
    """
    btn_id = f"custom_btn_{key or label.replace(' ', '_')}"
    
    # CSS Custom cho từng loại nút
    bg = C.PRIMARY
    hover_bg = C.PRIMARY_600
    shadow = SH.PRIMARY_SM
    text_color = C.WHITE
    border = "none"

    if action_type == "secondary":
        bg = C.WHITE
        hover_bg = C.NEUTRAL_100
        text_color = C.NEUTRAL_800
        border = f"1px solid {C.NEUTRAL_300}"
        shadow = SH.SM
    elif action_type == "danger":
        bg = C.ERROR
        hover_bg = C.ERROR_TEXT
        shadow = SH.ERROR_SM
    elif action_type == "success":
        bg = C.SUCCESS
        hover_bg = C.SUCCESS_TEXT
        shadow = SH.SUCCESS_SM

    css = f"""
    <style>
        div.stButton > button#{btn_id} {{
            background: {bg} !important;
            color: {text_color} !important;
            border: {border} !important;
            border-radius: {R.MD} !important;
            padding: 0.6rem 1.4rem !important;
            font-family: {T.FONT_PRIMARY} !important;
            font-weight: {T.WEIGHT_SEMIBOLD} !important;
            font-size: {T.TEXT_BASE} !important;
            box-shadow: {shadow} !important;
            transition: {A.FAST} !important;
            cursor: pointer !important;
        }}
        div.stButton > button#{btn_id}:hover {{
            background: {hover_bg} !important;
            transform: translateY(-1px) !important;
            box-shadow: {SH.MD} !important;
        }}
        div.stButton > button#{btn_id}:active {{
            transform: translateY(1px) !important;
        }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
    return st.button(label, key=btn_id, use_container_width=use_container_width)
