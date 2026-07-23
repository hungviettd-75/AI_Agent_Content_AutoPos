import streamlit as st
from ui.theme import C, T, R, S, SH, A

def render_card(title: str, content_html: str, subtitle: str = None, footer_html: str = None):
    """
    Render một Container Card dạng premium chuẩn Apex AI với glassmorphic layout.
    """
    sub_markup = f'<div style="font-size: {T.TEXT_SM}; color: {C.NEUTRAL_500}; margin-top: {S.SP_1};">{subtitle}</div>' if subtitle else ""
    footer_markup = f'<div style="margin-top: {S.SP_4}; padding-top: {S.SP_3}; border-top: 1px solid {C.NEUTRAL_200}; font-size: {T.TEXT_XS}; color: {C.NEUTRAL_500};">{footer_html}</div>' if footer_html else ""
    
    html = f"""
    <div style="
        background: {C.BG_CARD};
        border: 1px solid {C.NEUTRAL_200};
        border-radius: {R.LG};
        padding: {S.SP_5};
        box-shadow: {SH.CARD};
        transition: {A.BASE};
        margin-bottom: {S.SP_4};
    ">
        <div style="margin-bottom: {S.SP_3};">
            <div style="font-size: {T.TEXT_LG}; font-weight: {T.WEIGHT_SEMIBOLD}; color: {C.PRIMARY_900};">{title}</div>
            {sub_markup}
        </div>
        <div style="font-size: {T.TEXT_BASE}; color: {C.NEUTRAL_800}; line-height: {T.LEADING_NORMAL};">
            {content_html}
        </div>
        {footer_markup}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_kpi_card(label: str, value: str, icon: str, delta_pct: float = None, trend_up: bool = True):
    """
    Vẽ thẻ KPI Card chuyên nghiệp có hiển thị xu hướng phần trăm (delta) và hover micro-animations.
    """
    delta_markup = ""
    if delta_pct is not None:
        color = C.SUCCESS if trend_up else C.ERROR
        arrow = "▲" if trend_up else "▼"
        delta_markup = f"""
        <div style="font-size: {T.TEXT_XS}; font-weight: {T.WEIGHT_BOLD}; color: {color}; margin-top: {S.SP_2};">
            {arrow} {abs(delta_pct):.1f}% <span style="color: {C.NEUTRAL_500}; font-weight: {T.WEIGHT_REGULAR};">so với trước</span>
        </div>
        """

    html = f"""
    <div style="
        background: {C.BG_CARD};
        border: 1px solid {C.NEUTRAL_200};
        border-radius: {R.XL};
        padding: {S.SP_4} {S.SP_5};
        box-shadow: {SH.SM};
        position: relative;
        overflow: hidden;
        margin-bottom: {S.SP_3};
        transition: {A.BASE};
        border-top: 4px solid {C.PRIMARY};
    ">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: {S.SP_2};">
            <span style="font-size: {T.TEXT_XS}; font-weight: {T.WEIGHT_SEMIBOLD}; color: {C.NEUTRAL_500}; text-transform: uppercase; letter-spacing: {T.TRACKING_WIDE};">{label}</span>
            <span style="font-size: 1.5rem;">{icon}</span>
        </div>
        <div style="font-size: {T.TEXT_4XL}; font-weight: {T.WEIGHT_EXTRABOLD}; color: {C.NEUTRAL_900}; line-height: 1;">{value}</div>
        {delta_markup}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
