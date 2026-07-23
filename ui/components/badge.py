import streamlit as st
from ui.theme import C, T, R, S

def render_badge(text: str, badge_type: str = "primary") -> str:
    """
    Trả về chuỗi HTML của một badge. Tương thích để nhúng inline trong danh sách hoặc bảng.
    """
    bg = C.PRIMARY_50
    text_color = C.PRIMARY_700
    border = f"1px solid {C.PRIMARY_200}"

    if badge_type == "secondary":
        bg = C.SECONDARY_50
        text_color = C.SECONDARY_700
        border = f"1px solid {C.SECONDARY_200}"
    elif badge_type == "neutral":
        bg = C.NEUTRAL_100
        text_color = C.NEUTRAL_700
        border = f"1px solid {C.NEUTRAL_300}"
    elif badge_type == "success":
        bg = C.SUCCESS_BG
        text_color = C.SUCCESS_TEXT
        border = f"1px solid {C.SUCCESS_BORDER}"
    elif badge_type == "warning":
        bg = C.WARNING_BG
        text_color = C.WARNING_TEXT
        border = f"1px solid {C.WARNING_BORDER}"
    elif badge_type == "danger":
        bg = C.ERROR_BG
        text_color = C.ERROR_TEXT
        border = f"1px solid {C.ERROR_BORDER}"

    return f"""
    <span style="
        display: inline-flex;
        align-items: center;
        background-color: {bg};
        color: {text_color};
        border: {border};
        border-radius: {R.FULL};
        padding: 2px 10px;
        font-size: {T.TEXT_XS};
        font-weight: {T.WEIGHT_SEMIBOLD};
        line-height: 1;
        white-space: nowrap;
    ">{text}</span>
    """

def render_status_badge(status: str) -> str:
    """
    Tự động chuẩn hóa màu badge theo trạng thái (Success, Warning, Error...).
    """
    status_lower = status.lower()
    if any(x in status_lower for x in ["success", "approved", "đã đăng", "active", "published"]):
        return render_badge(status, "success")
    elif any(x in status_lower for x in ["pending", "phê duyệt", "chờ", "warning"]):
        return render_badge(status, "warning")
    elif any(x in status_lower for x in ["failed", "rejected", "lỗi", "error", "hủy"]):
        return render_badge(status, "danger")
    else:
        return render_badge(status, "neutral")
