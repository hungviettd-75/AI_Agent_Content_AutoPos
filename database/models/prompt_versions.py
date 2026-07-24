"""database/models/prompt_versions.py — CRUD cho bang prompt_versions."""
import json
from datetime import datetime
from database.connection import managed_connection, get_db_connection, _adapt_sql, _is_postgres
from config.config import logger

class PromptVersionModel:

    @staticmethod
    def create(prompt_name: str, content: str, variables: list = None,
               workspace_id: int = None, created_by: int = None) -> int:
        """Tạo một phiên bản prompt mới, tự động tăng version cho prompt_name đó trong workspace."""
        now = datetime.now().isoformat()
        
        # Tìm version tiếp theo
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            if workspace_id:
                cur.execute(
                    _adapt_sql("SELECT MAX(version) FROM prompt_versions WHERE prompt_name=? AND workspace_id=?"),
                    (prompt_name, workspace_id)
                )
            else:
                cur.execute(
                    _adapt_sql("SELECT MAX(version) FROM prompt_versions WHERE prompt_name=? AND workspace_id IS NULL"),
                    (prompt_name,)
                )
            max_v = cur.fetchone()[0]
            next_version = (max_v or 0) + 1
        finally:
            conn.close()

        # Set các version trước đó của prompt này thành inactive
        with managed_connection() as conn:
            cur = conn.cursor()
            if workspace_id:
                cur.execute(
                    _adapt_sql("UPDATE prompt_versions SET is_active=0 WHERE prompt_name=? AND workspace_id=?"),
                    (prompt_name, workspace_id)
                )
            else:
                cur.execute(
                    _adapt_sql("UPDATE prompt_versions SET is_active=0 WHERE prompt_name=? AND workspace_id IS NULL"),
                    (prompt_name,)
                )

        # Insert version mới làm active
        sql = _adapt_sql("""
            INSERT INTO prompt_versions (workspace_id, prompt_name, version, content, variables, is_active, created_by, created_at)
            VALUES (?,?,?,?,?,1,?,?)
        """)
        logger.info(f"[AUDIT] Tao version moi cho prompt {prompt_name}: v{next_version} (workspace={workspace_id})")
        with managed_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (
                workspace_id, prompt_name, next_version, content,
                json.dumps(variables or [], ensure_ascii=False),
                created_by, now
            ))
            if _is_postgres():
                cur.execute("SELECT lastval()")
                return cur.fetchone()[0]
            return cur.lastrowid

    @staticmethod
    def get_active(prompt_name: str, workspace_id: int = None) -> dict:
        """Return the active prompt version for the requested scope."""
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            if workspace_id:
                cur.execute(
                    _adapt_sql("SELECT * FROM prompt_versions WHERE prompt_name=? AND workspace_id=? AND is_active=1"),
                    (prompt_name, workspace_id)
                )
            else:
                cur.execute(
                    _adapt_sql("SELECT * FROM prompt_versions WHERE prompt_name=? AND workspace_id IS NULL AND is_active=1"),
                    (prompt_name,)
                )
            row = cur.fetchone()
            return dict(row) if row else {}
        finally:
            conn.close()

    @staticmethod
    def get_by_version(prompt_name: str, version: int, workspace_id: int = None) -> dict:
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            if workspace_id:
                cur.execute(
                    _adapt_sql("SELECT * FROM prompt_versions WHERE prompt_name=? AND version=? AND workspace_id=?"),
                    (prompt_name, version, workspace_id)
                )
            else:
                cur.execute(
                    _adapt_sql("SELECT * FROM prompt_versions WHERE prompt_name=? AND version=? AND workspace_id IS NULL"),
                    (prompt_name, version)
                )
            row = cur.fetchone()
            return dict(row) if row else {}
        finally:
            conn.close()

    @staticmethod
    def list_history(prompt_name: str, workspace_id: int = None) -> list:
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            if workspace_id:
                cur.execute(
                    _adapt_sql("SELECT * FROM prompt_versions WHERE prompt_name=? AND workspace_id=? ORDER BY version DESC"),
                    (prompt_name, workspace_id)
                )
            else:
                cur.execute(
                    _adapt_sql("SELECT * FROM prompt_versions WHERE prompt_name=? AND workspace_id IS NULL ORDER BY version DESC"),
                    (prompt_name,)
                )
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def update_performance_score(prompt_version_id: int, score: float, workspace_id: int = None) -> bool:
        sql = "UPDATE prompt_versions SET performance_score=? WHERE id=?"
        params = [score, prompt_version_id]
        if workspace_id is not None:
            sql += " AND workspace_id=?"
            params.append(workspace_id)
        with managed_connection() as conn:
            cur = conn.cursor()
            cur.execute(_adapt_sql(sql), params)
            return cur.rowcount > 0
