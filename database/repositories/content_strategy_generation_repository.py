"""Atomic persistence for AI-generated content strategy payloads."""

from database.connection import managed_connection, _adapt_sql, _is_postgres
from database.models.content_strategy import dumps_json, now_iso, slugify
from database.repositories.content_strategy_repository import ContentStrategyRepository


class ContentStrategyGenerationRepository:
    @staticmethod
    def _last_id(cur):
        if _is_postgres():
            cur.execute("SELECT lastval()")
            return cur.fetchone()[0]
        return cur.lastrowid

    @staticmethod
    def _insert(cur, table: str, values: dict) -> int:
        columns = ", ".join(values.keys())
        placeholders = ", ".join(["?"] * len(values))
        cur.execute(
            _adapt_sql(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"),
            tuple(values.values()),
        )
        return ContentStrategyGenerationRepository._last_id(cur)

    @staticmethod
    def create_strategy_with_sections(workspace_id: int, company_id: int, payload: dict, created_by: int = None) -> int:
        """Create root strategy and generated children in one transaction."""
        summary = payload.get("strategy_summary") or {}
        now = now_iso()
        with managed_connection() as conn:
            if not ContentStrategyRepository._company_belongs_to_workspace(conn, workspace_id, company_id):
                raise ValueError("Company does not belong to workspace")
            cur = conn.cursor()
            strategy_id = ContentStrategyGenerationRepository._insert(cur, "content_strategies", {
                "workspace_id": workspace_id,
                "company_id": company_id,
                "campaign_id": payload.get("campaign_id"),
                "project_id": payload.get("project_id"),
                "name": summary.get("name") or "AI Content Strategy",
                "description": summary.get("description", ""),
                "strategy_type": "content",
                "status": "generated",
                "start_date": payload.get("start_date"),
                "end_date": payload.get("end_date"),
                "metadata": dumps_json({
                    "schema_version": payload.get("schema_version"),
                    "task": payload.get("task"),
                    "campaign_theme": summary.get("campaign_theme", ""),
                    "source": "ai_content_strategy_service",
                }),
                "sort_order": 0,
                "created_by": created_by,
                "updated_by": created_by,
                "created_at": now,
                "updated_at": now,
            })
            ContentStrategyGenerationRepository._insert_children(cur, workspace_id, company_id, strategy_id, payload, created_by)
            return strategy_id

    @staticmethod
    def replace_sections(workspace_id: int, company_id: int, strategy_id: int, payload: dict, sections: list, updated_by: int = None) -> bool:
        """Replace selected generated sections while preserving unrelated sections."""
        table_groups = {
            "business_goals": ["business_goals"],
            "kpis": ["content_strategy_kpis"],
            "lead_magnets": ["lead_magnets"],
            "pillars": [
                "content_strategy_kpis",
                "content_calendar_items",
                "content_format_variants",
                "content_angles",
                "content_subtopics",
                "content_pillars",
                "lead_magnets",
            ],
            "subtopics": ["content_calendar_items", "content_format_variants", "content_angles", "content_subtopics"],
            "content_angles": ["content_calendar_items", "content_format_variants", "content_angles"],
            "content_formats": ["content_format_variants"],
            "content_calendar": ["content_calendar_items"],
        }
        tables = []
        for section in sections:
            for table in table_groups.get(section, []):
                if table not in tables:
                    tables.append(table)

        with managed_connection() as conn:
            ContentStrategyRepository._require_strategy(conn, workspace_id, company_id, strategy_id)
            cur = conn.cursor()
            for table in tables:
                cur.execute(
                    _adapt_sql(f"DELETE FROM {table} WHERE workspace_id=? AND company_id=? AND strategy_id=?"),
                    (workspace_id, company_id, strategy_id),
                )
            existing_refs = ContentStrategyGenerationRepository._load_reference_maps(
                cur, workspace_id, company_id, strategy_id
            )
            ContentStrategyGenerationRepository._insert_children(
                cur,
                workspace_id,
                company_id,
                strategy_id,
                payload,
                updated_by,
                only_sections=set(sections or []),
                existing_refs=existing_refs,
            )
            cur.execute(
                _adapt_sql(
                    """UPDATE content_strategies
                       SET status=?, updated_at=?, updated_by=?
                       WHERE id=? AND workspace_id=? AND company_id=?"""
                ),
                ("generated", now_iso(), updated_by, strategy_id, workspace_id, company_id),
            )
            return True

    @staticmethod
    def create_generation_job(workspace_id: int, company_id: int, strategy_id: int = None, **kwargs) -> int:
        with managed_connection() as conn:
            if strategy_id:
                ContentStrategyRepository._require_strategy(conn, workspace_id, company_id, strategy_id)
            elif not ContentStrategyRepository._company_belongs_to_workspace(conn, workspace_id, company_id):
                raise ValueError("Company does not belong to workspace")
            cur = conn.cursor()
            values = {
                "workspace_id": workspace_id,
                "company_id": company_id,
                "strategy_id": strategy_id,
                "job_type": kwargs.get("job_type", "strategy_generation"),
                "provider": kwargs.get("provider", "gemini"),
                "model_name": kwargs.get("model_name", "gemini-2.5-flash"),
                "status": kwargs.get("status", "queued"),
                "input_summary": kwargs.get("input_summary", ""),
                "output_summary": kwargs.get("output_summary", ""),
                "request_metadata": dumps_json(kwargs.get("request_metadata") or {}),
                "validation_errors": dumps_json(kwargs.get("validation_errors") or []),
                "error_message": kwargs.get("error_message", ""),
                "started_at": kwargs.get("started_at"),
                "completed_at": kwargs.get("completed_at"),
                "sort_order": 0,
                "created_by": kwargs.get("created_by"),
                "updated_by": kwargs.get("created_by"),
                "created_at": now_iso(),
                "updated_at": now_iso(),
            }
            return ContentStrategyGenerationRepository._insert(cur, "content_generation_jobs", values)

    @staticmethod
    def _load_reference_maps(cur, workspace_id: int, company_id: int, strategy_id: int) -> dict:
        refs = {"pillars": {}, "subtopics": {}, "content_angles": {}}
        queries = {
            "pillars": ("content_pillars", "slug"),
            "subtopics": ("content_subtopics", "slug"),
            "content_angles": ("content_angles", "slug"),
        }
        for key, (table, field) in queries.items():
            cur.execute(
                _adapt_sql(
                    f"""SELECT id, {field} FROM {table}
                        WHERE workspace_id=? AND company_id=? AND strategy_id=?"""
                ),
                (workspace_id, company_id, strategy_id),
            )
            for row in cur.fetchall():
                refs[key][row[1]] = row[0]
        return refs

    @staticmethod
    def _insert_children(cur, workspace_id: int, company_id: int, strategy_id: int, payload: dict, created_by: int = None, only_sections=None, existing_refs=None):
        base = {"workspace_id": workspace_id, "company_id": company_id, "strategy_id": strategy_id}
        now = now_iso()
        existing_refs = existing_refs or {}
        pillar_ids = dict(existing_refs.get("pillars") or {})
        subtopic_ids = dict(existing_refs.get("subtopics") or {})
        angle_ids = dict(existing_refs.get("content_angles") or {})
        all_sections = only_sections is None

        def include(section: str) -> bool:
            return all_sections or section in only_sections

        for index, goal in enumerate(payload.get("business_goals") or [] if include("business_goals") else []):
            ContentStrategyGenerationRepository._insert(cur, "business_goals", {
                **base,
                "name": goal["name"],
                "description": goal.get("description", ""),
                "target_metric": goal.get("target_metric", ""),
                "target_value": goal.get("target_value", 0),
                "timeframe": goal.get("timeframe", ""),
                "status": "active",
                "sort_order": index,
                "created_by": created_by,
                "updated_by": created_by,
                "created_at": now,
                "updated_at": now,
            })

        for index, pillar in enumerate(payload.get("pillars") or [] if include("pillars") else []):
            pillar_ids[pillar["key"]] = ContentStrategyGenerationRepository._insert(cur, "content_pillars", {
                **base,
                "name": pillar["name"],
                "slug": slugify(pillar.get("key") or pillar["name"]),
                "description": pillar.get("description", ""),
                "objective": pillar.get("business_goal", ""),
                "status": "active",
                "sort_order": pillar.get("priority", index),
                "created_by": created_by,
                "updated_by": created_by,
                "created_at": now,
                "updated_at": now,
            })

        for index, subtopic in enumerate(payload.get("subtopics") or [] if include("subtopics") or include("pillars") else []):
            pillar_id = pillar_ids.get(subtopic.get("pillar_key"))
            if not pillar_id:
                raise ValueError("Subtopic references missing pillar")
            subtopic_ids[subtopic["key"]] = ContentStrategyGenerationRepository._insert(cur, "content_subtopics", {
                **base,
                "pillar_id": pillar_id,
                "name": subtopic["name"],
                "slug": slugify(subtopic.get("key") or subtopic["name"]),
                "description": subtopic.get("description", ""),
                "status": "active",
                "sort_order": subtopic.get("priority", index),
                "created_by": created_by,
                "updated_by": created_by,
                "created_at": now,
                "updated_at": now,
            })

        for index, angle in enumerate(payload.get("content_angles") or [] if include("content_angles") or include("subtopics") or include("pillars") else []):
            pillar_id = pillar_ids.get(angle.get("pillar_key"))
            if not pillar_id:
                raise ValueError("Angle references missing pillar")
            angle_ids[angle["key"]] = ContentStrategyGenerationRepository._insert(cur, "content_angles", {
                **base,
                "pillar_id": pillar_id,
                "subtopic_id": subtopic_ids.get(angle.get("subtopic_key")),
                "title": angle["title"],
                "slug": slugify(angle.get("key") or angle["title"]),
                "description": angle.get("description", ""),
                "hook": angle.get("hook", ""),
                "cta": angle.get("cta", ""),
                "status": "active",
                "sort_order": index,
                "created_by": created_by,
                "updated_by": created_by,
                "created_at": now,
                "updated_at": now,
            })

        for index, fmt in enumerate(payload.get("content_formats") or [] if include("content_formats") or include("content_angles") or include("subtopics") or include("pillars") else []):
            ContentStrategyGenerationRepository._insert(cur, "content_format_variants", {
                **base,
                "angle_id": angle_ids.get(fmt.get("angle_key")),
                "platform": fmt.get("platform", "facebook"),
                "format_type": fmt["format_type"],
                "name": fmt["name"],
                "description": fmt.get("description", ""),
                "specs": dumps_json(fmt.get("specs") or {}),
                "status": "active",
                "sort_order": index,
                "created_by": created_by,
                "updated_by": created_by,
                "created_at": now,
                "updated_at": now,
            })

        for index, item in enumerate(payload.get("content_calendar") or [] if include("content_calendar") or include("content_formats") or include("content_angles") or include("subtopics") or include("pillars") else []):
            ContentStrategyGenerationRepository._insert(cur, "content_calendar_items", {
                **base,
                "pillar_id": pillar_ids.get(item.get("pillar_key")),
                "subtopic_id": subtopic_ids.get(item.get("subtopic_key")),
                "angle_id": angle_ids.get(item.get("angle_key")),
                "format_variant_id": None,
                "campaign_id": payload.get("campaign_id"),
                "post_id": None,
                "schedule_id": None,
                "title": item["title"],
                "brief": item.get("brief", ""),
                "platform": item.get("platform", "facebook"),
                "content_type": item.get("content_type", ""),
                "planned_date": item.get("planned_date"),
                "scheduled_at": None,
                "status": "draft",
                "metadata": dumps_json({"cta": item.get("cta", "")}),
                "sort_order": index,
                "created_by": created_by,
                "updated_by": created_by,
                "created_at": now,
                "updated_at": now,
            })

        for index, kpi in enumerate(payload.get("kpis") or [] if include("kpis") else []):
            ContentStrategyGenerationRepository._insert(cur, "content_strategy_kpis", {
                **base,
                "calendar_item_id": None,
                "analytics_id": None,
                "metric_name": kpi["metric_name"],
                "target_value": kpi.get("target_value", 0),
                "actual_value": None,
                "unit": kpi.get("unit", ""),
                "status": "tracking",
                "sort_order": index,
                "created_by": created_by,
                "updated_by": created_by,
                "created_at": now,
                "updated_at": now,
            })

        for index, lead in enumerate(payload.get("lead_magnets") or [] if include("lead_magnets") or include("pillars") else []):
            ContentStrategyGenerationRepository._insert(cur, "lead_magnets", {
                **base,
                "pillar_id": pillar_ids.get(lead.get("pillar_key")),
                "name": lead["name"],
                "description": lead.get("description", ""),
                "asset_type": lead.get("asset_type") or lead.get("type", "Checklist"),
                "type": lead.get("type") or lead.get("asset_type", "Checklist"),
                "offer_url": lead.get("destination_url") or lead.get("offer_url", ""),
                "target_persona": lead.get("target_persona", ""),
                "pain_point": lead.get("pain_point", ""),
                "value_proposition": lead.get("value_proposition", ""),
                "cta": lead.get("cta", ""),
                "destination_url": lead.get("destination_url") or lead.get("offer_url", ""),
                "campaign_id": payload.get("campaign_id"),
                "funnel_stage": lead.get("funnel_stage", "awareness"),
                "asset_reference": lead.get("asset_reference", ""),
                "metadata": dumps_json(lead.get("metadata") or {}),
                "status": "planned" if not lead.get("asset_reference") else lead.get("status", "draft"),
                "sort_order": index,
                "created_by": created_by,
                "updated_by": created_by,
                "created_at": now,
                "updated_at": now,
            })


