"""Repository layer for AI Content Strategy Center.

All public methods require ``workspace_id`` and ``company_id``. The repository
checks tenant ownership before reading or mutating strategy data.
"""

from datetime import datetime
from database.connection import managed_connection, get_db_connection, _adapt_sql, _is_postgres
from database.models.content_strategy import (
    ContentStrategyModel,
    dumps_json,
    now_iso,
    row_to_dict,
    rows_to_dicts,
    slugify,
)


class ContentStrategyRepository:
    @staticmethod
    def ensure_tables():
        ContentStrategyModel.ensure_tables()

    @staticmethod
    def _last_id(cur):
        if _is_postgres():
            cur.execute("SELECT lastval()")
            return cur.fetchone()[0]
        return cur.lastrowid

    @staticmethod
    def _company_belongs_to_workspace(conn, workspace_id: int, company_id: int) -> bool:
        cur = conn.cursor()
        cur.execute(
            _adapt_sql("SELECT 1 FROM companies WHERE id=? AND workspace_id=?"),
            (company_id, workspace_id),
        )
        return cur.fetchone() is not None

    @staticmethod
    def _get_strategy_row(conn, workspace_id: int, company_id: int, strategy_id: int, include_deleted=False):
        sql = "SELECT * FROM content_strategies WHERE id=? AND workspace_id=? AND company_id=?"
        params = [strategy_id, workspace_id, company_id]
        if not include_deleted:
            sql += " AND deleted_at IS NULL"
        cur = conn.cursor()
        cur.execute(_adapt_sql(sql), params)
        return cur.fetchone()

    @staticmethod
    def _require_strategy(conn, workspace_id: int, company_id: int, strategy_id: int) -> dict:
        row = ContentStrategyRepository._get_strategy_row(conn, workspace_id, company_id, strategy_id)
        if not row:
            raise ValueError("Strategy not found for this workspace/company")
        return row_to_dict(row)

    @staticmethod
    def _require_pillar(conn, workspace_id: int, company_id: int, strategy_id: int, pillar_id: int) -> dict:
        cur = conn.cursor()
        cur.execute(
            _adapt_sql(
                """SELECT * FROM content_pillars
                   WHERE id=? AND strategy_id=? AND workspace_id=? AND company_id=? AND deleted_at IS NULL"""
            ),
            (pillar_id, strategy_id, workspace_id, company_id),
        )
        row = cur.fetchone()
        if not row:
            raise ValueError("Pillar not found for this strategy")
        return row_to_dict(row)

    @staticmethod
    def _require_subtopic(conn, workspace_id: int, company_id: int, strategy_id: int, subtopic_id: int) -> dict:
        cur = conn.cursor()
        cur.execute(
            _adapt_sql(
                """SELECT * FROM content_subtopics
                   WHERE id=? AND strategy_id=? AND workspace_id=? AND company_id=? AND deleted_at IS NULL"""
            ),
            (subtopic_id, strategy_id, workspace_id, company_id),
        )
        row = cur.fetchone()
        if not row:
            raise ValueError("Subtopic not found for this strategy")
        return row_to_dict(row)

    @staticmethod
    def _insert(cur, table: str, values: dict) -> int:
        columns = ", ".join(values.keys())
        placeholders = ", ".join(["?"] * len(values))
        sql = _adapt_sql(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})")
        cur.execute(sql, tuple(values.values()))
        return ContentStrategyRepository._last_id(cur)

    @staticmethod
    def _insert_preserving_id(cur, table: str, values: dict):
        columns = ", ".join(values.keys())
        placeholders = ", ".join(["?"] * len(values))
        sql = _adapt_sql(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})")
        cur.execute(sql, tuple(values.values()))

    @staticmethod
    def _update(cur, table: str, record_id: int, values: dict, where: str, where_params: tuple) -> bool:
        if not values:
            return False
        set_clause = ", ".join([f"{key}=?" for key in values])
        sql = _adapt_sql(f"UPDATE {table} SET {set_clause} WHERE id=? AND {where}")
        cur.execute(sql, (*values.values(), record_id, *where_params))
        return cur.rowcount > 0

    @staticmethod
    def _audit(cur, action: str, workspace_id: int, user_id: int = None, entity_type: str = "", entity_id=None, description: str = "", new_value: dict = None):
        cur.execute(
            _adapt_sql(
                """INSERT INTO audit_logs
                   (timestamp, user_id, user_email, workspace_id, action, entity_type, entity_id, description, old_value, new_value, ip_address)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)"""
            ),
            (now_iso(), user_id, "", workspace_id, action, entity_type, str(entity_id) if entity_id is not None else None, description, None, dumps_json(new_value or {}), ""),
        )

    @staticmethod
    def create_strategy(workspace_id: int, company_id: int, name: str, **kwargs) -> int:
        now = now_iso()
        with managed_connection() as conn:
            if not ContentStrategyRepository._company_belongs_to_workspace(conn, workspace_id, company_id):
                raise ValueError("Company does not belong to workspace")
            cur = conn.cursor()
            values = {
                "workspace_id": workspace_id,
                "company_id": company_id,
                "campaign_id": kwargs.get("campaign_id"),
                "project_id": kwargs.get("project_id"),
                "name": name,
                "description": kwargs.get("description", ""),
                "strategy_type": kwargs.get("strategy_type", "content"),
                "status": kwargs.get("status", "draft"),
                "start_date": kwargs.get("start_date"),
                "end_date": kwargs.get("end_date"),
                "metadata": dumps_json(kwargs.get("metadata") or {}),
                "sort_order": kwargs.get("sort_order", 0),
                "created_by": kwargs.get("created_by"),
                "updated_by": kwargs.get("created_by"),
                "created_at": now,
                "updated_at": now,
            }
            try:
                return ContentStrategyRepository._insert(cur, "content_strategies", values)
            except Exception as exc:
                if "UNIQUE" in str(exc).upper() or "unique" in str(exc):
                    raise ValueError("Duplicate strategy name for workspace/company") from exc
                raise

    @staticmethod
    def get_strategy(workspace_id: int, company_id: int, strategy_id: int, include_children: bool = True) -> dict:
        conn = get_db_connection()
        try:
            strategy = row_to_dict(
                ContentStrategyRepository._get_strategy_row(conn, workspace_id, company_id, strategy_id)
            )
            if not strategy or not include_children:
                return strategy
            strategy.update(ContentStrategyRepository._load_children(conn, workspace_id, company_id, strategy_id))
            return strategy
        finally:
            conn.close()

    @staticmethod
    def list_strategies(workspace_id: int, company_id: int, status: str = None, include_archived: bool = False, limit: int = None, offset: int = 0) -> list:
        conn = get_db_connection()
        try:
            query = "SELECT * FROM content_strategies WHERE workspace_id=? AND company_id=? AND deleted_at IS NULL"
            params = [workspace_id, company_id]
            if status:
                query += " AND status=?"
                params.append(status)
            elif not include_archived:
                query += " AND status <> 'archived'"
            query += " ORDER BY sort_order ASC, updated_at DESC"
            if limit is not None:
                safe_limit = max(1, min(int(limit), 100))
                query += " LIMIT ? OFFSET ?"
                params.extend([safe_limit, max(0, int(offset or 0))])
            cur = conn.cursor()
            cur.execute(_adapt_sql(query), params)
            return rows_to_dicts(cur.fetchall())
        finally:
            conn.close()

    @staticmethod
    def update_strategy(workspace_id: int, company_id: int, strategy_id: int, **kwargs) -> bool:
        allowed = {
            "name",
            "description",
            "strategy_type",
            "status",
            "start_date",
            "end_date",
            "campaign_id",
            "project_id",
            "metadata",
            "sort_order",
            "updated_by",
        }
        values = {key: kwargs[key] for key in allowed if key in kwargs}
        if "metadata" in values:
            values["metadata"] = dumps_json(values["metadata"])
        values["updated_at"] = now_iso()
        with managed_connection() as conn:
            ContentStrategyRepository._require_strategy(conn, workspace_id, company_id, strategy_id)
            cur = conn.cursor()
            return ContentStrategyRepository._update(
                cur,
                "content_strategies",
                strategy_id,
                values,
                "workspace_id=? AND company_id=? AND deleted_at IS NULL",
                (workspace_id, company_id),
            )

    @staticmethod
    def archive_strategy(workspace_id: int, company_id: int, strategy_id: int, updated_by: int = None) -> bool:
        return ContentStrategyRepository.update_strategy(
            workspace_id,
            company_id,
            strategy_id,
            status="archived",
            updated_by=updated_by,
        )

    @staticmethod
    def create_pillar(workspace_id: int, company_id: int, strategy_id: int, name: str, **kwargs) -> int:
        now = now_iso()
        with managed_connection() as conn:
            ContentStrategyRepository._require_strategy(conn, workspace_id, company_id, strategy_id)
            cur = conn.cursor()
            values = {
                "workspace_id": workspace_id,
                "company_id": company_id,
                "strategy_id": strategy_id,
                "name": name,
                "slug": kwargs.get("slug") or slugify(name),
                "description": kwargs.get("description", ""),
                "objective": kwargs.get("objective", ""),
                "status": kwargs.get("status", "active"),
                "sort_order": kwargs.get("sort_order", 0),
                "created_by": kwargs.get("created_by"),
                "updated_by": kwargs.get("created_by"),
                "created_at": now,
                "updated_at": now,
            }
            try:
                return ContentStrategyRepository._insert(cur, "content_pillars", values)
            except Exception as exc:
                if "UNIQUE" in str(exc).upper() or "unique" in str(exc):
                    raise ValueError("Duplicate pillar slug for strategy") from exc
                raise

    @staticmethod
    def update_pillar(workspace_id: int, company_id: int, strategy_id: int, pillar_id: int, **kwargs) -> bool:
        allowed = {"name", "description", "objective", "status", "sort_order", "updated_by"}
        values = {key: kwargs[key] for key in allowed if key in kwargs}
        if "name" in values and "slug" not in kwargs:
            values["slug"] = slugify(values["name"])
        if "slug" in kwargs:
            values["slug"] = kwargs["slug"]
        values["updated_at"] = now_iso()
        with managed_connection() as conn:
            ContentStrategyRepository._require_pillar(conn, workspace_id, company_id, strategy_id, pillar_id)
            cur = conn.cursor()
            return ContentStrategyRepository._update(
                cur,
                "content_pillars",
                pillar_id,
                values,
                "strategy_id=? AND workspace_id=? AND company_id=? AND deleted_at IS NULL",
                (strategy_id, workspace_id, company_id),
            )

    @staticmethod
    def reorder_pillars(workspace_id: int, company_id: int, strategy_id: int, ordered_pillar_ids: list, updated_by: int = None) -> bool:
        with managed_connection() as conn:
            ContentStrategyRepository._require_strategy(conn, workspace_id, company_id, strategy_id)
            for pillar_id in ordered_pillar_ids:
                ContentStrategyRepository._require_pillar(conn, workspace_id, company_id, strategy_id, pillar_id)
            cur = conn.cursor()
            now = now_iso()
            for index, pillar_id in enumerate(ordered_pillar_ids):
                cur.execute(
                    _adapt_sql(
                        """UPDATE content_pillars
                           SET sort_order=?, updated_by=?, updated_at=?
                           WHERE id=? AND strategy_id=? AND workspace_id=? AND company_id=?"""
                    ),
                    (index, updated_by, now, pillar_id, strategy_id, workspace_id, company_id),
                )
            return True

    @staticmethod
    def create_subtopic(workspace_id: int, company_id: int, strategy_id: int, pillar_id: int, name: str, **kwargs) -> int:
        now = now_iso()
        with managed_connection() as conn:
            ContentStrategyRepository._require_pillar(conn, workspace_id, company_id, strategy_id, pillar_id)
            cur = conn.cursor()
            values = {
                "workspace_id": workspace_id,
                "company_id": company_id,
                "strategy_id": strategy_id,
                "pillar_id": pillar_id,
                "name": name,
                "slug": kwargs.get("slug") or slugify(name),
                "description": kwargs.get("description", ""),
                "target_persona": kwargs.get("target_persona", ""),
                "business_goal": kwargs.get("business_goal", ""),
                "intent": kwargs.get("intent", ""),
                "funnel_stage": kwargs.get("funnel_stage", ""),
                "priority": kwargs.get("priority", "medium"),
                "trend_classification": kwargs.get("trend_classification", "evergreen"),
                "suggested_channels": dumps_json(kwargs.get("suggested_channels") or []),
                "source": kwargs.get("source", "manual"),
                "metadata": dumps_json(kwargs.get("metadata") or {}),
                "status": kwargs.get("status", "active"),
                "sort_order": kwargs.get("sort_order", 0),
                "created_by": kwargs.get("created_by"),
                "updated_by": kwargs.get("created_by"),
                "created_at": now,
                "updated_at": now,
            }
            return ContentStrategyRepository._insert(cur, "content_subtopics", values)

    @staticmethod
    def update_subtopic(workspace_id: int, company_id: int, strategy_id: int, subtopic_id: int, **kwargs) -> bool:
        allowed = {
            "pillar_id", "name", "description", "status", "sort_order", "updated_by",
            "target_persona", "business_goal", "intent", "funnel_stage", "priority",
            "trend_classification", "suggested_channels", "source", "metadata",
        }
        values = {key: kwargs[key] for key in allowed if key in kwargs}
        if "name" in values and "slug" not in kwargs:
            values["slug"] = slugify(values["name"])
        if "slug" in kwargs:
            values["slug"] = kwargs["slug"]
        if "suggested_channels" in values:
            values["suggested_channels"] = dumps_json(values["suggested_channels"])
        if "metadata" in values:
            values["metadata"] = dumps_json(values["metadata"])
        values["updated_at"] = now_iso()
        with managed_connection() as conn:
            ContentStrategyRepository._require_subtopic(conn, workspace_id, company_id, strategy_id, subtopic_id)
            if values.get("pillar_id"):
                ContentStrategyRepository._require_pillar(conn, workspace_id, company_id, strategy_id, values["pillar_id"])
            cur = conn.cursor()
            return ContentStrategyRepository._update(
                cur,
                "content_subtopics",
                subtopic_id,
                values,
                "strategy_id=? AND workspace_id=? AND company_id=? AND deleted_at IS NULL",
                (strategy_id, workspace_id, company_id),
            )

    @staticmethod
    def reorder_subtopics(workspace_id: int, company_id: int, strategy_id: int, ordered_subtopic_ids: list, updated_by: int = None) -> bool:
        with managed_connection() as conn:
            ContentStrategyRepository._require_strategy(conn, workspace_id, company_id, strategy_id)
            for subtopic_id in ordered_subtopic_ids:
                ContentStrategyRepository._require_subtopic(conn, workspace_id, company_id, strategy_id, subtopic_id)
            cur = conn.cursor()
            now = now_iso()
            for index, subtopic_id in enumerate(ordered_subtopic_ids):
                cur.execute(
                    _adapt_sql(
                        """UPDATE content_subtopics
                           SET sort_order=?, updated_by=?, updated_at=?
                           WHERE id=? AND strategy_id=? AND workspace_id=? AND company_id=?"""
                    ),
                    (index, updated_by, now, subtopic_id, strategy_id, workspace_id, company_id),
                )
            return True

    @staticmethod
    def move_subtopic(workspace_id: int, company_id: int, strategy_id: int, subtopic_id: int, target_pillar_id: int, updated_by: int = None) -> bool:
        with managed_connection() as conn:
            ContentStrategyRepository._require_subtopic(conn, workspace_id, company_id, strategy_id, subtopic_id)
            ContentStrategyRepository._require_pillar(conn, workspace_id, company_id, strategy_id, target_pillar_id)
            cur = conn.cursor()
            cur.execute(
                _adapt_sql(
                    """UPDATE content_subtopics
                       SET pillar_id=?, updated_by=?, updated_at=?
                       WHERE id=? AND strategy_id=? AND workspace_id=? AND company_id=? AND deleted_at IS NULL"""
                ),
                (target_pillar_id, updated_by, now_iso(), subtopic_id, strategy_id, workspace_id, company_id),
            )
            return cur.rowcount > 0
    @staticmethod
    def create_angles_batch(workspace_id: int, company_id: int, strategy_id: int, angles: list, created_by: int = None) -> list:
        ids = []
        now = now_iso()
        with managed_connection() as conn:
            ContentStrategyRepository._require_strategy(conn, workspace_id, company_id, strategy_id)
            cur = conn.cursor()
            for index, angle in enumerate(angles):
                pillar_id = angle["pillar_id"]
                ContentStrategyRepository._require_pillar(conn, workspace_id, company_id, strategy_id, pillar_id)
                subtopic_id = angle.get("subtopic_id")
                if subtopic_id:
                    ContentStrategyRepository._require_subtopic(conn, workspace_id, company_id, strategy_id, subtopic_id)
                title = angle.get("title") or angle.get("working_title")
                values = {
                    "workspace_id": workspace_id,
                    "company_id": company_id,
                    "strategy_id": strategy_id,
                    "pillar_id": pillar_id,
                    "subtopic_id": subtopic_id,
                    "title": title,
                    "slug": angle.get("slug") or slugify(title),
                    "description": angle.get("description") or angle.get("core_insight", ""),
                    "hook": angle.get("hook") or angle.get("hook_idea", ""),
                    "cta": angle.get("cta") or angle.get("cta_type", ""),
                    "category": angle.get("category", ""),
                    "core_insight": angle.get("core_insight", ""),
                    "intended_emotion": angle.get("intended_emotion", ""),
                    "target_persona": angle.get("target_persona", ""),
                    "funnel_stage": angle.get("funnel_stage", ""),
                    "cta_type": angle.get("cta_type", ""),
                    "evidence_requirement": angle.get("evidence_requirement", ""),
                    "trend_classification": angle.get("trend_classification", "evergreen"),
                    "priority": angle.get("priority", "medium"),
                    "risk_level": angle.get("risk_level", "low"),
                    "source": angle.get("source", "manual"),
                    "metadata": dumps_json(angle.get("metadata") or {}),
                    "status": angle.get("status", "active"),
                    "sort_order": angle.get("sort_order", index),
                    "created_by": angle.get("created_by", created_by),
                    "updated_by": angle.get("created_by", created_by),
                    "created_at": now,
                    "updated_at": now,
                }
                ids.append(ContentStrategyRepository._insert(cur, "content_angles", values))
        return ids

    @staticmethod
    def _require_angle(conn, workspace_id: int, company_id: int, strategy_id: int, angle_id: int) -> dict:
        cur = conn.cursor()
        cur.execute(
            _adapt_sql(
                """SELECT * FROM content_angles
                   WHERE id=? AND strategy_id=? AND workspace_id=? AND company_id=? AND deleted_at IS NULL"""
            ),
            (angle_id, strategy_id, workspace_id, company_id),
        )
        row = cur.fetchone()
        if not row:
            raise ValueError("Angle not found for this strategy")
        return row_to_dict(row)

    @staticmethod
    def create_format_variants_batch(workspace_id: int, company_id: int, strategy_id: int, variants: list, created_by: int = None) -> list:
        ids = []
        now = now_iso()
        with managed_connection() as conn:
            ContentStrategyRepository._require_strategy(conn, workspace_id, company_id, strategy_id)
            cur = conn.cursor()
            for index, item in enumerate(variants):
                angle_id = item.get("angle_id")
                if angle_id:
                    ContentStrategyRepository._require_angle(conn, workspace_id, company_id, strategy_id, angle_id)
                values = {
                    "workspace_id": workspace_id,
                    "company_id": company_id,
                    "strategy_id": strategy_id,
                    "angle_id": angle_id,
                    "platform": item.get("platform", "facebook"),
                    "format_type": item.get("format_type") or item.get("format"),
                    "name": item.get("name") or f"{item.get('platform', 'facebook')} {item.get('format') or item.get('format_type')}",
                    "description": item.get("description") or item.get("adaptation_guidance", ""),
                    "specs": dumps_json(item.get("specs") or {}),
                    "target_length": item.get("target_length", ""),
                    "tone_override": item.get("tone_override", ""),
                    "cta": item.get("cta", ""),
                    "visual_requirement": item.get("visual_requirement", ""),
                    "hook_style": item.get("hook_style", ""),
                    "publishing_objective": item.get("publishing_objective", ""),
                    "repurposing_source": item.get("repurposing_source", ""),
                    "priority": item.get("priority", "medium"),
                    "publishing_enabled": 1 if item.get("publishing_enabled") else 0,
                    "production_effort": item.get("production_effort", ""),
                    "adaptation_guidance": item.get("adaptation_guidance", ""),
                    "brief": item.get("brief", ""),
                    "metadata": dumps_json(item.get("metadata") or {}),
                    "status": item.get("status", "active"),
                    "sort_order": item.get("sort_order", index),
                    "created_by": item.get("created_by", created_by),
                    "updated_by": item.get("created_by", created_by),
                    "created_at": now,
                    "updated_at": now,
                }
                ids.append(ContentStrategyRepository._insert(cur, "content_format_variants", values))
        return ids

    @staticmethod
    def list_format_variants(workspace_id: int, company_id: int, strategy_id: int, angle_id: int = None) -> list:
        conn = get_db_connection()
        try:
            ContentStrategyRepository._require_strategy(conn, workspace_id, company_id, strategy_id)
            query = """SELECT * FROM content_format_variants
                       WHERE workspace_id=? AND company_id=? AND strategy_id=? AND deleted_at IS NULL"""
            params = [workspace_id, company_id, strategy_id]
            if angle_id:
                query += " AND angle_id=?"
                params.append(angle_id)
            query += " ORDER BY sort_order ASC, id ASC"
            cur = conn.cursor()
            cur.execute(_adapt_sql(query), params)
            return rows_to_dicts(cur.fetchall())
        finally:
            conn.close()

    @staticmethod
    def update_format_variant(workspace_id: int, company_id: int, strategy_id: int, variant_id: int, **kwargs) -> bool:
        allowed = {
            "angle_id", "platform", "format_type", "name", "description", "specs",
            "target_length", "tone_override", "cta", "visual_requirement",
            "hook_style", "publishing_objective", "repurposing_source", "priority",
            "publishing_enabled", "production_effort", "adaptation_guidance", "brief",
            "metadata", "status", "sort_order", "updated_by",
        }
        values = {key: kwargs[key] for key in allowed if key in kwargs}
        if "format" in kwargs and "format_type" not in values:
            values["format_type"] = kwargs["format"]
        if "specs" in values:
            values["specs"] = dumps_json(values["specs"])
        if "metadata" in values:
            values["metadata"] = dumps_json(values["metadata"])
        if "publishing_enabled" in values:
            values["publishing_enabled"] = 1 if values["publishing_enabled"] else 0
        values["updated_at"] = now_iso()
        with managed_connection() as conn:
            ContentStrategyRepository._require_strategy(conn, workspace_id, company_id, strategy_id)
            if values.get("angle_id"):
                ContentStrategyRepository._require_angle(conn, workspace_id, company_id, strategy_id, values["angle_id"])
            cur = conn.cursor()
            return ContentStrategyRepository._update(
                cur,
                "content_format_variants",
                variant_id,
                values,
                "strategy_id=? AND workspace_id=? AND company_id=? AND deleted_at IS NULL",
                (strategy_id, workspace_id, company_id),
            )

    @staticmethod
    def create_calendar_items_batch(workspace_id: int, company_id: int, strategy_id: int, items: list, created_by: int = None) -> list:
        ids = []
        now = now_iso()
        with managed_connection() as conn:
            ContentStrategyRepository._require_strategy(conn, workspace_id, company_id, strategy_id)
            cur = conn.cursor()
            for index, item in enumerate(items):
                values = {
                    "workspace_id": workspace_id,
                    "company_id": company_id,
                    "strategy_id": strategy_id,
                    "pillar_id": item.get("pillar_id"),
                    "subtopic_id": item.get("subtopic_id"),
                    "angle_id": item.get("angle_id"),
                    "format_variant_id": item.get("format_variant_id"),
                    "campaign_id": item.get("campaign_id"),
                    "post_id": item.get("post_id"),
                    "schedule_id": item.get("schedule_id"),
                    "title": item["title"],
                    "brief": item.get("brief", ""),
                    "platform": item.get("platform", "facebook"),
                    "content_type": item.get("content_type"),
                    "planned_date": item.get("planned_date"),
                    "scheduled_at": item.get("scheduled_at"),
                    "status": item.get("status", "draft"),
                    "approval_status": item.get("approval_status") or (item.get("metadata") or {}).get("approval_status"),
                    "publishing_status": item.get("publishing_status") or (item.get("metadata") or {}).get("publishing_status"),
                    "metadata": dumps_json(item.get("metadata") or {}),
                    "sort_order": item.get("sort_order", index),
                    "created_by": item.get("created_by", created_by),
                    "updated_by": item.get("created_by", created_by),
                    "created_at": now,
                    "updated_at": now,
                }
                ContentStrategyRepository._validate_calendar_refs(conn, workspace_id, company_id, strategy_id, values)
                ids.append(ContentStrategyRepository._insert(cur, "content_calendar_items", values))
        return ids

    @staticmethod
    def _validate_calendar_refs(conn, workspace_id: int, company_id: int, strategy_id: int, values: dict):
        if values.get("pillar_id"):
            ContentStrategyRepository._require_pillar(conn, workspace_id, company_id, strategy_id, values["pillar_id"])
        if values.get("subtopic_id"):
            ContentStrategyRepository._require_subtopic(conn, workspace_id, company_id, strategy_id, values["subtopic_id"])
        checks = [
            ("content_angles", "angle_id"),
            ("content_format_variants", "format_variant_id"),
        ]
        cur = conn.cursor()
        for table, field in checks:
            if values.get(field):
                cur.execute(
                    _adapt_sql(f"SELECT 1 FROM {table} WHERE id=? AND strategy_id=? AND workspace_id=? AND company_id=?"),
                    (values[field], strategy_id, workspace_id, company_id),
                )
                if not cur.fetchone():
                    raise ValueError(f"Invalid {field} for this strategy")

    @staticmethod
    def list_calendar_items(workspace_id: int, company_id: int, strategy_id: int, status: str = None) -> list:
        conn = get_db_connection()
        try:
            ContentStrategyRepository._require_strategy(conn, workspace_id, company_id, strategy_id)
            query = """SELECT * FROM content_calendar_items
                       WHERE workspace_id=? AND company_id=? AND strategy_id=? AND deleted_at IS NULL"""
            params = [workspace_id, company_id, strategy_id]
            if status:
                query += " AND status=?"
                params.append(status)
            query += " ORDER BY planned_date ASC, sort_order ASC, id ASC"
            cur = conn.cursor()
            cur.execute(_adapt_sql(query), params)
            return rows_to_dicts(cur.fetchall())
        finally:
            conn.close()

    @staticmethod
    def update_calendar_item(workspace_id: int, company_id: int, strategy_id: int, calendar_item_id: int, **kwargs) -> bool:
        allowed = {
            "pillar_id",
            "subtopic_id",
            "angle_id",
            "format_variant_id",
            "campaign_id",
            "post_id",
            "schedule_id",
            "title",
            "brief",
            "platform",
            "content_type",
            "planned_date",
            "scheduled_at",
            "status",
            "approval_status",
            "publishing_status",
            "metadata",
            "sort_order",
            "updated_by",
        }
        values = {key: kwargs[key] for key in allowed if key in kwargs}
        if "metadata" in values:
            values["metadata"] = dumps_json(values["metadata"])
        values["updated_at"] = now_iso()
        with managed_connection() as conn:
            ContentStrategyRepository._require_strategy(conn, workspace_id, company_id, strategy_id)
            merged = dict(values, strategy_id=strategy_id)
            ContentStrategyRepository._validate_calendar_refs(conn, workspace_id, company_id, strategy_id, merged)
            cur = conn.cursor()
            return ContentStrategyRepository._update(
                cur,
                "content_calendar_items",
                calendar_item_id,
                values,
                "strategy_id=? AND workspace_id=? AND company_id=? AND deleted_at IS NULL",
                (strategy_id, workspace_id, company_id),
            )

    @staticmethod
    def delete_calendar_item(workspace_id: int, company_id: int, strategy_id: int, calendar_item_id: int, updated_by: int = None) -> bool:
        with managed_connection() as conn:
            ContentStrategyRepository._require_strategy(conn, workspace_id, company_id, strategy_id)
            cur = conn.cursor()
            cur.execute(
                _adapt_sql(
                    """UPDATE content_calendar_items
                       SET deleted_at=?, updated_at=?, updated_by=?
                       WHERE id=? AND strategy_id=? AND workspace_id=? AND company_id=? AND deleted_at IS NULL"""
                ),
                (now_iso(), now_iso(), updated_by, calendar_item_id, strategy_id, workspace_id, company_id),
            )
            return cur.rowcount > 0


    @staticmethod
    def _require_calendar_item(conn, workspace_id: int, company_id: int, strategy_id: int, calendar_item_id: int) -> dict:
        cur = conn.cursor()
        cur.execute(
            _adapt_sql(
                """SELECT * FROM content_calendar_items
                   WHERE id=? AND strategy_id=? AND workspace_id=? AND company_id=? AND deleted_at IS NULL"""
            ),
            (calendar_item_id, strategy_id, workspace_id, company_id),
        )
        row = cur.fetchone()
        if not row:
            raise ValueError("Calendar item not found for this strategy")
        return row_to_dict(row)

    @staticmethod
    def _require_campaign(conn, workspace_id: int, company_id: int, campaign_id: int) -> dict:
        cur = conn.cursor()
        cur.execute(
            _adapt_sql(
                """SELECT * FROM campaigns
                   WHERE id=? AND workspace_id=? AND (company_id=? OR company_id IS NULL)"""
            ),
            (campaign_id, workspace_id, company_id),
        )
        row = cur.fetchone()
        if not row:
            raise ValueError("Campaign not found for this workspace/company")
        return row_to_dict(row)

    @staticmethod
    def _require_lead_magnet(conn, workspace_id: int, company_id: int, strategy_id: int, lead_magnet_id: int) -> dict:
        cur = conn.cursor()
        cur.execute(
            _adapt_sql(
                """SELECT * FROM lead_magnets
                   WHERE id=? AND strategy_id=? AND workspace_id=? AND company_id=? AND deleted_at IS NULL"""
            ),
            (lead_magnet_id, strategy_id, workspace_id, company_id),
        )
        row = cur.fetchone()
        if not row:
            raise ValueError("Lead magnet not found for this strategy")
        return row_to_dict(row)

    @staticmethod
    def create_campaign(workspace_id: int, company_id: int, name: str, **kwargs) -> int:
        now = now_iso()
        with managed_connection() as conn:
            if not ContentStrategyRepository._company_belongs_to_workspace(conn, workspace_id, company_id):
                raise ValueError("Company does not belong to workspace")
            cur = conn.cursor()
            values = {
                "project_id": kwargs.get("project_id"),
                "workspace_id": workspace_id,
                "company_id": company_id,
                "name": (name or "Untitled Campaign").strip(),
                "objective": kwargs.get("objective", ""),
                "platforms": dumps_json(kwargs.get("platforms") or []),
                "target_audience": kwargs.get("target_audience", ""),
                "target_personas": dumps_json(kwargs.get("target_personas") or []),
                "business_goals": dumps_json(kwargs.get("business_goals") or []),
                "pillars": dumps_json(kwargs.get("pillars") or []),
                "key_message": kwargs.get("key_message", ""),
                "offer": kwargs.get("offer", ""),
                "cta": kwargs.get("cta", ""),
                "budget": kwargs.get("budget", 0),
                "owner": kwargs.get("owner", ""),
                "kpi": kwargs.get("kpi", ""),
                "start_date": kwargs.get("start_date", ""),
                "end_date": kwargs.get("end_date", ""),
                "status": kwargs.get("status", "draft"),
                "metadata": dumps_json(kwargs.get("metadata") or {}),
                "is_template": 1 if kwargs.get("is_template") else 0,
                "template_name": kwargs.get("template_name", ""),
                "created_by": kwargs.get("created_by"),
                "created_at": now,
                "updated_at": now,
            }
            campaign_id = ContentStrategyRepository._insert(cur, "campaigns", values)
            ContentStrategyRepository._audit(cur, "CREATE_CONTENT_STRATEGY_CAMPAIGN", workspace_id, kwargs.get("created_by"), "campaign", campaign_id, "Created Content Strategy campaign.", {"company_id": company_id, "status": values.get("status")})
            return campaign_id

    @staticmethod
    def create_campaign_from_calendar_items(workspace_id: int, company_id: int, strategy_id: int, calendar_item_ids: list, name: str, **kwargs) -> int:
        with managed_connection() as conn:
            ContentStrategyRepository._require_strategy(conn, workspace_id, company_id, strategy_id)
            items = [ContentStrategyRepository._require_calendar_item(conn, workspace_id, company_id, strategy_id, item_id) for item_id in (calendar_item_ids or [])]
            if not items:
                raise ValueError("At least one calendar item is required")
            cur = conn.cursor()
            values = {
                "project_id": kwargs.get("project_id"),
                "workspace_id": workspace_id,
                "company_id": company_id,
                "name": (name or "Calendar Campaign").strip(),
                "objective": kwargs.get("objective", ""),
                "platforms": dumps_json(kwargs.get("platforms") or sorted({item.get("platform") for item in items if item.get("platform")})),
                "target_audience": kwargs.get("target_audience", ""),
                "target_personas": dumps_json(kwargs.get("target_personas") or []),
                "business_goals": dumps_json(kwargs.get("business_goals") or []),
                "pillars": dumps_json(kwargs.get("pillars") or []),
                "key_message": kwargs.get("key_message", ""),
                "offer": kwargs.get("offer", ""),
                "cta": kwargs.get("cta", ""),
                "budget": kwargs.get("budget", 0),
                "owner": kwargs.get("owner", ""),
                "kpi": kwargs.get("kpi", ""),
                "start_date": kwargs.get("start_date") or min([item.get("planned_date") for item in items if item.get("planned_date")] or [""]),
                "end_date": kwargs.get("end_date") or max([item.get("planned_date") for item in items if item.get("planned_date")] or [""]),
                "status": kwargs.get("status", "draft"),
                "metadata": dumps_json({"source": "calendar_items", "calendar_item_ids": calendar_item_ids, **(kwargs.get("metadata") or {})}),
                "is_template": 0,
                "template_name": "",
                "created_by": kwargs.get("created_by"),
                "created_at": now_iso(),
                "updated_at": now_iso(),
            }
            campaign_id = ContentStrategyRepository._insert(cur, "campaigns", values)
            now = now_iso()
            for item_id in calendar_item_ids:
                cur.execute(
                    _adapt_sql(
                        """UPDATE content_calendar_items
                           SET campaign_id=?, updated_by=?, updated_at=?
                           WHERE id=? AND strategy_id=? AND workspace_id=? AND company_id=? AND deleted_at IS NULL"""
                    ),
                    (campaign_id, kwargs.get("created_by"), now, item_id, strategy_id, workspace_id, company_id),
                )
            ContentStrategyRepository._audit(cur, "CREATE_CAMPAIGN_FROM_CALENDAR_ITEMS", workspace_id, kwargs.get("created_by"), "campaign", campaign_id, "Created campaign from Content Calendar items.", {"company_id": company_id, "strategy_id": strategy_id, "calendar_item_count": len(calendar_item_ids or [])})
            return campaign_id

    @staticmethod
    def list_campaigns(workspace_id: int, company_id: int, status: str = None, templates_only: bool = False) -> list:
        conn = get_db_connection()
        try:
            if not ContentStrategyRepository._company_belongs_to_workspace(conn, workspace_id, company_id):
                raise ValueError("Company does not belong to workspace")
            query = "SELECT * FROM campaigns WHERE workspace_id=? AND (company_id=? OR company_id IS NULL)"
            params = [workspace_id, company_id]
            if status:
                query += " AND status=?"
                params.append(status)
            if templates_only:
                query += " AND is_template=1"
            query += " ORDER BY created_at DESC, id DESC"
            cur = conn.cursor()
            cur.execute(_adapt_sql(query), params)
            return rows_to_dicts(cur.fetchall())
        finally:
            conn.close()

    @staticmethod
    def update_campaign(workspace_id: int, company_id: int, campaign_id: int, **kwargs) -> bool:
        allowed = {"name", "objective", "platforms", "target_audience", "target_personas", "business_goals", "pillars", "key_message", "offer", "cta", "budget", "owner", "kpi", "start_date", "end_date", "status", "metadata", "is_template", "template_name"}
        values = {key: kwargs[key] for key in allowed if key in kwargs}
        for field in {"platforms", "target_personas", "business_goals", "pillars", "metadata"} & set(values):
            values[field] = dumps_json(values[field])
        if "is_template" in values:
            values["is_template"] = 1 if values["is_template"] else 0
        values["updated_at"] = now_iso()
        with managed_connection() as conn:
            ContentStrategyRepository._require_campaign(conn, workspace_id, company_id, campaign_id)
            cur = conn.cursor()
            ok = ContentStrategyRepository._update(cur, "campaigns", campaign_id, values, "workspace_id=? AND (company_id=? OR company_id IS NULL)", (workspace_id, company_id))
            if ok:
                ContentStrategyRepository._audit(cur, "UPDATE_CONTENT_STRATEGY_CAMPAIGN", workspace_id, kwargs.get("updated_by"), "campaign", campaign_id, "Updated Content Strategy campaign.", {"company_id": company_id, "fields": sorted(values.keys())})
            return ok

    @staticmethod
    def duplicate_campaign(workspace_id: int, company_id: int, campaign_id: int, created_by: int = None) -> int:
        with managed_connection() as conn:
            campaign = ContentStrategyRepository._require_campaign(conn, workspace_id, company_id, campaign_id)
            now = now_iso()
            values = {key: campaign.get(key) for key in ["project_id", "workspace_id", "company_id", "objective", "platforms", "target_audience", "target_personas", "business_goals", "pillars", "key_message", "offer", "cta", "budget", "owner", "kpi", "start_date", "end_date", "metadata", "is_template", "template_name"]}
            values.update({"name": f"{campaign.get('name') or 'Campaign'} Copy {datetime.now().strftime('%Y%m%d%H%M%S')}", "status": "draft", "created_by": created_by, "created_at": now, "updated_at": now})
            for field in ["platforms", "target_personas", "business_goals", "pillars", "metadata"]:
                values[field] = dumps_json(values.get(field) or ([] if field != "metadata" else {}))
            cur = conn.cursor()
            new_id = ContentStrategyRepository._insert(cur, "campaigns", values)
            ContentStrategyRepository._audit(cur, "DUPLICATE_CONTENT_STRATEGY_CAMPAIGN", workspace_id, created_by, "campaign", new_id, "Duplicated Content Strategy campaign.", {"company_id": company_id, "source_campaign_id": campaign_id})
            return new_id

    @staticmethod
    def link_calendar_items_to_campaign(workspace_id: int, company_id: int, strategy_id: int, campaign_id: int, calendar_item_ids: list, updated_by: int = None) -> int:
        with managed_connection() as conn:
            ContentStrategyRepository._require_campaign(conn, workspace_id, company_id, campaign_id)
            for item_id in calendar_item_ids or []:
                ContentStrategyRepository._require_calendar_item(conn, workspace_id, company_id, strategy_id, item_id)
            cur = conn.cursor()
            count = 0
            now = now_iso()
            for item_id in calendar_item_ids or []:
                cur.execute(_adapt_sql("""UPDATE content_calendar_items SET campaign_id=?, updated_by=?, updated_at=? WHERE id=? AND strategy_id=? AND workspace_id=? AND company_id=? AND deleted_at IS NULL"""), (campaign_id, updated_by, now, item_id, strategy_id, workspace_id, company_id))
                count += cur.rowcount
            ContentStrategyRepository._audit(cur, "LINK_CALENDAR_ITEMS_TO_CAMPAIGN", workspace_id, updated_by, "campaign", campaign_id, "Linked Content Calendar items to campaign.", {"company_id": company_id, "strategy_id": strategy_id, "count": count})
            return count

    @staticmethod
    def unlink_calendar_items_from_campaign(workspace_id: int, company_id: int, strategy_id: int, calendar_item_ids: list, updated_by: int = None) -> int:
        with managed_connection() as conn:
            for item_id in calendar_item_ids or []:
                ContentStrategyRepository._require_calendar_item(conn, workspace_id, company_id, strategy_id, item_id)
            cur = conn.cursor()
            count = 0
            now = now_iso()
            for item_id in calendar_item_ids or []:
                cur.execute(_adapt_sql("""UPDATE content_calendar_items SET campaign_id=NULL, updated_by=?, updated_at=? WHERE id=? AND strategy_id=? AND workspace_id=? AND company_id=? AND deleted_at IS NULL"""), (updated_by, now, item_id, strategy_id, workspace_id, company_id))
                count += cur.rowcount
            ContentStrategyRepository._audit(cur, "UNLINK_CALENDAR_ITEMS_FROM_CAMPAIGN", workspace_id, updated_by, "content_calendar_item", strategy_id, "Unlinked Content Calendar items from campaign.", {"company_id": company_id, "strategy_id": strategy_id, "count": count})
            return count

    @staticmethod
    def create_lead_magnet(workspace_id: int, company_id: int, strategy_id: int, name: str, **kwargs) -> int:
        now = now_iso()
        with managed_connection() as conn:
            ContentStrategyRepository._require_strategy(conn, workspace_id, company_id, strategy_id)
            if kwargs.get("campaign_id"):
                ContentStrategyRepository._require_campaign(conn, workspace_id, company_id, kwargs["campaign_id"])
            values = {
                "workspace_id": workspace_id,
                "company_id": company_id,
                "strategy_id": strategy_id,
                "pillar_id": kwargs.get("pillar_id"),
                "name": (name or "Untitled Lead Magnet").strip(),
                "description": kwargs.get("description", ""),
                "asset_type": kwargs.get("asset_type") or kwargs.get("type") or "Checklist",
                "type": kwargs.get("type") or kwargs.get("asset_type") or "Checklist",
                "offer_url": kwargs.get("offer_url") or kwargs.get("destination_url", ""),
                "target_persona": kwargs.get("target_persona", ""),
                "pain_point": kwargs.get("pain_point", ""),
                "value_proposition": kwargs.get("value_proposition", ""),
                "cta": kwargs.get("cta", ""),
                "destination_url": kwargs.get("destination_url") or kwargs.get("offer_url", ""),
                "campaign_id": kwargs.get("campaign_id"),
                "funnel_stage": kwargs.get("funnel_stage", "awareness"),
                "asset_reference": kwargs.get("asset_reference", ""),
                "status": kwargs.get("status") or ("draft" if kwargs.get("asset_reference") else "planned"),
                "metadata": dumps_json(kwargs.get("metadata") or {}),
                "sort_order": kwargs.get("sort_order", 0),
                "created_by": kwargs.get("created_by"),
                "updated_by": kwargs.get("created_by"),
                "created_at": now,
                "updated_at": now,
            }
            if values["status"] == "published":
                values["status"] = "planned"
            cur = conn.cursor()
            lead_magnet_id = ContentStrategyRepository._insert(cur, "lead_magnets", values)
            ContentStrategyRepository._audit(cur, "CREATE_LEAD_MAGNET", workspace_id, kwargs.get("created_by"), "lead_magnet", lead_magnet_id, "Created Content Strategy lead magnet.", {"company_id": company_id, "strategy_id": strategy_id, "status": values.get("status")})
            return lead_magnet_id

    @staticmethod
    def list_lead_magnets(workspace_id: int, company_id: int, strategy_id: int = None, campaign_id: int = None) -> list:
        conn = get_db_connection()
        try:
            query = "SELECT * FROM lead_magnets WHERE workspace_id=? AND company_id=? AND deleted_at IS NULL"
            params = [workspace_id, company_id]
            if strategy_id:
                ContentStrategyRepository._require_strategy(conn, workspace_id, company_id, strategy_id)
                query += " AND strategy_id=?"
                params.append(strategy_id)
            if campaign_id:
                ContentStrategyRepository._require_campaign(conn, workspace_id, company_id, campaign_id)
                query += " AND campaign_id=?"
                params.append(campaign_id)
            query += " ORDER BY sort_order ASC, id ASC"
            cur = conn.cursor()
            cur.execute(_adapt_sql(query), params)
            return rows_to_dicts(cur.fetchall())
        finally:
            conn.close()

    @staticmethod
    def link_lead_magnet_to_calendar_items(workspace_id: int, company_id: int, strategy_id: int, lead_magnet_id: int, calendar_item_ids: list, created_by: int = None) -> int:
        with managed_connection() as conn:
            ContentStrategyRepository._require_lead_magnet(conn, workspace_id, company_id, strategy_id, lead_magnet_id)
            cur = conn.cursor()
            count = 0
            for item_id in calendar_item_ids or []:
                ContentStrategyRepository._require_calendar_item(conn, workspace_id, company_id, strategy_id, item_id)
                values = {"workspace_id": workspace_id, "company_id": company_id, "strategy_id": strategy_id, "lead_magnet_id": lead_magnet_id, "calendar_item_id": item_id, "created_by": created_by, "created_at": now_iso()}
                try:
                    ContentStrategyRepository._insert(cur, "lead_magnet_calendar_items", values)
                    count += 1
                except Exception as exc:
                    if "UNIQUE" not in str(exc).upper() and "unique" not in str(exc):
                        raise
            ContentStrategyRepository._audit(cur, "LINK_LEAD_MAGNET_TO_CALENDAR_ITEMS", workspace_id, created_by, "lead_magnet", lead_magnet_id, "Linked lead magnet to Content Calendar items.", {"company_id": company_id, "strategy_id": strategy_id, "count": count})
            return count

    @staticmethod
    def list_lead_magnet_calendar_links(workspace_id: int, company_id: int, strategy_id: int, lead_magnet_id: int = None) -> list:
        conn = get_db_connection()
        try:
            ContentStrategyRepository._require_strategy(conn, workspace_id, company_id, strategy_id)
            query = "SELECT * FROM lead_magnet_calendar_items WHERE workspace_id=? AND company_id=? AND strategy_id=?"
            params = [workspace_id, company_id, strategy_id]
            if lead_magnet_id:
                query += " AND lead_magnet_id=?"
                params.append(lead_magnet_id)
            query += " ORDER BY id ASC"
            cur = conn.cursor()
            cur.execute(_adapt_sql(query), params)
            return rows_to_dicts(cur.fetchall())
        finally:
            conn.close()

    @staticmethod
    def create_kpi(workspace_id: int, company_id: int, strategy_id: int, metric_name: str, **kwargs) -> int:
        scope_level = kwargs.get("scope_level") or "strategy"
        if scope_level not in {"strategy", "campaign", "calendar_item", "platform"}:
            raise ValueError("Unsupported KPI scope level")
        now = now_iso()
        with managed_connection() as conn:
            ContentStrategyRepository._require_strategy(conn, workspace_id, company_id, strategy_id)
            calendar_item_id = kwargs.get("calendar_item_id")
            if calendar_item_id:
                ContentStrategyRepository._require_calendar_item(conn, workspace_id, company_id, strategy_id, calendar_item_id)
            campaign_id = kwargs.get("campaign_id")
            if campaign_id:
                ContentStrategyRepository._require_campaign(conn, workspace_id, company_id, campaign_id)
            values = {
                "workspace_id": workspace_id,
                "company_id": company_id,
                "strategy_id": strategy_id,
                "calendar_item_id": calendar_item_id,
                "campaign_id": campaign_id,
                "scope_level": scope_level,
                "platform": kwargs.get("platform"),
                "metric_name": metric_name,
                "baseline_value": kwargs.get("baseline"),
                "target_value": kwargs.get("target"),
                "actual_value": kwargs.get("actual_value"),
                "unit": kwargs.get("unit"),
                "period": kwargs.get("period"),
                "data_source": kwargs.get("data_source"),
                "owner": kwargs.get("owner"),
                "status": kwargs.get("status", "tracking"),
                "metadata": dumps_json(kwargs.get("metadata") or {}),
                "sort_order": kwargs.get("sort_order", 0),
                "created_by": kwargs.get("created_by"),
                "updated_by": kwargs.get("created_by"),
                "created_at": now,
                "updated_at": now,
            }
            cur = conn.cursor()
            return ContentStrategyRepository._insert(cur, "content_strategy_kpis", values)

    @staticmethod
    def list_kpis(workspace_id: int, company_id: int, strategy_id: int, scope_level: str = None) -> list:
        conn = get_db_connection()
        try:
            ContentStrategyRepository._require_strategy(conn, workspace_id, company_id, strategy_id)
            query = """SELECT * FROM content_strategy_kpis
                       WHERE workspace_id=? AND company_id=? AND strategy_id=? AND deleted_at IS NULL"""
            params = [workspace_id, company_id, strategy_id]
            if scope_level:
                query += " AND scope_level=?"
                params.append(scope_level)
            query += " ORDER BY sort_order ASC, id ASC"
            cur = conn.cursor()
            cur.execute(_adapt_sql(query), params)
            return rows_to_dicts(cur.fetchall())
        finally:
            conn.close()

    @staticmethod
    def update_kpi(workspace_id: int, company_id: int, strategy_id: int, kpi_id: int, **kwargs) -> bool:
        allowed = {"calendar_item_id", "campaign_id", "scope_level", "platform", "metric_name", "baseline_value", "target_value", "actual_value", "unit", "period", "data_source", "owner", "status", "metadata", "sort_order", "updated_by"}
        values = {key: kwargs[key] for key in allowed if key in kwargs}
        if "baseline" in kwargs:
            values["baseline_value"] = kwargs["baseline"]
        if "target" in kwargs:
            values["target_value"] = kwargs["target"]
        if "metadata" in values:
            values["metadata"] = dumps_json(values["metadata"])
        values["updated_at"] = now_iso()
        with managed_connection() as conn:
            ContentStrategyRepository._require_strategy(conn, workspace_id, company_id, strategy_id)
            if values.get("calendar_item_id"):
                ContentStrategyRepository._require_calendar_item(conn, workspace_id, company_id, strategy_id, values["calendar_item_id"])
            if values.get("campaign_id"):
                ContentStrategyRepository._require_campaign(conn, workspace_id, company_id, values["campaign_id"])
            cur = conn.cursor()
            return ContentStrategyRepository._update(cur, "content_strategy_kpis", kpi_id, values, "strategy_id=? AND workspace_id=? AND company_id=? AND deleted_at IS NULL", (strategy_id, workspace_id, company_id))

    @staticmethod
    def create_strategy_version(workspace_id: int, company_id: int, strategy_id: int, notes: str = "", created_by: int = None) -> int:
        with managed_connection() as conn:
            ContentStrategyRepository._require_strategy(conn, workspace_id, company_id, strategy_id)
            snapshot = ContentStrategyRepository._snapshot_strategy(conn, workspace_id, company_id, strategy_id)
            cur = conn.cursor()
            cur.execute(
                _adapt_sql("SELECT COALESCE(MAX(version), 0) + 1 FROM content_strategy_versions WHERE strategy_id=?"),
                (strategy_id,),
            )
            version = cur.fetchone()[0]
            values = {
                "workspace_id": workspace_id,
                "company_id": company_id,
                "strategy_id": strategy_id,
                "version": version,
                "snapshot": dumps_json(snapshot),
                "notes": notes,
                "created_by": created_by,
                "created_at": now_iso(),
            }
            version_id = ContentStrategyRepository._insert(cur, "content_strategy_versions", values)
            cur.execute(
                _adapt_sql("UPDATE content_strategies SET version=?, updated_at=?, updated_by=? WHERE id=?"),
                (version, now_iso(), created_by, strategy_id),
            )
            return version_id

    @staticmethod
    @staticmethod
    def list_strategy_versions(workspace_id: int, company_id: int, strategy_id: int) -> list:
        conn = get_db_connection()
        try:
            ContentStrategyRepository._require_strategy(conn, workspace_id, company_id, strategy_id)
            cur = conn.cursor()
            cur.execute(
                _adapt_sql(
                    """SELECT id, strategy_id, version, notes, created_by, created_at
                       FROM content_strategy_versions
                       WHERE workspace_id=? AND company_id=? AND strategy_id=?
                       ORDER BY version DESC, id DESC"""
                ),
                (workspace_id, company_id, strategy_id),
            )
            return rows_to_dicts(cur.fetchall())
        finally:
            conn.close()
    def restore_strategy_version(workspace_id: int, company_id: int, strategy_id: int, version_id: int, updated_by: int = None) -> bool:
        with managed_connection() as conn:
            ContentStrategyRepository._require_strategy(conn, workspace_id, company_id, strategy_id)
            cur = conn.cursor()
            cur.execute(
                _adapt_sql(
                    """SELECT * FROM content_strategy_versions
                       WHERE id=? AND strategy_id=? AND workspace_id=? AND company_id=?"""
                ),
                (version_id, strategy_id, workspace_id, company_id),
            )
            version_row = row_to_dict(cur.fetchone())
            if not version_row:
                raise ValueError("Strategy version not found for this workspace/company")
            snapshot = version_row["snapshot"]
            root = snapshot.get("strategy", {})
            update_values = {
                "name": root.get("name"),
                "description": root.get("description"),
                "strategy_type": root.get("strategy_type"),
                "status": root.get("status", "draft"),
                "start_date": root.get("start_date"),
                "end_date": root.get("end_date"),
                "metadata": dumps_json(root.get("metadata") or {}),
                "version": version_row["version"],
                "updated_by": updated_by,
                "updated_at": now_iso(),
            }
            update_values = {k: v for k, v in update_values.items() if v is not None}
            set_clause = ", ".join([f"{key}=?" for key in update_values])
            cur.execute(
                _adapt_sql(f"UPDATE content_strategies SET {set_clause} WHERE id=? AND workspace_id=? AND company_id=?"),
                (*update_values.values(), strategy_id, workspace_id, company_id),
            )
            ContentStrategyRepository._replace_children_from_snapshot(cur, workspace_id, company_id, strategy_id, snapshot, updated_by)
            return True

    @staticmethod
    def _load_children(conn, workspace_id: int, company_id: int, strategy_id: int) -> dict:
        child_tables = {
            "personas": "audience_personas",
            "goals": "business_goals",
            "pillars": "content_pillars",
            "subtopics": "content_subtopics",
            "angles": "content_angles",
            "format_variants": "content_format_variants",
            "calendar_items": "content_calendar_items",
            "kpis": "content_strategy_kpis",
            "lead_magnets": "lead_magnets",
            "generation_jobs": "content_generation_jobs",
            "lead_magnet_calendar_items": "lead_magnet_calendar_items",
        }
        children = {}
        cur = conn.cursor()
        for key, table in child_tables.items():
            order_by = "id ASC" if table == "lead_magnet_calendar_items" else "sort_order ASC, id ASC"
            deleted_filter = "" if table == "lead_magnet_calendar_items" else " AND deleted_at IS NULL"
            cur.execute(
                _adapt_sql(
                    f"""SELECT * FROM {table}
                        WHERE workspace_id=? AND company_id=? AND strategy_id=?{deleted_filter}
                        ORDER BY {order_by}"""
                ),
                (workspace_id, company_id, strategy_id),
            )
            children[key] = rows_to_dicts(cur.fetchall())
        return children

    @staticmethod
    def _snapshot_strategy(conn, workspace_id: int, company_id: int, strategy_id: int) -> dict:
        strategy = row_to_dict(ContentStrategyRepository._get_strategy_row(conn, workspace_id, company_id, strategy_id))
        return {
            "strategy": strategy,
            **ContentStrategyRepository._load_children(conn, workspace_id, company_id, strategy_id),
            "snapshot_created_at": datetime.now().isoformat(),
        }

    @staticmethod
    def _replace_children_from_snapshot(cur, workspace_id: int, company_id: int, strategy_id: int, snapshot: dict, actor_id: int = None):
        for table in [
            "lead_magnet_calendar_items",
            "content_generation_jobs",
            "content_strategy_kpis",
            "content_calendar_items",
            "content_format_variants",
            "content_angles",
            "content_subtopics",
            "content_pillars",
            "lead_magnets",
            "business_goals",
            "audience_personas",
        ]:
            cur.execute(
                _adapt_sql(f"DELETE FROM {table} WHERE workspace_id=? AND company_id=? AND strategy_id=?"),
                (workspace_id, company_id, strategy_id),
            )
        mapping = {
            "personas": "audience_personas",
            "goals": "business_goals",
            "pillars": "content_pillars",
            "subtopics": "content_subtopics",
            "angles": "content_angles",
            "format_variants": "content_format_variants",
            "calendar_items": "content_calendar_items",
            "kpis": "content_strategy_kpis",
            "lead_magnets": "lead_magnets",
            "generation_jobs": "content_generation_jobs",
            "lead_magnet_calendar_items": "lead_magnet_calendar_items",
        }
        json_fields = {"metadata", "pain_points", "goals", "preferred_channels", "specs", "request_metadata", "validation_errors", "target_personas", "business_goals", "pillars", "suggested_channels"}
        for key, table in mapping.items():
            for item in snapshot.get(key, []):
                values = dict(item)
                values["workspace_id"] = workspace_id
                values["company_id"] = company_id
                values["strategy_id"] = strategy_id
                if table != "lead_magnet_calendar_items":
                    values["updated_by"] = actor_id
                    values["updated_at"] = now_iso()
                for field in json_fields:
                    if field in values:
                        values[field] = dumps_json(values[field])
                ContentStrategyRepository._insert_preserving_id(cur, table, values)

















