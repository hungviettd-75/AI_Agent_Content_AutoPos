import os

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    load_dotenv = None

if load_dotenv:
    load_dotenv()

try:
    import streamlit as st
except Exception:
    st = None


def _get_secret(key: str, default: str = "") -> str:
    """Read config from env first, then Streamlit Cloud secrets."""
    value = os.getenv(key)
    if value not in (None, ""):
        return value
    if st is not None:
        try:
            if key in st.secrets:
                return str(st.secrets[key])
        except Exception:
            pass
    return default

# ============================================================
# DATABASE CONFIGURATION (Dual-Mode: SQLite hoac PostgreSQL)
# ============================================================
DB_ENGINE = _get_secret("DB_ENGINE", "sqlite").lower()

# SQLite Config (du phong / dev)
DB_PATH = _get_secret("DB_PATH", "content_manager.db")

# PostgreSQL Config
PG_HOST     = _get_secret("PG_HOST", "localhost")
PG_PORT     = _get_secret("PG_PORT", "5432")
PG_NAME     = _get_secret("PG_NAME", "ai_agent_marketing")
PG_USER     = _get_secret("PG_USER", "postgres")
PG_PASSWORD = _get_secret("PG_PASSWORD", "")

# DSN san sang dung (uu tien PG_DSN neu da set)
PG_DSN = _get_secret(
    "PG_DSN",
    f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_NAME}"
)

# ============================================================
# API KEYS & TOKENS
# ============================================================
GEMINI_API_KEY        = _get_secret("GEMINI_API_KEY", "")
FB_PAGE_ID            = _get_secret("FB_PAGE_ID", "")
FB_ACCESS_TOKEN       = _get_secret("FB_ACCESS_TOKEN", "")
ZALO_OA_ID            = _get_secret("ZALO_OA_ID", "")
ZALO_ACCESS_TOKEN     = _get_secret("ZALO_ACCESS_TOKEN", "")
LINKEDIN_AUTHOR_URN   = _get_secret("LINKEDIN_AUTHOR_URN", "")
LINKEDIN_ACCESS_TOKEN = _get_secret("LINKEDIN_ACCESS_TOKEN", "")

# ============================================================
# LOGGING CONFIGURATION
# ============================================================
LOG_LEVEL = _get_secret("LOG_LEVEL", "INFO")
LOG_FILE  = _get_secret("LOG_FILE", "app_execution.log")

# ============================================================
# SECURITY
# ============================================================
SECRET_KEY = _get_secret("SECRET_KEY", "ai-agent-marketing-super-secret-2024")
JWT_EXPIRE_HOURS = int(_get_secret("JWT_EXPIRE_HOURS", "24"))
