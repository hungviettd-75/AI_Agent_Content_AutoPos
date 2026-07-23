"""CRUD helpers for learning_insights (Learning Loop)."""

import json
from datetime import datetime, timedelta

from config.config import logger
from database.connection import managed_connection, get_db_connection, _adapt_sql, _is_postgres


JSON_FIELDS = {"data_snapshot", "affected_dimensions", "data_quality"}


def _json_dumps(value):
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)


def _json_loads(value, default=None):
    if value in (None, ""):
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return default


def _row_to_dict(row) -> dict:
    if not row:
        return {}
    data = dict(row)
    for field in JSON_FIELDS:
        if field in data:
            data[field] = _json_loads(data.get(field), [] if field == "affected_dimensions" else {})
    return data


class LearningInsightModel:
    VALID_STATUS = {"new", "accepted", "rejected", "applied", "dismissed", "expired"}
    VALID_TYPES = {
        "content_pattern",
        "platform_strategy",
        "timing",
        "audience",
        "cta_effectiveness",
        "topic_performance",
        "format_performance",
        "funnel_performance",
        "campaign_performance",
        "lead_magnet_performance",
        "strategy_recommendation",
    }

    @staticmethod
    def create(
        workspace_id: int,
        title: str,
        description: str = "",
        recommendation: str = "",
        insight_type: str = "content_pattern",
        platform: str = None,
        content_type: str = None,
        avg_reach: float = 0,
        avg_ctr: float = 0,
        avg_er: float = 0,
        avg_leads: float = 0,
        avg_roi: float = 0,
        sample_size: int = 0,
        confidence: float = 0.0,
        data_snapshot: dict = None,
        expires_days: int = 30,
        company_id: int = None,
        strategy_id: int = None,
        evidence_period: str = "",
        metric: str = "",
        observation: str = "",
        confidence_level: str = "",
        affected_pillar: str = "",
        affected_subtopic: str = "",
        affected_platform: str = "",
        affected_dimensions: list = None,
        data_quality: dict = None,
    ) -> int:
        now = datetime.now().isoformat()
        expires_at = (datetime.now() + timedelta(days=expires_days)).isoformat() if expires_days else None
        if insight_type not in LearningInsightModel.VALID_TYPES:
            insight_type = "content_pattern"
        sql = _adapt_sql(
            """
            INSERT INTO learning_insights (
                workspace_id, company_id, strategy_id, insight_type, platform, content_type,
                title, description, recommendation, data_snapshot,
                avg_reach, avg_ctr, avg_er, avg_leads, avg_roi,
                sample_size, confidence, status, generated_at, expires_at,
                evidence_period, metric, observation, confidence_level,
                affected_pillar, affected_subtopic, affected_platform,
                affected_dimensions, data_quality
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """
        )
        logger.info("[LEARNING] Create insight: %s", title[:80])
        with managed_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                sql,
                (
                    workspace_id,
                    company_id,
                    strategy_id,
                    insight_type,
                    platform,
                    content_type,
                    title,
                    description,
                    recommendation,
                    _json_dumps(data_snapshot or {}),
                    avg_reach,
                    avg_ctr,
                    avg_er,
                    avg_leads,
                    avg_roi,
                    sample_size,
                    confidence,
                    "new",
                    now,
                    expires_at,
                    evidence_period,
                    metric,
                    observation,
                    confidence_level,
                    affected_pillar,
                    affected_subtopic,
                    affected_platform,
                    _json_dumps(affected_dimensions or []),
                    _json_dumps(data_quality or {}),
                ),
            )
            if _is_postgres():
                cur.execute("SELECT lastval()")
                return cur.fetchone()[0]
            return cur.lastrowid

    @staticmethod
    def get_by_id(insight_id: int, workspace_id: int = None, company_id: int = None) -> dict:
        conn = get_db_connection()
        try:
            query = "SELECT * FROM learning_insights WHERE id=?"
            params = [insight_id]
            if workspace_id is not None:
                query += " AND workspace_id=?"
                params.append(workspace_id)
            if company_id is not None:
                query += " AND (company_id=? OR company_id IS NULL)"
                params.append(company_id)
            cur = conn.cursor()
            cur.execute(_adapt_sql(query), params)
            return _row_to_dict(cur.fetchone())
        finally:
            conn.close()

    @staticmethod
    def list_by_workspace(workspace_id: int, status: str = None, insight_type: str = None, limit: int = 50, company_id: int = None, strategy_id: int = None) -> list:
        conn = get_db_connection()
        try:
            query = "SELECT * FROM learning_insights WHERE workspace_id=?"
            params = [workspace_id]
            if company_id is not None:
                query += " AND (company_id=? OR company_id IS NULL)"
                params.append(company_id)
            if strategy_id is not None:
                query += " AND strategy_id=?"
                params.append(strategy_id)
            if status:
                query += " AND status=?"
                params.append(status)
            if insight_type:
                query += " AND insight_type=?"
                params.append(insight_type)
            query += " ORDER BY confidence DESC, generated_at DESC"
            if limit:
                query += _adapt_sql(" LIMIT ?")
                params.append(limit)
            cur = conn.cursor()
            cur.execute(_adapt_sql(query), params)
            return [_row_to_dict(row) for row in cur.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def get_active(workspace_id: int, company_id: int = None, strategy_id: int = None) -> list:
        now = datetime.now().isoformat()
        conn = get_db_connection()
        try:
            query = """
                SELECT * FROM learning_insights
                WHERE workspace_id=? AND status IN ('new', 'accepted')
                AND (expires_at IS NULL OR expires_at > ?)
            """
            params = [workspace_id, now]
            if company_id is not None:
                query += " AND (company_id=? OR company_id IS NULL)"
                params.append(company_id)
            if strategy_id is not None:
                query += " AND strategy_id=?"
                params.append(strategy_id)
            query += " ORDER BY confidence DESC, generated_at DESC"
            cur = conn.cursor()
            cur.execute(_adapt_sql(query), params)
            return [_row_to_dict(row) for row in cur.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def update_status(insight_id: int, status: str, user_id: int = None, reason: str = "", applied_version_id: int = None) -> bool:
        if status not in LearningInsightModel.VALID_STATUS:
            logger.warning("[LEARNING] Invalid status: %s", status)
            return False
        now = datetime.now().isoformat()
        values = {"status": status}
        if status == "accepted":
            values.update({"accepted_by": user_id, "accepted_at": now, "rejected_by": None, "rejected_at": None, "rejection_reason": None})
        elif status in {"rejected", "dismissed"}:
            values.update({"rejected_by": user_id, "rejected_at": now, "rejection_reason": reason})
        elif status == "applied":
            values.update({"applied_at": now, "applied_version_id": applied_version_id})
        set_clause = ", ".join([f"{key}=?" for key in values])
        sql = _adapt_sql(f"UPDATE learning_insights SET {set_clause} WHERE id=?")
        with managed_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (*values.values(), insight_id))
            return cur.rowcount > 0

    @staticmethod
    def increment_applied(insight_id: int) -> bool:
        sql = _adapt_sql("UPDATE learning_insights SET applied_count = applied_count + 1 WHERE id=?")
        with managed_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (insight_id,))
            return cur.rowcount > 0

    @staticmethod
    def delete_expired(workspace_id: int) -> int:
        now = datetime.now().isoformat()
        sql = _adapt_sql(
            """
            DELETE FROM learning_insights
            WHERE workspace_id=? AND (
                (expires_at IS NOT NULL AND expires_at < ?) OR status IN ('dismissed', 'expired')
            )
            """
        )
        with managed_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (workspace_id, now))
            deleted = cur.rowcount
            logger.info("[LEARNING] Deleted %s old insights", deleted)
            return deleted

    @staticmethod
    def count_by_type(workspace_id: int) -> dict:
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                _adapt_sql("SELECT insight_type, COUNT(*) FROM learning_insights WHERE workspace_id=? GROUP BY insight_type"),
                (workspace_id,),
            )
            return {row[0]: row[1] for row in cur.fetchall()}
        finally:
            conn.close()
