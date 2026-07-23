import streamlit as st
from ui.theme import C, T, R, S

def render_input_field(label: str, value: str = "", placeholder: str = "", type: str = "text", key: str = None) -> str:
    """
    Render input field chuẩn Design System của Streamlit.
    """
    st.markdown(f'<div style="font-size: {T.TEXT_SM}; font-weight: {T.WEIGHT_SEMIBOLD}; color: {C.NEUTRAL_700}; margin-bottom: {S.SP_1};">{label}</div>', unsafe_allow_html=True)
    if type == "password":
        return st.text_input(label, value=value, placeholder=placeholder, type="password", key=key, label_visibility="collapsed")
    elif type == "textarea":
        return st.text_area(label, value=value, placeholder=placeholder, key=key, label_visibility="collapsed")
    else:
        return st.text_input(label, value=value, placeholder=placeholder, key=key, label_visibility="collapsed")
