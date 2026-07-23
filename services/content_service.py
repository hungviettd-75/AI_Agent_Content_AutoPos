from config.config import logger
from database.connection import build_content_summary
from agents.prompt_templates import get_weekly_plan_prompt, get_ai_knowledge_sharing_prompt, get_illustration_image_prompt, get_viral_marketing_prompt
from services.gemini_client import generate_with_gemini, generate_weekly_plan_json

def create_weekly_plan(topic=None, target=None, goal=None, days=7, style=None, api_key=None):
    logger.info(f"[AUDIT] Yêu cầu lập kế hoạch tuần qua Service Layer. Chủ đề: {topic or 'Mặc định'}")
    try:
        prompt = get_weekly_plan_prompt(
            topic=topic,
            target=target,
            goal=goal,
            days=days,
            style=style
        )
        plan = generate_weekly_plan_json(prompt, api_key=api_key)
        logger.info(f"Lập thành công kế hoạch tuần gồm {len(plan) if plan else 0} ngày.")
        return plan
    except Exception as e:
        logger.error(f"Lỗi lập kế hoạch tuần tại Service Layer: {e}", exc_info=True)
        raise e

from services.vector_service import semantic_search_knowledge

def generate_marketing_or_knowledge_content(
    platform, 
    content_type, 
    topic, 
    target, 
    angle_selection, 
    ai_tool="", 
    ai_audience="", 
    ai_difficulty="", 
    ai_knowledge_type="", 
    api_key=None,
    workspace_id: int = 1,
    enable_research: bool = False
):
    logger.info(f"[AUDIT] Yêu cầu sinh nội dung qua Service Layer (Loại: {content_type}, Nền tảng: {platform}).")
    logger.debug(f"Chi tiết tham số sinh bài: Chủ đề={topic[:50]}, Đối tượng={target}, Góc={angle_selection}")
    
    try:
        # --- RAG: Tìm kiếm ngữ nghĩa trong kho tri thức của Workspace ---
        context_str = ""
        try:
            matched_knowledges = semantic_search_knowledge(
                query=topic,
                workspace_id=workspace_id,
                top_k=3,
                api_key=api_key
            )
            if matched_knowledges:
                context_parts = []
                for idx, item in enumerate(matched_knowledges, start=1):
                    # Chỉ lấy các tri thức có độ tương đồng tương đối tốt (ví dụ score > 0.15)
                    if item["score"] > 0.15:
                        context_parts.append(
                            f"[Tài liệu tri thức #{idx} - Tiêu đề: {item['title']}]\n{item['content']}"
                        )
                if context_parts:
                    context_str = "\n\n---\nNGỮ CẢNH TRI THỨC ĐƯỢC TÌM THẤY TRONG WORKSPACE (RAG):\n" + "\n\n".join(context_parts) + "\n---\n"
                    logger.info(f"[RAG] Đã đính kèm {len(context_parts)} tài liệu tri thức làm ngữ cảnh.")
        except Exception as rag_err:
            logger.warning(f"[RAG WARNING] Lỗi khi thực hiện Semantic Search: {rag_err}")

        # --- BRAND & COMPANY MEMORY: Lấy cấu hình thương hiệu và doanh nghiệp ---
        from database.models.brand import BrandModel
        from database.models.companies import CompanyModel
        
        brand = BrandModel.get_by_workspace(workspace_id)
        company = CompanyModel.get_by_workspace(workspace_id)
        
        brand_instructions = ""
        brand_rules = []
        
        # 1. Doanh nghiệp, sản phẩm, khách hàng (Company Memory)
        if company:
            if company.get("name"):
                brand_rules.append(f"- Tên doanh nghiệp: {company['name']}")
            if company.get("industry"):
                brand_rules.append(f"- Lĩnh vực hoạt động: {company['industry']}")
            if company.get("description"):
                brand_rules.append(f"- Mô tả doanh nghiệp: {company['description']}")
            if company.get("products"):
                brand_rules.append(f"- Sản phẩm & Dịch vụ chính (Sản phẩm): {company['products']}")
            if company.get("target_customers"):
                brand_rules.append(f"- Đối tượng khách hàng trọng tâm (Khách hàng): {company['target_customers']}")
        
        # 2. Hướng dẫn nhận diện thương hiệu
        if brand:
            if brand.get("tone_of_voice"):
                brand_rules.append(f"- Giọng văn (Tone of voice): {brand['tone_of_voice']}")
            if brand.get("cta"):
                brand_rules.append(f"- Lời kêu gọi hành động (CTA): {brand['cta']}")
            if brand.get("vision"):
                brand_rules.append(f"- Tầm nhìn (Vision): {brand['vision']}")
            if brand.get("mission"):
                brand_rules.append(f"- Sứ mệnh (Mission): {brand['mission']}")
            if brand.get("keywords"):
                keywords_str = ", ".join(brand["keywords"]) if isinstance(brand["keywords"], list) else str(brand["keywords"])
                if keywords_str.strip():
                    brand_rules.append(f"- Từ khóa cần lồng ghép tự nhiên: {keywords_str}")
            if brand.get("blacklist_words"):
                blacklist_str = ", ".join(brand["blacklist_words"]) if isinstance(brand["blacklist_words"], list) else str(brand["blacklist_words"])
                if blacklist_str.strip():
                    brand_rules.append(f"- Tuyệt đối KHÔNG sử dụng các từ sau (Từ cấm): {blacklist_str}")
            
        if brand_rules:
            brand_instructions = "\n\n---\nBỘ NHỚ THƯƠNG HIỆU & DOANH NGHIỆP (BRAND & COMPANY MEMORY):\n" + "\n".join(brand_rules) + "\n---\n"

        # --- LEARNING LOOP: Lấy context AI đã học từ Analytics ---
        learning_context_str = ""
        try:
            from workflow.learning_engine import get_insights_as_context
            lc = get_insights_as_context(workspace_id, max_insights=5)
            if lc:
                learning_context_str = f"\n\n{lc}\n"
                logger.info("[LEARNING] Đã đính kèm Learning Loop context vào prompt.")
        except Exception as lc_err:
            logger.warning(f"[LEARNING WARNING] Lỗi khi lấy Learning context: {lc_err}")

        if content_type == "AI Knowledge Sharing":
            prompt = get_ai_knowledge_sharing_prompt(
                tool_name=ai_tool, 
                topic=topic, 
                audience=ai_audience, 
                difficulty=ai_difficulty, 
                knowledge_type=ai_knowledge_type
            )
            if brand_instructions:
                prompt += brand_instructions
            if learning_context_str:
                prompt += learning_context_str
            if context_str:
                prompt += f"\n\nHãy ưu tiên sử dụng các thông tin và số liệu thực tế trong Ngữ cảnh tri thức (RAG) sau đây để làm phong phú thêm nội dung:\n{context_str}"
            content = generate_with_gemini(prompt, api_key=api_key, enable_research=enable_research)
        else:
            prompt = get_viral_marketing_prompt(
                platform=platform, 
                topic=topic, 
                target=target, 
                angle_selection=angle_selection
            )
            if brand_instructions:
                prompt += brand_instructions
            if learning_context_str:
                prompt += learning_context_str
            if context_str:
                prompt += f"\n\nHãy ưu tiên lồng ghép khéo léo thông tin, case study, hoặc dữ liệu thực tế từ Ngữ cảnh tri thức (RAG) sau đây vào bài viết:\n{context_str}"
            content = generate_with_gemini(prompt, api_key=api_key, enable_research=enable_research)
            
            if brand and brand.get("cta"):
                content += f"\n\n{brand['cta']}"
            else:
                content += "\n\n🌐 Website: hungvietai.com"
            
        logger.info("Đã tạo thành công nội dung bài đăng qua Gemini.")

        # --- BRAND VOICE ENGINE: Kiểm tra & Tinh chỉnh đảm bảo đúng thương hiệu ---
        from services.brand_voice_engine import BrandVoiceEngine
        content = BrandVoiceEngine.verify_and_refine_content(content, brand, api_key)
        
        # Sinh prompt ảnh minh họa
        logger.debug("Đang tạo các prompt gợi ý ảnh minh họa...")
        illustration_prompt = get_illustration_image_prompt(
            topic=topic,
            target=ai_audience if content_type == "AI Knowledge Sharing" else target,
            content_type=content_type,
            platform=platform,
            ai_tool=ai_tool if content_type == "AI Knowledge Sharing" else ""
        )
        
        summary = build_content_summary(content)
        logger.info("Hoàn tất việc sinh bài viết và tạo prompt ảnh.")
        return {
            "content": content,
            "illustration_prompt": illustration_prompt,
            "summary": summary
        }
    except Exception as e:
        logger.error(f"Lỗi sinh nội dung tại Service Layer: {e}", exc_info=True)
        raise e
