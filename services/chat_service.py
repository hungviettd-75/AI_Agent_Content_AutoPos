"""services/chat_service.py
==============================
Dịch vụ xử lý hội thoại tinh chỉnh bài viết sử dụng Conversation Memory.
"""

from config.config import logger
from services.gemini_client import generate_with_gemini
from services.brand_voice_engine import BrandVoiceEngine

def refine_content_with_history(
    chat_history: list,
    user_instruction: str,
    brand_profile: dict,
    api_key: str,
    company_profile: dict = None
) -> str:
    """
    Sử dụng lịch sử hội thoại để tinh chỉnh bài viết theo yêu cầu mới của người dùng.
    """
    logger.info("[ChatService] Thực hiện tinh chỉnh bài viết theo lịch sử hội thoại.")
    
    # Xây dựng ngữ cảnh hội thoại cho prompt
    context_turns = []
    for turn in chat_history:
        role_label = "Người dùng" if turn["role"] == "user" else "AI Assistant"
        context_turns.append(f"{role_label}: {turn['content']}")
        
    conversation_context = "\n\n".join(context_turns)
    
    # Brand & Company guidelines
    brand_instructions = ""
    brand_rules = []
    
    # 1. Doanh nghiệp, sản phẩm, khách hàng (Company Memory)
    if company_profile:
        if company_profile.get("name"):
            brand_rules.append(f"- Tên doanh nghiệp: {company_profile['name']}")
        if company_profile.get("industry"):
            brand_rules.append(f"- Lĩnh vực hoạt động: {company_profile['industry']}")
        if company_profile.get("description"):
            brand_rules.append(f"- Mô tả doanh nghiệp: {company_profile['description']}")
        if company_profile.get("products"):
            brand_rules.append(f"- Sản phẩm & Dịch vụ chính (Sản phẩm): {company_profile['products']}")
        if company_profile.get("target_customers"):
            brand_rules.append(f"- Đối tượng khách hàng trọng tâm (Khách hàng): {company_profile['target_customers']}")
            
    # 2. Hướng dẫn nhận diện thương hiệu
    if brand_profile:
        if brand_profile.get("tone_of_voice"):
            brand_rules.append(f"- Giọng văn (Tone of voice): {brand_profile['tone_of_voice']}")
        if brand_profile.get("cta"):
            brand_rules.append(f"- Lời kêu gọi hành động (CTA): {brand_profile['cta']}")
        if brand_profile.get("vision"):
            brand_rules.append(f"- Tầm nhìn (Vision): {brand_profile['vision']}")
        if brand_profile.get("mission"):
            brand_rules.append(f"- Sứ mệnh (Mission): {brand_profile['mission']}")
        if brand_profile.get("keywords"):
            keywords_str = ", ".join(brand_profile["keywords"]) if isinstance(brand_profile["keywords"], list) else str(brand_profile["keywords"])
            if keywords_str.strip():
                brand_rules.append(f"- Từ khóa cần lồng ghép tự nhiên: {keywords_str}")
        if brand_profile.get("blacklist_words"):
            blacklist_str = ", ".join(brand_profile["blacklist_words"]) if isinstance(brand_profile["blacklist_words"], list) else str(brand_profile["blacklist_words"])
            if blacklist_str.strip():
                brand_rules.append(f"- Tuyệt đối KHÔNG sử dụng các từ sau (Từ cấm): {blacklist_str}")
        
    if brand_rules:
        brand_instructions = "\n\n---\nBỘ NHỚ THƯƠNG HIỆU & DOANH NGHIỆP (BRAND & COMPANY MEMORY):\n" + "\n".join(brand_rules) + "\n---\n"

    # Prompt gửi Gemini
    prompt = f"""
Bạn là một trợ lý viết bài marketing chuyên nghiệp. Nhiệm vụ của bạn là tiếp tục tinh chỉnh bài viết dựa trên lịch sử hội thoại và yêu cầu mới nhất từ người dùng dưới đây.

LỊCH SỬ HỘI THOẠI TRƯỚC ĐÓ:
{conversation_context}

YÊU CẦU TINH CHỈNH MỚI NHẤT:
"{user_instruction}"
{brand_instructions}
YÊU CẦU QUAN TRỌNG:
- Trả về TOÀN BỘ nội dung bài viết mới sau khi đã được tinh chỉnh theo yêu cầu.
- Chỉ trả về nội dung bài viết hoàn chỉnh, không kèm bất kỳ lời giải thích, lời chào hay phần dẫn nhập nào khác.
"""
    
    try:
        response = generate_with_gemini(prompt, api_key=api_key)
        if response and response.strip():
            refined_content = response.strip()
            
            # Kiểm duyệt thương hiệu bằng Brand Voice Engine
            refined_content = BrandVoiceEngine.verify_and_refine_content(refined_content, brand_profile, api_key)
            return refined_content
            
    except Exception as e:
        logger.error(f"[ChatService] Lỗi khi tinh chỉnh với bộ nhớ hội thoại: {e}", exc_info=True)
        raise e
        
    return ""
