import streamlit as st
from ui.theme import C, T, S, R

def render_footer():
    """
    Render chân trang (Footer) cho ứng dụng Apex AI.
    """
    html = f"""
    <div style="
        margin-top: {S.SP_8};
        padding: {S.SP_4} 0;
        border-top: 1px solid {C.NEUTRAL_200};
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-family: {T.FONT_PRIMARY};
        font-size: {T.TEXT_XS};
        color: {C.NEUTRAL_500};
    ">
        <div>
            © 2026 Apex AI — Marketing Intelligence Platform. All rights reserved.
        </div>
        <div style="display: flex; gap: {S.SP_4};">
            <span style="cursor: pointer;">Tài liệu hướng dẫn</span>
            <span style="cursor: pointer;">Điều khoản dịch vụ</span>
            <span style="cursor: pointer;">Hỗ trợ khách hàng</span>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
