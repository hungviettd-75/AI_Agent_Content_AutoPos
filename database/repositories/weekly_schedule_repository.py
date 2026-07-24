import pandas as pd
import json
from database.connection import get_db_connection, managed_connection, _adapt_sql

class WeeklyScheduleRepository:
    @staticmethod
    def _require_workspace(workspace_id: int) -> None:
        if workspace_id is None:
            raise ValueError("workspace_id is required")

    @staticmethod
    def add_weekly_schedule(week_start: str, plan_json: str, workspace_id: int = None) -> int:
        WeeklyScheduleRepository._require_workspace(workspace_id)
        sql = _adapt_sql(
            "INSERT INTO weekly_schedules (week_start, plan_json, workspace_id) VALUES (?, ?, ?)"
        )
        with managed_connection() as conn:
            c = conn.cursor()
            c.execute(sql, (week_start, plan_json, workspace_id))
            try:
                from database.connection import _is_postgres
                if _is_postgres():
                    c.execute("SELECT lastval()")
                    return c.fetchone()[0]
            except Exception:
                pass
            return c.lastrowid

    @staticmethod
    def get_latest_weekly_schedule(workspace_id: int = None) -> dict:
        """Lấy kế hoạch tuần mới nhất của workspace này."""
        WeeklyScheduleRepository._require_workspace(workspace_id)
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            sql = _adapt_sql("SELECT plan_json FROM weekly_schedules WHERE workspace_id = ? ORDER BY id DESC LIMIT 1")
            cur.execute(sql, (workspace_id,))
            row = cur.fetchone()
            if row:
                try:
                    return json.loads(row[0])
                except Exception:
                    pass
            return {}
        finally:
            conn.close()
