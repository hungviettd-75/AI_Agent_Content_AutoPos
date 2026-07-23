import streamlit as st

st.set_page_config(layout="wide")

st.markdown("""
<style>
.my-test { border: 2px solid red; padding: 10px; }
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='my-test'>", unsafe_allow_html=True)
st.button("Button 1")
st.markdown("</div>", unsafe_allow_html=True)
