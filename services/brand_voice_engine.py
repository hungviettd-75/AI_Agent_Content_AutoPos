"""services/brand_voice_engine.py
==============================
Hệ thống kiểm soát và sửa đổi nội dung tự động để đảm bảo AI luôn tuân thủ 100% hướng dẫn thương hiệu.
"""

import re
from config.config import logger
from services.gemini_client import generate_with_gemini

class BrandVoiceEngine:
    
    @staticmethod
    def check_forbidden_words(content: str, blacklist_words: list) -> list:
        """
        Quét bài viết để tìm các từ bị cấm (Blacklist/Forbidden words).
        Trả về danh sách các từ bị vi phạm (không trùng lặp, giữ nguyên cách viết gốc tìm thấy).
        """
        if not blacklist_words or not content:
            return []
            
        violated = []
        for word in blacklist_words:
            w_strip = word.strip()
            if not w_strip:
                continue
            
            # Sử dụng regex để tìm kiếm chính xác từ (word boundary)
            # Hỗ trợ cả tiếng Việt có dấu
            pattern = re.compile(r'\b' + re.escape(w_strip) + r'\b', re.IGNORECASE)
            matches = pattern.findall(content)
            if matches:
                # Lưu từ cấm bị vi phạm (lấy từ chính xác trong danh sách cấm)
                violated.append(w_strip)
                
        return list(set(violated))

    @staticmethod
    def refine_with_llm(content: str, brand_profile: dict, violated_words: list, api_key: str) -> str:
        """
        Gửi yêu cầu tinh chỉnh bài viết tới Gemini để sửa lại các câu chứa từ cấm và tối ưu tone giọng.
        """
        logger.info(f"[BrandVoiceEngine] Phát hiện vi phạm từ cấm: {violated_words}. Tiến hành tối ưu hóa bằng AI...")
        
        tone = brand_profile.get("tone_of_voice", "casual")
        vision = brand_profile.get("vision", "")
        mission = brand_profile.get("mission", "")
        
        prompt = f"""
Bạn là một Biên tập viên thương hiệu chuyên nghiệp. 
Nhiệm vụ của bạn là chỉnh sửa bài viết dưới đây để đảm bảo bài viết tuân thủ TUYỆT ĐỐI các hướng dẫn thương hiệu sau:

1. KHÔNG được phép sử dụng bất kỳ từ cấm nào trong danh sách sau: {violated_words}
2. Giọng văn phải thể hiện đúng phong cách: "{tone}"
3. Nếu có thể, hãy lồng ghép nhẹ nhàng tinh thần sứ mệnh: "{mission}" và tầm nhìn: "{vision}" của thương hiệu.

YÊU CẦU:
- Giữ nguyên cấu trúc, thông điệp chính và định dạng của bài viết ban đầu.
- Chỉ chỉnh sửa, thay thế những từ cấm bằng từ ngữ tích cực/phù hợp hơn mà không làm giảm sức hút của bài viết.
- Đầu ra CHỈ TRẢ VỀ nội dung bài viết sau khi đã sửa đổi, không kèm theo lời giải thích nào khác.

Bài viết ban đầu:
{content}
"""
        try:
            refined_content = generate_with_gemini(prompt, api_key=api_key)
            if refined_content and refined_content.strip():
                logger.info("[BrandVoiceEngine] Đã tinh chỉnh bài viết thành công qua Gemini.")
                return refined_content.strip()
        except Exception as e:
            logger.error(f"[BrandVoiceEngine] Lỗi khi gọi Gemini để tinh chỉnh nội dung: {e}")
            
        # Fallback: Nếu LLM lỗi, thực hiện thay thế thô bằng regex (loại bỏ từ cấm trực tiếp)
        fallback_content = content
        for word in violated_words:
            pattern = re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE)
            fallback_content = pattern.sub("[đã được lược bỏ]", fallback_content)
        return fallback_content

    @classmethod
    def verify_and_refine_content(cls, content: str, brand_profile: dict, api_key: str) -> str:
        """
        Hàm điều phối chính để kiểm tra chất lượng thương hiệu và tự động tối ưu hóa bài viết.
        """
        if not brand_profile:
            return content
            
        blacklist_words = brand_profile.get("blacklist_words", [])
        if not blacklist_words:
            return content
            
        # Bước 1: Quét từ cấm
        violated_words = cls.check_forbidden_words(content, blacklist_words)
        
        # Bước 2: Tự động tinh chỉnh nếu phát hiện vi phạm
        if violated_words:
            content = cls.refine_with_llm(content, brand_profile, violated_words, api_key)
            
        return content
