"""
ui/top_navigation_tabs.py
=========================
Compact grouped top navigation for the Streamlit app.

Navigation uses native Streamlit buttons so selecting a feature updates the
current page inside the app instead of opening a browser tab.
"""

from itertools import zip_longest

import streamlit as st
from ui.theme import C
from ui.nav_config import get_nav_groups, DEFAULT_NAV


_BUTTONS_PER_ROW = 5

_TOPNAV_CSS = f"""
<style>
.apex-topnav-marker {{
    display: none;
}}
.apex-topnav-group-label {{
    display: flex;
    align-items: center;
    min-height: 33px;
    padding: 0 8px;
    color: #334155;
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 0.025em;
    line-height: 1.15;
    text-transform: uppercase;
    white-space: nowrap;
}}
.apex-topnav-group-spacer {{
    height: 5px;
    border-top: 1px solid #edf2fb;
    margin-top: 2px;
}}
div[data-testid="stVerticalBlock"]:has(.apex-topnav-marker) div[data-testid="column"] {{
    min-width: 0 !important;
}}
div[data-testid="stVerticalBlock"]:has(.apex-topnav-marker) div.stButton > button {{
    min-height: 31px !important;
    height: 31px !important;
    padding: 4px 10px !important;
    border-radius: 999px !important;
    font-size: 12px !important;
    font-weight: 650 !important;
    line-height: 1.12 !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}}
div[data-testid="stVerticalBlock"]:has(.apex-topnav-marker) div.stButton > button[data-testid="baseButton-secondary"],
div[data-testid="stVerticalBlock"]:has(.apex-topnav-marker) div.stButton > button[kind="secondary"] {{
    background: #ffffff !important;
    border: 1px solid #cbd5e1 !important;
    color: #263246 !important;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04) !important;
}}
div[data-testid="stVerticalBlock"]:has(.apex-topnav-marker) div.stButton > button[data-testid="baseButton-secondary"]:hover,
div[data-testid="stVerticalBlock"]:has(.apex-topnav-marker) div.stButton > button[kind="secondary"]:hover {{
    background: #f1f5f9 !important;
    border-color: #94a3b8 !important;
    color: #0f172a !important;
    transform: translateY(-1px) !important;
}}
div[data-testid="stVerticalBlock"]:has(.apex-topnav-marker) div.stButton > button[data-testid="baseButton-primary"],
div[data-testid="stVerticalBlock"]:has(.apex-topnav-marker) div.stButton > button[kind="primary"] {{
    background: linear-gradient(135deg, {C.PRIMARY} 0%, {C.PRIMARY_600} 100%) !important;
    border: 1px solid {C.PRIMARY} !important;
    color: #ffffff !important;
    box-shadow: 0 3px 7px rgba(0, 74, 198, 0.22) !important;
}}
</style>
"""


def _inject_css() -> None:
    # Browser refresh clears injected CSS while Streamlit session_state can remain alive.
    # Inject on every render so the top navigation always overrides global button styles.
    st.markdown(_TOPNAV_CSS, unsafe_allow_html=True)


def _button_key(tab_name: str) -> str:
    safe = "".join(ch if ch.isalnum() else "_" for ch in tab_name)
    return f"topnav_{safe}"


def _chunks(items: list[str], size: int) -> list[list[str]]:
    return [items[i:i + size] for i in range(0, len(items), size)]


def _render_button_grid(group_name: str, tab_items: list[str], active_nav: str) -> bool:
    tab_changed = False
    chunks = _chunks(tab_items, _BUTTONS_PER_ROW)

    for row_index, row_items in enumerate(chunks):
        cols = st.columns([1.28, 1, 1, 1, 1, 1], gap="small")

        with cols[0]:
            if row_index == 0:
                st.markdown(
                    f"<div class='apex-topnav-group-label'>{group_name}</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown("<div class='apex-topnav-group-label'>&nbsp;</div>", unsafe_allow_html=True)

        for col, tab_name in zip_longest(cols[1:], row_items):
            with col:
                if tab_name is None:
                    st.empty()
                    continue

                is_active = active_nav == tab_name
                clicked = st.button(
                    tab_name,
                    key=_button_key(tab_name),
                    type="primary" if is_active else "secondary",
                    use_container_width=True,
                )
                if clicked and not is_active:
                    st.session_state["active_nav"] = tab_name
                    tab_changed = True

    return tab_changed


def render_top_navigation_tabs(show_admin: bool = False) -> bool:
    """Render compact horizontal grouped navigation using Streamlit buttons."""
    if "active_nav" not in st.session_state:
        st.session_state["active_nav"] = DEFAULT_NAV

    _inject_css()

    nav_groups = get_nav_groups(show_admin=show_admin)
    valid_tabs = {tab for tabs in nav_groups.values() for tab in tabs}
    if st.session_state["active_nav"] not in valid_tabs:
        st.session_state["active_nav"] = DEFAULT_NAV

    tab_changed = False
    active_nav = st.session_state["active_nav"]

    with st.container(border=True):
        st.markdown("<div class='apex-topnav-marker'></div>", unsafe_allow_html=True)
        for group_index, (group_name, tab_items) in enumerate(nav_groups.items()):
            if group_index > 0:
                st.markdown("<div class='apex-topnav-group-spacer'></div>", unsafe_allow_html=True)
            tab_changed = _render_button_grid(group_name, tab_items, active_nav) or tab_changed

    if tab_changed:
        st.rerun()

    return tab_changed


def get_current_tab() -> str:
    """Return the current active tab from session_state."""
    return st.session_state.get("active_nav", DEFAULT_NAV)


