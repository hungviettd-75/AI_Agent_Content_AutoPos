"""database/models/projects.py — CRUD cho bang projects."""
from datetime import datetime
from database.connection import managed_connection, get_db_connection, _adapt_sql, _is_postgres
from config.config import logger


class ProjectModel:

    VALID_STATUS = {"planning", "active", "paused", "completed"}

    @staticmethod
    def create(workspace_id: int, name: str, company_id: int = None,
               description: str = "", status: str = "active",
               start_date: str = "", end_date: str = "",
               created_by: int = None) -> int:
        now = datetime.now().isoformat()
        sql = _adapt_sql("""
            INSERT INTO projects (workspace_id, company_id, name, description, status,
                                  start_date, end_date, created_by, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?)
        """)
        logger.info(f"[AUDIT] Tao project: {name} (workspace={workspace_id})")
        with managed_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (workspace_id, company_id, name, description, status,
                              start_date, end_date, created_by, now, now))
            if _is_postgres():
                cur.execute("SELECT lastval()")
                return cur.fetchone()[0]
            return cur.lastrowid

    @staticmethod
    def get_by_id(project_id: int, workspace_id: int = None) -> dict:
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            if workspace_id is not None:
                cur.execute(_adapt_sql("SELECT * FROM projects WHERE id=? AND workspace_id=?"), (project_id, workspace_id))
            else:
                cur.execute(_adapt_sql("SELECT * FROM projects WHERE id=?"), (project_id,))
            row = cur.fetchone()
            return dict(row) if row else {}
        finally:
            conn.close()

    @staticmethod
    def list_by_workspace(workspace_id: int, status: str = None) -> list:
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            if status:
                sql = _adapt_sql("SELECT * FROM projects WHERE workspace_id=? AND status=? ORDER BY created_at DESC")
                cur.execute(sql, (workspace_id, status))
            else:
                sql = _adapt_sql("SELECT * FROM projects WHERE workspace_id=? ORDER BY created_at DESC")
                cur.execute(sql, (workspace_id,))
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def update(project_id: int, **kwargs) -> bool:
        workspace_id = kwargs.pop("workspace_id", None)
        allowed = {"name", "description", "status", "start_date", "end_date", "company_id"}
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        if not fields:
            return False
        fields["updated_at"] = datetime.now().isoformat()
        set_clause = ", ".join([f"{k}=?" for k in fields])
        sql = f"UPDATE projects SET {set_clause} WHERE id=?"
        params = [*fields.values(), project_id]
        if workspace_id is not None:
            sql += " AND workspace_id=?"
            params.append(workspace_id)
        with managed_connection() as conn:
            cur = conn.cursor()
            cur.execute(_adapt_sql(sql), params)
            return cur.rowcount > 0

    @staticmethod
    def delete(project_id: int, workspace_id: int = None) -> bool:
        logger.info(f"[AUDIT] Xoa project ID={project_id}")
        with managed_connection() as conn:
            cur = conn.cursor()
            if workspace_id is not None:
                cur.execute(_adapt_sql("DELETE FROM projects WHERE id=? AND workspace_id=?"), (project_id, workspace_id))
            else:
                cur.execute(_adapt_sql("DELETE FROM projects WHERE id=?"), (project_id,))
            return cur.rowcount > 0
