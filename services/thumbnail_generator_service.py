"""
services/thumbnail_generator_service.py
=======================================
Thumbnail Generator Service — Tải, tạo, lưu trữ và sinh prompt cho Thumbnail.
Tách biệt toàn bộ logic sinh Prompt và gọi Gemini.
"""

import json
from typing import Dict, Any, Tuple
from database.models.brand import BrandModel
from services.gemini_client import generate_with_gemini
from config.config import logger

PLATFORM_DEFAULTS = {
    "LinkedIn":       {"aspect_ratio": "4:5",  "style": "Premium Corporate Editorial Photography"},
    "Facebook":       {"aspect_ratio": "16:9", "style": "Vibrant Lifestyle Photography"},
    "Facebook Ads":   {"aspect_ratio": "16:9", "style": "Clean High-Contrast Ad-Safe Commercial"},
    "YouTube":        {"aspect_ratio": "16:9", "style": "Bold YouTube Thumbnail Style"},
    "Zalo OA":        {"aspect_ratio": "1:1",  "style": "Friendly Vietnamese Context Photography"},
    "Instagram":      {"aspect_ratio": "1:1",  "style": "Aesthetic Minimal Lifestyle"},
    "TikTok / Reels": {"aspect_ratio": "9:16", "style": "Vibrant 3D Motion Graphics"},
}

class ThumbnailGeneratorService:
    """Service chịu trách nhiệm điều phối việc sinh Prompt & cấu hình Thumbnail."""

    @staticmethod
    def build_brand_context(workspace_id: int) -> dict:
        """Đọc Brand Profile từ DB."""
        brand = BrandModel.get_by_workspace(workspace_id)
        if brand:
            return {
                "status":     "applied",
                "tone":       brand.get("tone_of_voice", "Professional & Trustworthy"),
                "colors":     brand.get("brand_colors", {"primary": "#0f172a", "secondary": "#2563eb", "accent": "#fbbf24"}),
                "logo_url":   brand.get("logo_url", ""),
                "tagline":    brand.get("tagline", ""),
                "guidelines": brand.get("brand_guidelines", ""),
                "blacklist":  brand.get("blacklist_words", []),
                "keywords":   brand.get("keywords", []),
                "vision":     brand.get("vision", ""),
                "mission":    brand.get("mission", ""),
                "cta":        brand.get("cta", ""),
            }
        return {"status": "proposed"}

    @staticmethod
    def build_system_prompt(article: str, audience: str, platform: str, brand_ctx: dict) -> str:
        """Tạo system prompt cho Gemini."""
        platform_cfg = PLATFORM_DEFAULTS.get(
            platform, {"aspect_ratio": "16:9", "style": "Commercial Photography"}
        )

        if brand_ctx["status"] == "applied":
            blacklist_str = ", ".join(brand_ctx["blacklist"]) if isinstance(brand_ctx["blacklist"], list) else str(brand_ctx["blacklist"])
            keywords_str  = ", ".join(brand_ctx["keywords"]) if isinstance(brand_ctx["keywords"], list) else str(brand_ctx["keywords"])
            colors_str    = json.dumps(brand_ctx["colors"], ensure_ascii=False)
            brand_block   = f"""
## 🎨 BRAND PROFILE — BẮT BUỘC ÁP DỤNG CHÍNH XÁC:
- Brand Voice  : {brand_ctx['tone']}
- Brand Colors : {colors_str}
- Tagline      : {brand_ctx['tagline']}
- Keywords     : {keywords_str}
- Guidelines   : {brand_ctx['guidelines']}
- Logo URL     : {brand_ctx['logo_url']} → Chừa góc dưới bên trái cho logo.
- Blacklist    : {blacklist_str} → TUYỆT ĐỐI không dùng các từ này trên Text Overlay.
- Vision       : {brand_ctx['vision']}
- Mission      : {brand_ctx['mission']}
- CTA mặc định: {brand_ctx['cta']}
"""
        else:
            brand_block = """
## 🤖 BRAND PROPOSAL — CHƯA CÓ BRAND PROFILE:
Workspace chưa thiết lập Brand Profile. Phân tích Article và Audience để:
1. Đề xuất: Brand Voice, Brand Colors (3 HEX), Typography, Brand Style, 2–3 Guideline Rules.
2. Điền vào trường `brand_proposal` trong JSON đầu ra.
3. Giải thích lý do đề xuất trong `brand_proposal.brand_proposal_rationale`.
"""

        return f"""Bạn là Art Director chuyên nghiệp. Phân tích dữ liệu đầu vào và sinh JSON Thumbnail.

## INPUT:
- Article       : {article}
- Audience      : {audience}
- Platform      : {platform}
- Aspect Ratio  : {platform_cfg['aspect_ratio']}
- Default Style : {platform_cfg['style']}

{brand_block}

## OUTPUT SCHEMA:
Trả về đúng JSON schema có các trường sau:
- "brand_status": "{brand_ctx['status']}"
- "brand_proposal": {{"proposed_tone": "", "proposed_colors": {{"primary": "", "secondary": "", "accent": ""}}, "proposed_typography": "", "proposed_style": "", "proposed_guideline_rules": [], "brand_proposal_rationale": ""}} (chỉ điền nếu brand_status là proposed, ngược lại để trống)
- "thumbnail_prompt": "Mô tả tiếng Việt tổng quan..."
- "image_prompt": "Prompt tiếng Anh cho AI vẽ ảnh..."
- "text_overlay": {{"title": "TIÊU ĐỀ VIẾT HOA", "subtitle": "Phụ đề", "badge": "Nhãn", "cta": "Nút bấm"}}
- "color_suggestion": {{"background_theme": "", "text_color": "", "accent_color": ""}}
- "composition": "Mô tả bố cục..."
- "emotion": "Cảm xúc..."
- "camera": "Góc máy..."
- "lighting": "Ánh sáng..."
- "style": "Phong cách..."
- "negative_prompt": "ugly, deformed..."
- "aspect_ratio": "{platform_cfg['aspect_ratio']}"

Chỉ trả về JSON thuần túy trong thẻ markdown ```json...```. Không giải thích gì thêm ngoài JSON.
"""

    @classmethod
    def generate(cls, workspace_id: int, article: str, audience: str, platform: str, api_key: str) -> dict:
        """Thực thi gọi Gemini sinh prompt thumbnail."""
        brand_ctx = cls.build_brand_context(workspace_id)
        prompt = cls.build_system_prompt(article, audience, platform, brand_ctx)
        
        raw_output = generate_with_gemini(prompt, api_key=api_key)
        try:
            clean = raw_output.strip()
            if "```json" in clean:
                clean = clean.split("```json")[1].split("```")[0].strip()
            elif "```" in clean:
                clean = clean.split("```")[1].split("```")[0].strip()
            return json.loads(clean)
        except Exception as e:
            logger.error(f"[ThumbnailGeneratorService] Lỗi parse JSON: {e}. Raw output: {raw_output}")
            return {"error": "Không thể phân tích JSON từ Gemini.", "raw": raw_output}
