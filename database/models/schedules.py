"""database/models/schedules.py — CRUD cho bang schedules (lich dang bai)."""
from datetime import datetime
from database.connection import managed_connection, get_db_connection, _adapt_sql, _is_postgres
from config.config import logger


class ScheduleModel:

    VALID_STATUS = {"pending", "processing", "published", "failed", "cancelled"}

    @staticmethod
    def create(post_id: int, scheduled_at: str, platform: str = "facebook",
               workspace_id: int = None, created_by: int = None) -> int:
        now = datetime.now().isoformat()
        sql = _adapt_sql("""
            INSERT INTO schedules (workspace_id, post_id, scheduled_at, platform,
                                   status, retry_count, created_by, created_at, updated_at)
            VALUES (?,?,?,?,?,0,?,?,?)
        """)
        logger.info(f"[AUDIT] Them vao lich dang: post_id={post_id}, luc={scheduled_at}, platform={platform}")
        with managed_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (workspace_id, post_id, scheduled_at, platform, "pending", created_by, now, now))
            if _is_postgres():
                cur.execute("SELECT lastval()")
                return cur.fetchone()[0]
            return cur.lastrowid

    @staticmethod
    def get_by_id(schedule_id: int, workspace_id: int = None) -> dict:
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            if workspace_id is not None:
                cur.execute(_adapt_sql("SELECT * FROM schedules WHERE id=? AND workspace_id=?"), (schedule_id, workspace_id))
            else:
                cur.execute(_adapt_sql("SELECT * FROM schedules WHERE id=?"), (schedule_id,))
            row = cur.fetchone()
            return dict(row) if row else {}
        finally:
            conn.close()

    @staticmethod
    def get_pending(workspace_id: int = None, before: str = None) -> list:
        """Lay danh sach lich dang chua xu ly (status=pending)."""
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            query = "SELECT s.*, p.content, p.platform as post_platform FROM schedules s JOIN posts p ON p.id=s.post_id WHERE s.status='pending'"
            params = []
            if workspace_id:
                query += _adapt_sql(" AND s.workspace_id=?")
                params.append(workspace_id)
            if before:
                query += _adapt_sql(" AND s.scheduled_at <= ?")
                params.append(before)
            query += " ORDER BY s.scheduled_at ASC"
            cur.execute(query, params)
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def update_status(schedule_id: int, status: str,
                      error_message: str = None, published_at: str = None,
                      workspace_id: int = None) -> bool:
        now = datetime.now().isoformat()
        fields = {"status": status, "updated_at": now}
        if error_message is not None:
            fields["error_message"] = error_message
        if published_at:
            fields["published_at"] = published_at
        set_clause = ", ".join([f"{k}=?" for k in fields])
        sql = f"UPDATE schedules SET {set_clause} WHERE id=?"
        params = [*fields.values(), schedule_id]
        if workspace_id is not None:
            sql += " AND workspace_id=?"
            params.append(workspace_id)
        with managed_connection() as conn:
            cur = conn.cursor()
            cur.execute(_adapt_sql(sql), params)
            return cur.rowcount > 0

    @staticmethod
    def increment_retry(schedule_id: int, workspace_id: int = None) -> int:
        """Tang retry_count +1, tra ve gia tri moi."""
        with managed_connection() as conn:
            cur = conn.cursor()
            if workspace_id is not None:
                cur.execute(
                    _adapt_sql("UPDATE schedules SET retry_count=retry_count+1 WHERE id=? AND workspace_id=?"),
                    (schedule_id, workspace_id)
                )
            else:
                cur.execute(
                    _adapt_sql("UPDATE schedules SET retry_count=retry_count+1 WHERE id=?"),
                    (schedule_id,)
                )
        sched = ScheduleModel.get_by_id(schedule_id, workspace_id=workspace_id)
        return sched.get("retry_count", 0)

    @staticmethod
    def list_by_workspace(workspace_id: int, status: str = None, limit: int = 50) -> list:
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            if status:
                sql = _adapt_sql("SELECT * FROM schedules WHERE workspace_id=? AND status=? ORDER BY scheduled_at DESC LIMIT ?")
                cur.execute(sql, (workspace_id, status, limit))
            else:
                sql = _adapt_sql("SELECT * FROM schedules WHERE workspace_id=? ORDER BY scheduled_at DESC LIMIT ?")
                cur.execute(sql, (workspace_id, limit))
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def cancel(schedule_id: int, workspace_id: int = None) -> bool:
        logger.info(f"[AUDIT] Huy lich dang ID={schedule_id}")
        return ScheduleModel.update_status(schedule_id, "cancelled", workspace_id=workspace_id)
