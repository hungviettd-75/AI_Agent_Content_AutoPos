"""Validation and normalization for AI Content Strategy Center outputs."""

import json
from datetime import datetime
from services.gemini_client import clean_ai_json_text


class StrategyValidationError(ValueError):
    def __init__(self, errors):
        super().__init__("Content strategy validation failed")
        self.errors = errors


class ContentStrategyJSONParser:
    @staticmethod
    def clean(raw_text: str) -> str:
        text = (raw_text or "").strip()
        text = text.replace("```json", "").replace("```JSON", "").replace("```", "").strip()
        obj_start = text.find("{")
        obj_end = text.rfind("}")
        arr_start = text.find("[")
        arr_end = text.rfind("]")
        if obj_start != -1 and obj_end > obj_start:
            return text[obj_start:obj_end + 1].strip()
        if arr_start != -1 and arr_end > arr_start:
            return text[arr_start:arr_end + 1].strip()
        return clean_ai_json_text(text)

    @classmethod
    def parse(cls, raw_text: str):
        return json.loads(cls.clean(raw_text))


def _as_list(value):
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _string(value, field, errors, required=True, max_len=500):
    if value is None or value == "":
        if required:
            errors.append({"field": field, "message": "required"})
        return ""
    if not isinstance(value, str):
        errors.append({"field": field, "message": "must be string"})
        return str(value)
    return value.strip()[:max_len]


def _number(value, field, errors, default=0):
    if value in (None, ""):
        return default
    if isinstance(value, (int, float)):
        return value
    try:
        return float(value)
    except Exception:
        errors.append({"field": field, "message": "must be number"})
        return default


def _date(value, field, errors):
    value = _string(value, field, errors)
    if not value:
        return ""
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except Exception:
        errors.append({"field": field, "message": "must be YYYY-MM-DD"})
    return value


def _key(value: str) -> str:
    text = (value or "").lower().strip()
    allowed = []
    for ch in text:
        if ch.isalnum():
            allowed.append(ch)
        elif ch in (" ", "-", "_"):
            allowed.append("-")
    slug = "".join(allowed).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug[:80] or "item"


class ContentStrategyValidator:
    REQUIRED_ROOT_LISTS = [
        "pillars",
        "subtopics",
        "content_angles",
        "content_formats",
        "content_calendar",
    ]

    @classmethod
    def validate(cls, data: dict, expected_task: str = None) -> dict:
        errors = []
        if not isinstance(data, dict):
            raise StrategyValidationError([{"field": "$", "message": "root must be object"}])

        normalized = {
            "schema_version": _string(data.get("schema_version", "content_strategy.v1"), "schema_version", errors),
            "task": _string(data.get("task", expected_task or "full_strategy"), "task", errors),
            "strategy_summary": cls._summary(data.get("strategy_summary") or {}, errors),
            "business_goals": cls._business_goals(data.get("business_goals"), errors),
            "kpis": cls._kpis(data.get("kpis"), errors),
            "lead_magnets": cls._lead_magnets(data.get("lead_magnets"), errors),
            "pillars": cls._pillars(data.get("pillars"), errors),
            "subtopics": [],
            "content_angles": [],
            "content_formats": [],
            "content_calendar": [],
        }

        for field in cls.REQUIRED_ROOT_LISTS:
            if field in data and not isinstance(data.get(field), list):
                errors.append({"field": field, "message": "must be array"})

        pillar_keys = {item["key"] for item in normalized["pillars"]}
        normalized["subtopics"] = cls._subtopics(data.get("subtopics"), pillar_keys, errors)
        subtopic_keys = {item["key"] for item in normalized["subtopics"]}
        normalized["content_angles"] = cls._angles(data.get("content_angles"), pillar_keys, subtopic_keys, errors)
        angle_keys = {item["key"] for item in normalized["content_angles"]}
        normalized["content_formats"] = cls._formats(data.get("content_formats"), angle_keys, errors)
        normalized["content_calendar"] = cls._calendar(data.get("content_calendar"), pillar_keys, subtopic_keys, angle_keys, errors)

        if errors:
            raise StrategyValidationError(errors)
        return normalized

    @staticmethod
    def _summary(value, errors):
        if not isinstance(value, dict):
            errors.append({"field": "strategy_summary", "message": "must be object"})
            value = {}
        return {
            "name": _string(value.get("name", "AI Content Strategy"), "strategy_summary.name", errors),
            "description": _string(value.get("description", ""), "strategy_summary.description", errors, required=False, max_len=1000),
            "campaign_theme": _string(value.get("campaign_theme", ""), "strategy_summary.campaign_theme", errors, required=False),
        }

    @staticmethod
    def _business_goals(value, errors):
        result = []
        for index, item in enumerate(_as_list(value)):
            if not isinstance(item, dict):
                errors.append({"field": f"business_goals[{index}]", "message": "must be object"})
                continue
            result.append({
                "name": _string(item.get("name"), f"business_goals[{index}].name", errors),
                "description": _string(item.get("description", ""), f"business_goals[{index}].description", errors, required=False, max_len=1000),
                "target_metric": _string(item.get("target_metric", ""), f"business_goals[{index}].target_metric", errors, required=False),
                "target_value": _number(item.get("target_value"), f"business_goals[{index}].target_value", errors),
                "timeframe": _string(item.get("timeframe", ""), f"business_goals[{index}].timeframe", errors, required=False),
            })
        return result

    @staticmethod
    def _kpis(value, errors):
        result = []
        for index, item in enumerate(_as_list(value)):
            if not isinstance(item, dict):
                errors.append({"field": f"kpis[{index}]", "message": "must be object"})
                continue
            result.append({
                "metric_name": _string(item.get("metric_name"), f"kpis[{index}].metric_name", errors),
                "target_value": _number(item.get("target_value"), f"kpis[{index}].target_value", errors),
                "unit": _string(item.get("unit", ""), f"kpis[{index}].unit", errors, required=False),
            })
        return result

    @staticmethod
    def _lead_magnets(value, errors):
        result = []
        for index, item in enumerate(_as_list(value)):
            if not isinstance(item, dict):
                errors.append({"field": f"lead_magnets[{index}]", "message": "must be object"})
                continue
            result.append({
                "name": _string(item.get("name"), f"lead_magnets[{index}].name", errors),
                "description": _string(item.get("description", ""), f"lead_magnets[{index}].description", errors, required=False, max_len=1000),
                "asset_type": _string(item.get("asset_type", "other"), f"lead_magnets[{index}].asset_type", errors, required=False),
                "pillar_key": _string(item.get("pillar_key", ""), f"lead_magnets[{index}].pillar_key", errors, required=False),
            })
        return result

    @staticmethod
    def _pillars(value, errors):
        result = []
        seen = set()
        for index, item in enumerate(_as_list(value)):
            if not isinstance(item, dict):
                errors.append({"field": f"pillars[{index}]", "message": "must be object"})
                continue
            name = _string(item.get("name"), f"pillars[{index}].name", errors)
            key = _key(item.get("key") or name)
            if key in seen:
                errors.append({"field": f"pillars[{index}].name", "message": "duplicate pillar"})
            seen.add(key)
            result.append({
                "key": key,
                "name": name,
                "description": _string(item.get("description"), f"pillars[{index}].description", errors),
                "business_goal": _string(item.get("business_goal", ""), f"pillars[{index}].business_goal", errors, required=False),
                "target_persona": [str(x).strip() for x in _as_list(item.get("target_persona")) if str(x).strip()],
                "recommended_platforms": [str(x).strip() for x in _as_list(item.get("recommended_platforms")) if str(x).strip()],
                "priority": int(_number(item.get("priority", index + 1), f"pillars[{index}].priority", errors, index + 1)),
            })
        return result

    @staticmethod
    def _subtopics(value, pillar_keys, errors):
        result = []
        seen = set()
        for index, item in enumerate(_as_list(value)):
            if not isinstance(item, dict):
                errors.append({"field": f"subtopics[{index}]", "message": "must be object"})
                continue
            name = _string(item.get("name"), f"subtopics[{index}].name", errors)
            pillar_key = _key(item.get("pillar_key"))
            key = _key(item.get("key") or f"{pillar_key}-{name}")
            if pillar_key not in pillar_keys:
                errors.append({"field": f"subtopics[{index}].pillar_key", "message": "unknown pillar_key"})
            if key in seen:
                errors.append({"field": f"subtopics[{index}].key", "message": "duplicate subtopic"})
            seen.add(key)
            result.append({"key": key, "pillar_key": pillar_key, "name": name, "description": _string(item.get("description", ""), f"subtopics[{index}].description", errors, required=False), "priority": int(_number(item.get("priority", index + 1), f"subtopics[{index}].priority", errors, index + 1))})
        return result

    @staticmethod
    def _angles(value, pillar_keys, subtopic_keys, errors):
        result = []
        seen = set()
        for index, item in enumerate(_as_list(value)):
            if not isinstance(item, dict):
                errors.append({"field": f"content_angles[{index}]", "message": "must be object"})
                continue
            title = _string(item.get("title"), f"content_angles[{index}].title", errors)
            key = _key(item.get("key") or title)
            pillar_key = _key(item.get("pillar_key"))
            subtopic_key = _key(item.get("subtopic_key"))
            if pillar_key not in pillar_keys:
                errors.append({"field": f"content_angles[{index}].pillar_key", "message": "unknown pillar_key"})
            if subtopic_key and subtopic_key not in subtopic_keys:
                errors.append({"field": f"content_angles[{index}].subtopic_key", "message": "unknown subtopic_key"})
            if key in seen:
                errors.append({"field": f"content_angles[{index}].key", "message": "duplicate angle"})
            seen.add(key)
            result.append({"key": key, "pillar_key": pillar_key, "subtopic_key": subtopic_key, "title": title, "description": _string(item.get("description", ""), f"content_angles[{index}].description", errors, required=False), "hook": _string(item.get("hook", ""), f"content_angles[{index}].hook", errors, required=False), "cta": _string(item.get("cta", ""), f"content_angles[{index}].cta", errors, required=False), "goal": _string(item.get("goal", ""), f"content_angles[{index}].goal", errors, required=False)})
        return result

    @staticmethod
    def _formats(value, angle_keys, errors):
        result = []
        for index, item in enumerate(_as_list(value)):
            if not isinstance(item, dict):
                errors.append({"field": f"content_formats[{index}]", "message": "must be object"})
                continue
            angle_key = _key(item.get("angle_key"))
            if angle_key and angle_key not in angle_keys:
                errors.append({"field": f"content_formats[{index}].angle_key", "message": "unknown angle_key"})
            specs = item.get("specs") or {}
            if not isinstance(specs, dict):
                errors.append({"field": f"content_formats[{index}].specs", "message": "must be object"})
                specs = {}
            result.append({"angle_key": angle_key, "platform": _string(item.get("platform", "facebook"), f"content_formats[{index}].platform", errors), "format_type": _string(item.get("format_type"), f"content_formats[{index}].format_type", errors), "name": _string(item.get("name"), f"content_formats[{index}].name", errors), "description": _string(item.get("description", ""), f"content_formats[{index}].description", errors, required=False), "specs": specs})
        return result

    @staticmethod
    def _calendar(value, pillar_keys, subtopic_keys, angle_keys, errors):
        result = []
        seen = set()
        for index, item in enumerate(_as_list(value)):
            if not isinstance(item, dict):
                errors.append({"field": f"content_calendar[{index}]", "message": "must be object"})
                continue
            pillar_key = _key(item.get("pillar_key"))
            subtopic_key = _key(item.get("subtopic_key"))
            angle_key = _key(item.get("angle_key"))
            title = _string(item.get("title"), f"content_calendar[{index}].title", errors)
            planned_date = _date(item.get("planned_date"), f"content_calendar[{index}].planned_date", errors)
            platform = _string(item.get("platform", "facebook"), f"content_calendar[{index}].platform", errors)
            unique = (planned_date, platform, title.lower())
            if unique in seen:
                errors.append({"field": f"content_calendar[{index}]", "message": "duplicate calendar item"})
            seen.add(unique)
            if pillar_key and pillar_key not in pillar_keys:
                errors.append({"field": f"content_calendar[{index}].pillar_key", "message": "unknown pillar_key"})
            if subtopic_key and subtopic_key not in subtopic_keys:
                errors.append({"field": f"content_calendar[{index}].subtopic_key", "message": "unknown subtopic_key"})
            if angle_key and angle_key not in angle_keys:
                errors.append({"field": f"content_calendar[{index}].angle_key", "message": "unknown angle_key"})
            result.append({"planned_date": planned_date, "platform": platform, "title": title, "brief": _string(item.get("brief", ""), f"content_calendar[{index}].brief", errors, required=False, max_len=2000), "pillar_key": pillar_key, "subtopic_key": subtopic_key, "angle_key": angle_key, "content_type": _string(item.get("content_type", ""), f"content_calendar[{index}].content_type", errors, required=False), "cta": _string(item.get("cta", ""), f"content_calendar[{index}].cta", errors, required=False)})
        return result
