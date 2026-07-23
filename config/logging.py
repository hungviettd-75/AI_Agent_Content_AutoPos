import logging
import sys
from config.settings import LOG_LEVEL, LOG_FILE

def setup_logging():
    """
    Cấu hình hệ thống logging đa cấp cho dự án.
    Hỗ trợ: DEBUG, INFO, WARNING, ERROR, CRITICAL (Audit).
    """
    logger = logging.getLogger("ai_agent_marketing")

    # Tránh gắn lặp handlers nếu đã được cấu hình trước đó
    if not logger.handlers:
        # Lấy log level từ config (mặc định INFO)
        numeric_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
        logger.setLevel(numeric_level)

        # Format chuẩn cho log
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)-8s [%(name)s.%(funcName)s:%(lineno)d] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # --- Console Handler (UTF-8 safe cho Windows) ---
        try:
            # Python 3.7+: reconfigure stdout sang UTF-8 nếu có thể
            if hasattr(sys.stdout, "reconfigure"):
                sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.DEBUG)  # Hiện tất cả trên console
        logger.addHandler(console_handler)

        # --- File Handler (Lưu log ra file) ---
        try:
            file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
            file_handler.setFormatter(formatter)
            file_handler.setLevel(logging.INFO)   # Chỉ ghi INFO trở lên vào file
            logger.addHandler(file_handler)
        except Exception:
            # Bỏ qua nếu không có quyền ghi file log
            pass

        # --- Audit Handler (Ghi riêng file audit quan trọng) ---
        try:
            audit_handler = logging.FileHandler("audit.log", encoding="utf-8")
            audit_handler.setFormatter(formatter)
            audit_handler.setLevel(logging.INFO)
            # Chỉ ghi những message chứa [AUDIT]
            audit_handler.addFilter(_AuditFilter())
            logger.addHandler(audit_handler)
        except Exception:
            pass

    return logger


class _AuditFilter(logging.Filter):
    """Chỉ cho qua các log message bắt đầu bằng [AUDIT]."""
    def filter(self, record):
        return "[AUDIT]" in record.getMessage()


logger = setup_logging()
