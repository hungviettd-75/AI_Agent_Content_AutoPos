import streamlit as st
from ui.theme import C, T, R, S, SH

def render_empty_state(title: str, message: str, icon: str = "📥"):
    """
    Render giao diện trạng thái trống (Empty State) khi chưa có dữ liệu.
    """
    html = f"""
    <div style="
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: {S.SP_12} {S.SP_6};
        background: {C.WHITE};
        border: 2px dashed {C.NEUTRAL_300};
        border-radius: {R.XL};
        margin: {S.SP_6} 0;
    ">
        <div style="font-size: 3rem; margin-bottom: {S.SP_4};">{icon}</div>
        <div style="font-size: {T.TEXT_XL}; font-weight: {T.WEIGHT_SEMIBOLD}; color: {C.NEUTRAL_800}; margin-bottom: {S.SP_2};">{title}</div>
        <div style="font-size: {T.TEXT_SM}; color: {C.NEUTRAL_500}; max-width: 400px; line-height: {T.LEADING_NORMAL};">{message}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
