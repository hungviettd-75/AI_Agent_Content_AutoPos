"""Service layer for AI Content Strategy Center."""

import concurrent.futures
import copy
import hashlib
import json
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta

from agents.content_strategy_prompts import (
    PROMPT_VERSION,
    build_content_strategy_prompt,
    build_json_repair_prompt,
    build_persona_generation_prompt,
    build_pillar_generation_prompt,
    build_subtopic_generation_prompt,
    build_angle_generation_prompt,
)
from config import settings
from config.config import logger
from core.audit_logger import log_action
from database.models.approvals import ApprovalModel
from database.models.schedules import ScheduleModel
from database.models.ai_cost import AICostModel
from database.models.brand import BrandModel
from database.models.companies import CompanyModel
from database.models.posts import PostModel
from database.repositories.content_strategy_generation_repository import ContentStrategyGenerationRepository
from database.repositories.content_strategy_repository import ContentStrategyRepository
from database.repositories.knowledge_repository import KnowledgeRepository
from services.gemini_client import DEFAULT_MODEL, _call_model, get_gemini_client
from services.content_strategy_validation import (
    ContentStrategyJSONParser,
    ContentStrategyValidator,
    StrategyValidationError,
)




BUSINESS_CONTEXT_FIELDS = [
    "company_name", "industry", "website", "market", "business_model",
    "products", "services", "price_range", "competitive_advantages",
    "mission", "vision", "brand_story", "current_marketing_challenges",
    "main_competitors", "marketing_budget_range", "available_resources",
]

BRAND_IDENTITY_FIELDS = [
    "tone_of_voice", "personality", "writing_style", "brand_keywords",
    "forbidden_words", "standard_cta", "mission", "vision", "colors",
    "communication_principles",
]

PERSONA_FIELDS = [
    "name", "role", "industry", "company_size", "demographics", "goals",
    "pain_points", "fears", "desires", "objections", "buying_triggers",
    "decision_authority", "preferred_channels", "preferred_content_formats",
    "content_depth_preference", "language_style", "customer_journey_stage",
]

SENSITIVE_PERSONA_HINTS = [
    "national id", "passport", "credit card", "bank account", "password",
    "api key", "access token", "jwt", "social security", "ssn",
]


def _split_lines(value):
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if not value:
        return []
    text = str(value).replace("\r", "\n")
    parts = []
    for chunk in text.replace(",", "\n").split("\n"):
        item = chunk.strip(" -\t")
        if item:
            parts.append(item)
    return parts


def _safe_audit_payload(value):
    if not isinstance(value, dict):
        return {}
    business_context = value.get("business_context") or {}
    if isinstance(business_context, dict):
        business_context_fields = len([k for k, v in business_context.items() if str(v).strip()])
    else:
        business_context_fields = 1 if str(business_context).strip() else 0
    brand_identity = value.get("brand_identity") or {}
    brand_mode = brand_identity.get("mode", "") if isinstance(brand_identity, dict) else "legacy_text"
    personas = value.get("audience_personas") or []
    personas_count = len(personas) if isinstance(personas, list) else (1 if str(personas).strip() else 0)
    return {
        "strategy_name": value.get("strategy_name", ""),
        "business_context_fields": business_context_fields,
        "brand_mode": brand_mode,
        "personas_count": personas_count,
    }


def normalize_business_context(value=None, company=None, brand=None):
    data = {field: "" for field in BUSINESS_CONTEXT_FIELDS}
    if isinstance(value, str):
        data["current_marketing_challenges"] = value
    elif isinstance(value, dict):
        for field in BUSINESS_CONTEXT_FIELDS:
            data[field] = value.get(field, "")
    company = company or {}
    brand = brand or {}
    seeds = {
        "company_name": company.get("name", ""),
        "industry": company.get("industry", ""),
        "website": company.get("website", ""),
        "products": company.get("products", ""),
        "services": company.get("description", ""),
        "mission": brand.get("mission", ""),
        "vision": brand.get("vision", ""),
    }
    for field, seed in seeds.items():
        if not data.get(field) and seed:
            data[field] = seed
    return data


def normalize_brand_identity(value=None, brand=None):
    data = {field: "" for field in BRAND_IDENTITY_FIELDS}
    data["mode"] = "existing"
    data["save_back_confirmed"] = False
    if isinstance(value, str):
        data["communication_principles"] = value
    elif isinstance(value, dict):
        for field in [*BRAND_IDENTITY_FIELDS, "mode", "save_back_confirmed"]:
            if field in value:
                data[field] = value[field]
    brand = brand or {}
    colors = brand.get("brand_colors") or {}
    seeds = {
        "tone_of_voice": brand.get("tone_of_voice", ""),
        "brand_keywords": brand.get("keywords", []),
        "forbidden_words": brand.get("blacklist_words", []),
        "standard_cta": brand.get("cta", ""),
        "mission": brand.get("mission", ""),
        "vision": brand.get("vision", ""),
        "colors": colors,
        "communication_principles": brand.get("brand_guidelines", ""),
    }
    for field, seed in seeds.items():
        if not data.get(field) and seed:
            data[field] = seed
    if not isinstance(data.get("brand_keywords"), list):
        data["brand_keywords"] = _split_lines(data.get("brand_keywords"))
    if not isinstance(data.get("forbidden_words"), list):
        data["forbidden_words"] = _split_lines(data.get("forbidden_words"))
    return data


def normalize_persona(value=None, sort_order=0):
    raw = value if isinstance(value, dict) else {}
    persona = {field: raw.get(field, "") for field in PERSONA_FIELDS}
    for field in [
        "goals", "pain_points", "fears", "desires", "objections",
        "buying_triggers", "preferred_channels", "preferred_content_formats",
    ]:
        persona[field] = _split_lines(raw.get(field))
    persona["id"] = raw.get("id") or f"persona_{int(time.time() * 1000)}_{sort_order}"
    persona["sort_order"] = raw.get("sort_order", sort_order)
    persona["ai_generated_draft"] = bool(raw.get("ai_generated_draft", False))
    persona["status"] = raw.get("status", "draft" if persona["ai_generated_draft"] else "active")
    return persona


def validate_persona_completeness(persona: dict) -> list:
    errors = []
    required = ["name", "role", "goals", "pain_points", "buying_triggers", "decision_authority", "preferred_channels", "customer_journey_stage"]
    for field in required:
        value = persona.get(field)
        if isinstance(value, list):
            missing = not value
        else:
            missing = not str(value or "").strip()
        if missing:
            errors.append(field)
    combined = json.dumps(persona, ensure_ascii=False).lower()
    for hint in SENSITIVE_PERSONA_HINTS:
        if hint in combined:
            errors.append("sensitive_data")
            break
    return errors




BUSINESS_GOAL_OPTIONS = [
    "Brand Awareness",
    "Engagement",
    "Thought Leadership",
    "Community Growth",
    "Lead Generation",
    "Sales Conversion",
    "Customer Education",
    "Customer Retention",
    "Product Launch",
    "Recruitment",
    "Event/Webinar Registration",
    "Website Traffic",
]

PLATFORM_OPTIONS = ["facebook", "linkedin", "zalo_oa", "tiktok", "youtube_shorts", "blog", "email_newsletter"]
PUBLISHING_SUPPORTED_PLATFORMS = {"facebook", "linkedin", "zalo_oa"}
FORMAT_OPTIONS = [
    "Short post",
    "Long post",
    "Carousel",
    "Reels/Short video",
    "Infographic",
    "Case Study",
    "Blog",
    "Email",
    "Livestream outline",
    "Webinar outline",
    "Poll",
    "Story",
    "Lead Magnet",
]
FORMAT_STATUS_OPTIONS = ["draft", "planned", "ready_for_brief", "export_only", "publishing_disabled", "archived"]
PRIORITY_OPTIONS = ["high", "medium", "low"]

PLATFORM_PRESETS = {
    "facebook": {"target_length": "80-180 words", "hook_style": "short discussion hook", "publishing_objective": "discussion", "adaptation_guidance": "Open with a short hook and leave room for discussion, comments, or debate.", "default_formats": ["Short post", "Carousel", "Poll", "Story"]},
    "linkedin": {"target_length": "150-300 words", "hook_style": "B2B insight hook", "publishing_objective": "thought leadership", "adaptation_guidance": "Frame the angle as a B2B lesson, operator insight, or leadership POV.", "default_formats": ["Long post", "Carousel", "Case Study", "Lead Magnet"]},
    "zalo_oa": {"target_length": "60-140 words", "hook_style": "direct value hook", "publishing_objective": "owned audience update", "adaptation_guidance": "Keep it direct for existing followers; do not add hashtags unless the brand rules explicitly require them.", "default_formats": ["Short post", "Story", "Lead Magnet"]},
    "tiktok": {"target_length": "20-45 seconds", "hook_style": "first 3 seconds visual hook", "publishing_objective": "short-form discovery", "adaptation_guidance": "Use a distinct video structure with hook, body beats, and CTA outline instead of copying post text.", "default_formats": ["Reels/Short video", "Story"]},
    "youtube_shorts": {"target_length": "30-60 seconds", "hook_style": "problem-to-payoff hook", "publishing_objective": "short-form education", "adaptation_guidance": "Create a concise video outline with hook, body, and CTA beats.", "default_formats": ["Reels/Short video"]},
    "blog": {"target_length": "800-1400 words", "hook_style": "search intent intro", "publishing_objective": "SEO education", "adaptation_guidance": "Expand the angle into sections, evidence, and internal links; manage/export only unless a blog publisher is added.", "default_formats": ["Blog", "Case Study", "Lead Magnet"]},
    "email_newsletter": {"target_length": "250-600 words", "hook_style": "subject-line promise", "publishing_objective": "nurture", "adaptation_guidance": "Adapt as a subscriber note with subject idea, skimmable sections, and one CTA.", "default_formats": ["Email", "Lead Magnet", "Webinar outline"]},
}

BUSINESS_GOAL_FIELDS = [
    "name", "priority", "description", "target_metric", "target_value",
    "time_period", "target_personas", "preferred_platforms", "status",
]

CONTENT_PILLAR_FIELDS = [
    "name", "description", "strategic_purpose", "business_goals",
    "target_personas", "recommended_channels", "content_ratio", "priority",
    "differentiation_angle", "do_guidance", "dont_guidance", "status",
]

SUBTOPIC_FIELDS = [
    "name", "description", "target_persona", "business_goal", "intent",
    "funnel_stage", "priority", "trend_classification", "suggested_channels",
    "status", "source", "manual_edits", "approved",
]

ANGLE_CATEGORY_OPTIONS = [
    "How-to", "Mistakes", "Checklist", "Case Study", "Comparison", "Myth vs Fact",
    "Framework", "Step-by-step", "ROI", "Cost", "Risk", "Contrarian Opinion",
    "Trend", "Prediction", "Behind the Scenes", "Demonstration", "FAQ",
    "Before/After", "Storytelling", "Debate", "Template", "Prompt", "Tool List",
    "Executive Insight",
]

CONTENT_ANGLE_FIELDS = [
    "working_title", "hook_idea", "core_insight", "intended_emotion",
    "target_persona", "funnel_stage", "cta_type", "evidence_requirement",
    "trend_classification", "priority", "risk_level", "status", "category",
    "source", "manual_edits", "approved",
]

FORMAT_VARIANT_FIELDS = [
    "angle_id", "platform", "format", "target_length", "tone_override", "cta",
    "visual_requirement", "hook_style", "publishing_objective",
    "repurposing_source", "priority", "status", "adaptation_guidance",
    "publishing_enabled", "production_effort", "brief",
]

VIDEO_FORMATS = {"Reels/Short video", "Livestream outline", "Webinar outline"}

FUNNEL_STAGE_OPTIONS = ["awareness", "consideration", "evaluation", "conversion", "retention"]
FUNNEL_STAGE_ALIASES = {"decision": "conversion", "purchase": "conversion"}
TREND_CLASSIFICATION_OPTIONS = ["evergreen", "trending", "hybrid"]
RISK_LEVEL_OPTIONS = ["low", "medium", "high"]
SOURCE_OPTIONS = ["manual", "ai_generated"]
CALENDAR_VIEW_OPTIONS = ["list", "weekly", "monthly", "quarterly"]
CALENDAR_APPROVAL_STATUS_OPTIONS = ["draft", "in_review", "approved", "rejected"]
CALENDAR_PUBLISHING_STATUS_OPTIONS = ["planned", "draft_created", "approval_required", "in_review", "approved", "scheduled", "publishing", "published", "failed", "configuration_required", "skipped"]
KPI_METRIC_OPTIONS = [
    "Reach", "Impressions", "Engagement", "Comments", "Shares", "Saves",
    "Followers", "Link clicks", "CTR", "Leads", "Registrations", "Conversion",
    "Cost per lead", "Revenue attributed",
]
KPI_SCOPE_OPTIONS = ["strategy", "campaign", "calendar_item", "platform"]

DEFAULT_TIMEZONE = "Asia/Bangkok"


def _canonical_funnel_stage(value: str) -> str:
    key = str(value or "awareness").lower().strip().replace(" ", "_").replace("-", "_")
    key = FUNNEL_STAGE_ALIASES.get(key, key)
    return key if key in FUNNEL_STAGE_OPTIONS else "awareness"


def normalize_business_goal(value=None, sort_order=0):
    raw = value if isinstance(value, dict) else {"name": value} if value else {}
    goal = {field: raw.get(field, "") for field in BUSINESS_GOAL_FIELDS}
    goal["id"] = raw.get("id") or f"goal_{int(time.time() * 1000)}_{sort_order}"
    goal["name"] = str(goal.get("name") or "").strip()
    goal["priority"] = str(goal.get("priority") or "medium").lower()
    if goal["priority"] not in PRIORITY_OPTIONS:
        goal["priority"] = "medium"
    goal["target_personas"] = _split_lines(raw.get("target_personas"))
    goal["preferred_platforms"] = _split_lines(raw.get("preferred_platforms"))
    goal["target_value"] = str(raw.get("target_value", goal.get("target_value") or "")).strip()
    goal["time_period"] = str(raw.get("time_period") or raw.get("timeframe") or "").strip()
    goal["status"] = raw.get("status", "active") or "active"
    goal["sort_order"] = raw.get("sort_order", sort_order)
    return goal


def normalize_content_pillar(value=None, sort_order=0):
    raw = value if isinstance(value, dict) else {"name": value} if value else {}
    pillar = {field: raw.get(field, "") for field in CONTENT_PILLAR_FIELDS}
    pillar["id"] = raw.get("id") or f"pillar_{int(time.time() * 1000)}_{sort_order}"
    pillar["name"] = str(pillar.get("name") or "").strip()
    pillar["strategic_purpose"] = str(raw.get("strategic_purpose") or raw.get("objective") or "").strip()
    pillar["business_goals"] = _split_lines(raw.get("business_goals") or raw.get("business_goal"))
    pillar["target_personas"] = _split_lines(raw.get("target_personas") or raw.get("target_persona"))
    pillar["recommended_channels"] = _split_lines(raw.get("recommended_channels") or raw.get("recommended_platforms"))
    pillar["do_guidance"] = _split_lines(raw.get("do_guidance"))
    pillar["dont_guidance"] = _split_lines(raw.get("dont_guidance"))
    try:
        pillar["content_ratio"] = int(float(raw.get("content_ratio", 0) or 0))
    except Exception:
        pillar["content_ratio"] = 0
    pillar["priority"] = str(pillar.get("priority") or "medium").lower()
    if pillar["priority"] not in PRIORITY_OPTIONS:
        pillar["priority"] = "medium"
    pillar["status"] = raw.get("status", "active") or "active"
    pillar["sort_order"] = raw.get("sort_order", sort_order)
    return pillar


def normalize_business_goals(value=None):
    return [normalize_business_goal(item, index) for index, item in enumerate(value or []) if isinstance(item, (dict, str))]


def normalize_content_pillars(value=None):
    return [normalize_content_pillar(item, index) for index, item in enumerate(value or []) if isinstance(item, (dict, str))]


def _normalize_text_key(value: str) -> str:
    text = str(value or "").lower().strip()
    text = " ".join(text.replace("-", " ").replace("_", " ").split())
    return "".join(ch for ch in text if ch.isalnum() or ch.isspace()).strip()


def _similarity(a: str, b: str) -> float:
    left = set(_normalize_text_key(a).split())
    right = set(_normalize_text_key(b).split())
    if not left or not right:
        return 0.0
    return len(left & right) / max(len(left | right), 1)


def _fingerprint_dict(value: dict, fields: list) -> str:
    payload = {field: value.get(field) for field in fields}
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:16]


def _dedupe_items(items: list, name_getter, threshold: float = 0.72) -> tuple[list, list]:
    kept = []
    duplicates = []
    for item in items:
        name = name_getter(item)
        normalized = _normalize_text_key(name)
        duplicate_of = None
        for existing in kept:
            existing_name = name_getter(existing)
            if normalized and normalized == _normalize_text_key(existing_name):
                duplicate_of = existing_name
                break
            if _similarity(name, existing_name) >= threshold:
                duplicate_of = existing_name
                break
        if duplicate_of:
            duplicates.append({"name": name, "duplicate_of": duplicate_of})
        else:
            kept.append(item)
    return kept, duplicates


def normalize_subtopic(value=None, sort_order=0, default_pillar_id=None, source="manual"):
    raw = value if isinstance(value, dict) else {"name": value} if value else {}
    item = {field: raw.get(field, "") for field in SUBTOPIC_FIELDS}
    item["id"] = raw.get("id") or f"subtopic_{int(time.time() * 1000)}_{sort_order}"
    item["pillar_id"] = raw.get("pillar_id") or default_pillar_id or ""
    item["name"] = str(raw.get("name") or "").strip()
    item["description"] = str(raw.get("description") or "").strip()
    item["target_persona"] = str(raw.get("target_persona") or raw.get("target_personas") or "").strip()
    item["business_goal"] = str(raw.get("business_goal") or raw.get("business_goals") or "").strip()
    item["intent"] = str(raw.get("intent") or raw.get("search_intent") or raw.get("audience_intent") or "").strip()
    item["funnel_stage"] = _canonical_funnel_stage(raw.get("funnel_stage") or "awareness")
    item["priority"] = str(raw.get("priority") or "medium").lower()
    if item["priority"] not in PRIORITY_OPTIONS:
        item["priority"] = "medium"
    item["trend_classification"] = str(raw.get("trend_classification") or raw.get("evergreen_trending") or "evergreen").lower()
    if item["trend_classification"] not in TREND_CLASSIFICATION_OPTIONS:
        item["trend_classification"] = "evergreen"
    item["suggested_channels"] = list(dict.fromkeys([_canonical_platform(c) for c in _split_lines(raw.get("suggested_channels") or raw.get("recommended_channels")) if _canonical_platform(c) in PLATFORM_OPTIONS]))
    item["status"] = raw.get("status") or "draft"
    item["source"] = raw.get("source") if raw.get("source") in SOURCE_OPTIONS else source
    tracked_fields = ["name", "description", "target_persona", "business_goal", "intent", "funnel_stage", "priority", "trend_classification", "suggested_channels"]
    item["ai_fingerprint"] = raw.get("ai_fingerprint", "")
    current_fingerprint = _fingerprint_dict(item, tracked_fields)
    item["manual_edits"] = bool(raw.get("manual_edits", item["source"] == "manual"))
    if item["source"] == "ai_generated" and item["ai_fingerprint"] and item["ai_fingerprint"] != current_fingerprint:
        item["manual_edits"] = True
    if item["source"] == "ai_generated" and not item["ai_fingerprint"]:
        item["ai_fingerprint"] = current_fingerprint
    item["approved"] = bool(raw.get("approved", item.get("status") == "approved"))
    item["sort_order"] = raw.get("sort_order", sort_order)
    return item


def normalize_subtopics(value=None):
    return [normalize_subtopic(item, index) for index, item in enumerate(value or []) if isinstance(item, (dict, str))]


def normalize_content_angle(value=None, sort_order=0, default_subtopic_id=None, source="manual"):
    raw = value if isinstance(value, dict) else {"working_title": value} if value else {}
    item = {field: raw.get(field, "") for field in CONTENT_ANGLE_FIELDS}
    item["id"] = raw.get("id") or f"angle_{int(time.time() * 1000)}_{sort_order}"
    item["subtopic_id"] = raw.get("subtopic_id") or default_subtopic_id or ""
    item["category"] = raw.get("category") if raw.get("category") in ANGLE_CATEGORY_OPTIONS else "How-to"
    item["working_title"] = str(raw.get("working_title") or raw.get("title") or "").strip()
    item["hook_idea"] = str(raw.get("hook_idea") or raw.get("hook") or "").strip()
    item["core_insight"] = str(raw.get("core_insight") or raw.get("description") or "").strip()
    item["intended_emotion"] = str(raw.get("intended_emotion") or "").strip()
    item["target_persona"] = str(raw.get("target_persona") or "").strip()
    item["funnel_stage"] = _canonical_funnel_stage(raw.get("funnel_stage") or "awareness")
    item["cta_type"] = str(raw.get("cta_type") or raw.get("cta") or "soft").strip()
    item["evidence_requirement"] = str(raw.get("evidence_requirement") or "").strip()
    item["trend_classification"] = str(raw.get("trend_classification") or raw.get("evergreen_trending") or "evergreen").lower()
    if item["trend_classification"] not in TREND_CLASSIFICATION_OPTIONS:
        item["trend_classification"] = "evergreen"
    item["priority"] = str(raw.get("priority") or "medium").lower()
    if item["priority"] not in PRIORITY_OPTIONS:
        item["priority"] = "medium"
    item["risk_level"] = str(raw.get("risk_level") or "low").lower()
    if item["risk_level"] not in RISK_LEVEL_OPTIONS:
        item["risk_level"] = "low"
    item["status"] = raw.get("status") or "draft"
    item["source"] = raw.get("source") if raw.get("source") in SOURCE_OPTIONS else source
    tracked_fields = ["working_title", "hook_idea", "core_insight", "intended_emotion", "target_persona", "funnel_stage", "cta_type", "evidence_requirement", "trend_classification", "priority", "risk_level", "category"]
    item["ai_fingerprint"] = raw.get("ai_fingerprint", "")
    current_fingerprint = _fingerprint_dict(item, tracked_fields)
    item["manual_edits"] = bool(raw.get("manual_edits", item["source"] == "manual"))
    if item["source"] == "ai_generated" and item["ai_fingerprint"] and item["ai_fingerprint"] != current_fingerprint:
        item["manual_edits"] = True
    if item["source"] == "ai_generated" and not item["ai_fingerprint"]:
        item["ai_fingerprint"] = current_fingerprint
    item["approved"] = bool(raw.get("approved", item.get("status") == "approved"))
    item["sort_order"] = raw.get("sort_order", sort_order)
    return item


def normalize_content_angles(value=None):
    return [normalize_content_angle(item, index) for index, item in enumerate(value or []) if isinstance(item, (dict, str))]


def _canonical_platform(value: str) -> str:
    key = str(value or "").lower().strip().replace(" ", "_").replace("-", "_")
    aliases = {"zalo": "zalo_oa", "youtube": "youtube_shorts", "shorts": "youtube_shorts", "email": "email_newsletter", "newsletter": "email_newsletter"}
    return aliases.get(key, key if key in PLATFORM_OPTIONS else "facebook")


def _canonical_format(value: str) -> str:
    normalized = str(value or "").strip().lower()
    for option in FORMAT_OPTIONS:
        if normalized == option.lower():
            return option
    aliases = {"short video": "Reels/Short video", "reels": "Reels/Short video", "newsletter": "Email", "lead magnet": "Lead Magnet"}
    return aliases.get(normalized, "Short post")


def _brand_list(brand: dict, field: str) -> list:
    return _split_lines((brand or {}).get(field))


def estimate_format_effort(platform: str, format_type: str, visual_requirement: str = "") -> str:
    score = 1
    if _canonical_platform(platform) in {"tiktok", "youtube_shorts"}:
        score += 2
    if _canonical_format(format_type) in {"Carousel", "Reels/Short video", "Infographic", "Case Study", "Blog", "Lead Magnet", "Livestream outline", "Webinar outline"}:
        score += 1
    if str(visual_requirement or "").strip():
        score += 1
    if score >= 4:
        return "high"
    if score >= 3:
        return "medium"
    return "low"


def _build_content_brief(angle: dict, variant: dict, brand: dict = None) -> str:
    brand = normalize_brand_identity(brand or {})
    format_type = _canonical_format(variant.get("format"))
    parts = [
        f"Angle: {angle.get('working_title', '')}",
        f"Core insight: {angle.get('core_insight', '')}",
        f"Hook style: {variant.get('hook_style', '')}",
        f"Platform adaptation: {variant.get('adaptation_guidance', '')}",
        f"CTA direction: {variant.get('cta') or brand.get('standard_cta') or angle.get('cta_type', '')}",
        f"Visual requirement: {variant.get('visual_requirement', '')}",
    ]
    if format_type in VIDEO_FORMATS:
        parts.extend(["Video outline: hook beat, body beats, CTA beat.", "Do not write final script in this step."])
    else:
        parts.append("Do not write the full post in this step.")
    return "\n".join([p for p in parts if p and not p.endswith(': ')])


def normalize_format_variant(value=None, sort_order=0, default_angle_id=None, brand=None):
    raw = value if isinstance(value, dict) else {}
    platform = _canonical_platform(raw.get("platform"))
    format_type = _canonical_format(raw.get("format") or raw.get("format_type"))
    preset = PLATFORM_PRESETS.get(platform, PLATFORM_PRESETS["facebook"])
    item = {field: raw.get(field, "") for field in FORMAT_VARIANT_FIELDS}
    item["id"] = raw.get("id") or f"format_{int(time.time() * 1000)}_{sort_order}"
    item["angle_id"] = raw.get("angle_id") or default_angle_id or ""
    item["platform"] = platform
    item["format"] = format_type
    item["target_length"] = str(raw.get("target_length") or preset["target_length"]).strip()
    item["tone_override"] = str(raw.get("tone_override") or "").strip()
    item["cta"] = str(raw.get("cta") or (brand or {}).get("standard_cta") or "").strip()
    item["visual_requirement"] = str(raw.get("visual_requirement") or "").strip()
    item["hook_style"] = str(raw.get("hook_style") or preset["hook_style"]).strip()
    item["publishing_objective"] = str(raw.get("publishing_objective") or preset["publishing_objective"]).strip()
    item["repurposing_source"] = str(raw.get("repurposing_source") or item["angle_id"] or "").strip()
    item["priority"] = str(raw.get("priority") or "medium").lower()
    if item["priority"] not in PRIORITY_OPTIONS:
        item["priority"] = "medium"
    item["publishing_enabled"] = platform in PUBLISHING_SUPPORTED_PLATFORMS and bool(raw.get("publishing_enabled", platform in PUBLISHING_SUPPORTED_PLATFORMS))
    item["status"] = raw.get("status") or ("planned" if item["publishing_enabled"] else "export_only")
    if platform not in PUBLISHING_SUPPORTED_PLATFORMS and item["status"] not in {"draft", "archived"}:
        item["status"] = "export_only"
    item["adaptation_guidance"] = str(raw.get("adaptation_guidance") or preset["adaptation_guidance"]).strip()
    item["production_effort"] = raw.get("production_effort") or estimate_format_effort(platform, format_type, item["visual_requirement"])
    item["brief"] = str(raw.get("brief") or "").strip()
    item["sort_order"] = raw.get("sort_order", sort_order)
    item["source"] = raw.get("source", "manual")
    return item


def normalize_format_variants(value=None, brand=None):
    return [normalize_format_variant(item, index, brand=brand) for index, item in enumerate(value or []) if isinstance(item, dict)]


def recommend_format_variant(angle: dict, platform: str, format_type: str = None, brand: dict = None, sort_order: int = 0) -> dict:
    angle = normalize_content_angle(angle)
    brand = normalize_brand_identity(brand or {})
    platform = _canonical_platform(platform)
    preset = PLATFORM_PRESETS[platform]
    selected_format = _canonical_format(format_type or (preset["default_formats"][0] if preset.get("default_formats") else "Short post"))
    variant = normalize_format_variant({
        "angle_id": angle.get("id"),
        "platform": platform,
        "format": selected_format,
        "tone_override": brand.get("tone_of_voice", ""),
        "cta": brand.get("standard_cta") or angle.get("cta_type", ""),
        "visual_requirement": "hook frame, proof visual, CTA frame" if selected_format in VIDEO_FORMATS or selected_format in {"Carousel", "Infographic"} else "",
        "repurposing_source": angle.get("id"),
        "priority": angle.get("priority", "medium"),
        "source": "recommended",
    }, sort_order, default_angle_id=angle.get("id"), brand=brand)
    variant["brief"] = _build_content_brief(angle, variant, brand)
    return variant


def create_format_variants_from_angles(angles: list, platforms: list, format_type: str = None, brand: dict = None) -> list:
    variants = []
    for angle in normalize_content_angles(angles):
        for platform in platforms or []:
            variants.append(recommend_format_variant(angle, platform, format_type=format_type, brand=brand, sort_order=len(variants)))
    return variants


WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
WEEKDAY_ALIASES = {name.lower(): index for index, name in enumerate(WEEKDAY_NAMES)}
WEEKDAY_ALIASES.update({name[:3].lower(): index for index, name in enumerate(WEEKDAY_NAMES)})


def _parse_date(value, fallback=None):
    if isinstance(value, datetime):
        return value.date()
    if hasattr(value, "isoformat") and value.__class__.__name__ == "date":
        return value
    if isinstance(value, str) and value.strip():
        try:
            return datetime.fromisoformat(value.strip()).date()
        except ValueError:
            return fallback
    return fallback


def _parse_time_slot(value, fallback="09:00"):
    text = str(value or "").strip()
    if not text:
        return fallback
    try:
        parsed = datetime.strptime(text[:5], "%H:%M")
        return parsed.strftime("%H:%M")
    except ValueError:
        return fallback


def _weekday_indexes(values):
    indexes = []
    for value in values or []:
        if isinstance(value, int) and 0 <= value <= 6:
            indexes.append(value)
        else:
            key = str(value or "").strip().lower()
            if key in WEEKDAY_ALIASES:
                indexes.append(WEEKDAY_ALIASES[key])
    return sorted(set(indexes)) or [0, 1, 2, 3, 4]


def _ratio_plan(items: list, total: int, ratio_getter, key_getter):
    active = [item for item in items or [] if str(item.get("status", "active")).lower() not in {"inactive", "archived"}]
    if not active or total <= 0:
        return []
    raw_weights = []
    for item in active:
        try:
            weight = float(ratio_getter(item) or 0)
        except Exception:
            weight = 0
        raw_weights.append(max(weight, 0))
    if not any(raw_weights):
        raw_weights = [1 for _ in active]
    weight_sum = sum(raw_weights) or 1
    quotas = [total * weight / weight_sum for weight in raw_weights]
    counts = [int(q) for q in quotas]
    remainder = total - sum(counts)
    order = sorted(range(len(active)), key=lambda idx: quotas[idx] - counts[idx], reverse=True)
    for idx in order[:remainder]:
        counts[idx] += 1
    planned = []
    for item, count in zip(active, counts):
        planned.extend([key_getter(item)] * count)
    if len(planned) < total:
        planned.extend([key_getter(active[i % len(active)]) for i in range(total - len(planned))])
    return planned[:total]


def normalize_calendar_settings(value=None, draft: dict = None) -> dict:
    raw = value if isinstance(value, dict) else {}
    draft = draft or {}
    start = _parse_date(raw.get("start_date"), _parse_date(draft.get("start_date"), datetime.now().date()))
    end = _parse_date(raw.get("end_date"), _parse_date(draft.get("end_date"), start + timedelta(days=29)))
    if end < start:
        end = start
    if (end - start).days > 364:
        end = start + timedelta(days=364)
    platforms = [_canonical_platform(p) for p in (raw.get("platforms") or ["facebook", "linkedin"])]
    platforms = list(dict.fromkeys([p for p in platforms if p in PLATFORM_OPTIONS])) or ["facebook"]
    time_slots = [_parse_time_slot(slot) for slot in (raw.get("time_slots") or ["09:00"])] or ["09:00"]
    preferred_days = _weekday_indexes(raw.get("preferred_days") or raw.get("preferred_posting_days"))
    blackout_dates = sorted({str(_parse_date(d)) for d in raw.get("blackout_dates") or [] if _parse_date(d)})
    campaign_periods = raw.get("campaign_periods") or []
    important_events = raw.get("important_events") or []
    pillar_ratios = raw.get("pillar_ratios") or {}
    return {
        "start_date": str(start),
        "end_date": str(end),
        "posting_frequency": max(1, int(raw.get("posting_frequency") or raw.get("posts_per_week") or 3)),
        "platforms": platforms,
        "preferred_days": preferred_days,
        "time_slots": time_slots,
        "timezone": str(raw.get("timezone") or DEFAULT_TIMEZONE),
        "pillar_ratios": pillar_ratios if isinstance(pillar_ratios, dict) else {},
        "campaign_periods": campaign_periods if isinstance(campaign_periods, list) else [],
        "important_events": important_events if isinstance(important_events, list) else [],
        "blackout_dates": blackout_dates,
        "available_production_capacity": max(1, int(raw.get("available_production_capacity") or raw.get("production_capacity") or 20)),
        "evergreen_ratio": max(0, min(100, int(raw.get("evergreen_ratio") or 70))),
        "promotional_ratio": max(0, min(100, int(raw.get("promotional_ratio") or 20))),
        "view": raw.get("view") if raw.get("view") in CALENDAR_VIEW_OPTIONS else "list",
        "page_size": max(10, min(100, int(raw.get("page_size") or 50))),
    }


def normalize_calendar_item(value=None, sort_order=0, defaults: dict = None) -> dict:
    raw = value if isinstance(value, dict) else {}
    defaults = defaults or {}
    item_date = str(_parse_date(raw.get("date") or raw.get("planned_date"), _parse_date(defaults.get("date"), datetime.now().date())))
    item = {
        "id": raw.get("id") or f"calendar_{int(time.time() * 1000)}_{sort_order}",
        "date": item_date,
        "time": _parse_time_slot(raw.get("time") or defaults.get("time"), "09:00"),
        "timezone": raw.get("timezone") or defaults.get("timezone") or DEFAULT_TIMEZONE,
        "platform": _canonical_platform(raw.get("platform") or defaults.get("platform") or "facebook"),
        "format": _canonical_format(raw.get("format") or raw.get("content_type") or defaults.get("format") or "Short post"),
        "pillar": str(raw.get("pillar") or defaults.get("pillar") or "").strip(),
        "pillar_id": raw.get("pillar_id") or defaults.get("pillar_id") or "",
        "subtopic": str(raw.get("subtopic") or defaults.get("subtopic") or "").strip(),
        "subtopic_id": raw.get("subtopic_id") or defaults.get("subtopic_id") or "",
        "angle": str(raw.get("angle") or defaults.get("angle") or "").strip(),
        "angle_id": raw.get("angle_id") or defaults.get("angle_id") or "",
        "persona": str(raw.get("persona") or defaults.get("persona") or "").strip(),
        "business_goal": str(raw.get("business_goal") or defaults.get("business_goal") or "").strip(),
        "funnel_stage": _canonical_funnel_stage(raw.get("funnel_stage") or defaults.get("funnel_stage") or "awareness"),
        "working_title": str(raw.get("working_title") or raw.get("title") or defaults.get("working_title") or "Untitled content").strip(),
        "hook": str(raw.get("hook") or defaults.get("hook") or "").strip(),
        "cta": str(raw.get("cta") or defaults.get("cta") or "").strip(),
        "campaign": str(raw.get("campaign") or defaults.get("campaign") or "").strip(),
        "lead_magnet": str(raw.get("lead_magnet") or defaults.get("lead_magnet") or "").strip(),
        "production_owner": str(raw.get("production_owner") or defaults.get("production_owner") or "").strip(),
        "approval_status": raw.get("approval_status") if raw.get("approval_status") in CALENDAR_APPROVAL_STATUS_OPTIONS else defaults.get("approval_status", "draft"),
        "publishing_status": raw.get("publishing_status") if raw.get("publishing_status") in CALENDAR_PUBLISHING_STATUS_OPTIONS else defaults.get("publishing_status", "planned"),
        "notes": str(raw.get("notes") or defaults.get("notes") or "").strip(),
        "locked": bool(raw.get("locked", defaults.get("locked", False))),
        "content_mix": raw.get("content_mix") or defaults.get("content_mix") or "evergreen",
        "promotion_type": raw.get("promotion_type") or defaults.get("promotion_type") or "non_promotional",
        "sort_order": raw.get("sort_order", sort_order),
    }
    item["funnel_stage"] = _canonical_funnel_stage(item["funnel_stage"])
    return item


def normalize_content_calendar(value=None, draft: dict = None) -> dict:
    raw = value if isinstance(value, dict) else {}
    if isinstance(value, list):
        raw = {"items": value}
    settings = normalize_calendar_settings(raw.get("settings") or raw, draft=draft)
    items = [normalize_calendar_item(item, index, {"timezone": settings["timezone"]}) for index, item in enumerate(raw.get("items") or []) if isinstance(item, dict)]
    return {"settings": settings, "items": items}


def _calendar_campaign_for(item_date, settings: dict) -> str:
    for campaign in settings.get("campaign_periods") or []:
        if not isinstance(campaign, dict):
            continue
        start = _parse_date(campaign.get("start_date") or campaign.get("start"))
        end = _parse_date(campaign.get("end_date") or campaign.get("end"), start)
        if start and end and start <= item_date <= end:
            return campaign.get("name") or campaign.get("campaign") or "Campaign"
    for event in settings.get("important_events") or []:
        if not isinstance(event, dict):
            continue
        event_date = _parse_date(event.get("date"))
        if event_date == item_date:
            return event.get("name") or event.get("event") or "Important event"
    return ""


def _eligible_calendar_slots(settings: dict) -> list:
    start = _parse_date(settings.get("start_date"), datetime.now().date())
    end = _parse_date(settings.get("end_date"), start)
    blackout = set(settings.get("blackout_dates") or [])
    preferred_days = set(settings.get("preferred_days") or [0, 1, 2, 3, 4])
    slots = []
    cursor = start
    per_week = defaultdict(int)
    while cursor <= end:
        week_key = cursor.isocalendar()[:2]
        if str(cursor) not in blackout and cursor.weekday() in preferred_days and per_week[week_key] < settings["posting_frequency"]:
            for platform in settings["platforms"]:
                for time_slot in settings["time_slots"]:
                    slots.append({"date": cursor, "platform": platform, "time": time_slot})
            per_week[week_key] += 1
        cursor += timedelta(days=1)
    max_items = min(len(slots), settings["available_production_capacity"] * max(1, ((end - start).days // 7) + 1))
    return slots[:max_items]


def generate_content_calendar(draft: dict, settings: dict = None, existing_items: list = None, regenerate_unlocked: bool = False) -> dict:
    draft = draft or {}
    normalized_settings = normalize_calendar_settings(settings or {}, draft=draft)
    existing = [normalize_calendar_item(item, idx, {"timezone": normalized_settings["timezone"]}) for idx, item in enumerate(existing_items or [])]
    locked = [item for item in existing if item.get("locked")] if regenerate_unlocked else []
    slots = _eligible_calendar_slots(normalized_settings)
    occupied = {(item["date"], item["time"], item["platform"]) for item in locked}
    slots = [slot for slot in slots if (str(slot["date"]), slot["time"], slot["platform"]) not in occupied]

    pillars = normalize_content_pillars(draft.get("content_pillars") or [])
    subtopics = normalize_subtopics(draft.get("subtopics") or [])
    angles = normalize_content_angles(draft.get("content_angles") or [])
    variants = normalize_format_variants(draft.get("formats_channels") or [], brand=draft.get("brand_identity") or {})
    personas = [normalize_persona(p, idx) for idx, p in enumerate(draft.get("audience_personas") or []) if isinstance(p, dict)]
    goals = normalize_business_goals(draft.get("business_goals") or [])
    brand = normalize_brand_identity(draft.get("brand_identity") or {})

    total = len(slots)
    ratio_overrides = normalized_settings.get("pillar_ratios") or {}
    pillar_plan = _ratio_plan(
        pillars,
        total,
        lambda p: ratio_overrides.get(p.get("id"), ratio_overrides.get(p.get("name"), p.get("content_ratio", 0))),
        lambda p: p.get("id"),
    )
    if not pillar_plan:
        pillar_plan = ["" for _ in range(total)]

    funnel_cycle = ["awareness", "consideration", "evaluation", "retention", "conversion"]
    cta_cycle = ["comment", "save", "share", "learn_more", "lead_capture", "book_call"]
    items = list(locked)
    last_subtopic_by_pillar = {}
    promo_limit = int(total * normalized_settings["promotional_ratio"] / 100)
    evergreen_limit = int(total * normalized_settings["evergreen_ratio"] / 100)

    for index, slot in enumerate(slots):
        pillar_id = pillar_plan[index % len(pillar_plan)]
        pillar = next((p for p in pillars if str(p.get("id")) == str(pillar_id)), {})
        pillar_subtopics = [s for s in subtopics if str(s.get("pillar_id")) == str(pillar_id)] or subtopics
        subtopic = pillar_subtopics[index % len(pillar_subtopics)] if pillar_subtopics else {}
        if len(pillar_subtopics) > 1 and last_subtopic_by_pillar.get(pillar_id) == subtopic.get("id"):
            subtopic = pillar_subtopics[(index + 1) % len(pillar_subtopics)]
        last_subtopic_by_pillar[pillar_id] = subtopic.get("id")
        angle_pool = [a for a in angles if str(a.get("subtopic_id")) == str(subtopic.get("id"))] or angles
        angle = angle_pool[index % len(angle_pool)] if angle_pool else {}
        variant_pool = [v for v in variants if str(v.get("angle_id")) == str(angle.get("id")) and v.get("platform") == slot["platform"]] or [v for v in variants if v.get("platform") == slot["platform"]] or variants
        variant = variant_pool[index % len(variant_pool)] if variant_pool else {}
        persona = personas[index % len(personas)] if personas else {}
        goal = goals[index % len(goals)] if goals else {}
        is_promo = index < promo_limit and (index % 4 == 0 or promo_limit >= total)
        is_evergreen = index < evergreen_limit
        lead_capture = cta_cycle[index % len(cta_cycle)] == "lead_capture" or is_promo
        campaign = _calendar_campaign_for(slot["date"], normalized_settings)
        working_title = angle.get("working_title") or f"{subtopic.get('name') or pillar.get('name') or 'Content'} for {persona.get('name') or 'audience'}"
        item = normalize_calendar_item({
            "date": str(slot["date"]),
            "time": slot["time"],
            "timezone": normalized_settings["timezone"],
            "platform": slot["platform"],
            "format": variant.get("format") or "Short post",
            "pillar": pillar.get("name", ""),
            "pillar_id": pillar.get("id", ""),
            "subtopic": subtopic.get("name", ""),
            "subtopic_id": subtopic.get("id", ""),
            "angle": angle.get("working_title", ""),
            "angle_id": angle.get("id", ""),
            "persona": persona.get("name", ""),
            "business_goal": goal.get("name") or subtopic.get("business_goal", ""),
            "funnel_stage": angle.get("funnel_stage") or subtopic.get("funnel_stage") or funnel_cycle[index % len(funnel_cycle)],
            "working_title": working_title,
            "hook": angle.get("hook_idea") or variant.get("hook_style") or f"What most teams miss about {subtopic.get('name') or pillar.get('name') or 'this topic'}",
            "cta": variant.get("cta") or brand.get("standard_cta") or ("Download the guide" if lead_capture else cta_cycle[index % len(cta_cycle)]),
            "campaign": campaign,
            "lead_magnet": "Lead capture asset" if lead_capture else "",
            "production_owner": "",
            "approval_status": "draft",
            "publishing_status": "planned",
            "notes": variant.get("brief", ""),
            "content_mix": "evergreen" if is_evergreen else "trending",
            "promotion_type": "promotional" if is_promo else "non_promotional",
            "sort_order": len(items),
        }, len(items), {"timezone": normalized_settings["timezone"]})
        items.append(item)
    items = sorted(items, key=lambda item: (item["date"], item["time"], item["platform"], item.get("sort_order", 0)))
    for index, item in enumerate(items):
        item["sort_order"] = index
    return {"settings": normalized_settings, "items": items, "diagnostics": analyze_content_calendar(items, normalized_settings)}


def analyze_content_calendar(items: list, settings: dict = None) -> dict:
    settings = normalize_calendar_settings(settings or {})
    normalized = [normalize_calendar_item(item, idx, {"timezone": settings["timezone"]}) for idx, item in enumerate(items or [])]
    start = _parse_date(settings.get("start_date"))
    end = _parse_date(settings.get("end_date"))
    conflicts = []
    seen_slots = {}
    seen_titles = {}
    repetition = []
    subtopic_dates = defaultdict(list)
    for item in normalized:
        item_date = _parse_date(item.get("date"))
        if start and end and item_date and not (start <= item_date <= end):
            conflicts.append({"id": item.get("id"), "type": "out_of_range", "message": "Item date is outside calendar range."})
        slot_key = (item.get("date"), item.get("time"), item.get("platform"))
        if slot_key in seen_slots:
            conflicts.append({"id": item.get("id"), "type": "slot_conflict", "message": "Same date/time/platform as another item."})
        seen_slots[slot_key] = item.get("id")
        title_key = _normalize_text_key(item.get("working_title"))
        if title_key and title_key in seen_titles:
            repetition.append({"id": item.get("id"), "type": "duplicate_title", "message": "Working title repeats."})
        seen_titles[title_key] = item.get("id")
        if item.get("subtopic") and item_date:
            subtopic_dates[item.get("subtopic")].append((item_date, item.get("id")))
    for subtopic, dated in subtopic_dates.items():
        dated = sorted(dated)
        for previous, current in zip(dated, dated[1:]):
            if (current[0] - previous[0]).days < 7:
                repetition.append({"id": current[1], "type": "subtopic_too_close", "message": f"Subtopic repeats within 7 days: {subtopic}."})
    pillar_counts = Counter(item.get("pillar") for item in normalized if item.get("pillar"))
    promo_count = sum(1 for item in normalized if item.get("promotion_type") == "promotional")
    return {
        "total_items": len(normalized),
        "conflicts": conflicts,
        "repetition": repetition,
        "pillar_counts": dict(pillar_counts),
        "promotional_count": promo_count,
        "promotional_ratio": round((promo_count / len(normalized) * 100), 2) if normalized else 0,
        "locked_count": sum(1 for item in normalized if item.get("locked")),
    }


def validate_campaign_missing_cta(campaigns: list) -> dict:
    normalized = campaigns or []
    missing = [campaign for campaign in normalized if not str(campaign.get("cta") or "").strip()]
    return {"ok": not missing, "missing_count": len(missing), "campaign_ids": [item.get("id") for item in missing], "campaigns": missing}


def validate_funnel_stage_balance(items: list, minimum_share: float = 0.1, maximum_share: float = 0.45) -> dict:
    normalized = [normalize_calendar_item(item, index) for index, item in enumerate(items or [])]
    counts = Counter(_canonical_funnel_stage(item.get("funnel_stage")) for item in normalized)
    total = len(normalized)
    stages = {stage: counts.get(stage, 0) for stage in FUNNEL_STAGE_OPTIONS}
    issues = []
    for stage, count in stages.items():
        share = (count / total) if total else 0
        if total and share < minimum_share:
            issues.append({"type": "underrepresented", "stage": stage, "count": count, "share": round(share, 4)})
        if total and share > maximum_share:
            issues.append({"type": "overrepresented", "stage": stage, "count": count, "share": round(share, 4)})
    return {"ok": not issues, "total_items": total, "stage_counts": stages, "issues": issues}


def validate_sales_content_ratio(items: list, maximum_ratio: float = 0.3) -> dict:
    normalized = [normalize_calendar_item(item, index) for index, item in enumerate(items or [])]
    sales_terms = {"book", "demo", "buy", "purchase", "consult", "pricing", "sales", "call"}
    sales_items = []
    for item in normalized:
        cta_text = str(item.get("cta") or "").lower()
        is_sales = item.get("promotion_type") == "promotional" or any(term in cta_text for term in sales_terms) or item.get("funnel_stage") == "conversion"
        if is_sales:
            sales_items.append(item)
    ratio = (len(sales_items) / len(normalized)) if normalized else 0
    return {"ok": ratio <= maximum_ratio, "sales_count": len(sales_items), "total_items": len(normalized), "sales_ratio": round(ratio, 4), "item_ids": [item.get("id") for item in sales_items]}


def recommend_lead_magnet(draft: dict, calendar_items: list = None, campaign: dict = None) -> dict:
    draft = draft or {}
    personas = [normalize_persona(item, idx) for idx, item in enumerate(draft.get("audience_personas") or []) if isinstance(item, dict)]
    subtopics = normalize_subtopics(draft.get("subtopics") or [])
    items = [normalize_calendar_item(item, idx) for idx, item in enumerate(calendar_items or [])]
    target = personas[0] if personas else {}
    pain_points = target.get("pain_points") or []
    conversion_item = next((item for item in items if item.get("funnel_stage") in {"consideration", "evaluation", "conversion"}), {})
    subtopic = next((item for item in subtopics if str(item.get("id")) == str(conversion_item.get("subtopic_id"))), subtopics[0] if subtopics else {})
    asset_type = "Checklist"
    if conversion_item.get("funnel_stage") == "evaluation":
        asset_type = "Assessment"
    elif conversion_item.get("funnel_stage") == "conversion":
        asset_type = "Consultation"
    elif "prompt" in str(subtopic.get("name") or "").lower():
        asset_type = "Prompt Pack"
    name_seed = subtopic.get("name") or conversion_item.get("working_title") or ((campaign or {}).get("name")) or "Lead Magnet"
    return {
        "name": f"{name_seed} {asset_type}",
        "type": asset_type,
        "description": f"Planned {asset_type.lower()} for {target.get('name') or 'target persona'}.",
        "target_persona": target.get("name", ""),
        "pain_point": pain_points[0] if pain_points else subtopic.get("intent", ""),
        "value_proposition": f"Help the audience act on {subtopic.get('name') or conversion_item.get('working_title') or 'the campaign message'}.",
        "cta": campaign.get("cta", "") if campaign else "",
        "destination_url": "",
        "campaign_id": campaign.get("id") if campaign else None,
        "funnel_stage": conversion_item.get("funnel_stage") or subtopic.get("funnel_stage") or "consideration",
        "status": "planned",
        "asset_reference": "",
        "source": "ai_recommendation",
    }


def _post_platform_for_calendar(platform: str) -> str:
    platform = _canonical_platform(platform)
    return "zalo" if platform == "zalo_oa" else platform


def _calendar_platform_for_post(platform: str) -> str:
    return "zalo_oa" if str(platform or "").lower() == "zalo" else _canonical_platform(platform)


def _configuration_issue(platform: str) -> str:
    platform = _calendar_platform_for_post(platform)
    if platform == "facebook" and not (settings.FB_PAGE_ID and settings.FB_ACCESS_TOKEN):
        return "Facebook Page ID or access token is not configured."
    if platform == "zalo_oa" and not settings.ZALO_ACCESS_TOKEN:
        return "Zalo OA access token is not configured."
    if platform == "linkedin" and not (settings.LINKEDIN_AUTHOR_URN and settings.LINKEDIN_ACCESS_TOKEN):
        return "LinkedIn author URN or access token is not configured."
    if platform not in PUBLISHING_SUPPORTED_PLATFORMS:
        return "Publishing is not supported for this platform."
    return ""


def _safe_calendar_item_content(item: dict) -> str:
    metadata = item.get("metadata") or {}
    content_parts = [item.get("brief") or "", metadata.get("hook") or "", metadata.get("notes") or ""]
    return "\n\n".join([part for part in content_parts if str(part).strip()]) or item.get("title") or "Draft content"


def _approval_required_for_item(item: dict, explicit: bool = None) -> bool:
    if explicit is not None:
        return bool(explicit)
    metadata = item.get("metadata") or {}
    return bool(metadata.get("approval_required") or metadata.get("requires_approval"))


def _latest_approval_status(post_id: int) -> str:
    latest = ApprovalModel.get_latest_by_post(post_id)
    return latest.get("status") or "not_requested"


def sync_calendar_publishing_status(workspace_id: int, company_id: int, strategy_id: int, calendar_item_id: int, updated_by: int = None) -> dict:
    try:
        ContentStrategyRepository.ensure_tables()
        items = ContentStrategyRepository.list_calendar_items(workspace_id, company_id, strategy_id)
        item = next((row for row in items if int(row.get("id")) == int(calendar_item_id)), None)
        if not item:
            return {"ok": False, "error": "Calendar item not found for this strategy"}
        publishing_status = item.get("publishing_status") or (item.get("metadata") or {}).get("publishing_status") or "planned"
        approval_status = item.get("approval_status") or (item.get("metadata") or {}).get("approval_status") or "draft"
        post_id = item.get("post_id")
        schedule_id = item.get("schedule_id")
        if post_id:
            post = PostModel.get_by_id(post_id)
            if not post or post.get("workspace_id") != workspace_id:
                return {"ok": False, "error": "Linked post not found for this workspace"}
            post_status = post.get("status")
            if post_status in {"pending_manager_approval", "pending_ceo_approval", "pending_approval"}:
                approval_status = "in_review"
                publishing_status = "approval_required"
            elif post_status == "approved":
                approval_status = "approved"
                publishing_status = "approved"
            elif post_status == "published":
                approval_status = "approved"
                publishing_status = "published"
            elif post_status == "failed":
                publishing_status = "failed"
            elif post_status == "draft" and publishing_status == "planned":
                publishing_status = "draft_created"
            latest = ApprovalModel.get_latest_by_post(post_id)
            if latest.get("status") == "pending":
                approval_status = "in_review"
            elif latest.get("status") == "approved":
                approval_status = "approved"
            elif latest.get("status") in {"rejected", "revision_requested"}:
                approval_status = "rejected"
        if schedule_id:
            schedule = ScheduleModel.get_by_id(schedule_id)
            if schedule and schedule.get("workspace_id") == workspace_id:
                sched_status = schedule.get("status")
                if sched_status == "published":
                    publishing_status = "published"
                elif sched_status == "failed":
                    publishing_status = "failed"
                elif sched_status == "processing":
                    publishing_status = "publishing"
                elif sched_status == "pending":
                    publishing_status = "scheduled"
        metadata = dict(item.get("metadata") or {})
        metadata.update({"approval_status": approval_status, "publishing_status": publishing_status})
        ContentStrategyRepository.update_calendar_item(workspace_id, company_id, strategy_id, calendar_item_id, approval_status=approval_status, publishing_status=publishing_status, metadata=metadata, updated_by=updated_by)
        return {"ok": True, "approval_status": approval_status, "publishing_status": publishing_status}
    except Exception as exc:
        return {"ok": False, "error": _safe_error_message(exc)}


def check_publishing_readiness(workspace_id: int, company_id: int, strategy_id: int, calendar_item_id: int = None, platform: str = None) -> dict:
    try:
        ContentStrategyRepository.ensure_tables()
        strategy = ContentStrategyRepository.get_strategy(workspace_id, company_id, strategy_id, include_children=True)
        if not strategy:
            return {"ok": False, "ready": False, "issues": [{"code": "not_found", "message": "Strategy not found for this workspace/company"}]}
        items = strategy.get("calendar_items") or []
        if calendar_item_id:
            items = [item for item in items if int(item.get("id")) == int(calendar_item_id)]
        if platform:
            items = [item for item in items if _calendar_platform_for_post(item.get("platform")) == _calendar_platform_for_post(platform)]
        issues = []
        rows = []
        for item in items:
            item_platform = _calendar_platform_for_post(item.get("platform"))
            issue = _configuration_issue(item_platform)
            status = item.get("publishing_status") or (item.get("metadata") or {}).get("publishing_status") or "planned"
            if issue:
                issues.append({"calendar_item_id": item.get("id"), "platform": item_platform, "code": "configuration_required", "message": issue})
                status = "configuration_required"
            if item.get("post_id"):
                sync = sync_calendar_publishing_status(workspace_id, company_id, strategy_id, item.get("id"))
                if sync.get("ok"):
                    status = sync.get("publishing_status", status)
            rows.append({"calendar_item_id": item.get("id"), "platform": item_platform, "ready": not issue, "publishing_status": status, "post_id": item.get("post_id"), "schedule_id": item.get("schedule_id")})
        return {"ok": True, "ready": not issues, "issues": issues, "items": rows}
    except Exception as exc:
        return {"ok": False, "ready": False, "issues": [{"code": "readiness_failed", "message": _safe_error_message(exc)}]}


def handoff_calendar_item_to_content_studio_draft(workspace_id: int, company_id: int, strategy_id: int, calendar_item_id: int, confirmed: bool = False, created_by: int = None, approval_required: bool = None) -> dict:
    if not confirmed:
        return {"ok": False, "error": "User confirmation required before creating a Content Studio draft."}
    try:
        ContentStrategyRepository.ensure_tables()
        strategy = ContentStrategyRepository.get_strategy(workspace_id, company_id, strategy_id, include_children=True)
        if not strategy:
            return {"ok": False, "error": "Strategy not found for this workspace/company"}
        item = next((row for row in strategy.get("calendar_items", []) if int(row.get("id")) == int(calendar_item_id)), None)
        if not item:
            return {"ok": False, "error": "Calendar item not found for this strategy"}
        if item.get("post_id"):
            post = PostModel.get_by_id(item["post_id"])
            if post and post.get("workspace_id") == workspace_id:
                sync_calendar_publishing_status(workspace_id, company_id, strategy_id, calendar_item_id, updated_by=created_by)
                return {"ok": True, "post_id": item["post_id"], "status": post.get("status", "draft"), "duplicate_prevented": True}
        metadata = dict(item.get("metadata") or {})
        requires_approval = _approval_required_for_item(item, approval_required)
        post_status = "pending_manager_approval" if requires_approval else "draft"
        post_id = PostModel.create(
            content=_safe_calendar_item_content(item),
            platform=_post_platform_for_calendar(item.get("platform") or "facebook"),
            content_type=item.get("content_type") or "marketing_viral",
            topic=metadata.get("subtopic") or item.get("title") or "",
            title=item.get("title") or metadata.get("working_title") or "Untitled draft",
            status=post_status,
            campaign_id=item.get("campaign_id"),
            workspace_id=workspace_id,
            ai_metadata={"source": "content_strategy_calendar", "strategy_id": strategy_id, "calendar_item_id": calendar_item_id, "approval_required": requires_approval, "publishing_status": "draft_created"},
            created_by=created_by,
        )
        approval_status = "in_review" if requires_approval else "draft"
        publishing_status = "approval_required" if requires_approval else "draft_created"
        metadata.update({"approval_status": approval_status, "publishing_status": publishing_status})
        ContentStrategyRepository.update_calendar_item(workspace_id, company_id, strategy_id, calendar_item_id, post_id=post_id, approval_status=approval_status, publishing_status=publishing_status, metadata=metadata, updated_by=created_by)
        approval_id = None
        if requires_approval:
            approval_id = ApprovalModel.request(post_id, requested_by=created_by, workspace_id=workspace_id)
        log_action(action="HANDOFF_CALENDAR_ITEM_TO_DRAFT", user_id=created_by, workspace_id=workspace_id, entity_type="post", entity_id=post_id, description="Converted Content Calendar item to Content Studio draft.", new_value={"company_id": company_id, "strategy_id": strategy_id, "calendar_item_id": calendar_item_id, "status": post_status, "approval_required": requires_approval})
        return {"ok": True, "post_id": post_id, "approval_id": approval_id, "status": post_status, "publishing_status": publishing_status, "approval_status": approval_status}
    except Exception as exc:
        return {"ok": False, "error": _safe_error_message(exc)}


def send_selected_calendar_items_to_content_studio(workspace_id: int, company_id: int, strategy_id: int, calendar_item_ids: list, confirmed: bool = False, created_by: int = None, approval_required: bool = None) -> dict:
    results = [handoff_calendar_item_to_content_studio_draft(workspace_id, company_id, strategy_id, item_id, confirmed=confirmed, created_by=created_by, approval_required=approval_required) for item_id in (calendar_item_ids or [])]
    return {"ok": all(item.get("ok") for item in results), "results": results, "created": len([item for item in results if item.get("ok") and not item.get("duplicate_prevented")]), "duplicates": len([item for item in results if item.get("duplicate_prevented")])}


def send_campaign_batch_to_content_studio(workspace_id: int, company_id: int, strategy_id: int, campaign_id: int, confirmed: bool = False, created_by: int = None, approval_required: bool = None) -> dict:
    try:
        items = ContentStrategyRepository.list_calendar_items(workspace_id, company_id, strategy_id)
        selected = [item.get("id") for item in items if item.get("campaign_id") == campaign_id]
        return send_selected_calendar_items_to_content_studio(workspace_id, company_id, strategy_id, selected, confirmed=confirmed, created_by=created_by, approval_required=approval_required)
    except Exception as exc:
        return {"ok": False, "error": _safe_error_message(exc), "results": []}


def create_strategy_kpi(workspace_id: int, company_id: int, strategy_id: int, metric: str, **kwargs) -> dict:
    try:
        ContentStrategyRepository.ensure_tables()
        metric = str(metric or "").strip()
        if metric not in KPI_METRIC_OPTIONS:
            return {"ok": False, "error": "Unsupported KPI metric"}
        kpi_id = ContentStrategyRepository.create_kpi(workspace_id, company_id, strategy_id, metric, **kwargs)
        return {"ok": True, "kpi_id": kpi_id}
    except Exception as exc:
        return {"ok": False, "error": _safe_error_message(exc)}


def list_strategy_kpis(workspace_id: int, company_id: int, strategy_id: int, scope_level: str = None) -> dict:
    try:
        ContentStrategyRepository.ensure_tables()
        return {"ok": True, "kpis": ContentStrategyRepository.list_kpis(workspace_id, company_id, strategy_id, scope_level=scope_level)}
    except Exception as exc:
        return {"ok": False, "error": _safe_error_message(exc), "kpis": []}


def move_calendar_item(items: list, item_id: str, new_date: str, new_time: str = None) -> list:
    moved = []
    for index, item in enumerate(items or []):
        normalized = normalize_calendar_item(item, index)
        if str(normalized.get("id")) == str(item_id) and not normalized.get("locked"):
            normalized["date"] = str(_parse_date(new_date, _parse_date(normalized["date"])))
            if new_time:
                normalized["time"] = _parse_time_slot(new_time, normalized["time"])
        moved.append(normalized)
    return moved


def duplicate_calendar_item(items: list, item_id: str) -> list:
    duplicated = [normalize_calendar_item(item, index) for index, item in enumerate(items or [])]
    source = next((item for item in duplicated if str(item.get("id")) == str(item_id)), None)
    if source:
        copy_item = dict(source)
        copy_item["id"] = f"calendar_{int(time.time() * 1000)}_{len(duplicated)}"
        copy_item["working_title"] = f"{source.get('working_title', 'Untitled content')} Copy"
        copy_item["locked"] = False
        copy_item["sort_order"] = len(duplicated)
        duplicated.append(copy_item)
    return duplicated


def delete_calendar_items(items: list, item_ids: list) -> list:
    ids = {str(item_id) for item_id in item_ids or []}
    return [normalize_calendar_item(item, index) for index, item in enumerate(items or []) if str(item.get("id")) not in ids or item.get("locked")]


def bulk_reschedule_calendar_items(items: list, item_ids: list, day_delta: int = 0, timezone: str = None) -> list:
    ids = {str(item_id) for item_id in item_ids or []}
    rescheduled = []
    for index, item in enumerate(items or []):
        normalized = normalize_calendar_item(item, index)
        if str(normalized.get("id")) in ids and not normalized.get("locked"):
            item_date = _parse_date(normalized["date"])
            normalized["date"] = str(item_date + timedelta(days=int(day_delta or 0))) if item_date else normalized["date"]
            if timezone:
                normalized["timezone"] = timezone
        rescheduled.append(normalized)
    return rescheduled


def lock_calendar_items(items: list, item_ids: list, locked: bool = True) -> list:
    ids = {str(item_id) for item_id in item_ids or []}
    locked_items = []
    for index, item in enumerate(items or []):
        normalized = normalize_calendar_item(item, index)
        if str(normalized.get("id")) in ids:
            normalized["locked"] = bool(locked)
        locked_items.append(normalized)
    return locked_items


def validate_format_variants(variants: list, angles: list = None, brand: dict = None) -> tuple[list, list]:
    errors = []
    warnings = []
    normalized = normalize_format_variants(variants, brand=brand)
    angle_ids = {str(a.get("id")) for a in normalize_content_angles(angles or []) if a.get("id")}
    seen = set()
    forbidden = [w.lower() for w in _brand_list(brand or {}, "forbidden_words")]
    brand_cta = (normalize_brand_identity(brand or {}).get("standard_cta") or "").strip()
    for index, item in enumerate(normalized):
        label = f"Format variant {index + 1}"
        key = (item.get("angle_id"), item.get("platform"), item.get("format"))
        if key in seen:
            errors.append(f"Duplicate format variant for angle/platform/format: {item.get('platform')} / {item.get('format')}.")
        seen.add(key)
        if angle_ids and str(item.get("angle_id")) not in angle_ids:
            errors.append(f"{label} must link to an existing Content Angle.")
        for field in ["platform", "format", "target_length", "cta", "hook_style", "publishing_objective", "repurposing_source", "adaptation_guidance"]:
            if not str(item.get(field, "")).strip():
                errors.append(f"{label} missing: {field.replace('_', ' ')}.")
        if item.get("platform") not in PUBLISHING_SUPPORTED_PLATFORMS and item.get("publishing_enabled"):
            errors.append(f"{label} cannot enable direct publishing for unsupported platform: {item.get('platform')}.")
        if item.get("platform") == "zalo_oa" and "#" in f"{item.get('hook_style')} {item.get('adaptation_guidance')}" and "hashtag" not in json.dumps(brand or {}, ensure_ascii=False).lower():
            errors.append(f"{label} must not add Zalo hashtags unless brand rules require them.")
        if item.get("format") in VIDEO_FORMATS:
            brief = (item.get("brief") or "").lower()
            if not all(token in brief for token in ["hook", "body", "cta"]):
                errors.append(f"{label} video brief needs hook, body, and CTA outline.")
        text = json.dumps(item, ensure_ascii=False).lower()
        for word in forbidden:
            if word and word in text:
                errors.append(f"{label} contains forbidden brand word: {word}.")
        if brand_cta and item.get("cta") and brand_cta.lower() not in item.get("cta", "").lower():
            warnings.append(f"{label} CTA differs from brand guideline.")
    if not normalized:
        errors.append("Formats and Channels needs at least one variant.")
    repurpose_counts = {}
    for item in normalized:
        repurpose_counts[item.get("repurposing_source")] = repurpose_counts.get(item.get("repurposing_source"), 0) + 1
    if normalized and max(repurpose_counts.values() or [0]) <= 1:
        warnings.append("No angle is repurposed across multiple platforms yet.")
    return errors, warnings


def validate_subtopics(subtopics: list, pillars: list = None) -> tuple[list, list]:
    errors = []
    warnings = []
    normalized = normalize_subtopics(subtopics)
    pillar_ids = {str(p.get("id")) for p in normalize_content_pillars(pillars or []) if p.get("id")}
    seen = set()
    served_pillars = set()
    for index, item in enumerate(normalized):
        label = f"Subtopic {index + 1}"
        key = _normalize_text_key(item.get("name"))
        if not item.get("name"):
            errors.append(f"{label} needs a name.")
        elif key in seen:
            errors.append(f"Duplicate subtopic name: {item['name']}.")
        seen.add(key)
        for field in ["description", "target_persona", "business_goal", "intent"]:
            if not str(item.get(field, "")).strip():
                errors.append(f"{label} missing: {field.replace('_', ' ')}.")
        if pillar_ids and str(item.get("pillar_id")) not in pillar_ids:
            errors.append(f"{label} must belong to an existing Pillar.")
        if not item.get("suggested_channels"):
            warnings.append(f"{label} has no suggested channels.")
        served_pillars.add(str(item.get("pillar_id")))
    missing = sorted(pillar_ids - served_pillars)
    if pillar_ids and missing:
        warnings.append(f"Pillars without subtopics: {len(missing)}.")
    if not normalized:
        errors.append("Subtopics needs at least one item.")
    _, duplicates = _dedupe_items(normalized, lambda x: x.get("name", ""))
    for duplicate in duplicates:
        warnings.append(f"Subtopics may overlap: {duplicate['name']} / {duplicate['duplicate_of']}.")
    return errors, warnings


def validate_content_angles(angles: list, subtopics: list = None) -> tuple[list, list]:
    errors = []
    warnings = []
    normalized = normalize_content_angles(angles)
    subtopic_ids = {str(s.get("id")) for s in normalize_subtopics(subtopics or []) if s.get("id")}
    seen = set()
    for index, item in enumerate(normalized):
        label = f"Angle {index + 1}"
        key = _normalize_text_key(item.get("working_title"))
        if not item.get("working_title"):
            errors.append(f"{label} needs a working title.")
        elif key in seen:
            errors.append(f"Duplicate angle title: {item['working_title']}.")
        seen.add(key)
        for field in ["hook_idea", "core_insight", "intended_emotion", "target_persona", "evidence_requirement"]:
            if not str(item.get(field, "")).strip():
                errors.append(f"{label} missing: {field.replace('_', ' ')}.")
        if subtopic_ids and str(item.get("subtopic_id")) not in subtopic_ids:
            errors.append(f"{label} must belong to an existing Subtopic.")
        if item.get("risk_level") == "high":
            warnings.append(f"{label} is high risk and needs stronger evidence/review.")
    if not normalized:
        errors.append("Content Angles needs at least one item.")
    _, duplicates = _dedupe_items(normalized, lambda x: f"{x.get('working_title', '')} {x.get('core_insight', '')}")
    for duplicate in duplicates:
        warnings.append(f"Angles may overlap: {duplicate['name']} / {duplicate['duplicate_of']}.")
    return errors, warnings


def merge_subtopics(items: list, index: int) -> list:
    if index <= 0 or index >= len(items):
        return items
    previous = normalize_subtopic(items[index - 1], index - 1)
    current = normalize_subtopic(items[index], index)
    previous["description"] = "\n".join([x for x in [previous.get("description"), current.get("description")] if x]).strip()
    for field in ["target_persona", "business_goal", "intent"]:
        previous[field] = previous.get(field) or current.get(field)
    previous["suggested_channels"] = list(dict.fromkeys((previous.get("suggested_channels") or []) + (current.get("suggested_channels") or [])))
    previous["manual_edits"] = True
    previous["source"] = "manual"
    merged = list(items)
    merged[index - 1] = previous
    merged.pop(index)
    for idx, item in enumerate(merged):
        item["sort_order"] = idx
    return merged


def split_subtopic(item: dict) -> list:
    source = normalize_subtopic(item)
    first = normalize_subtopic({**source, "id": f"{source.get('id')}_a", "name": f"{source.get('name')} - Part 1", "source": "manual", "manual_edits": True}, 0)
    second = normalize_subtopic({**source, "id": f"{source.get('id')}_b", "name": f"{source.get('name')} - Part 2", "description": "", "source": "manual", "manual_edits": True}, 1)
    return [first, second]


def validate_business_goals(goals: list) -> tuple[list, list]:
    errors = []
    warnings = []
    normalized = normalize_business_goals(goals)
    seen = set()
    for index, goal in enumerate(normalized):
        label = f"Business goal {index + 1}"
        key = goal.get("name", "").lower()
        if not goal.get("name"):
            errors.append(f"{label} needs a name.")
        elif key in seen:
            errors.append(f"Duplicate business goal name: {goal['name']}.")
        seen.add(key)
        for field in ["description", "target_metric", "target_value", "time_period"]:
            if not str(goal.get(field, "")).strip():
                errors.append(f"{label} missing: {field.replace('_', ' ')}.")
        if not goal.get("target_personas"):
            warnings.append(f"{label} has no target personas.")
        if not goal.get("preferred_platforms"):
            warnings.append(f"{label} has no preferred platforms.")
    if not normalized:
        errors.append("Business Goals needs at least one selected goal.")
    return errors, warnings


def validate_content_pillars(pillars: list, business_goals: list = None, personas: list = None) -> tuple[list, list]:
    errors = []
    warnings = []
    normalized = normalize_content_pillars(pillars)
    active = [p for p in normalized if p.get("status") == "active"]
    seen = set()
    active_ratio = sum(int(p.get("content_ratio") or 0) for p in active)
    goal_names = {g.get("name") for g in normalize_business_goals(business_goals or []) if g.get("name")}
    persona_names = {p.get("name") for p in [normalize_persona(x, i) for i, x in enumerate(personas or [])] if p.get("name")}
    served_personas = set()

    for index, pillar in enumerate(normalized):
        label = f"Pillar {index + 1}"
        key = pillar.get("name", "").lower()
        if not pillar.get("name"):
            errors.append(f"{label} needs a name.")
        elif key in seen:
            errors.append(f"Duplicate pillar name: {pillar['name']}.")
        seen.add(key)
        for field in ["description", "strategic_purpose", "differentiation_angle"]:
            if not str(pillar.get(field, "")).strip():
                errors.append(f"{label} missing: {field.replace('_', ' ')}.")
        if pillar.get("status") == "active" and int(pillar.get("content_ratio") or 0) <= 0:
            errors.append(f"{label} active content ratio must be greater than 0.")
        if not pillar.get("business_goals"):
            warnings.append(f"{label} is not attached to a Business Goal.")
        elif goal_names:
            missing_goals = [goal for goal in pillar.get("business_goals") if goal not in goal_names]
            if missing_goals:
                warnings.append(f"{label} references goal not selected in Step 4: {', '.join(missing_goals)}.")
        if not pillar.get("target_personas"):
            warnings.append(f"{label} has no target personas.")
        served_personas.update(pillar.get("target_personas") or [])
        word_count = len(str(pillar.get("description", "")).split())
        if word_count > 45 or any(term in pillar.get("name", "").lower() for term in ["everything", "all", "general"]):
            warnings.append(f"{label} may be too broad.")

    if normalized and active_ratio != 100:
        errors.append(f"Active pillar content ratio must total 100%. Current total: {active_ratio}%.")
    if not normalized:
        errors.append("Content Pillars needs at least one pillar.")
    for idx, first in enumerate(normalized):
        first_words = set(first.get("name", "").lower().split())
        for second in normalized[idx + 1:]:
            second_words = set(second.get("name", "").lower().split())
            if first_words and second_words and len(first_words & second_words) / max(len(first_words | second_words), 1) >= 0.6:
                warnings.append(f"Pillars may be too similar: {first.get('name')} / {second.get('name')}.")
    unserved = sorted(persona_names - served_personas)
    if unserved:
        warnings.append("Personas not served by any pillar: " + ", ".join(unserved) + ".")
    return errors, warnings


class ContentStrategyGenerationError(RuntimeError):
    def __init__(self, code: str, message: str, retryable: bool = False, details=None):
        super().__init__(message)
        self.code = code
        self.retryable = retryable
        self.details = details or {}

    def to_dict(self):
        return {
            "ok": False,
            "error": {
                "code": self.code,
                "message": str(self),
                "retryable": self.retryable,
                "details": self.details,
            },
        }


def _safe_error_message(exc: Exception) -> str:
    text = str(exc)
    sensitive_words = ["api_key", "authorization", "access_token", "bearer", "jwt", "password", "secret"]
    lowered = text.lower()
    if any(word in lowered for word in sensitive_words):
        return "Sensitive provider error redacted"
    return text[:500]


def _is_retryable(exc: Exception) -> bool:
    text = str(exc).lower()
    retry_markers = [
        "429", "rate limit", "quota", "503", "unavailable",
        "timeout", "timed out", "database is locked", "database locked",
        "connection reset", "connection aborted", "lost connection", "temporarily",
    ]
    return any(code in text for code in retry_markers)


class StrategyContextService:
    MAX_KNOWLEDGE_ITEMS = 5
    MAX_KNOWLEDGE_CHARS = 900

    @staticmethod
    def build_context(workspace_id: int, company_id: int, inputs: dict = None) -> dict:
        inputs = inputs or {}
        company = CompanyModel.get_by_id(company_id)
        if not company or company.get("workspace_id") != workspace_id:
            raise ValueError("Company does not belong to workspace")

        brand = BrandModel.get_by_workspace(workspace_id)
        knowledge = []
        try:
            df = KnowledgeRepository.get_knowledge_posts(workspace_id=workspace_id, limit=StrategyContextService.MAX_KNOWLEDGE_ITEMS)
            if hasattr(df, "to_dict"):
                for item in df.to_dict("records")[:StrategyContextService.MAX_KNOWLEDGE_ITEMS]:
                    knowledge.append({
                        "title": str(item.get("title") or item.get("topic") or "")[:120],
                        "summary": str(item.get("summary") or item.get("content") or "")[:StrategyContextService.MAX_KNOWLEDGE_CHARS],
                        "type": item.get("knowledge_type", ""),
                    })
        except Exception as exc:
            logger.warning("[CONTENT_STRATEGY] Could not load knowledge context: %s", _safe_error_message(exc))

        learning_context = ""
        try:
            from workflow.learning_engine import get_insights_as_context
            learning_context = get_insights_as_context(workspace_id, max_insights=5)
        except Exception as exc:
            logger.warning("[CONTENT_STRATEGY] Could not load learning context: %s", _safe_error_message(exc))

        return {
            "company": {
                "name": company.get("name", ""),
                "industry": company.get("industry", ""),
                "description": company.get("description", ""),
                "products_services": company.get("products", ""),
                "target_customers": company.get("target_customers", ""),
            },
            "brand_identity": {
                "tone_of_voice": brand.get("tone_of_voice", ""),
                "target_audiences": brand.get("target_audiences", []),
                "tagline": brand.get("tagline", ""),
                "brand_guidelines": brand.get("brand_guidelines", ""),
                "cta": brand.get("cta", ""),
                "vision": brand.get("vision", ""),
                "mission": brand.get("mission", ""),
                "keywords": brand.get("keywords", []),
                "blacklist_words": brand.get("blacklist_words", []),
            },
            "strategy_inputs": {
                "audience_personas": inputs.get("audience_personas", []),
                "business_goals": inputs.get("business_goals", []),
                "preferred_platforms": inputs.get("preferred_platforms", []),
                "publishing_frequency": inputs.get("publishing_frequency", ""),
                "start_date": inputs.get("start_date"),
                "end_date": inputs.get("end_date"),
                "constraints": inputs.get("constraints", ""),
            },
            "existing_knowledge_center": knowledge,
            "existing_content_history": inputs.get("existing_content_history", []),
            "existing_analytics": inputs.get("existing_analytics", {}),
            "learning_context": learning_context,
        }


class StrategyGenerationService:
    def __init__(self, api_key: str = None, timeout_seconds: int = 45, max_retries: int = 2, backoff_seconds: float = 1.0):
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds

    def generate_json(self, prompt: str, task: str, workspace_id: int = None) -> dict:
        start = time.monotonic()
        raw_text = self._call_with_retry(prompt)
        try:
            parsed = ContentStrategyJSONParser.parse(raw_text)
            normalized = ContentStrategyValidator.validate(parsed, expected_task=task)
            self._log_cost(workspace_id, prompt, raw_text, start, "success")
            return normalized
        except Exception as first_error:
            validation_errors = getattr(first_error, "errors", [{"message": _safe_error_message(first_error)}])
            repair_prompt = build_json_repair_prompt(raw_text, validation_errors, task)
            try:
                repaired_text = self._call_with_retry(repair_prompt)
                parsed = ContentStrategyJSONParser.parse(repaired_text)
                normalized = ContentStrategyValidator.validate(parsed, expected_task=task)
                self._log_cost(workspace_id, prompt + repair_prompt, repaired_text, start, "success")
                return normalized
            except Exception as second_error:
                self._log_cost(workspace_id, prompt, raw_text, start, "failed")
                if isinstance(second_error, StrategyValidationError):
                    raise ContentStrategyGenerationError(
                        "validation_failed",
                        "AI output failed schema validation after repair",
                        retryable=False,
                        details={"errors": second_error.errors},
                    ) from second_error
                raise ContentStrategyGenerationError(
                    "malformed_json",
                    "AI returned malformed JSON after repair",
                    retryable=True,
                    details={"first_error": _safe_error_message(first_error), "second_error": _safe_error_message(second_error)},
                ) from second_error

    def _call_with_retry(self, prompt: str) -> str:
        client = get_gemini_client(self.api_key)
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                return self._call_once(client, prompt)
            except concurrent.futures.TimeoutError as exc:
                last_error = exc
                retryable = True
            except Exception as exc:
                last_error = exc
                retryable = _is_retryable(exc)
            if attempt >= self.max_retries or not retryable:
                break
            delay = self.backoff_seconds * (2 ** attempt)
            logger.warning("[CONTENT_STRATEGY] Gemini retry %s/%s after retryable error: %s", attempt + 1, self.max_retries, _safe_error_message(last_error))
            time.sleep(delay)
        code = "timeout" if isinstance(last_error, concurrent.futures.TimeoutError) else "provider_unavailable"
        raise ContentStrategyGenerationError(code, _safe_error_message(last_error), retryable=_is_retryable(last_error)) from last_error

    def _call_once(self, client, prompt: str) -> str:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_call_model, client, prompt, False)
            return future.result(timeout=self.timeout_seconds)

    @staticmethod
    def _token_estimate(text: str) -> int:
        return max(1, len(text or "") // 4)

    def _log_cost(self, workspace_id: int, prompt: str, output: str, started: float, status: str):
        if not workspace_id:
            return
        try:
            AICostModel.ensure_table()
            prompt_tokens = self._token_estimate(prompt)
            completion_tokens = self._token_estimate(output)
            latency_ms = int((time.monotonic() - started) * 1000)
            cost = (prompt_tokens * 0.075 + completion_tokens * 0.3) / 1_000_000
            AICostModel.log(
                workspace_id=workspace_id,
                provider="Gemini",
                model_name=DEFAULT_MODEL,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                cost=cost,
                latency_ms=latency_ms,
                feature="Content Strategy Center",
                status=status,
            )
        except Exception as exc:
            logger.warning("[CONTENT_STRATEGY] Could not log AI cost: %s", _safe_error_message(exc))


class ContentStrategyService:
    VALID_SECTIONS = {
        "business_goals",
        "kpis",
        "lead_magnets",
        "pillars",
        "subtopics",
        "content_angles",
        "content_formats",
        "content_calendar",
    }

    def __init__(self, api_key: str = None, generation_service: StrategyGenerationService = None):
        self.generation = generation_service or StrategyGenerationService(api_key=api_key)


    recommend_lead_magnet = staticmethod(recommend_lead_magnet)
    validate_campaign_missing_cta = staticmethod(validate_campaign_missing_cta)
    validate_funnel_stage_balance = staticmethod(validate_funnel_stage_balance)
    validate_sales_content_ratio = staticmethod(validate_sales_content_ratio)
    handoff_calendar_item_to_content_studio_draft = staticmethod(handoff_calendar_item_to_content_studio_draft)
    send_selected_calendar_items_to_content_studio = staticmethod(send_selected_calendar_items_to_content_studio)
    send_campaign_batch_to_content_studio = staticmethod(send_campaign_batch_to_content_studio)
    check_publishing_readiness = staticmethod(check_publishing_readiness)
    sync_calendar_publishing_status = staticmethod(sync_calendar_publishing_status)
    create_strategy_kpi = staticmethod(create_strategy_kpi)
    list_strategy_kpis = staticmethod(list_strategy_kpis)

    @staticmethod
    def get_business_context_seed(workspace_id: int, company_id: int) -> dict:
        company = CompanyModel.get_by_id(company_id)
        if not company or company.get("workspace_id") != workspace_id:
            raise ValueError("Company does not belong to workspace")
        brand = BrandModel.get_by_workspace(workspace_id)
        return normalize_business_context(company=company, brand=brand)

    @staticmethod
    def get_brand_identity_seed(workspace_id: int, company_id: int = None) -> dict:
        if company_id:
            company = CompanyModel.get_by_id(company_id)
            if not company or company.get("workspace_id") != workspace_id:
                raise ValueError("Company does not belong to workspace")
        return normalize_brand_identity(brand=BrandModel.get_by_workspace(workspace_id))

    @staticmethod
    def normalize_draft(draft: dict, workspace_id: int = None, company_id: int = None) -> dict:
        draft = draft or {}
        company = CompanyModel.get_by_id(company_id) if company_id else {}
        if company_id and (not company or company.get("workspace_id") != workspace_id):
            raise ValueError("Company does not belong to workspace")
        brand = BrandModel.get_by_workspace(workspace_id) if workspace_id else {}
        normalized = dict(draft)
        normalized["business_context"] = normalize_business_context(draft.get("business_context"), company=company, brand=brand)
        normalized["brand_identity"] = normalize_brand_identity(draft.get("brand_identity"), brand=brand)
        normalized["audience_personas"] = [
            normalize_persona(persona, index)
            for index, persona in enumerate(draft.get("audience_personas") or [])
            if isinstance(persona, dict)
        ]
        normalized["business_goals"] = normalize_business_goals(draft.get("business_goals") or [])
        normalized["content_pillars"] = normalize_content_pillars(draft.get("content_pillars") or [])
        normalized["subtopics"] = normalize_subtopics(draft.get("subtopics") or [])
        normalized["content_angles"] = normalize_content_angles(draft.get("content_angles") or [])
        normalized["formats_channels"] = normalize_format_variants(draft.get("formats_channels") or [], brand=normalized.get("brand_identity"))
        normalized["content_calendar"] = normalize_content_calendar(draft.get("content_calendar") or {}, draft=normalized)
        return normalized

    @staticmethod
    def save_brand_identity_customization(workspace_id: int, company_id: int, customization: dict, confirmed: bool = False, updated_by: int = None, user_email: str = "") -> dict:
        try:
            if not confirmed:
                return {"ok": False, "error": "Explicit confirmation is required before updating global Brand Identity."}
            company = CompanyModel.get_by_id(company_id)
            if not company or company.get("workspace_id") != workspace_id:
                return {"ok": False, "error": "Company does not belong to workspace"}
            brand_data = normalize_brand_identity(customization)
            brand_id = BrandModel.upsert(
                workspace_id=workspace_id,
                company_id=company_id,
                tone_of_voice=brand_data.get("tone_of_voice", ""),
                brand_colors=brand_data.get("colors") if isinstance(brand_data.get("colors"), dict) else {},
                brand_guidelines=brand_data.get("communication_principles", ""),
                blacklist_words=brand_data.get("forbidden_words", []),
                cta=brand_data.get("standard_cta", ""),
                vision=brand_data.get("vision", ""),
                mission=brand_data.get("mission", ""),
                keywords=brand_data.get("brand_keywords", []),
            )
            log_action(
                action="UPDATE_STRATEGY_BRAND_IDENTITY",
                user_id=updated_by,
                user_email=user_email,
                workspace_id=workspace_id,
                entity_type="brand",
                entity_id=brand_id,
                description="Saved Content Strategy Center brand customization back to global Brand Identity.",
                new_value={
                    "tone_of_voice": brand_data.get("tone_of_voice", ""),
                    "keywords_count": len(brand_data.get("brand_keywords") or []),
                    "forbidden_words_count": len(brand_data.get("forbidden_words") or []),
                    "has_cta": bool(brand_data.get("standard_cta")),
                },
            )
            return {"ok": True, "brand_id": brand_id}
        except Exception as exc:
            return {"ok": False, "error": _safe_error_message(exc)}

    def generate_persona_drafts(self, workspace_id: int, company_id: int, draft: dict, count: int = 1, created_by: int = None) -> dict:
        try:
            context = StrategyContextService.build_context(workspace_id, company_id, draft or {})
            context["business_context"] = normalize_business_context((draft or {}).get("business_context"))
            context["brand_identity_override"] = normalize_brand_identity((draft or {}).get("brand_identity"))
            prompt = build_persona_generation_prompt(context, count=max(1, min(int(count or 1), 5)))
            if hasattr(self.generation, "generate_personas"):
                payload = self.generation.generate_personas(prompt, workspace_id=workspace_id)
            else:
                raw_text = self.generation._call_with_retry(prompt)
                payload = ContentStrategyJSONParser.parse(raw_text)
            personas = payload.get("personas") if isinstance(payload, dict) else []
            normalized = []
            for index, persona in enumerate(personas or []):
                item = normalize_persona(persona, index)
                item["ai_generated_draft"] = True
                item["status"] = "draft"
                normalized.append(item)
            if not normalized:
                return {"ok": False, "error": {"code": "empty_ai_personas", "message": "AI did not return persona drafts.", "retryable": True}}
            log_action(
                action="GENERATE_STRATEGY_PERSONA_DRAFT",
                user_id=created_by,
                workspace_id=workspace_id,
                entity_type="content_strategy_persona",
                description="Generated AI persona drafts for Content Strategy Center.",
                new_value={"company_id": company_id, "draft_count": len(normalized)},
            )
            return {"ok": True, "personas": normalized}
        except Exception as exc:
            logger.warning("[CONTENT_STRATEGY] Persona generation failed: %s", _safe_error_message(exc))
            return {"ok": False, "error": {"code": "persona_generation_failed", "message": _safe_error_message(exc), "retryable": _is_retryable(exc)}}


    def generate_pillar_drafts(self, workspace_id: int, company_id: int, draft: dict, count: int = 10, regenerate_index: int = None, created_by: int = None) -> dict:
        try:
            count = max(1, min(int(count or 10), 20))
            normalized_draft = ContentStrategyService.normalize_draft(draft or {}, workspace_id=workspace_id, company_id=company_id)
            context = StrategyContextService.build_context(workspace_id, company_id, normalized_draft)
            context["business_context"] = normalized_draft.get("business_context") or {}
            context["brand_identity_override"] = normalized_draft.get("brand_identity") or {}
            context["audience_personas"] = normalized_draft.get("audience_personas") or []
            context["business_goals"] = normalized_draft.get("business_goals") or []
            context["existing_pillars"] = normalized_draft.get("content_pillars") or []
            context["requested_pillar_count"] = count
            if regenerate_index is not None:
                context["regenerate_index"] = regenerate_index
            prompt = build_pillar_generation_prompt(context, count=count, regenerate_index=regenerate_index)
            if hasattr(self.generation, "generate_pillars"):
                payload = self.generation.generate_pillars(prompt, workspace_id=workspace_id)
            else:
                raw_text = self.generation._call_with_retry(prompt)
                payload = ContentStrategyJSONParser.parse(raw_text)
            pillars = payload.get("pillars") if isinstance(payload, dict) else []
            normalized = normalize_content_pillars(pillars)
            if not normalized:
                return {"ok": False, "error": {"code": "empty_ai_pillars", "message": "AI did not return content pillar drafts.", "retryable": True}}
            log_action(
                action="GENERATE_STRATEGY_PILLAR_DRAFT",
                user_id=created_by,
                workspace_id=workspace_id,
                entity_type="content_strategy_pillar",
                description="Generated AI content pillar drafts for Content Strategy Center.",
                new_value={"company_id": company_id, "draft_count": len(normalized), "regenerate_index": regenerate_index},
            )
            return {"ok": True, "pillars": normalized}
        except Exception as exc:
            logger.warning("[CONTENT_STRATEGY] Pillar generation failed: %s", _safe_error_message(exc))
            return {"ok": False, "error": {"code": "pillar_generation_failed", "message": _safe_error_message(exc), "retryable": _is_retryable(exc)}}

    @staticmethod
    def _generation_batches(selected_ids: list, batch_size: int) -> list:
        batch_size = max(1, min(int(batch_size or 5), 25))
        return [selected_ids[i:i + batch_size] for i in range(0, len(selected_ids), batch_size)]

    @staticmethod
    def estimate_generation_cost(item_count: int, item_type: str = "subtopics") -> dict:
        units = max(0, int(item_count or 0))
        prompt_tokens = 900 + units * (180 if item_type == "angles" else 140)
        completion_tokens = units * (220 if item_type == "angles" else 160)
        estimated_cost = (prompt_tokens * 0.075 + completion_tokens * 0.3) / 1_000_000
        return {
            "provider": "Gemini",
            "model_name": DEFAULT_MODEL,
            "estimated_prompt_tokens": prompt_tokens,
            "estimated_completion_tokens": completion_tokens,
            "estimated_cost": round(estimated_cost, 6),
            "cost_center_supported": True,
        }

    def _batch_context(self, workspace_id: int, company_id: int, draft: dict) -> dict:
        normalized_draft = ContentStrategyService.normalize_draft(draft or {}, workspace_id=workspace_id, company_id=company_id)
        context = StrategyContextService.build_context(workspace_id, company_id, normalized_draft)
        context["business_context"] = normalized_draft.get("business_context") or {}
        context["brand_identity_override"] = normalized_draft.get("brand_identity") or {}
        context["audience_personas"] = normalized_draft.get("audience_personas") or []
        context["business_goals"] = normalized_draft.get("business_goals") or []
        context["content_pillars"] = normalized_draft.get("content_pillars") or []
        context["subtopics"] = normalized_draft.get("subtopics") or []
        context["content_angles"] = normalized_draft.get("content_angles") or []
        return context

    def generate_subtopic_batches(self, workspace_id: int, company_id: int, draft: dict, subtopics_per_pillar: int = 3, batch_size: int = 3, selected_pillar_ids: list = None, resume_from_batch: int = 0, retry_batch_indexes: list = None, cancel: bool = False, created_by: int = None) -> dict:
        if cancel:
            return {"ok": True, "cancelled": True, "progress": {"completed_batches": 0, "total_batches": 0}, "subtopics": normalize_subtopics((draft or {}).get("subtopics") or [])}
        try:
            subtopics_per_pillar = max(1, min(int(subtopics_per_pillar or 3), 20))
            context = self._batch_context(workspace_id, company_id, draft)
            pillars = context.get("content_pillars") or []
            selected = [str(x) for x in (selected_pillar_ids or [p.get("id") for p in pillars if p.get("status") == "active"])]
            batches = ContentStrategyService._generation_batches(selected, batch_size)
            existing = normalize_subtopics((draft or {}).get("subtopics") or [])
            retry_set = set(retry_batch_indexes or [])
            results = list(existing)
            batch_results = []
            for batch_index, pillar_ids in enumerate(batches):
                if batch_index < int(resume_from_batch or 0) and batch_index not in retry_set:
                    batch_results.append({"index": batch_index, "status": "skipped"})
                    continue
                try:
                    selected_pillars = [p for p in pillars if str(p.get("id")) in pillar_ids]
                    batch = {"batch_index": batch_index, "selected_pillars": selected_pillars, "existing_subtopics": results}
                    prompt = build_subtopic_generation_prompt(context, subtopics_per_pillar=subtopics_per_pillar, batch=batch)
                    if hasattr(self.generation, "generate_subtopics"):
                        payload = self.generation.generate_subtopics(prompt, workspace_id=workspace_id)
                    else:
                        payload = ContentStrategyJSONParser.parse(self.generation._call_with_retry(prompt))
                    generated = [normalize_subtopic(item, len(results) + i, source="ai_generated") for i, item in enumerate(payload.get("subtopics") or [])]
                    generated = [item for item in generated if str(item.get("pillar_id")) in pillar_ids]
                    merged, duplicates = _dedupe_items(results + generated, lambda x: f"{x.get('pillar_id')} {x.get('name')} {x.get('intent')}")
                    added_count = max(0, len(merged) - len(results))
                    results = merged
                    batch_results.append({"index": batch_index, "status": "success", "added": added_count, "duplicates": duplicates})
                    ContentStrategyGenerationRepository.create_generation_job(workspace_id, company_id, None, job_type="subtopic_batch_generation", status="success", output_summary=f"batch={batch_index}; added={added_count}", request_metadata={"batch_index": batch_index, "pillar_count": len(pillar_ids)}, completed_at=datetime.now().isoformat(), created_by=created_by)
                except Exception as exc:
                    batch_results.append({"index": batch_index, "status": "failed", "error": _safe_error_message(exc), "retryable": _is_retryable(exc)})
                    ContentStrategyGenerationRepository.create_generation_job(workspace_id, company_id, None, job_type="subtopic_batch_generation", status="failed", error_message=_safe_error_message(exc), request_metadata={"batch_index": batch_index}, completed_at=datetime.now().isoformat(), created_by=created_by)
            log_action(action="GENERATE_STRATEGY_SUBTOPIC_BATCH", user_id=created_by, workspace_id=workspace_id, entity_type="content_strategy_subtopic", description="Generated subtopic batches for Content Strategy Center.", new_value={"company_id": company_id, "total_batches": len(batches), "success_batches": len([b for b in batch_results if b.get("status") == "success"])})
            return {"ok": True, "subtopics": results, "batches": batch_results, "progress": {"completed_batches": len([b for b in batch_results if b.get("status") == "success"]), "total_batches": len(batches)}}
        except Exception as exc:
            logger.warning("[CONTENT_STRATEGY] Subtopic batch generation failed: %s", _safe_error_message(exc))
            return {"ok": False, "error": {"code": "subtopic_generation_failed", "message": _safe_error_message(exc), "retryable": _is_retryable(exc)}}

    def generate_angle_batches(self, workspace_id: int, company_id: int, draft: dict, angles_per_subtopic: int = 5, batch_size: int = 5, selected_subtopic_ids: list = None, resume_from_batch: int = 0, retry_batch_indexes: list = None, cancel: bool = False, created_by: int = None) -> dict:
        if cancel:
            return {"ok": True, "cancelled": True, "progress": {"completed_batches": 0, "total_batches": 0}, "content_angles": normalize_content_angles((draft or {}).get("content_angles") or [])}
        try:
            angles_per_subtopic = max(1, min(int(angles_per_subtopic or 5), 20))
            context = self._batch_context(workspace_id, company_id, draft)
            subtopics = context.get("subtopics") or []
            selected = [str(x) for x in (selected_subtopic_ids or [s.get("id") for s in subtopics if s.get("status") in {"draft", "active", "approved"}])]
            batches = ContentStrategyService._generation_batches(selected, batch_size)
            existing = normalize_content_angles((draft or {}).get("content_angles") or [])
            retry_set = set(retry_batch_indexes or [])
            results = list(existing)
            batch_results = []
            for batch_index, subtopic_ids in enumerate(batches):
                if batch_index < int(resume_from_batch or 0) and batch_index not in retry_set:
                    batch_results.append({"index": batch_index, "status": "skipped"})
                    continue
                try:
                    selected_subtopics = [s for s in subtopics if str(s.get("id")) in subtopic_ids]
                    batch = {"batch_index": batch_index, "selected_subtopics": selected_subtopics, "existing_angles": results, "allowed_categories": ANGLE_CATEGORY_OPTIONS}
                    prompt = build_angle_generation_prompt(context, angles_per_subtopic=angles_per_subtopic, batch=batch)
                    if hasattr(self.generation, "generate_angles"):
                        payload = self.generation.generate_angles(prompt, workspace_id=workspace_id)
                    else:
                        payload = ContentStrategyJSONParser.parse(self.generation._call_with_retry(prompt))
                    generated = [normalize_content_angle(item, len(results) + i, source="ai_generated") for i, item in enumerate(payload.get("content_angles") or [])]
                    generated = [item for item in generated if str(item.get("subtopic_id")) in subtopic_ids]
                    merged, duplicates = _dedupe_items(results + generated, lambda x: f"{x.get('subtopic_id')} {x.get('working_title')} {x.get('core_insight')}")
                    added_count = max(0, len(merged) - len(results))
                    results = merged
                    batch_results.append({"index": batch_index, "status": "success", "added": added_count, "duplicates": duplicates})
                    ContentStrategyGenerationRepository.create_generation_job(workspace_id, company_id, None, job_type="angle_batch_generation", status="success", output_summary=f"batch={batch_index}; added={added_count}", request_metadata={"batch_index": batch_index, "subtopic_count": len(subtopic_ids)}, completed_at=datetime.now().isoformat(), created_by=created_by)
                except Exception as exc:
                    batch_results.append({"index": batch_index, "status": "failed", "error": _safe_error_message(exc), "retryable": _is_retryable(exc)})
                    ContentStrategyGenerationRepository.create_generation_job(workspace_id, company_id, None, job_type="angle_batch_generation", status="failed", error_message=_safe_error_message(exc), request_metadata={"batch_index": batch_index}, completed_at=datetime.now().isoformat(), created_by=created_by)
            log_action(action="GENERATE_STRATEGY_ANGLE_BATCH", user_id=created_by, workspace_id=workspace_id, entity_type="content_strategy_angle", description="Generated angle batches for Content Strategy Center.", new_value={"company_id": company_id, "total_batches": len(batches), "success_batches": len([b for b in batch_results if b.get("status") == "success"])})
            return {"ok": True, "content_angles": results, "batches": batch_results, "progress": {"completed_batches": len([b for b in batch_results if b.get("status") == "success"]), "total_batches": len(batches)}}
        except Exception as exc:
            logger.warning("[CONTENT_STRATEGY] Angle batch generation failed: %s", _safe_error_message(exc))
            return {"ok": False, "error": {"code": "angle_generation_failed", "message": _safe_error_message(exc), "retryable": _is_retryable(exc)}}
    @staticmethod
    def list_companies(workspace_id: int) -> list:
        return CompanyModel.list_by_workspace(workspace_id)

    @staticmethod
    def list_strategies(workspace_id: int, company_id: int, include_archived: bool = False, limit: int = None, offset: int = 0) -> dict:
        try:
            ContentStrategyRepository.ensure_tables()
            fetch_limit = (int(limit) + 1) if limit is not None else None
            strategies = ContentStrategyRepository.list_strategies(workspace_id, company_id, include_archived=include_archived, limit=fetch_limit, offset=offset)
            has_more = bool(limit is not None and len(strategies) > int(limit))
            if limit is not None:
                strategies = strategies[:int(limit)]
            return {"ok": True, "strategies": strategies, "pagination": {"limit": limit, "offset": offset, "has_more": has_more} if limit is not None else None}
        except Exception as exc:
            return {"ok": False, "error": _safe_error_message(exc), "strategies": []}

    @staticmethod
    def open_strategy(workspace_id: int, company_id: int, strategy_id: int) -> dict:
        try:
            ContentStrategyRepository.ensure_tables()
            strategy = ContentStrategyRepository.get_strategy(workspace_id, company_id, strategy_id, include_children=True)
            if not strategy:
                return {"ok": False, "error": "Strategy not found for this workspace/company"}
            return {"ok": True, "strategy": strategy}
        except Exception as exc:
            return {"ok": False, "error": _safe_error_message(exc)}

    @staticmethod
    def create_draft_strategy(workspace_id: int, company_id: int, name: str, draft: dict = None, created_by: int = None) -> dict:
        try:
            ContentStrategyRepository.ensure_tables()
            draft = draft or {}
            metadata = {
                "source": "strategy_center_wizard_shell",
                "wizard_draft": draft,
                "autosaved_at": datetime.now().isoformat(),
            }
            strategy_id = ContentStrategyRepository.create_strategy(
                workspace_id,
                company_id,
                (name or "Untitled Content Strategy").strip(),
                description=draft.get("description", ""),
                start_date=draft.get("start_date"),
                end_date=draft.get("end_date"),
                metadata=metadata,
                status="draft",
                created_by=created_by,
            )
            log_action(
                action="CREATE_CONTENT_STRATEGY_DRAFT",
                user_id=created_by,
                workspace_id=workspace_id,
                entity_type="content_strategy",
                entity_id=strategy_id,
                description="Created Content Strategy Center draft.",
                new_value=_safe_audit_payload(metadata.get("wizard_draft") or {}),
            )
            return {"ok": True, "strategy_id": strategy_id}
        except Exception as exc:
            return {"ok": False, "error": _safe_error_message(exc)}

    @staticmethod
    def save_draft(workspace_id: int, company_id: int, strategy_id: int, draft: dict, updated_by: int = None, create_version: bool = True) -> dict:
        try:
            ContentStrategyRepository.ensure_tables()
            strategy = ContentStrategyRepository.get_strategy(workspace_id, company_id, strategy_id, include_children=False)
            if not strategy:
                return {"ok": False, "error": "Strategy not found for this workspace/company"}
            metadata = dict(strategy.get("metadata") or {})
            metadata["wizard_draft"] = draft or {}
            metadata["autosaved_at"] = datetime.now().isoformat()
            metadata["wizard_schema"] = "content_strategy_wizard_shell.v1"
            name = (draft or {}).get("strategy_name") or strategy.get("name") or "Untitled Content Strategy"
            update = {
                "name": name.strip(),
                "description": (draft or {}).get("description", strategy.get("description", "")),
                "start_date": (draft or {}).get("start_date") or strategy.get("start_date"),
                "end_date": (draft or {}).get("end_date") or strategy.get("end_date"),
                "metadata": metadata,
                "updated_by": updated_by,
            }
            if strategy.get("status") not in {"active", "archived"}:
                update["status"] = "draft"
            ContentStrategyRepository.update_strategy(workspace_id, company_id, strategy_id, **update)
            version_id = None
            if create_version:
                version_id = ContentStrategyRepository.create_strategy_version(
                    workspace_id,
                    company_id,
                    strategy_id,
                    notes="Draft saved",
                    created_by=updated_by,
                )
            log_action(
                action="UPDATE_CONTENT_STRATEGY_DRAFT",
                user_id=updated_by,
                workspace_id=workspace_id,
                entity_type="content_strategy",
                entity_id=strategy_id,
                description="Updated Content Strategy Center draft.",
                new_value=_safe_audit_payload(metadata.get("wizard_draft") or {}),
            )
            return {"ok": True, "strategy_id": strategy_id, "version_id": version_id, "metadata": metadata}
        except Exception as exc:
            return {"ok": False, "error": _safe_error_message(exc)}

    @staticmethod
    def duplicate_strategy(workspace_id: int, company_id: int, strategy_id: int, created_by: int = None) -> dict:
        try:
            ContentStrategyRepository.ensure_tables()
            strategy = ContentStrategyRepository.get_strategy(workspace_id, company_id, strategy_id, include_children=False)
            if not strategy:
                return {"ok": False, "error": "Strategy not found for this workspace/company"}
            base_name = strategy.get("name") or "Untitled Content Strategy"
            metadata = copy.deepcopy(strategy.get("metadata") or {})
            metadata["duplicated_from_strategy_id"] = strategy_id
            metadata["duplicated_at"] = datetime.now().isoformat()
            new_id = ContentStrategyRepository.create_strategy(
                workspace_id,
                company_id,
                f"{base_name} Copy {datetime.now().strftime('%Y%m%d%H%M%S')}",
                description=strategy.get("description", ""),
                start_date=strategy.get("start_date"),
                end_date=strategy.get("end_date"),
                metadata=metadata,
                status="draft",
                created_by=created_by,
            )
            return {"ok": True, "strategy_id": new_id}
        except Exception as exc:
            return {"ok": False, "error": _safe_error_message(exc)}

    @staticmethod
    def archive_strategy(workspace_id: int, company_id: int, strategy_id: int, updated_by: int = None) -> dict:
        try:
            ContentStrategyRepository.ensure_tables()
            ok = ContentStrategyRepository.archive_strategy(workspace_id, company_id, strategy_id, updated_by=updated_by)
            return {"ok": ok}
        except Exception as exc:
            return {"ok": False, "error": _safe_error_message(exc)}

    @staticmethod
    def activate_strategy(workspace_id: int, company_id: int, strategy_id: int, updated_by: int = None) -> dict:
        try:
            ContentStrategyRepository.ensure_tables()
            ok = ContentStrategyRepository.update_strategy(
                workspace_id,
                company_id,
                strategy_id,
                status="active",
                updated_by=updated_by,
            )
            return {"ok": ok}
        except Exception as exc:
            return {"ok": False, "error": _safe_error_message(exc)}

    @staticmethod
    def list_versions(workspace_id: int, company_id: int, strategy_id: int) -> dict:
        try:
            ContentStrategyRepository.ensure_tables()
            return {"ok": True, "versions": ContentStrategyRepository.list_strategy_versions(workspace_id, company_id, strategy_id)}
        except Exception as exc:
            return {"ok": False, "error": _safe_error_message(exc), "versions": []}

    @staticmethod
    def restore_version(workspace_id: int, company_id: int, strategy_id: int, version_id: int, updated_by: int = None) -> dict:
        try:
            ContentStrategyRepository.ensure_tables()
            ok = ContentStrategyRepository.restore_strategy_version(workspace_id, company_id, strategy_id, version_id, updated_by=updated_by)
            return {"ok": ok}
        except Exception as exc:
            return {"ok": False, "error": _safe_error_message(exc)}
    def generate_strategy(self, workspace_id: int, company_id: int, inputs: dict, created_by: int = None, persist: bool = True) -> dict:
        return self._generate(
            workspace_id=workspace_id,
            company_id=company_id,
            inputs=inputs,
            task="full_strategy",
            sections=None,
            strategy_id=None,
            created_by=created_by,
            persist=persist,
        )

    def regenerate_section(self, workspace_id: int, company_id: int, strategy_id: int, section: str, inputs: dict = None, updated_by: int = None, persist: bool = True) -> dict:
        if section not in self.VALID_SECTIONS:
            raise ValueError(f"Unsupported section: {section}")
        existing = ContentStrategyRepository.get_strategy(workspace_id, company_id, strategy_id, include_children=True)
        if not existing:
            raise ValueError("Strategy not found for this workspace/company")
        return self._generate(
            workspace_id=workspace_id,
            company_id=company_id,
            inputs=inputs or {},
            task=f"regenerate_{section}",
            sections=[section],
            strategy_id=strategy_id,
            existing_strategy=existing,
            created_by=updated_by,
            persist=persist,
        )

    def _generate(self, workspace_id: int, company_id: int, inputs: dict, task: str, sections=None, strategy_id=None, existing_strategy=None, created_by=None, persist=True) -> dict:
        request_id = hashlib.sha256(json.dumps({
            "workspace_id": workspace_id,
            "company_id": company_id,
            "task": task,
            "inputs": inputs,
            "strategy_id": strategy_id,
        }, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:16]
        started_at = datetime.now().isoformat()
        try:
            context = StrategyContextService.build_context(workspace_id, company_id, inputs)
            prompt = build_content_strategy_prompt(task, context, existing_strategy=existing_strategy)
            payload = self.generation.generate_json(prompt, task=task, workspace_id=workspace_id)
            payload["start_date"] = inputs.get("start_date")
            payload["end_date"] = inputs.get("end_date")

            saved_strategy_id = strategy_id
            if persist:
                if strategy_id:
                    ContentStrategyGenerationRepository.replace_sections(workspace_id, company_id, strategy_id, payload, sections or [], updated_by=created_by)
                else:
                    saved_strategy_id = ContentStrategyGenerationRepository.create_strategy_with_sections(workspace_id, company_id, payload, created_by=created_by)
            ContentStrategyGenerationRepository.create_generation_job(
                workspace_id,
                company_id,
                saved_strategy_id,
                job_type=task,
                status="success",
                input_summary=f"request_id={request_id}; prompt_version={PROMPT_VERSION}",
                output_summary=f"pillars={len(payload.get('pillars', []))}; calendar={len(payload.get('content_calendar', []))}",
                request_metadata={"request_id": request_id, "prompt_version": PROMPT_VERSION, "sections": sections or []},
                started_at=started_at,
                completed_at=datetime.now().isoformat(),
                created_by=created_by,
            )
            return {"ok": True, "strategy_id": saved_strategy_id, "request_id": request_id, "payload": payload}
        except ContentStrategyGenerationError as exc:
            self._record_failed_job(workspace_id, company_id, strategy_id, task, request_id, started_at, exc, created_by)
            return exc.to_dict()
        except StrategyValidationError as exc:
            err = ContentStrategyGenerationError("validation_failed", "AI output failed schema validation", False, {"errors": exc.errors})
            self._record_failed_job(workspace_id, company_id, strategy_id, task, request_id, started_at, err, created_by)
            return err.to_dict()
        except Exception as exc:
            logger.error("[CONTENT_STRATEGY] Generation failed: %s", _safe_error_message(exc), exc_info=True)
            err = ContentStrategyGenerationError("generation_failed", _safe_error_message(exc), _is_retryable(exc))
            self._record_failed_job(workspace_id, company_id, strategy_id, task, request_id, started_at, err, created_by)
            return err.to_dict()

    @staticmethod
    def _record_failed_job(workspace_id, company_id, strategy_id, task, request_id, started_at, exc, created_by):
        try:
            ContentStrategyGenerationRepository.create_generation_job(
                workspace_id,
                company_id,
                strategy_id,
                job_type=task,
                status="failed",
                input_summary=f"request_id={request_id}; prompt_version={PROMPT_VERSION}",
                request_metadata={"request_id": request_id, "prompt_version": PROMPT_VERSION},
                validation_errors=exc.details.get("errors", []),
                error_message=str(exc),
                started_at=started_at,
                completed_at=datetime.now().isoformat(),
                created_by=created_by,
            )
        except Exception as log_exc:
            logger.warning("[CONTENT_STRATEGY] Could not persist failed generation job: %s", _safe_error_message(log_exc))





















