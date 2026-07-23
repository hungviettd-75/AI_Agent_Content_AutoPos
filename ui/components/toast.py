import streamlit as st

def show_toast(message: str, type: str = "default"):
    """
    Sử dụng helper toast của Streamlit kết hợp với icon Design System.
    """
    icon = "✨"
    if type == "success":
        icon = "✅"
    elif type == "error":
        icon = "🚨"
    elif type == "warning":
        icon = "⚠️"
    
    st.toast(message, icon=icon)
