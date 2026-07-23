import streamlit as st

st.set_page_config(layout="wide")

st.button("Primary Button", type="primary")
st.button("Secondary Button", type="secondary")

st.markdown("""
<script>
const btns = document.querySelectorAll('button');
let out = "";
btns.forEach(b => {
    out += b.outerHTML + "\\n";
});
console.log(out);
</script>
""", unsafe_allow_html=True)
