"""Models/helpers for AI Content Strategy Center tables."""

import json
import re
from datetime import datetime
from database.migrations.content_strategy_center import up as migrate_content_strategy


JSON_FIELDS = {
    "metadata",
    "snapshot",
    "pain_points",
    "goals",
    "preferred_channels",
    "specs",
    "request_metadata",
    "validation_errors",
    "suggested_channels",
    "target_personas",
    "business_goals",
    "pillars",
}


def now_iso() -> str:
    return datetime.now().isoformat()


def slugify(value: str) -> str:
    slug = (value or "").lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_-]+", "-", slug)
    return slug[:80] or "item"


def dumps_json(value):
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)


def loads_json(value, default=None):
    if value in (None, ""):
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return default


def row_to_dict(row) -> dict:
    if not row:
        return {}
    data = dict(row)
    for field in JSON_FIELDS:
        if field in data:
            fallback = [] if field in {"pain_points", "goals", "preferred_channels", "validation_errors", "target_personas", "business_goals", "pillars"} else {}
            data[field] = loads_json(data.get(field), fallback)
    return data


def rows_to_dicts(rows) -> list:
    return [row_to_dict(row) for row in rows]


class ContentStrategyModel:
    VALID_STATUS = {
        "draft",
        "generating",
        "generated",
        "editing",
        "ready_for_review",
        "approved",
        "scheduled",
        "active",
        "archived",
        "failed",
    }

    @staticmethod
    def ensure_tables():
        migrate_content_strategy()







