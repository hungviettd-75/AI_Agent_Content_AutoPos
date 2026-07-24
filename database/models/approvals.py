"""database/models/approvals.py — CRUD cho bang approvals (luong phe duyet)."""
from datetime import datetime
from database.connection import managed_connection, get_db_connection, _adapt_sql, _is_postgres
from config.config import logger


class ApprovalModel:

    VALID_STATUS = {"pending", "approved", "rejected", "revision_requested"}

    @staticmethod
    def request(post_id: int, requested_by: int = None, workspace_id: int = None) -> int:
        """Gui yeu cau phe duyet bai viet."""
        now = datetime.now().isoformat()
        sql = _adapt_sql("""
            INSERT INTO approvals (post_id, workspace_id, requested_by, status, requested_at)
            VALUES (?,?,?,?,?)
        """)
        logger.info(f"[AUDIT] Gui yeu cau phe duyet post_id={post_id}")
        with managed_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (post_id, workspace_id, requested_by, "pending", now))
            if _is_postgres():
                cur.execute("SELECT lastval()")
                return cur.fetchone()[0]
            return cur.lastrowid

    @staticmethod
    def respond(approval_id: int, status: str,
                approved_by: int = None, notes: str = "", workspace_id: int = None) -> bool:
        """Phe duyet / tu choi / yeu cau chinh sua."""
        if status not in ApprovalModel.VALID_STATUS:
            logger.warning(f"Trang thai phe duyet khong hop le: {status}")
            return False
        now = datetime.now().isoformat()
        sql = """
            UPDATE approvals SET status=?, approved_by=?, notes=?, responded_at=? WHERE id=?
        """
        params = [status, approved_by, notes, now, approval_id]
        if workspace_id is not None:
            sql += " AND workspace_id=?"
            params.append(workspace_id)
        logger.info(f"[AUDIT] Phan hoi phe duyet ID={approval_id}: {status}")
        with managed_connection() as conn:
            cur = conn.cursor()
            cur.execute(_adapt_sql(sql), params)
            return cur.rowcount > 0

    @staticmethod
    def get_by_post(post_id: int, workspace_id: int = None) -> list:
        """Lay lich su phe duyet cua mot bai viet."""
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            if workspace_id is not None:
                cur.execute(
                    _adapt_sql("SELECT * FROM approvals WHERE post_id=? AND workspace_id=? ORDER BY requested_at DESC"),
                    (post_id, workspace_id)
                )
            else:
                cur.execute(
                    _adapt_sql("SELECT * FROM approvals WHERE post_id=? ORDER BY requested_at DESC"),
                    (post_id,)
                )
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def get_pending_by_workspace(workspace_id: int) -> list:
        """Lay danh sach bai cho phe duyet trong workspace."""
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            sql = _adapt_sql("""
                SELECT a.*, p.title, p.content, p.platform, p.content_type
                FROM approvals a
                JOIN posts p ON p.id = a.post_id
                WHERE a.workspace_id=? AND a.status='pending'
                ORDER BY a.requested_at DESC
            """)
            cur.execute(sql, (workspace_id,))
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def get_latest_by_post(post_id: int, workspace_id: int = None) -> dict:
        """Lay trang thai phe duyet moi nhat cua bai viet."""
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            if workspace_id is not None:
                cur.execute(
                    _adapt_sql("SELECT * FROM approvals WHERE post_id=? AND workspace_id=? ORDER BY requested_at DESC LIMIT 1"),
                    (post_id, workspace_id)
                )
            else:
                cur.execute(
                    _adapt_sql("SELECT * FROM approvals WHERE post_id=? ORDER BY requested_at DESC LIMIT 1"),
                    (post_id,)
                )
            row = cur.fetchone()
            return dict(row) if row else {}
        finally:
            conn.close()

    @staticmethod
    def count_by_status(workspace_id: int) -> dict:
        """Thong ke so luong phe duyet theo trang thai."""
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                _adapt_sql("SELECT status, COUNT(*) as cnt FROM approvals WHERE workspace_id=? GROUP BY status"),
                (workspace_id,)
            )
            return {row[0]: row[1] for row in cur.fetchall()}
        finally:
            conn.close()

    @staticmethod
    def list_by_workspace(workspace_id: int, status: str = None, limit: int = 100) -> list:
        """Lay danh sach phe duyet trong workspace, co the loc theo trang thai."""
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            if status:
                sql = _adapt_sql(
                    "SELECT * FROM approvals WHERE workspace_id=? AND status=? ORDER BY requested_at DESC LIMIT ?"
                )
                cur.execute(sql, (workspace_id, status, limit))
            else:
                sql = _adapt_sql(
                    "SELECT * FROM approvals WHERE workspace_id=? ORDER BY requested_at DESC LIMIT ?"
                )
                cur.execute(sql, (workspace_id, limit))
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
        finally:
            conn.close()

