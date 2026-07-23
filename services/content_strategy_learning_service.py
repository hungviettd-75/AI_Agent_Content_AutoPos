"""Analytics-driven learning loop for AI Content Strategy Center.

This service only uses persisted analytics mapped to a workspace/company/strategy.
It does not create demo data and does not call an AI provider directly.
"""

import json
from collections import defaultdict
from datetime import datetime, timedelta

from database.connection import get_db_connection, _adapt_sql
from database.models.content_strategy import dumps_json, now_iso, row_to_dict
from database.models.learning_insights import LearningInsightModel
from database.repositories.content_strategy_repository import ContentStrategyRepository


MIN_TOTAL_SAMPLE = 5
MIN_GROUP_SAMPLE = 3
SUPPORTED_METRICS = {"engagement_rate", "ctr", "leads", "reach", "viral_score"}


DIMENSIONS = [
    ("pillar", "pillar_name", "Pillar"),
    ("subtopic", "subtopic_name", "Subtopic"),
    ("angle", "angle_title", "Angle"),
    ("platform", "platform", "Platform"),
    ("format", "format_type", "Format"),
    ("cta", "cta", "CTA"),
    ("persona", "persona", "Persona"),
    ("funnel_stage", "funnel_stage", "Funnel stage"),
    ("time_slot", "time_slot", "Time slot"),
    ("campaign", "campaign_name", "Campaign"),
    ("lead_magnet", "lead_magnet_name", "Lead Magnet"),
]


def _loads(value, default=None):
    if value in (None, ""):
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return default


def _number(value, default=0.0):
    try:
        return float(value or 0)
    except Exception:
        return default


def _safe_date(value):
    text = str(value or "")[:10]
    try:
        datetime.strptime(text, "%Y-%m-%d")
        return text
    except Exception:
        return ""


def _confidence(sample_size: int, lift: float, missing_ratio: float) -> tuple[float, str]:
    base = min(0.82, 0.42 + min(sample_size, 30) / 60)
    lift_bonus = min(0.12, abs(lift) / 400)
    penalty = min(0.25, missing_ratio * 0.35)
    score = max(0.0, min(0.95, base + lift_bonus - penalty))
    if score >= 0.75:
        return score, "high"
    if score >= 0.55:
        return score, "medium"
    return score, "low"


def _metric_value(row: dict, metric: str) -> float:
    impressions = _number(row.get("impressions"))
    clicks = _number(row.get("clicks"))
    reach = _number(row.get("reach"))
    interactions = sum(_number(row.get(k)) for k in ["likes", "comments", "shares", "saves"])
    if metric == "ctr":
        return (clicks / impressions * 100) if impressions > 0 else 0.0
    if metric == "leads":
        return _number(row.get("leads"))
    if metric == "reach":
        return reach
    if metric == "viral_score":
        return _number(row.get("viral_score"))
    if row.get("engagement_rate") not in (None, ""):
        return _number(row.get("engagement_rate"))
    return (interactions / reach * 100) if reach > 0 else 0.0


def _avg(rows: list, metric: str) -> float:
    if not rows:
        return 0.0
    return sum(_metric_value(row, metric) for row in rows) / len(rows)


def _insight_type_for_dimension(dimension: str) -> str:
    return {
        "platform": "platform_strategy",
        "format": "format_performance",
        "cta": "cta_effectiveness",
        "persona": "audience",
        "funnel_stage": "funnel_performance",
        "time_slot": "timing",
        "campaign": "campaign_performance",
        "lead_magnet": "lead_magnet_performance",
        "pillar": "topic_performance",
        "subtopic": "topic_performance",
        "angle": "content_pattern",
    }.get(dimension, "strategy_recommendation")


def _recommendation_for(dimension_label: str, winner: str, metric: str, affected: dict) -> str:
    scope = f"{dimension_label} '{winner}'"
    return (
        f"Review the content strategy mix and consider prioritizing {scope} in the next planning cycle. "
        f"Treat this as a correlation from available analytics for {metric}, then validate with future posts or an A/B test before making a larger permanent shift."
    )


class ContentStrategyLearningService:
    @staticmethod
    def fetch_mapped_analytics(workspace_id: int, company_id: int, strategy_id: int, days: int = 30) -> list:
        ContentStrategyRepository.ensure_tables()
        cutoff = (datetime.now() - timedelta(days=max(1, int(days or 30)))).strftime("%Y-%m-%d")
        conn = get_db_connection()
        try:
            ContentStrategyRepository._require_strategy(conn, workspace_id, company_id, strategy_id)
            query = """
                SELECT
                    a.id AS analytics_id, a.post_id, a.platform AS analytics_platform, a.metric_date,
                    a.impressions, a.reach, a.likes, a.comments, a.shares, a.saves,
                    a.clicks, a.link_clicks, a.engagement_rate, a.raw_data,
                    p.title AS post_title, p.topic, p.content_type, p.viral_score,
                    ci.id AS calendar_item_id, ci.platform AS calendar_platform, ci.scheduled_at,
                    ci.planned_date, ci.metadata AS calendar_metadata,
                    cp.id AS pillar_id, cp.name AS pillar_name,
                    cs.id AS subtopic_id, cs.name AS subtopic_name, cs.target_persona AS subtopic_persona,
                    cs.funnel_stage AS subtopic_funnel_stage,
                    ca.id AS angle_id, ca.title AS angle_title, ca.cta AS angle_cta,
                    ca.cta_type AS angle_cta_type, ca.target_persona AS angle_persona,
                    ca.funnel_stage AS angle_funnel_stage,
                    cf.id AS format_variant_id, cf.format_type, cf.name AS format_name, cf.cta AS format_cta,
                    c.id AS campaign_id, c.name AS campaign_name, c.cta AS campaign_cta,
                    lm.id AS lead_magnet_id, lm.name AS lead_magnet_name, lm.cta AS lead_magnet_cta,
                    lm.funnel_stage AS lead_magnet_funnel_stage, lm.target_persona AS lead_magnet_persona
                FROM content_calendar_items ci
                JOIN analytics a ON a.post_id = ci.post_id AND a.workspace_id = ci.workspace_id
                LEFT JOIN posts p ON p.id = a.post_id AND p.workspace_id = ci.workspace_id
                LEFT JOIN content_pillars cp ON cp.id = ci.pillar_id AND cp.workspace_id = ci.workspace_id AND cp.company_id = ci.company_id
                LEFT JOIN content_subtopics cs ON cs.id = ci.subtopic_id AND cs.workspace_id = ci.workspace_id AND cs.company_id = ci.company_id
                LEFT JOIN content_angles ca ON ca.id = ci.angle_id AND ca.workspace_id = ci.workspace_id AND ca.company_id = ci.company_id
                LEFT JOIN content_format_variants cf ON cf.id = ci.format_variant_id AND cf.workspace_id = ci.workspace_id AND cf.company_id = ci.company_id
                LEFT JOIN campaigns c ON c.id = ci.campaign_id AND c.workspace_id = ci.workspace_id AND (c.company_id = ci.company_id OR c.company_id IS NULL)
                LEFT JOIN lead_magnet_calendar_items lmci ON lmci.calendar_item_id = ci.id AND lmci.workspace_id = ci.workspace_id AND lmci.company_id = ci.company_id
                LEFT JOIN lead_magnets lm ON lm.id = lmci.lead_magnet_id AND lm.workspace_id = ci.workspace_id AND lm.company_id = ci.company_id
                WHERE ci.workspace_id=? AND ci.company_id=? AND ci.strategy_id=?
                  AND ci.deleted_at IS NULL AND ci.post_id IS NOT NULL
                  AND a.metric_date >= ?
                ORDER BY a.metric_date ASC, a.id ASC
            """
            cur = conn.cursor()
            cur.execute(_adapt_sql(query), (workspace_id, company_id, strategy_id, cutoff))
            rows = []
            for row in cur.fetchall():
                item = dict(row)
                raw = _loads(item.get("raw_data"), {}) or {}
                metadata = _loads(item.get("calendar_metadata"), {}) or {}
                item["leads"] = _number(raw.get("leads"))
                item["revenue"] = _number(raw.get("revenue"))
                item["ad_spend"] = _number(raw.get("ad_spend"))
                item["platform"] = item.get("analytics_platform") or item.get("calendar_platform")
                item["cta"] = item.get("lead_magnet_cta") or item.get("format_cta") or item.get("angle_cta") or item.get("angle_cta_type") or item.get("campaign_cta") or metadata.get("cta")
                item["persona"] = item.get("lead_magnet_persona") or item.get("angle_persona") or item.get("subtopic_persona") or metadata.get("persona")
                item["funnel_stage"] = item.get("lead_magnet_funnel_stage") or item.get("angle_funnel_stage") or item.get("subtopic_funnel_stage") or metadata.get("funnel_stage")
                scheduled = str(item.get("scheduled_at") or item.get("planned_date") or "")
                item["time_slot"] = ContentStrategyLearningService._time_slot(scheduled)
                rows.append(item)
            return rows
        finally:
            conn.close()

    @staticmethod
    def _time_slot(value: str) -> str:
        text = str(value or "")
        hour = None
        if "T" in text and len(text.split("T", 1)[1]) >= 2:
            try:
                hour = int(text.split("T", 1)[1][:2])
            except Exception:
                hour = None
        if hour is None:
            return ""
        if 5 <= hour < 11:
            return "morning"
        if 11 <= hour < 15:
            return "midday"
        if 15 <= hour < 19:
            return "afternoon"
        return "evening"

    @staticmethod
    def analyze_strategy(workspace_id: int, company_id: int, strategy_id: int, days: int = 30, metric: str = "engagement_rate") -> dict:
        metric = metric if metric in SUPPORTED_METRICS else "engagement_rate"
        try:
            rows = ContentStrategyLearningService.fetch_mapped_analytics(workspace_id, company_id, strategy_id, days)
        except ValueError as exc:
            return {"ok": False, "error": str(exc), "sample_size": 0, "insights": [], "leaders": {}, "warnings": []}
        if not rows:
            return {"ok": True, "sample_size": 0, "insights": [], "leaders": {}, "warnings": ["No mapped analytics data available for this strategy."]}

        dates = [_safe_date(row.get("metric_date")) for row in rows if _safe_date(row.get("metric_date"))]
        period = {"start": min(dates) if dates else "", "end": max(dates) if dates else "", "days": days}
        warnings = []
        if len(rows) < MIN_TOTAL_SAMPLE:
            warnings.append(f"Insufficient total sample: {len(rows)} analytics rows; minimum is {MIN_TOTAL_SAMPLE}.")

        leaders = {}
        candidates = []
        for dimension, field, label in DIMENSIONS:
            groups = defaultdict(list)
            missing = 0
            for row in rows:
                value = str(row.get(field) or "").strip()
                if value:
                    groups[value].append(row)
                else:
                    missing += 1
            valid_groups = {key: vals for key, vals in groups.items() if len(vals) >= MIN_GROUP_SAMPLE}
            missing_ratio = missing / max(len(rows), 1)
            if missing:
                warnings.append(f"Missing {label} mapping for {missing}/{len(rows)} analytics rows.")
            if not valid_groups:
                leaders[dimension] = {"status": "insufficient_sample", "sample_size": 0, "missing": missing}
                continue
            ranked = sorted(valid_groups.items(), key=lambda item: _avg(item[1], metric), reverse=True)
            winner, winner_rows = ranked[0]
            winner_avg = _avg(winner_rows, metric)
            baseline_rows = [row for key, vals in valid_groups.items() if key != winner for row in vals]
            baseline = _avg(baseline_rows, metric) if baseline_rows else _avg(rows, metric)
            lift = ((winner_avg - baseline) / baseline * 100) if baseline > 0 else 0.0
            confidence, confidence_level = _confidence(len(winner_rows), lift, missing_ratio)
            leader = {
                "dimension": dimension,
                "label": label,
                "value": winner,
                "metric": metric,
                "metric_value": winner_avg,
                "baseline_value": baseline,
                "lift_percent": lift,
                "sample_size": len(winner_rows),
                "total_sample_size": len(rows),
                "confidence": confidence,
                "confidence_level": confidence_level,
                "missing_count": missing,
                "data_quality": {
                    "missing_count": missing,
                    "missing_ratio": missing_ratio,
                    "is_reliable": len(winner_rows) >= MIN_GROUP_SAMPLE and missing_ratio <= 0.4,
                    "notes": [] if missing_ratio <= 0.4 else ["High missing mapping ratio for this dimension."],
                },
            }
            leaders[dimension] = leader
            if len(rows) >= MIN_TOTAL_SAMPLE and leader["data_quality"]["is_reliable"]:
                candidates.append(leader)

        return {"ok": True, "sample_size": len(rows), "evidence_period": period, "leaders": leaders, "insights": candidates, "warnings": warnings}

    @staticmethod
    def generate_recommendations(workspace_id: int, company_id: int, strategy_id: int, days: int = 30, metric: str = "engagement_rate", created_by: int = None) -> dict:
        analysis = ContentStrategyLearningService.analyze_strategy(workspace_id, company_id, strategy_id, days, metric)
        if not analysis.get("ok"):
            return analysis
        if analysis.get("sample_size", 0) < MIN_TOTAL_SAMPLE:
            return {**analysis, "created": 0, "insight_ids": []}

        period = analysis.get("evidence_period") or {}
        period_text = f"{period.get('start', '')} to {period.get('end', '')}".strip()
        insight_ids = []
        for leader in analysis.get("insights", []):
            dimension = leader["dimension"]
            label = leader["label"]
            winner = leader["value"]
            observation = (
                f"{label} '{winner}' is correlated with the strongest {leader['metric']} "
                f"in the available mapped analytics sample. Sample size: {leader['sample_size']} rows."
            )
            recommendation = _recommendation_for(label, winner, leader["metric"], leader)
            affected = [{"dimension": dimension, "value": winner}]
            insight_id = LearningInsightModel.create(
                workspace_id=workspace_id,
                company_id=company_id,
                strategy_id=strategy_id,
                title=f"{label}: {winner} leads {leader['metric']}",
                description=observation,
                recommendation=recommendation,
                insight_type=_insight_type_for_dimension(dimension),
                platform=winner if dimension == "platform" else None,
                content_type=winner if dimension == "format" else None,
                avg_reach=leader["metric_value"] if leader["metric"] == "reach" else 0,
                avg_ctr=leader["metric_value"] if leader["metric"] == "ctr" else 0,
                avg_er=leader["metric_value"] if leader["metric"] == "engagement_rate" else 0,
                avg_leads=leader["metric_value"] if leader["metric"] == "leads" else 0,
                sample_size=leader["sample_size"],
                confidence=leader["confidence"],
                evidence_period=period_text,
                metric=leader["metric"],
                observation=observation,
                confidence_level=leader["confidence_level"],
                affected_pillar=winner if dimension == "pillar" else "",
                affected_subtopic=winner if dimension == "subtopic" else "",
                affected_platform=winner if dimension == "platform" else "",
                affected_dimensions=affected,
                data_quality=leader["data_quality"],
                data_snapshot={"leader": leader, "warnings": analysis.get("warnings", [])},
            )
            insight_ids.append(insight_id)
        return {**analysis, "created": len(insight_ids), "insight_ids": insight_ids}

    @staticmethod
    def accept_recommendation(workspace_id: int, company_id: int, insight_id: int, user_id: int = None) -> dict:
        insight = LearningInsightModel.get_by_id(insight_id, workspace_id=workspace_id, company_id=company_id)
        if not insight:
            return {"ok": False, "error": "Insight not found for this workspace/company"}
        ok = LearningInsightModel.update_status(insight_id, "accepted", user_id=user_id)
        return {"ok": ok, "insight_id": insight_id, "status": "accepted" if ok else insight.get("status")}

    @staticmethod
    def reject_recommendation(workspace_id: int, company_id: int, insight_id: int, user_id: int = None, reason: str = "") -> dict:
        insight = LearningInsightModel.get_by_id(insight_id, workspace_id=workspace_id, company_id=company_id)
        if not insight:
            return {"ok": False, "error": "Insight not found for this workspace/company"}
        ok = LearningInsightModel.update_status(insight_id, "rejected", user_id=user_id, reason=reason)
        return {"ok": ok, "insight_id": insight_id, "status": "rejected" if ok else insight.get("status")}

    @staticmethod
    def create_revised_version(workspace_id: int, company_id: int, strategy_id: int, insight_id: int, user_id: int = None) -> dict:
        insight = LearningInsightModel.get_by_id(insight_id, workspace_id=workspace_id, company_id=company_id)
        if not insight or insight.get("strategy_id") != strategy_id:
            return {"ok": False, "error": "Insight not found for this strategy"}
        if insight.get("status") != "accepted":
            return {"ok": False, "error": "Insight must be accepted before applying"}
        strategy = ContentStrategyRepository.get_strategy(workspace_id, company_id, strategy_id, include_children=False)
        if not strategy:
            return {"ok": False, "error": "Strategy not found for this workspace/company"}

        version_id = ContentStrategyRepository.create_strategy_version(
            workspace_id,
            company_id,
            strategy_id,
            notes=f"Before applying learning insight #{insight_id}",
            created_by=user_id,
        )
        metadata = dict(strategy.get("metadata") or {})
        applied = list(metadata.get("applied_learning_insights") or [])
        applied.append(
            {
                "insight_id": insight_id,
                "applied_at": now_iso(),
                "recommendation": insight.get("recommendation"),
                "evidence_period": insight.get("evidence_period"),
                "sample_size": insight.get("sample_size"),
                "metric": insight.get("metric"),
                "affected_dimensions": insight.get("affected_dimensions") or [],
                "pre_apply_version_id": version_id,
            }
        )
        metadata["applied_learning_insights"] = applied
        metadata["strategy_revision_source"] = "learning_loop"
        ContentStrategyRepository.update_strategy(workspace_id, company_id, strategy_id, metadata=metadata, updated_by=user_id)
        LearningInsightModel.update_status(insight_id, "applied", user_id=user_id, applied_version_id=version_id)
        LearningInsightModel.increment_applied(insight_id)
        return {"ok": True, "strategy_id": strategy_id, "insight_id": insight_id, "version_id": version_id}

    @staticmethod
    def compare_versions(workspace_id: int, company_id: int, strategy_id: int, left_version_id: int, right_version_id: int) -> dict:
        ContentStrategyRepository.ensure_tables()
        conn = get_db_connection()
        try:
            ContentStrategyRepository._require_strategy(conn, workspace_id, company_id, strategy_id)
            cur = conn.cursor()
            cur.execute(
                _adapt_sql(
                    """SELECT * FROM content_strategy_versions
                       WHERE strategy_id=? AND workspace_id=? AND company_id=? AND id IN (?,?)"""
                ),
                (strategy_id, workspace_id, company_id, left_version_id, right_version_id),
            )
            versions = {row["id"]: row_to_dict(row) for row in cur.fetchall()}
            if left_version_id not in versions or right_version_id not in versions:
                return {"ok": False, "error": "Both versions must belong to this workspace/company/strategy"}
            left = versions[left_version_id]["snapshot"]
            right = versions[right_version_id]["snapshot"]
            summary = {}
            for key in ["pillars", "subtopics", "angles", "format_variants", "calendar_items", "lead_magnets", "kpis"]:
                summary[key] = {"left_count": len(left.get(key, [])), "right_count": len(right.get(key, []))}
            left_meta = (left.get("strategy") or {}).get("metadata") or {}
            right_meta = (right.get("strategy") or {}).get("metadata") or {}
            return {"ok": True, "left_version": versions[left_version_id]["version"], "right_version": versions[right_version_id]["version"], "summary": summary, "metadata_changed": left_meta != right_meta}
        finally:
            conn.close()

    @staticmethod
    def restore_previous_version(workspace_id: int, company_id: int, strategy_id: int, version_id: int, user_id: int = None) -> dict:
        ok = ContentStrategyRepository.restore_strategy_version(workspace_id, company_id, strategy_id, version_id, updated_by=user_id)
        return {"ok": ok, "strategy_id": strategy_id, "restored_version_id": version_id}

