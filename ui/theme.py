"""
ui/theme.py
===========
Apex AI — Design System Tokens
Phiên bản: 1.0.0
Mô tả: Nguồn duy nhất của các design token cho toàn bộ ứng dụng Apex AI.
       Không bao giờ hardcode màu sắc, kích cỡ, hay shadow trong các tab.
       Luôn import từ module này.
"""

# ============================================================
#  1. COLOR PALETTE
# ============================================================

class Colors:
    # --- Primary Blue --- 
    PRIMARY_900  = "#001d6c"
    PRIMARY_800  = "#003399"
    PRIMARY_700  = "#003dbf"
    PRIMARY      = "#004ac6"   # ← brand primary
    PRIMARY_600  = "#0053db"
    PRIMARY_500  = "#1a67f5"
    PRIMARY_400  = "#4d8cff"
    PRIMARY_300  = "#86aeff"
    PRIMARY_200  = "#b8cfff"
    PRIMARY_100  = "#dce8ff"
    PRIMARY_50   = "#f0f5ff"

    # --- Secondary Purple (AI accent) ---
    SECONDARY_900 = "#3b0764"
    SECONDARY_800 = "#5a0d97"
    SECONDARY_700 = "#6d18bf"
    SECONDARY     = "#712ae2"   # ← AI/premium accent
    SECONDARY_500 = "#8b4cf5"
    SECONDARY_400 = "#a57af7"
    SECONDARY_300 = "#c4a5fa"
    SECONDARY_200 = "#e1d4fe"
    SECONDARY_100 = "#f3eeff"
    SECONDARY_50  = "#faf5ff"

    # --- Neutral / Slate ---
    NEUTRAL_950 = "#060d1f"
    NEUTRAL_900 = "#0f172a"
    NEUTRAL_800 = "#1e293b"
    NEUTRAL_700 = "#293040"
    NEUTRAL_600 = "#434655"
    NEUTRAL_500 = "#737686"
    NEUTRAL_400 = "#94a3b8"
    NEUTRAL_300 = "#c3c6d7"
    NEUTRAL_200 = "#e1e8fd"
    NEUTRAL_100 = "#edf0ff"
    NEUTRAL_50  = "#f1f3ff"
    WHITE       = "#ffffff"

    # --- Canvas / Background ---
    BG_APP      = "#f9f9ff"
    BG_CARD     = "#ffffff"
    BG_SIDEBAR  = "#1e293b"
    BG_FORM     = "#ffffff"

    # --- Status Colors ---
    SUCCESS     = "#10b981"
    SUCCESS_BG  = "#f0fdf4"
    SUCCESS_BORDER = "#a7f3d0"
    SUCCESS_TEXT   = "#065f46"

    WARNING     = "#f59e0b"
    WARNING_BG  = "#fffbeb"
    WARNING_BORDER = "#fcd34d"
    WARNING_TEXT   = "#78350f"

    ERROR       = "#ef4444"
    ERROR_BG    = "#fef2f2"
    ERROR_BORDER   = "#fca5a5"
    ERROR_TEXT     = "#991b1b"

    INFO        = "#3b82f6"
    INFO_BG     = "#eff6ff"
    INFO_BORDER    = "#93c5fd"
    INFO_TEXT      = "#1e40af"

    # --- Platform Colors ---
    FACEBOOK    = "#1d4ed8"
    FACEBOOK_BG = "#e7effd"
    ZALO        = "#be185d"
    ZALO_BG     = "#ffe4f3"
    LINKEDIN    = "#0369a1"
    LINKEDIN_BG = "#e6f4ff"

    # --- Role Badge Colors ---
    ROLE_SUPER_ADMIN = "#004ac6"
    ROLE_ADMIN       = "#712ae2"
    ROLE_EDITOR      = "#10b981"
    ROLE_VIEWER      = "#94a3b8"
    ROLE_OWNER       = "#f59e0b"
    ROLE_MARKETING   = "#ec4899"

    # --- KPI Gradient Pairs (start, end) ---
    KPI_REACH   = ("#3b82f6", "#60a5fa")
    KPI_CTR     = ("#8b5cf6", "#a78bfa")
    KPI_LEAD    = ("#10b981", "#34d399")
    KPI_ROI     = ("#f59e0b", "#fbbf24")
    KPI_IMP     = ("#ef4444", "#f87171")
    KPI_ENG     = ("#ec4899", "#f472b6")


# ============================================================
#  2. TYPOGRAPHY
# ============================================================

class Typography:
    # Font families
    FONT_PRIMARY   = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    FONT_MONO      = "'JetBrains Mono', 'Fira Code', 'Courier New', monospace"
    FONT_IMPORT    = "@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');"

    # Font sizes (rem)
    TEXT_XS   = "0.72rem"   # 11.5px
    TEXT_SM   = "0.78rem"   # 12.5px
    TEXT_BASE = "0.875rem"  # 14px
    TEXT_MD   = "0.95rem"   # 15.2px
    TEXT_LG   = "1rem"      # 16px
    TEXT_XL   = "1.125rem"  # 18px
    TEXT_2XL  = "1.25rem"   # 20px
    TEXT_3XL  = "1.4rem"    # 22.4px
    TEXT_4XL  = "1.6rem"    # 25.6px
    TEXT_5XL  = "1.75rem"   # 28px
    TEXT_6XL  = "2rem"      # 32px
    TEXT_7XL  = "2.25rem"   # 36px

    # Font weights
    WEIGHT_LIGHT    = "300"
    WEIGHT_REGULAR  = "400"
    WEIGHT_MEDIUM   = "500"
    WEIGHT_SEMIBOLD = "600"
    WEIGHT_BOLD     = "700"
    WEIGHT_EXTRABOLD= "800"

    # Line heights
    LEADING_TIGHT   = "1.25"
    LEADING_SNUG    = "1.375"
    LEADING_NORMAL  = "1.5"
    LEADING_RELAXED = "1.625"
    LEADING_LOOSE   = "1.75"

    # Letter spacing
    TRACKING_TIGHTER = "-0.03em"
    TRACKING_TIGHT   = "-0.02em"
    TRACKING_NORMAL  = "-0.01em"
    TRACKING_WIDE    = "0.05em"
    TRACKING_WIDER   = "0.08em"
    TRACKING_WIDEST  = "0.1em"


# ============================================================
#  3. SPACING SYSTEM (8pt grid)
# ============================================================

class Spacing:
    SP_0  = "0"
    SP_1  = "4px"
    SP_2  = "8px"
    SP_3  = "12px"
    SP_4  = "16px"
    SP_5  = "20px"
    SP_6  = "24px"
    SP_7  = "28px"
    SP_8  = "32px"
    SP_10 = "40px"
    SP_12 = "48px"
    SP_14 = "56px"
    SP_16 = "64px"
    SP_20 = "80px"
    SP_24 = "96px"


# ============================================================
#  4. BORDER RADIUS
# ============================================================

class Radius:
    NONE   = "0"
    SM     = "4px"
    MD     = "8px"
    LG     = "12px"
    XL     = "16px"
    XXL    = "20px"
    XXXL   = "24px"
    FULL   = "9999px"  # pill / badge


# ============================================================
#  5. SHADOWS
# ============================================================

class Shadow:
    NONE   = "none"
    XS     = "0 1px 2px rgba(0,0,0,0.05)"
    SM     = "0 1px 3px rgba(0,0,0,0.05), 0 1px 2px rgba(0,0,0,0.06)"
    MD     = "0 4px 6px -1px rgba(0,0,0,0.07), 0 2px 4px -1px rgba(0,0,0,0.05)"
    LG     = "0 10px 15px -3px rgba(0,0,0,0.08), 0 4px 6px -2px rgba(0,0,0,0.04)"
    XL     = "0 20px 25px -5px rgba(0,0,0,0.10), 0 10px 10px -5px rgba(0,0,0,0.04)"
    XXL    = "0 25px 50px -12px rgba(0,0,0,0.25)"

    # Colored / Brand shadows
    PRIMARY_SM = "0 4px 6px -1px rgba(0,74,198,0.15)"
    PRIMARY_MD = "0 6px 12px -2px rgba(0,74,198,0.25)"
    PRIMARY_LG = "0 8px 16px -4px rgba(0,74,198,0.35)"

    SECONDARY_SM = "0 4px 6px -1px rgba(113,42,226,0.15)"
    SECONDARY_MD = "0 6px 12px -2px rgba(113,42,226,0.25)"

    SUCCESS_SM = "0 4px 6px -1px rgba(16,185,129,0.20)"
    ERROR_SM   = "0 4px 6px -1px rgba(239,68,68,0.20)"

    # Card / Inner glow
    CARD       = "0 1px 3px rgba(0,0,0,0.05), 0 10px 15px -3px rgba(0,0,0,0.02)"
    CARD_HOVER = "0 8px 25px rgba(0,0,0,0.10)"
    INSET      = "inset 0 2px 4px rgba(0,0,0,0.06)"


# ============================================================
#  6. RESPONSIVE BREAKPOINTS
# ============================================================

class Breakpoints:
    """
    Chú ý: Streamlit không có true responsive CSS breakpoints như web thông thường.
    Dùng st.columns() để tạo responsive layout.
    Các breakpoint này dùng cho CSS media queries trong HTML nhúng.
    """
    XS  = "360px"
    SM  = "576px"
    MD  = "768px"
    LG  = "1024px"
    XL  = "1280px"
    XXL = "1536px"


# ============================================================
#  7. Z-INDEX SCALE
# ============================================================

class ZIndex:
    BASE    = "0"
    RAISED  = "10"
    OVERLAY = "100"
    MODAL   = "1000"
    TOAST   = "9000"
    TOOLTIP = "9999"


# ============================================================
#  8. TRANSITION / ANIMATION
# ============================================================

class Animation:
    DURATION_FAST   = "0.15s"
    DURATION_BASE   = "0.2s"
    DURATION_SLOW   = "0.3s"
    DURATION_SLOWER = "0.5s"

    EASE_DEFAULT    = "ease-in-out"
    EASE_IN         = "ease-in"
    EASE_OUT        = "ease-out"
    EASE_SPRING     = "cubic-bezier(0.34, 1.56, 0.64, 1)"

    # Shorthand (duration + easing)
    FAST  = f"all 0.15s ease-in-out"
    BASE  = f"all 0.2s ease-in-out"
    SLOW  = f"all 0.3s ease-in-out"


# ============================================================
#  CONVENIENCE — Export tất cả vào 1 dict (cho template strings)
# ============================================================

THEME = {
    "colors": Colors,
    "typography": Typography,
    "spacing": Spacing,
    "radius": Radius,
    "shadow": Shadow,
    "breakpoints": Breakpoints,
    "animation": Animation,
    "zindex": ZIndex,
}

# Alias ngắn gọn
C = Colors
T = Typography
S = Spacing
R = Radius
SH = Shadow
A = Animation
