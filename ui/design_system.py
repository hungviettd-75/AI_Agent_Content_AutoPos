import streamlit as st
from ui.theme import C, T, S, R, SH, A

class DesignSystem:
    @staticmethod
    def get_global_css() -> str:
        """
        Trả về chuỗi CSS toàn cục để nhúng vào Streamlit thông qua st.markdown(css, unsafe_allow_html=True)
        Bao gồm các cấu hình cơ bản cho App, Sidebar, Input, Tab, và Table.
        """
        css = f"""
        <style>
            {T.FONT_IMPORT}

            /* ============================================================
               1. CANVASES & FONTS
               ============================================================ */
            html, body, [class*="css"], .stApp {{
                font-family: {T.FONT_PRIMARY} !important;
                background-color: {C.BG_APP} !important;
                color: {C.NEUTRAL_900} !important;
            }}

            /* ============================================================
               2. SIDEBAR - Dark slate anchor
               ============================================================ */
            [data-testid="stSidebar"] {{
                background-color: {C.BG_SIDEBAR} !important;
                border-right: 1px solid {C.NEUTRAL_700} !important;
            }}
            [data-testid="stSidebar"] .stMarkdown p,
            [data-testid="stSidebar"] .stMarkdown li,
            [data-testid="stSidebar"] label {{
                color: {C.NEUTRAL_100} !important;
                font-family: {T.FONT_PRIMARY} !important;
            }}
            [data-testid="stSidebar"] hr {{
                border-color: {C.NEUTRAL_700} !important;
            }}
            [data-testid="stSidebar"] h2,
            [data-testid="stSidebar"] h3 {{
                color: {C.PRIMARY_200} !important;
                font-size: {T.TEXT_SM} !important;
                font-weight: {T.WEIGHT_SEMIBOLD} !important;
                letter-spacing: {T.TRACKING_WIDER} !important;
                text-transform: uppercase !important;
            }}

            /* Input trong sidebar */
            [data-testid="stSidebar"] input {{
                background-color: {C.NEUTRAL_700} !important;
                color: {C.NEUTRAL_100} !important;
                border: 1px solid {C.NEUTRAL_600} !important;
                border-radius: {R.MD} !important;
            }}
            [data-testid="stSidebar"] .stSelectbox > div > div {{
                background-color: {C.NEUTRAL_700} !important;
                border: 1px solid {C.NEUTRAL_600} !important;
                color: {C.NEUTRAL_100} !important;
                border-radius: {R.MD} !important;
            }}
            [data-testid="stSidebar"] details > summary {{
                background-color: {C.NEUTRAL_700} !important;
                border: 1px solid {C.NEUTRAL_600} !important;
                border-radius: {R.MD} !important;
                color: {C.NEUTRAL_100} !important;
                padding: 8px 12px !important;
            }}

            /* Nút logout sidebar */
            [data-testid="stSidebar"] .stButton > button {{
                background: {C.NEUTRAL_700} !important;
                border: 1px solid {C.NEUTRAL_600} !important;
                color: {C.NEUTRAL_100} !important;
                width: 100% !important;
                border-radius: {R.MD} !important;
                font-size: {T.TEXT_SM} !important;
                transition: {A.FAST} !important;
            }}
            [data-testid="stSidebar"] .stButton > button:hover {{
                background: {C.ERROR} !important;
                border-color: {C.ERROR} !important;
                color: {C.WHITE} !important;
            }}

            /* ============================================================
               3. BLOCK CONTAINER (MAIN CONTENT CANVAS)
               ============================================================ */
            .block-container {{
                background: {C.BG_CARD};
                border-radius: {R.XL};
                padding: 2.5rem !important;
                margin-top: 1.5rem;
                margin-bottom: 1.5rem;
                box-shadow: {SH.CARD};
                border: 1px solid {C.NEUTRAL_200};
            }}

            /* Typography */
            h1 {{
                color: {C.PRIMARY} !important;
                font-family: {T.FONT_PRIMARY} !important;
                font-weight: {T.WEIGHT_SEMIBOLD} !important;
                font-size: {T.TEXT_6XL} !important;
                letter-spacing: {T.TRACKING_TIGHT} !important;
                margin-bottom: 0.5rem !important;
            }}
            h2 {{
                color: {C.SECONDARY} !important;
                font-family: {T.FONT_PRIMARY} !important;
                font-weight: {T.WEIGHT_SEMIBOLD} !important;
                font-size: {T.TEXT_2XL} !important;
                letter-spacing: {T.TRACKING_NORMAL} !important;
            }}
            h3 {{
                color: {C.PRIMARY_900} !important;
                font-family: {T.FONT_PRIMARY} !important;
                font-weight: {T.WEIGHT_SEMIBOLD} !important;
                font-size: {T.TEXT_XL} !important;
            }}
            p, label {{
                font-family: {T.FONT_PRIMARY} !important;
                line-height: {T.LEADING_RELAXED} !important;
            }}

            /* ============================================================
               4. INPUTS, TEXTAREAS & SELECTBOXES
               ============================================================ */
            .stTextInput>div>div>input, 
            .stTextArea>div>div>textarea, 
            .stSelectbox>div>div>div {{
                border: 1px solid {C.NEUTRAL_300} !important;
                border-radius: {R.MD} !important;
                background-color: {C.WHITE} !important;
                color: {C.NEUTRAL_900} !important;
                transition: {A.FAST} !important;
            }}
            .stTextInput>div>div>input:focus, 
            .stTextArea>div>div>textarea:focus {{
                border-color: {C.PRIMARY_500} !important;
                box-shadow: 0 0 0 2px rgba(26, 103, 245, 0.15) !important;
            }}

            /* Container Form Card */
            [data-testid="stForm"] {{
                background-color: {C.BG_FORM} !important;
                border: 1px solid {C.NEUTRAL_200} !important;
                border-radius: {R.XL} !important;
                box-shadow: {SH.CARD} !important;
                padding: {S.SP_6} !important;
            }}

            /* ============================================================
               5. TAB NAVIGATION
               ============================================================ */
            .stTabs [role="tablist"],
            .stTabs [data-baseweb="tab-list"] {{
                gap: 0.4rem !important;
                flex-wrap: wrap !important;
                overflow: visible !important;
                background-color: {C.NEUTRAL_50} !important;
                padding: 6px !important;
                border-radius: {R.LG} !important;
                border: 1px solid {C.NEUTRAL_300} !important;
            }}
            .stTabs [role="tab"],
            .stTabs [data-baseweb="tab"] {{
                height: auto !important;
                min-height: 36px !important;
                white-space: nowrap !important;
                background-color: {C.WHITE} !important;
                border: 1px solid {C.NEUTRAL_300} !important;
                border-radius: {R.MD} !important;
                padding: 6px 12px !important;
                font-weight: {T.WEIGHT_SEMIBOLD} !important;
                font-size: 14px !important;
                color: {C.NEUTRAL_600} !important;
                transition: {A.FAST} !important;
                margin: 2px !important;
            }}
            .stTabs [role="tab"]:hover,
            .stTabs [data-baseweb="tab"]:hover {{
                background-color: {C.PRIMARY_50} !important;
                color: {C.NEUTRAL_900} !important;
                border-color: {C.NEUTRAL_400} !important;
            }}
            .stTabs [role="tab"][aria-selected="true"],
            .stTabs [aria-selected="true"] {{
                color: {C.WHITE} !important;
                background: linear-gradient(135deg, {C.PRIMARY} 0%, {C.PRIMARY_600} 100%) !important;
                border: 1px solid {C.PRIMARY} !important;
                box-shadow: {SH.PRIMARY_SM} !important;
            }}
            .stTabs [data-baseweb="tab-highlight-block"],
            .stTabs [data-testid="stTabHighlight"] {{
                display: none !important;
            }}

            /* ============================================================
               6. DATAFRAME / TABLES
               ============================================================ */
            [data-testid="stDataFrame"] {{
                border: 1px solid {C.NEUTRAL_200};
                border-radius: {R.LG};
                overflow: hidden;
                box-shadow: {SH.XS};
                background: {C.WHITE};
            }}
        </style>
        """
        return css

    @staticmethod
    def inject_styles():
        """
        Nhúng CSS toàn cục trực tiếp vào giao diện Streamlit hiện tại.
        """
        st.markdown(DesignSystem.get_global_css(), unsafe_allow_html=True)
