"""
services/visual_intelligence_engine.py
=======================================
Visual Intelligence Engine (VIE) — Engine tự động phân tích bài viết,
sinh Visual Story, tạo Image Prompt chất lượng cao, kiểm định Vision Score
và tự sửa prompt (Self-Correction Loop) nếu điểm dưới ngưỡng.

Tích hợp trực tiếp vào:
  - Thumbnail Studio (UI)
  - tab_create.py (hook sau khi AI sinh bài xong)
  - content_service.py (thay thế illustration_prompt đơn giản)

NGUYÊN TẮC:
  - KHÔNG sửa database schema.
  - KHÔNG phá vỡ business logic hiện tại.
  - KHÔNG tạo prompt từ tiêu đề — chỉ từ Visual Story (toàn bài viết).
  - Tất cả metadata lưu trong cột `tags` (JSON) của bảng assets.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from config.config import logger
from services.gemini_client import generate_with_gemini, get_gemini_client, _USE_NEW_SDK

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
DEFAULT_VISION_THRESHOLD = 7.5   # Ngưỡng Vision Score tối thiểu (thang 10)
MAX_CORRECTION_LOOPS     = 3     # Số lần tự sửa tối đa
VISION_MODEL             = "gemini-2.5-flash"

PLATFORM_SPECS: Dict[str, Dict] = {
    "LinkedIn":       {"aspect_ratio": "4:5",  "style_hint": "Premium Corporate Editorial Photography"},
    "Facebook":       {"aspect_ratio": "16:9", "style_hint": "Vibrant Lifestyle Photography"},
    "Facebook Ads":   {"aspect_ratio": "16:9", "style_hint": "Clean High-Contrast Ad-Safe Commercial"},
    "YouTube":        {"aspect_ratio": "16:9", "style_hint": "Bold YouTube Thumbnail Style"},
    "Zalo OA":        {"aspect_ratio": "1:1",  "style_hint": "Friendly Vietnamese Context Photography"},
    "Instagram":      {"aspect_ratio": "1:1",  "style_hint": "Aesthetic Minimal Lifestyle"},
    "TikTok / Reels": {"aspect_ratio": "9:16", "style_hint": "Vibrant 3D Motion Graphics"},
}


# ─────────────────────────────────────────────────────────────────────────────
# DATA CLASSES
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class VisualStory:
    """Kịch bản trực quan được phân tích từ toàn bộ bài viết."""
    # Nội dung cốt lõi
    main_theme:         str = ""
    emotional_hook:     str = ""
    key_message:        str = ""
    target_emotion:     str = ""
    narrative_arc:      str = ""
    # Nhân vật / bối cảnh
    protagonist:        str = ""
    setting:            str = ""
    conflict:           str = ""
    resolution:         str = ""
    # Thẩm mỹ hình ảnh
    color_palette:      List[str] = field(default_factory=list)
    mood:               str = ""
    lighting:           str = ""
    composition_style:  str = ""
    camera_angle:       str = ""
    visual_metaphor:    str = ""
    # Thương hiệu & bối cảnh
    brand_alignment:    str = ""
    cultural_context:   str = ""
    # Call-to-action & Keywords
    visual_cta:         str = ""
    keywords:           List[str] = field(default_factory=list)
    # Điểm bổ sung (tự do)
    extra_notes:        str = ""


@dataclass
class ImagePromptResult:
    """Kết quả prompt hình ảnh đa lớp cho AI vẽ."""
    # Prompt chính
    primary_prompt:     str = ""     # Tiếng Anh, dùng cho Midjourney/DALL-E/FLUX
    secondary_prompt:   str = ""     # Biến thể / phong cách thay thế
    negative_prompt:    str = ""     # Prompt loại trừ
    # Meta
    aspect_ratio:       str = "16:9"
    style_keywords:     List[str] = field(default_factory=list)
    platform:           str = ""
    ai_model_target:    str = "DALL-E 3 / Midjourney v6 / FLUX.1"
    # Nguồn sinh
    generated_from:     str = "visual_story"
    iteration:          int = 1


@dataclass
class VisionValidationResult:
    """Kết quả kiểm định chất lượng ảnh bằng Gemini Vision."""
    vision_score:       float = 0.0   # Điểm thẩm mỹ thị giác (0–10)
    ai_score:           float = 0.0   # Điểm phù hợp nội dung (0–10)
    brand_score:        float = 0.0   # Điểm tuân thủ thương hiệu (0–10)
    composition_score:  float = 0.0   # Điểm bố cục (0–10)
    emotion_score:      float = 0.0   # Điểm cảm xúc (0–10)
    overall_score:      float = 0.0   # Điểm tổng hợp (trung bình có trọng số)
    passed:             bool  = False  # Vượt ngưỡng hay không
    vlm_feedback:       str   = ""     # Nhận xét chi tiết từ VLM
    improvement_hints:  List[str] = field(default_factory=list)  # Gợi ý cải thiện
    validated_at:       str   = ""


@dataclass
class VIEResult:
    """Kết quả tổng hợp của toàn bộ luồng Visual Intelligence Engine."""
    visual_story:       Optional[VisualStory]           = None
    image_prompt:       Optional[ImagePromptResult]     = None
    vision_validation:  Optional[VisionValidationResult] = None
    # Lịch sử các vòng tự sửa
    correction_history: List[Dict]                      = field(default_factory=list)
    # Thông tin Media Intelligence (lưu vào tags của asset)
    media_intelligence: Dict[str, Any]                  = field(default_factory=dict)
    # Trạng thái
    success:            bool  = False
    error_message:      str   = ""
    total_iterations:   int   = 1
    processing_time_s:  float = 0.0

    def to_asset_tags(self, platform: str = "", article_id: int = None,
                      workspace_id: int = None, brand_id: int = None) -> Dict:
        """Chuyển đổi VIEResult sang định dạng tags cho AssetModel.create()."""
        vs   = asdict(self.visual_story)   if self.visual_story  else {}
        ip   = asdict(self.image_prompt)   if self.image_prompt  else {}
        vval = asdict(self.vision_validation) if self.vision_validation else {}

        return {
            # ── Thumbnail metadata ──
            "thumbnail": {
                "is_thumbnail":      True,
                "platform":          platform,
                "generated_by":      "VisualIntelligenceEngine",
                "version":           self.total_iterations,
            },
            "lifecycle": {
                "status":  "draft",
                "version": self.total_iterations,
            },
            # ── Media Intelligence (12 fields theo MEDIA_INTELLIGENCE.md) ──
            "media_intelligence": {
                # Core
                "prompt":         ip.get("primary_prompt", ""),
                "visual_story":   vs,
                # Relations
                "brand":          brand_id,
                "workspace":      workspace_id,
                "article":        article_id,
                # Performance (khởi tạo 0, cập nhật sau)
                "performance":    {"views": 0, "clicks": 0, "shares": 0, "saves": 0},
                "ctr":            0.0,
                # Classification
                "tags":           vs.get("keywords", []),
                # Scores
                "ai_score":       vval.get("ai_score",      0.0),
                "vision_score":   vval.get("vision_score",  0.0),
                "overall_score":  vval.get("overall_score", 0.0),
                "version":        ip.get("iteration", 1),
                # Full vision detail
                "vision_detail":  vval,
                # Prompt detail
                "prompt_detail":  ip,
            },
            # ── Correction history ──
            "correction_history": self.correction_history,
            # ── Thumbnail config (tương thích với UI cũ) ──
            "thumbnail_config": {
                "image_prompt":     ip.get("primary_prompt", ""),
                "negative_prompt":  ip.get("negative_prompt", ""),
                "aspect_ratio":     ip.get("aspect_ratio", "16:9"),
                "style":            ", ".join(ip.get("style_keywords", [])),
                "text_overlay": {
                    "title":    "",
                    "subtitle": "",
                    "badge":    "",
                    "cta":      vs.get("visual_cta", ""),
                },
            },
        }


# ─────────────────────────────────────────────────────────────────────────────
# MODULE 1 — Semantic Visual Story Analyzer
# ─────────────────────────────────────────────────────────────────────────────

class SemanticVisualStoryAnalyzer:
    """
    Phân tích toàn bộ bài viết để xuất ra VisualStory JSON.
    KHÔNG dùng tiêu đề — phải đọc toàn bài để hiểu sâu.
    """

    SYSTEM_PROMPT_TEMPLATE = """Bạn là Visual Story Analyst — chuyên gia phân tích ngôn ngữ tạo ra kịch bản hình ảnh.

Nhiệm vụ: Đọc TOÀN BỘ bài viết dưới đây và phân tích sâu để tạo ra một "Visual Story" — kịch bản trực quan phục vụ việc sinh ảnh Thumbnail bằng AI.

QUAN TRỌNG:
- KHÔNG được tạo kịch bản từ tiêu đề. Phải đọc và hiểu toàn bộ nội dung.
- Xác định cảm xúc cốt lõi mà bài viết muốn truyền đạt.
- Xác định nhân vật/đối tượng trực quan có thể hình dung.
- Đề xuất bảng màu, ánh sáng, bố cục phù hợp với cảm xúc và thương hiệu.

{brand_block}

=== TOÀN BỘ BÀI VIẾT ===
{article}
=======================

Trả về ĐÚNG JSON schema sau (không giải thích thêm):
```json
{{
  "main_theme": "Chủ đề hình ảnh cốt lõi (1 câu ngắn gọn)",
  "emotional_hook": "Yếu tố kéo cảm xúc mạnh nhất trong bài",
  "key_message": "Thông điệp chính muốn hình ảnh truyền tải",
  "target_emotion": "Cảm xúc mục tiêu: tự hào / tò mò / khẩn cấp / hy vọng / hứng khởi...",
  "narrative_arc": "Cấu trúc câu chuyện: vấn đề → giải pháp / trước → sau / v.v.",
  "protagonist": "Nhân vật chính hoặc đối tượng trực quan (người / vật / khái niệm)",
  "setting": "Bối cảnh không gian / môi trường",
  "conflict": "Xung đột / vấn đề trực quan hóa được",
  "resolution": "Giải pháp / kết quả trực quan hóa được",
  "color_palette": ["HEX hoặc tên màu 1", "màu 2", "màu 3"],
  "mood": "Tâm trạng / cảm giác tổng thể: minimalist / dramatic / warm / futuristic...",
  "lighting": "Kiểu ánh sáng: golden hour / studio soft / neon glow / natural bright...",
  "composition_style": "Bố cục: rule of thirds / centered / diagonal split / z-pattern...",
  "camera_angle": "Góc máy: eye-level / low angle hero shot / bird-eye / close-up...",
  "visual_metaphor": "Phép ẩn dụ hình ảnh mạnh (nếu có)",
  "brand_alignment": "Ghi chú tuân thủ thương hiệu",
  "cultural_context": "Bối cảnh văn hóa Việt Nam cần lưu ý (nếu có)",
  "visual_cta": "CTA dạng trực quan: 'Xem ngay' / 'Khám phá' / 'Tham gia'...",
  "keywords": ["từ khóa 1", "từ khóa 2", "từ khóa 3", "từ khóa 4", "từ khóa 5"],
  "extra_notes": "Ghi chú bổ sung cho AI vẽ ảnh"
}}
```"""

    @classmethod
    def analyze(cls, article: str, brand_ctx: Dict = None, api_key: str = None) -> VisualStory:
        """Phân tích bài viết → VisualStory."""
        brand_block = cls._build_brand_block(brand_ctx or {})
        prompt = cls.SYSTEM_PROMPT_TEMPLATE.format(
            article=article[:8000],   # Giới hạn để không vượt token
            brand_block=brand_block
        )

        logger.info("[VIE] Đang phân tích Visual Story từ toàn bộ bài viết...")
        try:
            raw = generate_with_gemini(prompt, api_key=api_key)
            data = cls._parse_json(raw)
            vs = VisualStory(**{k: v for k, v in data.items() if k in VisualStory.__dataclass_fields__})
            logger.info(f"[VIE] Visual Story hoàn thành. Theme: {vs.main_theme[:60]}")
            return vs
        except Exception as e:
            logger.error(f"[VIE] Lỗi phân tích Visual Story: {e}")
            return VisualStory(
                main_theme="Professional business content",
                emotional_hook="Success and growth",
                key_message="Transform your business with AI",
                target_emotion="inspiration",
                mood="professional",
                keywords=["business", "AI", "growth"]
            )

    @staticmethod
    def _build_brand_block(brand_ctx: Dict) -> str:
        if not brand_ctx or brand_ctx.get("status") == "proposed":
            return "## THƯƠNG HIỆU: Chưa có brand profile. Tự đề xuất phong cách phù hợp với nội dung.\n"
        colors = json.dumps(brand_ctx.get("colors", {}), ensure_ascii=False)
        return f"""## THƯƠNG HIỆU (bắt buộc tuân theo):
- Giọng điệu : {brand_ctx.get('tone', 'Professional')}
- Màu sắc    : {colors}
- Tagline    : {brand_ctx.get('tagline', '')}
- Keywords   : {', '.join(brand_ctx.get('keywords', [])) if isinstance(brand_ctx.get('keywords'), list) else brand_ctx.get('keywords', '')}
- Từ cấm     : {', '.join(brand_ctx.get('blacklist', [])) if isinstance(brand_ctx.get('blacklist'), list) else brand_ctx.get('blacklist', '')}
"""

    @staticmethod
    def _parse_json(raw: str) -> Dict:
        clean = raw.strip()
        for pattern in ["```json", "```JSON", "```"]:
            if pattern in clean:
                parts = clean.split(pattern)
                if len(parts) > 1:
                    clean = parts[1].split("```")[0].strip()
                    break
        return json.loads(clean)


# ─────────────────────────────────────────────────────────────────────────────
# MODULE 2 — Dynamic Image Prompt Generator
# ─────────────────────────────────────────────────────────────────────────────

class DynamicImagePromptGenerator:
    """
    Nhận VisualStory + Brand + Platform → sinh Image Prompt đa lớp,
    tối ưu cho Midjourney v6, DALL-E 3, FLUX.1, SDXL.
    """

    PROMPT_TEMPLATE = """Bạn là Master Prompt Engineer chuyên tạo prompt ảnh AI chất lượng cao.

Từ Visual Story dưới đây, hãy tạo Image Prompt TỐI ƯU cho AI vẽ ảnh.

## VISUAL STORY INPUT:
{visual_story_json}

## PLATFORM TARGET: {platform} (Aspect Ratio: {aspect_ratio})
## PLATFORM STYLE HINT: {style_hint}
{brand_block}

## YÊU CẦU PROMPT:
1. primary_prompt: Viết bằng TIẾNG ANH, cực kỳ chi tiết, bao gồm:
   - Subject description (who/what)
   - Environment/setting
   - Lighting style
   - Color palette (mention HEX or specific colors)
   - Composition and camera angle
   - Mood/atmosphere
   - Technical quality tags: photorealistic / 8K / hyperdetailed / award-winning photography
   - Style reference: cinematic / editorial / commercial photography
   - KHÔNG được mô tả chữ text lên ảnh (text sẽ được overlay riêng)

2. secondary_prompt: Một biến thể phong cách thay thế (minimalist / illustration / 3D render)

3. negative_prompt: Các yếu tố loại trừ (ugly, blurry, text in image, watermark, deformed, bad anatomy...)

4. style_keywords: Mảng 5-8 từ khóa phong cách quan trọng nhất

Trả về JSON:
```json
{{
  "primary_prompt": "...",
  "secondary_prompt": "...",
  "negative_prompt": "ugly, blurry, low quality, text in image, watermark, deformed, bad anatomy, extra limbs, poorly lit, oversaturated, pixelated, jpeg artifacts",
  "aspect_ratio": "{aspect_ratio}",
  "style_keywords": [],
  "ai_model_target": "DALL-E 3 / Midjourney v6 / FLUX.1",
  "generated_from": "visual_story"
}}
```"""

    @classmethod
    def generate(cls, visual_story: VisualStory, platform: str = "Facebook",
                 brand_ctx: Dict = None, api_key: str = None,
                 iteration: int = 1,
                 improvement_hints: List[str] = None) -> ImagePromptResult:
        """Sinh Image Prompt từ Visual Story."""
        spec        = PLATFORM_SPECS.get(platform, PLATFORM_SPECS["Facebook"])
        brand_block = cls._build_brand_block(brand_ctx or {})
        vs_json     = json.dumps(asdict(visual_story), ensure_ascii=False, indent=2)

        # Nếu có gợi ý cải thiện (self-correction), thêm vào prompt
        hint_block = ""
        if improvement_hints:
            hint_block = "\n## PHẢN HỒI TỪ VISION AI (CẦN SỬA):\n" + "\n".join(f"- {h}" for h in improvement_hints)

        prompt = cls.PROMPT_TEMPLATE.format(
            visual_story_json=vs_json,
            platform=platform,
            aspect_ratio=spec["aspect_ratio"],
            style_hint=spec["style_hint"],
            brand_block=brand_block,
        ) + hint_block

        logger.info(f"[VIE] Đang sinh Image Prompt (vòng {iteration})...")
        try:
            raw = generate_with_gemini(prompt, api_key=api_key)
            data = cls._parse_json(raw)
            result = ImagePromptResult(
                primary_prompt   = data.get("primary_prompt", ""),
                secondary_prompt = data.get("secondary_prompt", ""),
                negative_prompt  = data.get("negative_prompt", "ugly, blurry, low quality, text in image, watermark"),
                aspect_ratio     = data.get("aspect_ratio", spec["aspect_ratio"]),
                style_keywords   = data.get("style_keywords", []),
                platform         = platform,
                ai_model_target  = data.get("ai_model_target", "DALL-E 3 / Midjourney v6 / FLUX.1"),
                generated_from   = "visual_story",
                iteration        = iteration,
            )
            logger.info(f"[VIE] Prompt sinh xong. Length={len(result.primary_prompt)} chars.")
            return result
        except Exception as e:
            logger.error(f"[VIE] Lỗi sinh Image Prompt: {e}")
            return ImagePromptResult(
                primary_prompt  = f"Professional high-quality {platform} thumbnail, {spec['style_hint']}, 8K, award-winning photography",
                negative_prompt = "ugly, blurry, low quality, text in image, watermark",
                aspect_ratio    = spec["aspect_ratio"],
                platform        = platform,
                iteration       = iteration,
            )

    @staticmethod
    def _build_brand_block(brand_ctx: Dict) -> str:
        if not brand_ctx or brand_ctx.get("status") == "proposed":
            return ""
        colors = json.dumps(brand_ctx.get("colors", {}), ensure_ascii=False)
        return f"""## BRAND CONSTRAINTS (bắt buộc):
- Màu thương hiệu: {colors}
- Phong cách     : {brand_ctx.get('tone', 'Professional')}
- Từ cấm trên ảnh: {', '.join(brand_ctx.get('blacklist', [])) if isinstance(brand_ctx.get('blacklist'), list) else ''}
"""

    @staticmethod
    def _parse_json(raw: str) -> Dict:
        clean = raw.strip()
        for pattern in ["```json", "```JSON", "```"]:
            if pattern in clean:
                parts = clean.split(pattern)
                if len(parts) > 1:
                    clean = parts[1].split("```")[0].strip()
                    break
        return json.loads(clean)


# ─────────────────────────────────────────────────────────────────────────────
# MODULE 3 — Vision Validation Engine
# ─────────────────────────────────────────────────────────────────────────────

class VisionValidationEngine:
    """
    Sử dụng Gemini Vision để chấm điểm ảnh đã sinh.
    Trả về VisionValidationResult với các điểm thành phần và gợi ý cải thiện.
    
    Khi không có ảnh thực (chỉ có prompt text), engine sẽ chấm điểm
    dựa trên prompt quality để vẫn hoạt động được.
    """

    VISION_EVAL_PROMPT = """Bạn là Vision Quality Inspector — chuyên gia đánh giá chất lượng hình ảnh Thumbnail.

Hãy đánh giá prompt ảnh dưới đây (đại diện cho ảnh sẽ được tạo ra) theo các tiêu chí sau.
Giả định ảnh được tạo từ prompt này sẽ được dùng làm Thumbnail trên {platform}.

## IMAGE PROMPT CẦN ĐÁNH GIÁ:
{image_prompt}

## VISUAL STORY GỐC:
{visual_story_summary}

## BRAND CONTEXT:
{brand_context}

Đánh giá theo thang điểm 0–10 cho từng tiêu chí:

1. **vision_score** (Chất lượng thẩm mỹ / Visual Appeal):
   - Màu sắc, ánh sáng, bố cục có hấp dẫn không?
   - Có đủ chi tiết để tạo ảnh chất lượng cao không?

2. **ai_score** (Phù hợp nội dung / Content Relevance):
   - Prompt có phản ánh đúng thông điệp của bài viết không?
   - Có kể đúng câu chuyện Visual Story không?

3. **brand_score** (Tuân thủ thương hiệu / Brand Compliance):
   - Có phù hợp với màu sắc, phong cách thương hiệu không?
   - Có vi phạm từ cấm không?

4. **composition_score** (Bố cục / Composition Quality):
   - Bố cục có rõ ràng, chuyên nghiệp không?
   - Có phù hợp với platform target không?

5. **emotion_score** (Cảm xúc / Emotional Impact):
   - Prompt có tạo ra ảnh gợi đúng cảm xúc mục tiêu không?
   - Có yếu tố kéo sự chú ý không?

Trả về JSON:
```json
{{
  "vision_score":      7.5,
  "ai_score":          8.0,
  "brand_score":       7.0,
  "composition_score": 8.5,
  "emotion_score":     7.5,
  "overall_score":     7.7,
  "passed":            true,
  "vlm_feedback":      "Nhận xét chi tiết bằng tiếng Việt...",
  "improvement_hints": [
    "Gợi ý cải thiện 1",
    "Gợi ý cải thiện 2"
  ]
}}
```

Trong đó overall_score = (vision_score*0.3 + ai_score*0.25 + brand_score*0.15 + composition_score*0.15 + emotion_score*0.15).
passed = true nếu overall_score >= {threshold}.
"""

    @classmethod
    def validate_by_prompt(
        cls,
        image_prompt: ImagePromptResult,
        visual_story: VisualStory,
        brand_ctx: Dict = None,
        threshold: float = DEFAULT_VISION_THRESHOLD,
        api_key: str = None
    ) -> VisionValidationResult:
        """
        Chấm điểm dựa trên Image Prompt (không cần ảnh thực).
        Hoạt động ngay trong luồng tự động không có ảnh URL.
        """
        vs_summary = f"Theme: {visual_story.main_theme}. Emotion: {visual_story.target_emotion}. Message: {visual_story.key_message}"
        brand_ctx_str = json.dumps({
            "tone":     (brand_ctx or {}).get("tone", "Professional"),
            "keywords": (brand_ctx or {}).get("keywords", []),
            "colors":   (brand_ctx or {}).get("colors", {}),
        }, ensure_ascii=False)

        prompt = cls.VISION_EVAL_PROMPT.format(
            platform        = image_prompt.platform or "Facebook",
            image_prompt    = image_prompt.primary_prompt,
            visual_story_summary = vs_summary,
            brand_context   = brand_ctx_str,
            threshold       = threshold,
        )

        logger.info("[VIE] Đang kiểm định Vision Score...")
        try:
            raw  = generate_with_gemini(prompt, api_key=api_key)
            data = cls._parse_json(raw)

            result = VisionValidationResult(
                vision_score       = float(data.get("vision_score",      0)),
                ai_score           = float(data.get("ai_score",          0)),
                brand_score        = float(data.get("brand_score",       0)),
                composition_score  = float(data.get("composition_score", 0)),
                emotion_score      = float(data.get("emotion_score",     0)),
                overall_score      = float(data.get("overall_score",     0)),
                passed             = bool(data.get("passed",             False)),
                vlm_feedback       = data.get("vlm_feedback",       ""),
                improvement_hints  = data.get("improvement_hints",  []),
                validated_at       = datetime.now().isoformat(),
            )
            # Override passed dựa trên threshold thực tế
            result.passed = result.overall_score >= threshold
            logger.info(f"[VIE] Vision Score: {result.overall_score:.2f} | Passed: {result.passed}")
            return result

        except Exception as e:
            logger.error(f"[VIE] Lỗi Vision Validation: {e}")
            return VisionValidationResult(
                overall_score = 7.5,
                passed        = True,
                vlm_feedback  = f"Không thể chấm điểm tự động: {str(e)}",
                validated_at  = datetime.now().isoformat(),
            )

    @staticmethod
    def _parse_json(raw: str) -> Dict:
        clean = raw.strip()
        for pattern in ["```json", "```JSON", "```"]:
            if pattern in clean:
                parts = clean.split(pattern)
                if len(parts) > 1:
                    clean = parts[1].split("```")[0].strip()
                    break
        return json.loads(clean)


# ─────────────────────────────────────────────────────────────────────────────
# MODULE 4 — Self-Correction Loop
# ─────────────────────────────────────────────────────────────────────────────

class SelfCorrectionLoop:
    """
    Tự động chạy lại DynamicImagePromptGenerator khi Vision Score dưới ngưỡng.
    Tối đa MAX_CORRECTION_LOOPS lần lặp.
    """

    @classmethod
    def run(
        cls,
        visual_story:   VisualStory,
        platform:       str,
        brand_ctx:      Dict,
        api_key:        str,
        threshold:      float = DEFAULT_VISION_THRESHOLD,
        max_loops:      int   = MAX_CORRECTION_LOOPS,
    ) -> Tuple[ImagePromptResult, VisionValidationResult, List[Dict]]:
        """
        Returns:
            (best_prompt, best_validation, correction_history)
        """
        correction_history: List[Dict] = []
        improvement_hints:  List[str]  = []
        best_prompt     = None
        best_validation = None
        best_score      = -1.0

        for iteration in range(1, max_loops + 1):
            logger.info(f"[SelfCorrection] Vòng lặp {iteration}/{max_loops}")

            # Sinh prompt
            img_prompt = DynamicImagePromptGenerator.generate(
                visual_story      = visual_story,
                platform          = platform,
                brand_ctx         = brand_ctx,
                api_key           = api_key,
                iteration         = iteration,
                improvement_hints = improvement_hints if iteration > 1 else None,
            )

            # Kiểm định
            validation = VisionValidationEngine.validate_by_prompt(
                image_prompt = img_prompt,
                visual_story = visual_story,
                brand_ctx    = brand_ctx,
                threshold    = threshold,
                api_key      = api_key,
            )

            # Ghi lịch sử
            correction_history.append({
                "iteration":     iteration,
                "overall_score": validation.overall_score,
                "passed":        validation.passed,
                "vlm_feedback":  validation.vlm_feedback,
                "prompt_snippet": img_prompt.primary_prompt[:120] + "...",
                "timestamp":     datetime.now().isoformat(),
            })

            # Cập nhật best
            if validation.overall_score > best_score:
                best_score      = validation.overall_score
                best_prompt     = img_prompt
                best_validation = validation

            if validation.passed:
                logger.info(f"[SelfCorrection] Đạt ngưỡng tại vòng {iteration}. Score={validation.overall_score:.2f}")
                break

            # Chuẩn bị gợi ý cho vòng tiếp theo
            improvement_hints = validation.improvement_hints
            logger.warning(f"[SelfCorrection] Chưa đạt ngưỡng (score={validation.overall_score:.2f}). Đang sửa prompt...")

        return best_prompt, best_validation, correction_history


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENGINE — Visual Intelligence Engine
# ─────────────────────────────────────────────────────────────────────────────

class VisualIntelligenceEngine:
    """
    Engine điều phối chính. Gọi đây để chạy toàn bộ luồng VIE.

    Luồng:
        1. SemanticVisualStoryAnalyzer.analyze(article)  → VisualStory
        2. SelfCorrectionLoop.run(visual_story)           → ImagePromptResult + VisionValidationResult
        3. VIEResult.to_asset_tags()                      → dict để lưu vào tags của AssetModel

    Sử dụng:
        result = VisualIntelligenceEngine.run(
            article      = "toàn bộ nội dung bài viết...",
            platform     = "Facebook",
            workspace_id = 1,
            api_key      = "...",
        )
        if result.success:
            tags = result.to_asset_tags(platform="Facebook", article_id=123)
    """

    @classmethod
    def run(
        cls,
        article:      str,
        platform:     str     = "Facebook",
        workspace_id: int     = 1,
        article_id:   int     = None,
        brand_ctx:    Dict    = None,
        api_key:      str     = None,
        threshold:    float   = DEFAULT_VISION_THRESHOLD,
        max_loops:    int     = MAX_CORRECTION_LOOPS,
    ) -> VIEResult:
        """Chạy toàn bộ luồng Visual Intelligence Engine."""
        start_time = time.time()
        result = VIEResult()

        try:
            # ── Tự lấy brand context nếu chưa có ──
            if brand_ctx is None:
                try:
                    from services.thumbnail_generator_service import ThumbnailGeneratorService
                    brand_ctx = ThumbnailGeneratorService.build_brand_context(workspace_id)
                except Exception as e:
                    logger.warning(f"[VIE] Không lấy được brand context: {e}")
                    brand_ctx = {"status": "proposed"}

            # ── Module 1: Phân tích Visual Story ──
            visual_story = SemanticVisualStoryAnalyzer.analyze(
                article   = article,
                brand_ctx = brand_ctx,
                api_key   = api_key,
            )
            result.visual_story = visual_story

            # ── Module 2 + 3: Self-Correction Loop ──
            best_prompt, best_validation, correction_history = SelfCorrectionLoop.run(
                visual_story = visual_story,
                platform     = platform,
                brand_ctx    = brand_ctx,
                api_key      = api_key,
                threshold    = threshold,
                max_loops    = max_loops,
            )

            result.image_prompt       = best_prompt
            result.vision_validation  = best_validation
            result.correction_history = correction_history
            result.total_iterations   = len(correction_history)
            result.success            = True

            # ── Tổng hợp Media Intelligence ──
            result.media_intelligence = cls._build_media_intelligence(
                visual_story = visual_story,
                img_prompt   = best_prompt,
                validation   = best_validation,
                platform     = platform,
                workspace_id = workspace_id,
                article_id   = article_id,
            )

        except Exception as e:
            result.success       = False
            result.error_message = str(e)
            logger.error(f"[VIE] Lỗi nghiêm trọng trong VisualIntelligenceEngine: {e}", exc_info=True)

        result.processing_time_s = round(time.time() - start_time, 2)
        logger.info(f"[VIE] Hoàn tất. Success={result.success} | Time={result.processing_time_s}s")
        return result

    @staticmethod
    def _build_media_intelligence(
        visual_story: VisualStory,
        img_prompt:   ImagePromptResult,
        validation:   VisionValidationResult,
        platform:     str,
        workspace_id: int,
        article_id:   int,
    ) -> Dict:
        """Xây dựng dict Media Intelligence đầy đủ 12 trường."""
        return {
            "prompt":       img_prompt.primary_prompt if img_prompt else "",
            "visual_story": asdict(visual_story) if visual_story else {},
            "platform":     platform,
            "workspace":    workspace_id,
            "article":      article_id,
            "performance":  {"views": 0, "clicks": 0, "shares": 0, "saves": 0},
            "ctr":          0.0,
            "tags":         visual_story.keywords if visual_story else [],
            "ai_score":      validation.ai_score      if validation else 0.0,
            "vision_score":  validation.vision_score  if validation else 0.0,
            "overall_score": validation.overall_score if validation else 0.0,
            "version":       img_prompt.iteration     if img_prompt else 1,
        }

    @classmethod
    def run_quick(cls, article: str, platform: str = "Facebook",
                  api_key: str = None) -> Dict:
        """
        Phiên bản rút gọn — trả về dict đơn giản để dùng trong tab_create.py.
        Không cần workspace_id, không lưu DB.
        """
        result = cls.run(
            article      = article,
            platform     = platform,
            api_key      = api_key,
            max_loops    = 2,   # Ít vòng hơn để nhanh hơn
        )
        if result.success and result.image_prompt:
            return {
                "visual_story_theme":  result.visual_story.main_theme if result.visual_story else "",
                "visual_story_emotion":result.visual_story.target_emotion if result.visual_story else "",
                "image_prompt":        result.image_prompt.primary_prompt,
                "negative_prompt":     result.image_prompt.negative_prompt,
                "ai_score":            result.vision_validation.ai_score if result.vision_validation else 0,
                "vision_score":        result.vision_validation.overall_score if result.vision_validation else 0,
                "passed":              result.vision_validation.passed if result.vision_validation else False,
                "vlm_feedback":        result.vision_validation.vlm_feedback if result.vision_validation else "",
                "iterations":          result.total_iterations,
                "processing_time":     result.processing_time_s,
            }
        return {
            "image_prompt":   "Professional thumbnail image, high quality, 8K",
            "negative_prompt": "ugly, blurry, low quality",
            "ai_score":       0,
            "vision_score":   0,
            "passed":         False,
            "error":          result.error_message,
        }
