import streamlit as st
from ui.theme import C, T, R, S, SH

def render_loading(text: str = "Đang xử lý..."):
    """
    Vẽ Spinner với thiết kế premium.
    """
    html = f"""
    <div style="display: flex; align-items: center; gap: {S.SP_3}; padding: {S.SP_4};">
        <div class="custom-spinner"></div>
        <span style="font-size: {T.TEXT_BASE}; font-weight: {T.WEIGHT_MEDIUM}; color: {C.NEUTRAL_600};">{text}</span>
    </div>
    <style>
        .custom-spinner {{
            width: 24px;
            height: 24px;
            border: 3px solid {C.NEUTRAL_200};
            border-top: 3px solid {C.PRIMARY};
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }}
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
    </style>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_skeleton(height: str = "20px", width: str = "100%", border_radius: str = R.MD):
    """
    Vẽ Skeleton loading animation cho UI placeholders.
    """
    html = f"""
    <div style="
        height: {height};
        width: {width};
        border-radius: {border_radius};
        background: linear-gradient(90deg, {C.NEUTRAL_100} 25%, {C.NEUTRAL_200} 50%, {C.NEUTRAL_100} 75%);
        background-size: 200% 100%;
        animation: loading-skeleton 1.5s infinite;
        margin-bottom: {S.SP_2};
    "></div>
    <style>
        @keyframes loading-skeleton {{
            0% {{ background-position: 200% 0; }}
            100% {{ background-position: -200% 0; }}
        }}
    </style>
    """
    st.markdown(html, unsafe_allow_html=True)
