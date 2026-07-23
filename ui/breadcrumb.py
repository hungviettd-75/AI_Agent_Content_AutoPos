import streamlit as st
from ui.theme import C, T, S, R

def render_breadcrumb(path_steps: list):
    """
    Hiển thị đường dẫn Breadcrumb điều hướng trong phần Main Content.
    path_steps: list of dict, ví dụ: [{'name': 'Home', 'url': '#'}, {'name': 'Analytics', 'active': True}]
    """
    steps_html = []
    for i, step in enumerate(path_steps):
        is_last = (i == len(path_steps) - 1)
        if is_last:
            steps_html.append(f"""
            <span style="
                font-size: {T.TEXT_SM};
                font-weight: {T.WEIGHT_SEMIBOLD};
                color: {C.NEUTRAL_900};
            ">{step.get('name')}</span>
            """)
        else:
            steps_html.append(f"""
            <span style="
                font-size: {T.TEXT_SM};
                color: {C.NEUTRAL_500};
                cursor: pointer;
            ">{step.get('name')}</span>
            <span style="font-size: {T.TEXT_SM}; color: {C.NEUTRAL_300}; margin: 0 6px;">/</span>
            """)

    html = f"""
    <div style="
        display: flex;
        align-items: center;
        padding: {S.SP_2} 0;
        margin-bottom: {S.SP_3};
        font-family: {T.FONT_PRIMARY};
    ">
        {"".join(steps_html)}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
