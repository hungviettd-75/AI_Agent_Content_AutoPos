import streamlit as st

st.set_page_config(layout="wide")

st.markdown("""
<style>
/* CSS to target ONLY the container with the marker */
div[data-testid="stVerticalBlock"]:has(#apex-topnav-marker) {
    display: flex !important;
    flex-wrap: wrap !important;
    align-items: center !important;
    gap: 8px !important;
    padding: 12px;
    background: #f8fafc;
    border-radius: 8px;
    border: 1px solid #e2e8f0;
}

div[data-testid="stVerticalBlock"]:has(#apex-topnav-marker) > div.element-container {
    width: auto !important;
    display: inline-block !important;
}

/* Group header styling */
.group-header {
    font-size: 11px;
    font-weight: 700;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-right: 4px;
    margin-left: 8px;
}

/* Reset button styling inside topnav */
div[data-testid="stVerticalBlock"]:has(#apex-topnav-marker) div.stButton > button {
    border-radius: 99px !important;
    padding: 4px 12px !important;
    height: 32px !important;
    min-height: 32px !important;
    font-size: 13px !important;
    white-space: nowrap !important;
}
</style>
""", unsafe_allow_html=True)

with st.container():
    st.markdown("<div id='apex-topnav-marker' style='display:none;'></div>", unsafe_allow_html=True)
    
    st.markdown("<span class='group-header'>Group 1</span>", unsafe_allow_html=True)
    st.button("Tab 1")
    st.button("Tab 2")
    st.button("Tab 3")
    
    st.markdown("<span class='group-header'>Group 2</span>", unsafe_allow_html=True)
    st.button("Tab 4")
    st.button("Tab 5")

st.write("This button is outside and should be normal:")
st.button("Normal Button")
