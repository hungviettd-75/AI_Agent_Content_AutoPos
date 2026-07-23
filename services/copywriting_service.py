"""
services/copywriting_service.py
================================
Copywriting Agent – Service layer tạo copy bán hàng chuyên nghiệp
theo các framework copywriting kinh điển.
"""
from config.config import logger
from agents.copywriting_prompts import get_copywriting_prompt
from services.gemini_client import generate_with_gemini


def generate_copy(
    product: str,
    benefit: str,
    target: str,
    framework: str,
    copy_type: str,
    tone: str,
    api_key: str = None,
    workspace_id: int = 1,
    enable_research: bool = False,
    enable_ab: bool = False,
) -> dict:
    """
    Tạo copy bán hàng chuyên nghiệp theo framework đã chọn.

    Args:
        product: Tên sản phẩm / dịch vụ
        benefit: Lợi ích nổi bật / USP
        target: Đối tượng khách hàng mục tiêu
        framework: Framework copywriting
        copy_type: Loại copy cần tạo
        tone: Giọng điệu
        api_key: Gemini API Key
        workspace_id: ID workspace (để load Brand & Company Memory)
        enable_research: Bật Google Search Grounding
        enable_ab: Tạo 3 biến thể A/B thay vì 1 bản

    Returns:
        dict gồm: copy (str), framework_used (str), ab_variants (list|None)
    """
    logger.info(
        f"[CopywritingAgent] Tạo copy: product='{product[:30]}', "
        f"framework='{framework}', type='{copy_type}', ab={enable_ab}"
    )

    # ── Brand & Company Memory ─────────────────────────────────────────────────
    brand_instructions = _build_brand_instructions(workspace_id)

    # ── Build prompt ───────────────────────────────────────────────────────────
    prompt = get_copywriting_prompt(
        product=product,
        benefit=benefit,
        target=target,
        framework=framework,
        copy_type=copy_type,
        tone=tone,
        brand_instructions=brand_instructions,
        enable_ab=enable_ab,
    )

    # ── Gọi Gemini ────────────────────────────────────────────────────────────
    try:
        raw_copy = generate_with_gemini(
            prompt=prompt,
            api_key=api_key,
            enable_research=enable_research,
        )
    except Exception as e:
        logger.error(f"[CopywritingAgent] Lỗi gọi Gemini: {e}", exc_info=True)
        raise

    # ── Brand Voice Engine: lọc từ cấm ───────────────────────────────────────
    try:
        from database.models.brand import BrandModel
        from services.brand_voice_engine import BrandVoiceEngine
        brand = BrandModel.get_by_workspace(workspace_id)
        if brand:
            raw_copy = BrandVoiceEngine.verify_and_refine_content(raw_copy, brand, api_key)
    except Exception as bve_err:
        logger.warning(f"[CopywritingAgent] Brand Voice Engine lỗi (bỏ qua): {bve_err}")

    logger.info("[CopywritingAgent] Đã tạo copy thành công.")

    # ── Parse A/B variants nếu được yêu cầu ───────────────────────────────────
    ab_variants = None
    if enable_ab:
        ab_variants = _parse_ab_variants(raw_copy)

    return {
        "copy": raw_copy,
        "framework_used": framework,
        "ab_variants": ab_variants,
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_brand_instructions(workspace_id: int) -> str:
    """Đọc Brand & Company Memory và tạo chuỗi hướng dẫn nhúng vào prompt."""
    rules = []
    try:
        from database.models.brand import BrandModel
        from database.models.companies import CompanyModel

        company = CompanyModel.get_by_workspace(workspace_id)
        brand = BrandModel.get_by_workspace(workspace_id)

        if company:
            if company.get("name"):
                rules.append(f"- Tên doanh nghiệp: {company['name']}")
            if company.get("products"):
                rules.append(f"- Sản phẩm & Dịch vụ: {company['products']}")
            if company.get("target_customers"):
                rules.append(f"- Khách hàng mục tiêu: {company['target_customers']}")

        if brand:
            if brand.get("tone_of_voice"):
                rules.append(f"- Giọng văn thương hiệu: {brand['tone_of_voice']}")
            if brand.get("cta"):
                rules.append(f"- CTA thương hiệu: {brand['cta']}")
            if brand.get("keywords"):
                kw = brand["keywords"]
                kw_str = ", ".join(kw) if isinstance(kw, list) else str(kw)
                if kw_str.strip():
                    rules.append(f"- Từ khóa lồng ghép: {kw_str}")
            if brand.get("blacklist_words"):
                bl = brand["blacklist_words"]
                bl_str = ", ".join(bl) if isinstance(bl, list) else str(bl)
                if bl_str.strip():
                    rules.append(f"- TUYỆT ĐỐI KHÔNG dùng các từ: {bl_str}")

    except Exception as e:
        logger.warning(f"[CopywritingAgent] Không load được Brand Memory: {e}")

    if not rules:
        return ""

    return (
        "\n\n---\nBỘ NHỚ THƯƠNG HIỆU (BRAND MEMORY – BẮT BUỘC TUÂN THỦ):\n"
        + "\n".join(rules)
        + "\n---\n"
    )


def _parse_ab_variants(raw_text: str) -> list:
    """
    Tách 3 biến thể A/B/C từ text nếu Gemini trả về theo format chuẩn.
    Fallback: trả về list chứa toàn bộ text nếu không tách được.
    """
    import re
    parts = re.split(r"-{3,}\s*PHIÊN BẢN\s+[ABC]\s*-{3,}", raw_text, flags=re.IGNORECASE)
    if len(parts) >= 3:
        # parts[0] có thể là text intro, parts[1..3] là 3 biến thể
        variants = [p.strip() for p in parts if p.strip()]
        return variants[:3]
    return [raw_text.strip()]
