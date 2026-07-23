"""
services/gemini_client.py
==========================
Client giao tiếp với Google Gemini API.
Sử dụng SDK mới: google-genai (thay thế google.generativeai đã deprecated).
"""
import json
from config.config import logger, settings

# ============================================================
# SDK: Dùng google.genai (SDK mới) với fallback sang google.generativeai
# ============================================================
try:
    from google import genai as google_genai
    from google.genai import types as genai_types
    _USE_NEW_SDK = True
    logger.debug("Sử dụng Google Gemini SDK mới (google.genai)")
except ImportError:
    import google.generativeai as google_genai
    _USE_NEW_SDK = False
    logger.warning("Đang dùng google.generativeai (deprecated). Hãy cài: pip install google-genai")

# Tên model mặc định
DEFAULT_MODEL = "gemini-2.5-flash"


# ============================================================
# PUBLIC: Khởi tạo client / model
# ============================================================

def get_gemini_client(api_key: str = None):
    """
    Trả về client Gemini đã được xác thực.
    Hỗ trợ cả SDK mới (google.genai) và SDK cũ (google.generativeai).
    """
    key = api_key or settings.GEMINI_API_KEY
    if not key:
        logger.error("Không tìm thấy Gemini API Key.")
        raise ValueError("Chưa cấu hình Gemini API Key.")

    logger.debug("Đang khởi tạo Gemini client...")

    if _USE_NEW_SDK:
        client = google_genai.Client(api_key=key)
        return client
    else:
        google_genai.configure(api_key=key)
        return google_genai.GenerativeModel(DEFAULT_MODEL)


def _call_model(client, prompt: str, enable_research: bool = False) -> str:
    """Gọi model và trả về text, tương thích cả 2 SDK."""
    if _USE_NEW_SDK:
        config = None
        if enable_research:
            try:
                config = genai_types.GenerateContentConfig(
                    tools=[{"google_search": {}}]
                )
            except Exception as e:
                logger.warning(f"Không thể cấu hình Google Search Tool: {e}")
                
        response = client.models.generate_content(
            model=DEFAULT_MODEL,
            contents=prompt,
            config=config
        )
        return response.text.strip()
    else:
        response = client.generate_content(prompt)
        return response.text.strip()


# ============================================================
# PUBLIC: JSON Helpers
# ============================================================

def clean_ai_json_text(raw_text: str) -> str:
    """Làm sạch chuỗi JSON trả về từ AI (loại bỏ markdown code block)."""
    logger.debug("Chuẩn hóa văn bản JSON từ AI...")
    clean_json = (raw_text or "").replace('```json', '').replace('```JSON', '').replace('```', '').strip()
    start_idx = clean_json.find("[")
    end_idx   = clean_json.rfind("]")
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        clean_json = clean_json[start_idx:end_idx + 1]
    return clean_json.strip()


def validate_weekly_plan_items(plan_data) -> list:
    """Kiểm tra cấu trúc danh sách kế hoạch tuần."""
    if not isinstance(plan_data, list):
        logger.warning("Dữ liệu kế hoạch không phải JSON Array.")
        raise ValueError("Ket qua khong phai JSON Array.")
    for index, item in enumerate(plan_data, start=1):
        if not isinstance(item, dict):
            logger.warning(f"Dong {index} trong danh sach khong phai JSON Object.")
            raise ValueError(f"Dong {index} khong phai object JSON.")
    return plan_data


# ============================================================
# PUBLIC: Generate functions
# ============================================================

def generate_with_gemini(prompt: str, api_key: str = None, enable_research: bool = False) -> str:
    """Gọi Gemini tạo nội dung văn bản đơn giản."""
    logger.info("[AUDIT] Gui yeu cau sinh noi dung van ban toi Gemini API.")
    logger.debug(f"Prompt (300 ky dau): {prompt[:300]}...")
    try:
        client = get_gemini_client(api_key)
        text = _call_model(client, prompt, enable_research=enable_research)
        logger.info("Da nhan phan hoi thanh cong tu Gemini API.")
        return text
    except Exception as e:
        logger.error(f"Loi khi gui yeu cau toi Gemini API: {e}", exc_info=True)
        raise


def generate_weekly_plan_json(prompt: str, api_key: str = None) -> list:
    """
    Gọi Gemini tạo kế hoạch tuần dạng JSON Array.
    Tự động sửa lỗi JSON nếu lần đầu thất bại.
    """
    logger.info("[AUDIT] Gui yeu cau lap ke hoach tuan toi Gemini API.")
    try:
        client = get_gemini_client(api_key)
        raw_text = _call_model(client, prompt)
        logger.info("Da nhan ke hoach tuan tu Gemini. Bat dau phan tach JSON...")

        clean_json = clean_ai_json_text(raw_text)
        try:
            plan_data = json.loads(clean_json)
            return validate_weekly_plan_items(plan_data)
        except Exception as first_error:
            logger.warning(f"JSON thu nhat khong hop le: {first_error}. Thu qua buoc sua loi AI...")

            repair_prompt = f"""
            Ban la he thong sua JSON. Hay sua noi dung duoi day thanh JSON Array hop le.

            Yeu cau bat buoc:
            - Chi tra ve JSON Array thuan tuy, khong markdown, khong giai thich.
            - Moi object chi dung cac field: "day", "topic", "target", "goal", "format", "angle", "hook", "cta".
            - Escape toan bo dau ngoac kep ben trong value neu co.
            - Khong de xuong dong tho ben trong value.
            - Khong them dau phay thua.

            JSON can sua:
            {clean_json}
            """

            repaired_text = _call_model(client, repair_prompt)
            repaired_json = clean_ai_json_text(repaired_text)
            try:
                plan_data = json.loads(repaired_json)
                logger.info("Da khoi phuc JSON ke hoach tuan sau khi sua loi.")
                return validate_weekly_plan_items(plan_data)
            except Exception as second_error:
                logger.error(f"That bai trong viec sua loi JSON: {second_error}", exc_info=True)
                raise Exception(
                    "AI tra ve ke hoach chua dung dinh dang JSON Array sau khi tu sua. "
                    "Vui long bam tao lai hoac rut gon chu de. "
                    f"Loi ban dau: {first_error}. Loi sau khi sua: {second_error}"
                )
    except Exception as e:
        logger.error(f"Loi nghiem trong trong luong xu ly Gemini API: {e}", exc_info=True)
        raise


# Alias giữ tương thích ngược nếu code cũ dùng get_gemini_model
def get_gemini_model(api_key: str = None):
    """Alias tương thích ngược. Dùng get_gemini_client() thay thế."""
    return get_gemini_client(api_key)
