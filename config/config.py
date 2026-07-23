"""
config/config.py
=================
Entry point thống nhất cho toàn bộ config của dự án.
Các module khác chỉ cần: from config.config import logger, settings, ...
"""

# Re-export toàn bộ settings variables
from config.settings import (
    DB_ENGINE, DB_PATH,
    PG_HOST, PG_PORT, PG_NAME, PG_USER, PG_PASSWORD, PG_DSN,
    GEMINI_API_KEY,
    FB_PAGE_ID, FB_ACCESS_TOKEN,
    ZALO_OA_ID, ZALO_ACCESS_TOKEN,
    LINKEDIN_AUTHOR_URN, LINKEDIN_ACCESS_TOKEN,
    LOG_LEVEL, LOG_FILE,
)

# Re-export constants
from config.constants import (
    AI_TOOLS, CONTENT_TYPES, AI_AUDIENCES, AI_DIFFICULTIES, AI_KNOWLEDGE_TYPES,
    CONTENT_MIX, TARGETS, DIFFICULTIES, FORMATS, TOPIC_BANK, GOALS,
    DEFAULT_STYLE_RULES, COMPANY_SIZE_PROFILES, INDUSTRY_CONTEXT,
    CRITERIA, COMPARISON_DATA,
)

# Re-export logger (phải import sau settings vì logging.py cần LOG_LEVEL)
from config.logging import logger

# Namespace object tiện dụng (optional - dùng khi cần pass settings như object)
import config.settings as settings
