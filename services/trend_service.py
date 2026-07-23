"""
services/trend_service.py
==========================
Trend Agent – Phân tích xu hướng nội dung thời gian thực
bằng cách sử dụng Gemini API + Google Search Grounding.
"""
import json
import re
from config.config import logger
from services.gemini_client import generate_with_gemini

# Danh sách lĩnh vực hỗ trợ
NICHES = [
    "AI & Công nghệ",
    "Kinh doanh & Khởi nghiệp",
    "Marketing & Thương hiệu",
    "Thương mại điện tử",
    "Tài chính & Đầu tư",
    "Sức khoẻ & Lifestyle",
    "Giáo dục & Kỹ năng",
    "Bất động sản",
    "Du lịch & Ẩm thực",
]

# Nền tảng hỗ trợ
TREND_PLATFORMS = ["Facebook", "LinkedIn", "Zalo OA", "TikTok", "Instagram", "Tất cả nền tảng"]


def _build_trend_prompt(niche: str, platform: str) -> str:
    """Tạo prompt yêu cầu Gemini phân tích xu hướng."""
    today_hint = "Hãy tìm kiếm thông tin cập nhật nhất tính đến ngày hôm nay."
    return f"""Bạn là một chuyên gia phân tích xu hướng nội dung mạng xã hội hàng đầu Việt Nam.
{today_hint}

Nhiệm vụ: Phân tích và liệt kê 10 CHỦ ĐỀ / XU HƯỚNG NỘI DUNG đang được quan tâm và có tỷ lệ viral cao nhất 
trong lĩnh vực "{niche}" trên nền tảng "{platform}" tại thị trường Việt Nam và toàn cầu hiện tại.

Yêu cầu đầu ra: Trả về ĐÚNG định dạng JSON sau, không thêm bất kỳ văn bản nào khác ngoài JSON:

{{
  "trends": [
    {{
      "title": "Tiêu đề xu hướng ngắn gọn, hấp dẫn (tối đa 15 từ)",
      "description": "Mô tả lý do xu hướng này đang viral, bối cảnh và tại sao người dùng quan tâm (2-3 câu)",
      "viral_score": 9,
      "content_angle": "Góc khai thác nội dung gợi ý cho creator trong lĩnh vực {niche} (1-2 câu)",
      "hashtags": ["#hashtag1", "#hashtag2", "#hashtag3"]
    }}
  ]
}}

Quy tắc:
- viral_score là số nguyên từ 1 đến 10 (10 = cực kỳ viral)
- Mỗi xu hướng phải THỰC SỰ đang diễn ra, có dẫn chứng thực tế
- Ưu tiên xu hướng có thể tạo nội dung cho {platform}
- Hashtags phải phù hợp thị trường Việt Nam
- CHỈ trả về JSON, không có markdown, không có giải thích thêm
"""


def parse_trend_response(text: str) -> list[dict]:
    """
    Parse JSON từ phản hồi của Gemini một cách an toàn.
    Hỗ trợ cả trường hợp Gemini bọc JSON trong markdown code block.
    """
    try:
        # Thử parse trực tiếp
        data = json.loads(text.strip())
        return data.get("trends", [])
    except json.JSONDecodeError:
        pass

    # Thử trích xuất JSON từ markdown code block ```json ... ```
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(1))
            return data.get("trends", [])
        except json.JSONDecodeError:
            pass

    # Thử tìm bất kỳ chuỗi JSON nào trong text
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(0))
            return data.get("trends", [])
        except json.JSONDecodeError:
            pass

    logger.error(f"[TrendAgent] Không thể parse JSON từ phản hồi Gemini: {text[:300]}")
    return []


def analyze_trends(niche: str, platform: str, api_key: str = None) -> list[dict]:
    """
    Phân tích xu hướng nội dung đang hot cho lĩnh vực và nền tảng đã chọn.
    
    Args:
        niche: Lĩnh vực nội dung (VD: "AI & Công nghệ")
        platform: Nền tảng mạng xã hội (VD: "Facebook")
        api_key: Gemini API Key (tùy chọn, dùng key mặc định nếu không truyền)
    
    Returns:
        Danh sách các xu hướng, mỗi xu hướng là một dict gồm:
        title, description, viral_score, content_angle, hashtags
    """
    logger.info(f"[TrendAgent] Bắt đầu phân tích xu hướng: niche='{niche}', platform='{platform}'")

    prompt = _build_trend_prompt(niche, platform)

    try:
        raw_text = generate_with_gemini(
            prompt=prompt,
            api_key=api_key,
            enable_research=True  # Bật Google Search Grounding để lấy dữ liệu thời gian thực
        )
        trends = parse_trend_response(raw_text)

        if not trends:
            logger.warning("[TrendAgent] Không parse được xu hướng từ phản hồi Gemini.")
            return []

        # Đảm bảo viral_score là số nguyên hợp lệ (1-10)
        for t in trends:
            try:
                t["viral_score"] = max(1, min(10, int(t.get("viral_score", 5))))
            except (ValueError, TypeError):
                t["viral_score"] = 5
            # Đảm bảo hashtags là list
            if not isinstance(t.get("hashtags"), list):
                t["hashtags"] = []

        logger.info(f"[TrendAgent] Phân tích thành công: {len(trends)} xu hướng.")
        return trends

    except Exception as e:
        logger.error(f"[TrendAgent] Lỗi khi phân tích xu hướng: {e}", exc_info=True)
        raise
