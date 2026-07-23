"""
tests/test_visual_intelligence_engine.py
=========================================
Unit Tests & Integration Tests cho Visual Intelligence Engine (VIE).

Coverage:
  - DataClass khởi tạo & serialization
  - SemanticVisualStoryAnalyzer (mock Gemini)
  - DynamicImagePromptGenerator (mock Gemini)
  - VisionValidationEngine (mock Gemini)
  - SelfCorrectionLoop (mock Gemini)
  - VIEResult.to_asset_tags() — Media Intelligence 12 fields
  - VisualIntelligenceEngine.run_quick() (mock Gemini)
  - JSON parsing & error fallback
"""

import unittest
import sys
import os
import json
from unittest.mock import patch, MagicMock
from dataclasses import asdict

# Thêm đường dẫn dự án
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.visual_intelligence_engine import (
    VisualStory,
    ImagePromptResult,
    VisionValidationResult,
    VIEResult,
    SemanticVisualStoryAnalyzer,
    DynamicImagePromptGenerator,
    VisionValidationEngine,
    SelfCorrectionLoop,
    VisualIntelligenceEngine,
    PLATFORM_SPECS,
    DEFAULT_VISION_THRESHOLD,
    MAX_CORRECTION_LOOPS,
)


# ─────────────────────────────────────────────────────────────────────────────
# SAMPLE DATA
# ─────────────────────────────────────────────────────────────────────────────

SAMPLE_ARTICLE = """
Trong thế giới kinh doanh hiện đại, AI Agent đang thay đổi hoàn toàn cách các doanh nghiệp
vận hành và tiếp cận khách hàng. Không còn là tương lai xa xôi, AI Agent đã trở thành công cụ
thiết yếu giúp tự động hóa quy trình, tối ưu chi phí và tăng trưởng doanh thu.

Câu chuyện thực tế: Một startup thương mại điện tử tại TP.HCM đã áp dụng AI Agent vào quy trình
chăm sóc khách hàng, kết quả là tỷ lệ phản hồi tăng 400%, chi phí nhân sự giảm 60% trong 3 tháng.

Không chỉ vậy, AI Agent còn giúp phân tích dữ liệu khách hàng theo thời gian thực, đề xuất
chiến lược marketing cá nhân hóa và dự đoán xu hướng mua sắm với độ chính xác 87%.

Tuy nhiên, nhiều doanh nghiệp vẫn chưa biết bắt đầu từ đâu. Đây chính là vấn đề mà chúng tôi
muốn giải quyết hôm nay — hướng dẫn từng bước để triển khai AI Agent hiệu quả mà không cần
đội ngũ kỹ thuật lớn.

Kết quả mong đợi: Sau 30 ngày áp dụng, doanh nghiệp của bạn sẽ tiết kiệm được 20 giờ/tuần
cho công việc thủ công và tăng tỷ lệ chuyển đổi lên ít nhất 150%.
"""

SAMPLE_VISUAL_STORY_JSON = {
    "main_theme": "AI Agent transforming Vietnamese businesses",
    "emotional_hook": "From struggling to thriving with AI automation",
    "key_message": "AI Agent is accessible and delivers measurable ROI in 30 days",
    "target_emotion": "inspiration",
    "narrative_arc": "problem → AI solution → success story",
    "protagonist": "Vietnamese SME business owner",
    "setting": "Modern office in Ho Chi Minh City",
    "conflict": "Manual processes wasting time and money",
    "resolution": "AI Agent automates everything, saving 20 hours/week",
    "color_palette": ["#0f172a", "#2563eb", "#fbbf24"],
    "mood": "professional and inspiring",
    "lighting": "studio soft light with warm accent",
    "composition_style": "rule of thirds with dynamic diagonal",
    "camera_angle": "low angle hero shot",
    "visual_metaphor": "Rocket launching from laptop screen",
    "brand_alignment": "Professional, trustworthy, modern",
    "cultural_context": "Vietnamese business context, TP.HCM setting",
    "visual_cta": "Khám phá ngay",
    "keywords": ["AI Agent", "automation", "ROI", "business growth", "Vietnam"],
    "extra_notes": "Show data visualization elements, upward trend arrows"
}

SAMPLE_IMAGE_PROMPT_JSON = {
    "primary_prompt": "Vietnamese entrepreneur in modern office, confident smile, laptop showing AI dashboard, dynamic upward chart on screen, professional business attire, golden hour lighting through floor-to-ceiling windows, rule of thirds composition, photorealistic, 8K, award-winning commercial photography, shallow depth of field, vibrant colors",
    "secondary_prompt": "Minimalist 3D render of rocket launching from digital grid, blue and gold color scheme, tech startup aesthetic, clean white background",
    "negative_prompt": "ugly, blurry, low quality, text in image, watermark, deformed, bad anatomy, extra limbs, poorly lit, oversaturated, pixelated, jpeg artifacts",
    "aspect_ratio": "16:9",
    "style_keywords": ["commercial photography", "editorial", "cinematic", "8K", "professional", "dynamic"],
    "ai_model_target": "DALL-E 3 / Midjourney v6 / FLUX.1",
    "generated_from": "visual_story"
}

SAMPLE_VISION_RESULT_JSON = {
    "vision_score": 8.5,
    "ai_score": 8.8,
    "brand_score": 7.5,
    "composition_score": 8.0,
    "emotion_score": 8.2,
    "overall_score": 8.3,
    "passed": True,
    "vlm_feedback": "Prompt mô tả rõ ràng nhân vật và bối cảnh phù hợp với thị trường Việt Nam. Ánh sáng vàng và cửa kính tạo cảm giác thành công. Bố cục rule of thirds mạnh.",
    "improvement_hints": []
}

SAMPLE_BRAND_CTX = {
    "status": "applied",
    "tone": "Professional & Trustworthy",
    "colors": {"primary": "#0f172a", "secondary": "#2563eb", "accent": "#fbbf24"},
    "logo_url": "https://example.com/logo.png",
    "tagline": "AI cho mọi doanh nghiệp",
    "guidelines": "Sử dụng tông màu Navy và Gold",
    "blacklist": ["rẻ tiền", "chất lượng thấp"],
    "keywords": ["AI", "tự động hóa", "hiệu quả"],
    "vision": "Dẫn đầu chuyển đổi số tại Việt Nam",
    "mission": "Giúp SME Việt Nam tăng trưởng với AI",
    "cta": "Đăng ký dùng thử miễn phí →",
}


# ─────────────────────────────────────────────────────────────────────────────
# TEST CLASS 1: DataClasses
# ─────────────────────────────────────────────────────────────────────────────

class TestVIEDataClasses(unittest.TestCase):
    """Kiểm tra khởi tạo và serialization của các dataclass VIE."""

    def test_visual_story_defaults(self):
        """VisualStory khởi tạo với giá trị mặc định."""
        vs = VisualStory()
        self.assertEqual(vs.main_theme, "")
        self.assertEqual(vs.keywords, [])
        self.assertEqual(vs.color_palette, [])

    def test_visual_story_full(self):
        """VisualStory nhận đầy đủ dữ liệu."""
        vs = VisualStory(
            main_theme="AI transforms business",
            target_emotion="inspiration",
            keywords=["AI", "growth"],
            color_palette=["#0f172a", "#2563eb"]
        )
        self.assertEqual(vs.main_theme, "AI transforms business")
        self.assertEqual(len(vs.keywords), 2)
        self.assertEqual(len(vs.color_palette), 2)

    def test_visual_story_asdict(self):
        """VisualStory chuyển sang dict đúng các key."""
        vs = VisualStory(main_theme="test", mood="professional")
        d = asdict(vs)
        expected_keys = [
            "main_theme", "emotional_hook", "key_message", "target_emotion",
            "narrative_arc", "protagonist", "setting", "conflict", "resolution",
            "color_palette", "mood", "lighting", "composition_style", "camera_angle",
            "visual_metaphor", "brand_alignment", "cultural_context", "visual_cta",
            "keywords", "extra_notes"
        ]
        for key in expected_keys:
            self.assertIn(key, d, f"Missing key in VisualStory dict: {key}")

    def test_image_prompt_result_defaults(self):
        """ImagePromptResult khởi tạo với giá trị mặc định đúng."""
        ip = ImagePromptResult()
        self.assertEqual(ip.aspect_ratio, "16:9")
        self.assertEqual(ip.generated_from, "visual_story")
        self.assertEqual(ip.iteration, 1)
        self.assertEqual(ip.style_keywords, [])

    def test_vision_validation_result(self):
        """VisionValidationResult tính passed đúng."""
        vval = VisionValidationResult(overall_score=8.5, passed=True)
        self.assertTrue(vval.passed)
        self.assertEqual(vval.overall_score, 8.5)

    def test_vie_result_to_asset_tags_structure(self):
        """VIEResult.to_asset_tags() trả về đúng 5 key cấp cao nhất."""
        vs   = VisualStory(**{k: v for k, v in SAMPLE_VISUAL_STORY_JSON.items()
                              if k in VisualStory.__dataclass_fields__})
        ip   = ImagePromptResult(**{k: v for k, v in SAMPLE_IMAGE_PROMPT_JSON.items()
                                    if k in ImagePromptResult.__dataclass_fields__})
        vval = VisionValidationResult(**{k: v for k, v in SAMPLE_VISION_RESULT_JSON.items()
                                         if k in VisionValidationResult.__dataclass_fields__})

        result = VIEResult(visual_story=vs, image_prompt=ip, vision_validation=vval, success=True)
        tags = result.to_asset_tags(platform="Facebook", workspace_id=1, article_id=42)

        # 5 key cấp cao
        for key in ["thumbnail", "lifecycle", "media_intelligence", "correction_history", "thumbnail_config"]:
            self.assertIn(key, tags, f"Missing top-level tag key: {key}")

    def test_vie_result_media_intelligence_12_fields(self):
        """to_asset_tags() phải có đầy đủ 12 fields theo MEDIA_INTELLIGENCE spec."""
        vs = VisualStory(
            main_theme="Test", target_emotion="inspiration",
            key_message="Test message", keywords=["k1", "k2"]
        )
        ip = ImagePromptResult(
            primary_prompt="Test prompt", platform="LinkedIn",
            aspect_ratio="4:5", iteration=2
        )
        vval = VisionValidationResult(
            vision_score=8.5, ai_score=8.8, brand_score=7.5,
            composition_score=8.0, emotion_score=8.2, overall_score=8.3, passed=True
        )
        result = VIEResult(visual_story=vs, image_prompt=ip, vision_validation=vval, success=True)
        tags = result.to_asset_tags(platform="LinkedIn", workspace_id=2, article_id=10, brand_id=5)

        mi = tags["media_intelligence"]
        required_fields = ["prompt", "visual_story", "brand", "workspace", "article",
                           "performance", "ctr", "tags", "ai_score", "vision_score",
                           "overall_score", "version"]
        for field in required_fields:
            self.assertIn(field, mi, f"Media Intelligence thiếu field: {field}")

        # Kiểm tra giá trị cụ thể
        self.assertEqual(mi["workspace"], 2)
        self.assertEqual(mi["article"], 10)
        self.assertEqual(mi["brand"], 5)
        self.assertAlmostEqual(mi["ai_score"], 8.8, places=1)
        self.assertAlmostEqual(mi["vision_score"], 8.5, places=1)
        self.assertEqual(mi["ctr"], 0.0)
        self.assertEqual(mi["performance"]["views"], 0)

    def test_thumbnail_config_text_overlay_structure(self):
        """thumbnail_config phải có text_overlay với 4 keys."""
        vs = VisualStory(visual_cta="Khám phá ngay")
        ip = ImagePromptResult(primary_prompt="test", negative_prompt="bad", aspect_ratio="1:1")
        vval = VisionValidationResult(overall_score=8.0, passed=True)
        result = VIEResult(visual_story=vs, image_prompt=ip, vision_validation=vval, success=True)
        tags = result.to_asset_tags(platform="Instagram")

        overlay = tags["thumbnail_config"].get("text_overlay", {})
        for key in ["title", "subtitle", "badge", "cta"]:
            self.assertIn(key, overlay, f"text_overlay thiếu key: {key}")
        self.assertEqual(overlay["cta"], "Khám phá ngay")


# ─────────────────────────────────────────────────────────────────────────────
# TEST CLASS 2: JSON Parsing Utilities
# ─────────────────────────────────────────────────────────────────────────────

class TestJSONParsing(unittest.TestCase):
    """Kiểm tra các hàm parse JSON từ output của Gemini."""

    def test_parse_clean_json(self):
        """Parse JSON thuần túy không có markdown wrapper."""
        raw = json.dumps(SAMPLE_VISUAL_STORY_JSON)
        result = SemanticVisualStoryAnalyzer._parse_json(raw)
        self.assertEqual(result["main_theme"], SAMPLE_VISUAL_STORY_JSON["main_theme"])

    def test_parse_json_with_markdown_wrapper(self):
        """Parse JSON bọc trong ```json ... ``` block."""
        raw = "```json\n" + json.dumps(SAMPLE_IMAGE_PROMPT_JSON) + "\n```"
        result = DynamicImagePromptGenerator._parse_json(raw)
        self.assertIn("primary_prompt", result)
        self.assertEqual(result["aspect_ratio"], "16:9")

    def test_parse_json_uppercase_wrapper(self):
        """Parse JSON bọc trong ```JSON ... ``` (uppercase)."""
        raw = "```JSON\n" + json.dumps(SAMPLE_VISION_RESULT_JSON) + "\n```"
        result = VisionValidationEngine._parse_json(raw)
        self.assertAlmostEqual(result["vision_score"], 8.5, places=1)
        self.assertTrue(result["passed"])

    def test_parse_json_with_leading_text(self):
        """Parse JSON khi có text trước block JSON."""
        inner = json.dumps({"key": "value"})
        raw = "Đây là kết quả phân tích:\n```json\n" + inner + "\n```"
        result = SemanticVisualStoryAnalyzer._parse_json(raw)
        self.assertEqual(result["key"], "value")

    def test_parse_json_invalid_raises(self):
        """JSON không hợp lệ phải raise exception."""
        with self.assertRaises(Exception):
            SemanticVisualStoryAnalyzer._parse_json("This is not JSON at all {broken}")


# ─────────────────────────────────────────────────────────────────────────────
# TEST CLASS 3: SemanticVisualStoryAnalyzer
# ─────────────────────────────────────────────────────────────────────────────

class TestSemanticVisualStoryAnalyzer(unittest.TestCase):
    """Kiểm tra SemanticVisualStoryAnalyzer với mock Gemini."""

    @patch("services.visual_intelligence_engine.generate_with_gemini")
    def test_analyze_returns_visual_story(self, mock_gemini):
        """analyze() trả về VisualStory với dữ liệu đúng."""
        mock_gemini.return_value = "```json\n" + json.dumps(SAMPLE_VISUAL_STORY_JSON) + "\n```"

        vs = SemanticVisualStoryAnalyzer.analyze(
            article=SAMPLE_ARTICLE,
            brand_ctx=SAMPLE_BRAND_CTX,
            api_key="test-key"
        )

        self.assertIsInstance(vs, VisualStory)
        self.assertEqual(vs.main_theme, SAMPLE_VISUAL_STORY_JSON["main_theme"])
        self.assertEqual(vs.target_emotion, "inspiration")
        self.assertEqual(len(vs.keywords), 5)
        mock_gemini.assert_called_once()

    @patch("services.visual_intelligence_engine.generate_with_gemini")
    def test_analyze_fallback_on_error(self, mock_gemini):
        """analyze() trả về VisualStory mặc định khi Gemini lỗi."""
        mock_gemini.side_effect = Exception("API timeout")

        vs = SemanticVisualStoryAnalyzer.analyze(
            article=SAMPLE_ARTICLE,
            api_key="test-key"
        )

        self.assertIsInstance(vs, VisualStory)
        # Fallback values
        self.assertNotEqual(vs.main_theme, "")
        self.assertIn("AI", vs.keywords)

    def test_build_brand_block_applied(self):
        """_build_brand_block() với brand đầy đủ trả về block text có brand info."""
        block = SemanticVisualStoryAnalyzer._build_brand_block(SAMPLE_BRAND_CTX)
        self.assertIn("Professional", block)
        self.assertIn("rẻ tiền", block)   # blacklist word
        self.assertIn("AI cho mọi doanh nghiệp", block)  # tagline

    def test_build_brand_block_proposed(self):
        """_build_brand_block() với brand chưa có trả về thông báo đề xuất."""
        block = SemanticVisualStoryAnalyzer._build_brand_block({"status": "proposed"})
        self.assertIn("Chưa có brand profile", block)

    def test_build_brand_block_empty(self):
        """_build_brand_block() với dict rỗng trả về fallback."""
        block = SemanticVisualStoryAnalyzer._build_brand_block({})
        self.assertIsInstance(block, str)
        self.assertGreater(len(block), 0)

    @patch("services.visual_intelligence_engine.generate_with_gemini")
    def test_analyze_article_truncated_to_8000(self, mock_gemini):
        """analyze() cắt article tối đa 8000 ký tự trước khi gửi Gemini."""
        mock_gemini.return_value = "```json\n" + json.dumps(SAMPLE_VISUAL_STORY_JSON) + "\n```"
        long_article = "X" * 10000  # Article gốc 10000 ký tự

        SemanticVisualStoryAnalyzer.analyze(article=long_article, api_key="test")

        call_args = mock_gemini.call_args[0][0]  # prompt string
        x_count = call_args.count("X")
        # Article bị cắt tại 8000 → không thể có đủ 10000 ký tự 'X'
        self.assertLess(x_count, 10000, f"Article không bị truncate: vẫn có {x_count} ký tự 'X'")
        # Đảm bảo có truncate thực sự (< 8100 tính cả overhead template nhỏ)
        self.assertLessEqual(x_count, 8100, f"Truncate không đủ chặt: {x_count} ký tự 'X'")
        # Đảm bảo Gemini được gọi đúng 1 lần
        mock_gemini.assert_called_once()


# ─────────────────────────────────────────────────────────────────────────────
# TEST CLASS 4: DynamicImagePromptGenerator
# ─────────────────────────────────────────────────────────────────────────────

class TestDynamicImagePromptGenerator(unittest.TestCase):
    """Kiểm tra DynamicImagePromptGenerator với mock Gemini."""

    def _make_visual_story(self) -> VisualStory:
        return VisualStory(**{k: v for k, v in SAMPLE_VISUAL_STORY_JSON.items()
                              if k in VisualStory.__dataclass_fields__})

    @patch("services.visual_intelligence_engine.generate_with_gemini")
    def test_generate_returns_image_prompt(self, mock_gemini):
        """generate() trả về ImagePromptResult đúng cấu trúc."""
        mock_gemini.return_value = "```json\n" + json.dumps(SAMPLE_IMAGE_PROMPT_JSON) + "\n```"
        vs = self._make_visual_story()

        ip = DynamicImagePromptGenerator.generate(
            visual_story=vs,
            platform="Facebook",
            brand_ctx=SAMPLE_BRAND_CTX,
            api_key="test-key",
            iteration=1
        )

        self.assertIsInstance(ip, ImagePromptResult)
        self.assertIn("Vietnamese entrepreneur", ip.primary_prompt)
        self.assertEqual(ip.aspect_ratio, "16:9")
        self.assertEqual(ip.platform, "Facebook")
        self.assertEqual(ip.iteration, 1)
        self.assertGreater(len(ip.style_keywords), 0)

    @patch("services.visual_intelligence_engine.generate_with_gemini")
    def test_generate_uses_correct_platform_spec(self, mock_gemini):
        """generate() sử dụng đúng aspect_ratio cho từng platform."""
        mock_gemini.return_value = "```json\n" + json.dumps({
            **SAMPLE_IMAGE_PROMPT_JSON, "aspect_ratio": "4:5"
        }) + "\n```"
        vs = self._make_visual_story()

        ip = DynamicImagePromptGenerator.generate(
            visual_story=vs, platform="LinkedIn", api_key="test"
        )
        self.assertEqual(ip.platform, "LinkedIn")

    @patch("services.visual_intelligence_engine.generate_with_gemini")
    def test_generate_fallback_on_error(self, mock_gemini):
        """generate() trả về fallback prompt khi Gemini lỗi."""
        mock_gemini.side_effect = RuntimeError("Network error")
        vs = self._make_visual_story()

        ip = DynamicImagePromptGenerator.generate(
            visual_story=vs, platform="YouTube", api_key="test"
        )

        self.assertIsInstance(ip, ImagePromptResult)
        self.assertNotEqual(ip.primary_prompt, "")  # Có fallback
        self.assertEqual(ip.platform, "YouTube")

    @patch("services.visual_intelligence_engine.generate_with_gemini")
    def test_generate_with_improvement_hints(self, mock_gemini):
        """generate() đính kèm improvement_hints vào prompt khi iteration > 1."""
        mock_gemini.return_value = "```json\n" + json.dumps(SAMPLE_IMAGE_PROMPT_JSON) + "\n```"
        vs = self._make_visual_story()
        hints = ["Cần thêm yếu tố con người", "Ánh sáng tối hơn"]

        DynamicImagePromptGenerator.generate(
            visual_story=vs, platform="Facebook", api_key="test",
            iteration=2, improvement_hints=hints
        )

        call_prompt = mock_gemini.call_args[0][0]
        self.assertIn("PHẢN HỒI TỪ VISION AI", call_prompt)
        self.assertIn("Cần thêm yếu tố con người", call_prompt)


# ─────────────────────────────────────────────────────────────────────────────
# TEST CLASS 5: VisionValidationEngine
# ─────────────────────────────────────────────────────────────────────────────

class TestVisionValidationEngine(unittest.TestCase):
    """Kiểm tra VisionValidationEngine với mock Gemini."""

    def _make_prompt(self) -> ImagePromptResult:
        return ImagePromptResult(**{k: v for k, v in SAMPLE_IMAGE_PROMPT_JSON.items()
                                    if k in ImagePromptResult.__dataclass_fields__})

    def _make_story(self) -> VisualStory:
        return VisualStory(**{k: v for k, v in SAMPLE_VISUAL_STORY_JSON.items()
                              if k in VisualStory.__dataclass_fields__})

    @patch("services.visual_intelligence_engine.generate_with_gemini")
    def test_validate_returns_passed(self, mock_gemini):
        """validate_by_prompt() trả về passed=True khi overall_score >= threshold."""
        mock_gemini.return_value = "```json\n" + json.dumps(SAMPLE_VISION_RESULT_JSON) + "\n```"

        result = VisionValidationEngine.validate_by_prompt(
            image_prompt=self._make_prompt(),
            visual_story=self._make_story(),
            brand_ctx=SAMPLE_BRAND_CTX,
            threshold=7.5,
            api_key="test"
        )

        self.assertIsInstance(result, VisionValidationResult)
        self.assertTrue(result.passed)
        self.assertAlmostEqual(result.overall_score, 8.3, places=1)
        self.assertNotEqual(result.validated_at, "")

    @patch("services.visual_intelligence_engine.generate_with_gemini")
    def test_validate_fails_when_score_below_threshold(self, mock_gemini):
        """validate_by_prompt() trả về passed=False khi score < threshold."""
        low_score = {**SAMPLE_VISION_RESULT_JSON, "overall_score": 6.5, "passed": False}
        mock_gemini.return_value = "```json\n" + json.dumps(low_score) + "\n```"

        result = VisionValidationEngine.validate_by_prompt(
            image_prompt=self._make_prompt(),
            visual_story=self._make_story(),
            threshold=7.5,
            api_key="test"
        )

        self.assertFalse(result.passed)
        self.assertAlmostEqual(result.overall_score, 6.5, places=1)

    @patch("services.visual_intelligence_engine.generate_with_gemini")
    def test_validate_fallback_on_error(self, mock_gemini):
        """validate_by_prompt() trả về fallback khi Gemini lỗi."""
        mock_gemini.side_effect = ConnectionError("Timeout")

        result = VisionValidationEngine.validate_by_prompt(
            image_prompt=self._make_prompt(),
            visual_story=self._make_story(),
            api_key="test"
        )

        # Fallback: overall_score=7.5, passed=True
        self.assertIsInstance(result, VisionValidationResult)
        self.assertGreaterEqual(result.overall_score, 0)

    @patch("services.visual_intelligence_engine.generate_with_gemini")
    def test_validate_overrides_passed_based_on_threshold(self, mock_gemini):
        """validate_by_prompt() tự tính lại passed dựa trên threshold thực tế."""
        # AI trả về passed=True nhưng overall_score=6.0, threshold=7.5 → override False
        misleading = {**SAMPLE_VISION_RESULT_JSON, "overall_score": 6.0, "passed": True}
        mock_gemini.return_value = "```json\n" + json.dumps(misleading) + "\n```"

        result = VisionValidationEngine.validate_by_prompt(
            image_prompt=self._make_prompt(),
            visual_story=self._make_story(),
            threshold=7.5,
            api_key="test"
        )

        # Dù AI trả passed=True, nhưng score 6.0 < 7.5 → engine override thành False
        self.assertFalse(result.passed)


# ─────────────────────────────────────────────────────────────────────────────
# TEST CLASS 6: SelfCorrectionLoop
# ─────────────────────────────────────────────────────────────────────────────

class TestSelfCorrectionLoop(unittest.TestCase):
    """Kiểm tra SelfCorrectionLoop — logic tự sửa và vòng lặp."""

    def _make_story(self) -> VisualStory:
        return VisualStory(**{k: v for k, v in SAMPLE_VISUAL_STORY_JSON.items()
                              if k in VisualStory.__dataclass_fields__})

    @patch("services.visual_intelligence_engine.VisionValidationEngine.validate_by_prompt")
    @patch("services.visual_intelligence_engine.DynamicImagePromptGenerator.generate")
    def test_loop_stops_when_passed(self, mock_gen, mock_val):
        """SelfCorrectionLoop dừng ngay khi validation passed ở vòng đầu."""
        mock_gen.return_value = ImagePromptResult(
            primary_prompt="Great prompt", platform="Facebook", iteration=1
        )
        mock_val.return_value = VisionValidationResult(
            overall_score=8.5, passed=True, vlm_feedback="Excellent!"
        )

        prompt, validation, history = SelfCorrectionLoop.run(
            visual_story=self._make_story(),
            platform="Facebook",
            brand_ctx=SAMPLE_BRAND_CTX,
            api_key="test",
            threshold=7.5,
            max_loops=3
        )

        # Chỉ 1 lần gọi vì đã pass
        self.assertEqual(mock_gen.call_count, 1)
        self.assertEqual(mock_val.call_count, 1)
        self.assertEqual(len(history), 1)
        self.assertTrue(validation.passed)

    @patch("services.visual_intelligence_engine.VisionValidationEngine.validate_by_prompt")
    @patch("services.visual_intelligence_engine.DynamicImagePromptGenerator.generate")
    def test_loop_retries_until_max(self, mock_gen, mock_val):
        """SelfCorrectionLoop chạy tối đa max_loops khi không bao giờ pass."""
        mock_gen.return_value = ImagePromptResult(primary_prompt="Weak prompt", platform="Facebook")
        mock_val.return_value = VisionValidationResult(
            overall_score=5.0, passed=False,
            improvement_hints=["Cần cải thiện ánh sáng", "Thêm con người"]
        )

        prompt, validation, history = SelfCorrectionLoop.run(
            visual_story=self._make_story(),
            platform="Facebook",
            brand_ctx={},
            api_key="test",
            threshold=7.5,
            max_loops=3
        )

        # Phải chạy đúng 3 lần
        self.assertEqual(mock_gen.call_count, 3)
        self.assertEqual(mock_val.call_count, 3)
        self.assertEqual(len(history), 3)

    @patch("services.visual_intelligence_engine.VisionValidationEngine.validate_by_prompt")
    @patch("services.visual_intelligence_engine.DynamicImagePromptGenerator.generate")
    def test_loop_returns_best_score(self, mock_gen, mock_val):
        """SelfCorrectionLoop trả về prompt có điểm cao nhất, không nhất thiết là lần cuối."""
        # Vòng 1: 6.0, Vòng 2: 8.5 (best), Vòng 3 không xảy ra vì đã pass ở vòng 2
        scores = [
            VisionValidationResult(overall_score=6.0, passed=False),
            VisionValidationResult(overall_score=8.5, passed=True, vlm_feedback="Pass!"),
        ]
        mock_gen.return_value = ImagePromptResult(primary_prompt="Evolving prompt", platform="Facebook")
        mock_val.side_effect = scores

        prompt, validation, history = SelfCorrectionLoop.run(
            visual_story=self._make_story(),
            platform="Facebook",
            brand_ctx={},
            api_key="test",
            threshold=7.5,
            max_loops=3
        )

        self.assertEqual(len(history), 2)  # Dừng ở vòng 2
        self.assertAlmostEqual(validation.overall_score, 8.5, places=1)
        self.assertTrue(validation.passed)

    @patch("services.visual_intelligence_engine.VisionValidationEngine.validate_by_prompt")
    @patch("services.visual_intelligence_engine.DynamicImagePromptGenerator.generate")
    def test_loop_history_structure(self, mock_gen, mock_val):
        """Mỗi entry trong correction_history có đủ các key cần thiết."""
        mock_gen.return_value = ImagePromptResult(
            primary_prompt="Test prompt here", platform="Facebook", iteration=1
        )
        mock_val.return_value = VisionValidationResult(overall_score=8.0, passed=True)

        _, _, history = SelfCorrectionLoop.run(
            visual_story=self._make_story(),
            platform="Facebook",
            brand_ctx={},
            api_key="test",
            max_loops=1
        )

        self.assertEqual(len(history), 1)
        entry = history[0]
        for key in ["iteration", "overall_score", "passed", "vlm_feedback", "prompt_snippet", "timestamp"]:
            self.assertIn(key, entry, f"History entry thiếu key: {key}")
        self.assertEqual(entry["iteration"], 1)


# ─────────────────────────────────────────────────────────────────────────────
# TEST CLASS 7: VisualIntelligenceEngine (End-to-End)
# ─────────────────────────────────────────────────────────────────────────────

class TestVisualIntelligenceEngine(unittest.TestCase):
    """Kiểm tra end-to-end VisualIntelligenceEngine với toàn bộ các bước bị mock."""

    @patch("services.visual_intelligence_engine.SelfCorrectionLoop.run")
    @patch("services.visual_intelligence_engine.SemanticVisualStoryAnalyzer.analyze")
    def test_run_success_full_flow(self, mock_analyze, mock_loop):
        """VisualIntelligenceEngine.run() trả về VIEResult.success=True khi tất cả thành công."""
        vs = VisualStory(main_theme="Test theme", target_emotion="inspiration")
        ip = ImagePromptResult(primary_prompt="Great prompt", platform="Facebook", iteration=2)
        vval = VisionValidationResult(overall_score=8.5, passed=True)

        mock_analyze.return_value = vs
        mock_loop.return_value = (ip, vval, [
            {"iteration": 1, "overall_score": 7.0, "passed": False, "vlm_feedback": "", "prompt_snippet": "...", "timestamp": ""},
            {"iteration": 2, "overall_score": 8.5, "passed": True,  "vlm_feedback": "", "prompt_snippet": "...", "timestamp": ""},
        ])

        result = VisualIntelligenceEngine.run(
            article      = SAMPLE_ARTICLE,
            platform     = "Facebook",
            workspace_id = 1,
            article_id   = 42,
            brand_ctx    = SAMPLE_BRAND_CTX,
            api_key      = "test-key",
        )

        self.assertTrue(result.success)
        self.assertIsNotNone(result.visual_story)
        self.assertIsNotNone(result.image_prompt)
        self.assertIsNotNone(result.vision_validation)
        self.assertEqual(result.total_iterations, 2)
        self.assertGreaterEqual(result.processing_time_s, 0)  # có thể = 0 khi mock nhanh
        self.assertNotEqual(result.media_intelligence, {})

    @patch("services.visual_intelligence_engine.SemanticVisualStoryAnalyzer.analyze")
    def test_run_failure_returns_error(self, mock_analyze):
        """VisualIntelligenceEngine.run() trả về success=False khi có lỗi."""
        mock_analyze.side_effect = RuntimeError("Gemini API key invalid")

        result = VisualIntelligenceEngine.run(
            article      = SAMPLE_ARTICLE,
            platform     = "Facebook",
            workspace_id = 1,
            brand_ctx    = SAMPLE_BRAND_CTX,
            api_key      = "invalid-key",
        )

        self.assertFalse(result.success)
        self.assertIn("Gemini API key invalid", result.error_message)

    @patch("services.visual_intelligence_engine.SelfCorrectionLoop.run")
    @patch("services.visual_intelligence_engine.SemanticVisualStoryAnalyzer.analyze")
    def test_run_media_intelligence_12_fields(self, mock_analyze, mock_loop):
        """media_intelligence trong VIEResult phải có đầy đủ 12 fields."""
        vs = VisualStory(main_theme="Media Test", keywords=["k1", "k2"])
        ip = ImagePromptResult(primary_prompt="Prompt X", platform="YouTube", iteration=1)
        vval = VisionValidationResult(
            vision_score=9.0, ai_score=8.5, overall_score=8.7, passed=True
        )
        mock_analyze.return_value = vs
        mock_loop.return_value = (ip, vval, [])

        result = VisualIntelligenceEngine.run(
            article=SAMPLE_ARTICLE, platform="YouTube",
            workspace_id=3, article_id=77,
            brand_ctx=SAMPLE_BRAND_CTX, api_key="test"
        )

        mi = result.media_intelligence
        required = ["prompt", "visual_story", "platform", "workspace", "article",
                    "performance", "ctr", "tags", "ai_score", "vision_score",
                    "overall_score", "version"]
        for f in required:
            self.assertIn(f, mi, f"media_intelligence thiếu field: {f}")
        self.assertEqual(mi["workspace"], 3)
        self.assertEqual(mi["article"], 77)

    @patch("services.visual_intelligence_engine.SelfCorrectionLoop.run")
    @patch("services.visual_intelligence_engine.SemanticVisualStoryAnalyzer.analyze")
    def test_run_quick_returns_dict(self, mock_analyze, mock_loop):
        """run_quick() trả về dict đơn giản phù hợp cho tab_create."""
        vs = VisualStory(main_theme="Quick test", target_emotion="hứng khởi")
        ip = ImagePromptResult(primary_prompt="Quick prompt", platform="Facebook", iteration=1)
        vval = VisionValidationResult(
            ai_score=8.0, overall_score=8.0, vision_score=7.5, passed=True
        )
        mock_analyze.return_value = vs
        mock_loop.return_value = (ip, vval, [])

        quick = VisualIntelligenceEngine.run_quick(
            article  = SAMPLE_ARTICLE,
            platform = "Facebook",
            api_key  = "test"
        )

        self.assertIsInstance(quick, dict)
        for key in ["image_prompt", "negative_prompt", "ai_score", "vision_score",
                    "passed", "vlm_feedback", "iterations", "processing_time"]:
            self.assertIn(key, quick, f"run_quick() thiếu key: {key}")
        self.assertEqual(quick["image_prompt"], "Quick prompt")
        self.assertTrue(quick["passed"])


# ─────────────────────────────────────────────────────────────────────────────
# TEST CLASS 8: Constants & Platform Specs
# ─────────────────────────────────────────────────────────────────────────────

class TestConstantsAndSpecs(unittest.TestCase):
    """Kiểm tra hằng số và cấu hình nền tảng."""

    def test_default_vision_threshold(self):
        """DEFAULT_VISION_THRESHOLD phải là 7.5."""
        self.assertEqual(DEFAULT_VISION_THRESHOLD, 7.5)

    def test_max_correction_loops(self):
        """MAX_CORRECTION_LOOPS phải là 3."""
        self.assertEqual(MAX_CORRECTION_LOOPS, 3)

    def test_platform_specs_all_platforms(self):
        """PLATFORM_SPECS có đủ 7 nền tảng với aspect_ratio và style_hint."""
        expected_platforms = [
            "LinkedIn", "Facebook", "Facebook Ads",
            "YouTube", "Zalo OA", "Instagram", "TikTok / Reels"
        ]
        for plat in expected_platforms:
            self.assertIn(plat, PLATFORM_SPECS, f"PLATFORM_SPECS thiếu: {plat}")
            self.assertIn("aspect_ratio", PLATFORM_SPECS[plat])
            self.assertIn("style_hint", PLATFORM_SPECS[plat])

    def test_platform_specs_aspect_ratios(self):
        """Kiểm tra aspect_ratio đúng cho từng platform."""
        self.assertEqual(PLATFORM_SPECS["LinkedIn"]["aspect_ratio"], "4:5")
        self.assertEqual(PLATFORM_SPECS["Facebook"]["aspect_ratio"], "16:9")
        self.assertEqual(PLATFORM_SPECS["Zalo OA"]["aspect_ratio"], "1:1")
        self.assertEqual(PLATFORM_SPECS["TikTok / Reels"]["aspect_ratio"], "9:16")
        self.assertEqual(PLATFORM_SPECS["Instagram"]["aspect_ratio"], "1:1")


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    unittest.main(verbosity=2)
