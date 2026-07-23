"""database/models/campaigns.py — CRUD cho bang campaigns."""
import json
from datetime import datetime
from database.connection import managed_connection, get_db_connection, _adapt_sql, _is_postgres
from config.config import logger


class CampaignModel:

    VALID_STATUS = {"draft", "active", "paused", "completed", "archived"}

    @staticmethod
    def create(workspace_id: int, name: str, project_id: int = None,
               objective: str = "", platforms: list = None,
               target_audience: str = "", budget: float = 0,
               start_date: str = "", end_date: str = "",
               status: str = "draft", created_by: int = None) -> int:
        now = datetime.now().isoformat()
        sql = _adapt_sql("""
            INSERT INTO campaigns (project_id, workspace_id, name, objective, platforms,
                                   target_audience, budget, start_date, end_date, status,
                                   created_by, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """)
        logger.info(f"[AUDIT] Tao campaign: {name} (workspace={workspace_id})")
        with managed_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (
                project_id, workspace_id, name, objective,
                json.dumps(platforms or ["facebook"], ensure_ascii=False),
                target_audience, budget, start_date, end_date, status,
                created_by, now, now
            ))
            if _is_postgres():
                cur.execute("SELECT lastval()")
                return cur.fetchone()[0]
            return cur.lastrowid

    @staticmethod
    def get_by_id(campaign_id: int) -> dict:
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute(_adapt_sql("SELECT * FROM campaigns WHERE id=?"), (campaign_id,))
            row = cur.fetchone()
            if not row:
                return {}
            data = dict(row)
            try:
                data["platforms"] = json.loads(data.get("platforms") or "[]")
            except Exception:
                pass
            return data
        finally:
            conn.close()

    @staticmethod
    def list_by_workspace(workspace_id: int, status: str = None) -> list:
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            if status:
                cur.execute(
                    _adapt_sql("SELECT * FROM campaigns WHERE workspace_id=? AND status=? ORDER BY created_at DESC"),
                    (workspace_id, status)
                )
            else:
                cur.execute(
                    _adapt_sql("SELECT * FROM campaigns WHERE workspace_id=? ORDER BY created_at DESC"),
                    (workspace_id,)
                )
            cols = [d[0] for d in cur.description]
            rows = []
            for row in cur.fetchall():
                data = dict(zip(cols, row))
                try:
                    data["platforms"] = json.loads(data.get("platforms") or "[]")
                except Exception:
                    pass
                rows.append(data)
            return rows
        finally:
            conn.close()

    @staticmethod
    def list_by_project(project_id: int) -> list:
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                _adapt_sql("SELECT * FROM campaigns WHERE project_id=? ORDER BY created_at DESC"),
                (project_id,)
            )
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def update(campaign_id: int, **kwargs) -> bool:
        allowed = {"name", "objective", "platforms", "target_audience",
                   "budget", "start_date", "end_date", "status"}
        fields = {}
        for k, v in kwargs.items():
            if k not in allowed:
                continue
            fields[k] = json.dumps(v, ensure_ascii=False) if isinstance(v, list) else v
        if not fields:
            return False
        fields["updated_at"] = datetime.now().isoformat()
        set_clause = ", ".join([f"{k}=?" for k in fields])
        sql = _adapt_sql(f"UPDATE campaigns SET {set_clause} WHERE id=?")
        with managed_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (*fields.values(), campaign_id))
            return cur.rowcount > 0

    @staticmethod
    def get_post_count(campaign_id: int) -> int:
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute(_adapt_sql("SELECT COUNT(*) FROM posts WHERE campaign_id=?"), (campaign_id,))
            return cur.fetchone()[0]
        finally:
            conn.close()
