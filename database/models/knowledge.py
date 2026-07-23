"""database/models/knowledge.py — CRUD cho bang knowledge (kho tri thuc AI)."""
import json
import pandas as pd
from datetime import datetime
from database.connection import managed_connection, get_db_connection, _adapt_sql, _is_postgres
from config.config import logger


class KnowledgeModel:

    @staticmethod
    def create(content: str, topic: str = "", title: str = "",
               summary: str = "", knowledge_type: str = "tutorial",
               ai_tool: str = "", audience: str = "", difficulty: str = "Beginner",
               platform: str = "facebook", tags: list = None,
               workspace_id: int = None, post_id: int = None,
               status: str = "draft", created_by: int = None,
               folder: str = "Chung", collection: str = "Mặc định", version: str = "1.0") -> int:
        now = datetime.now().isoformat()
        sql = _adapt_sql("""
            INSERT INTO knowledge (workspace_id, title, content, summary, knowledge_type,
                                   ai_tool, audience, difficulty, platform, tags,
                                   post_id, topic, date, status, created_by, created_at, updated_at,
                                   folder, collection, version)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """)
        logger.info(f"[AUDIT] Tao knowledge post: {topic[:50] if topic else title[:50]}")
        with managed_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (
                workspace_id, title or topic, content, summary, knowledge_type,
                ai_tool, audience, difficulty, platform,
                json.dumps(tags or [], ensure_ascii=False),
                post_id, topic, now, status, created_by, now, now,
                folder or "Chung", collection or "Mặc định", version or "1.0"
            ))
            if _is_postgres():
                cur.execute("SELECT lastval()")
                return cur.fetchone()[0]
            return cur.lastrowid

    @staticmethod
    def get_by_id(knowledge_id: int) -> dict:
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute(_adapt_sql("SELECT * FROM knowledge WHERE id=?"), (knowledge_id,))
            row = cur.fetchone()
            if not row:
                return {}
            data = dict(row)
            try:
                data["tags"] = json.loads(data.get("tags") or "[]")
            except Exception:
                pass
            return data
        finally:
            conn.close()

    @staticmethod
    def list_all(workspace_id: int = None, status: str = None,
                 platform: str = None, limit: int = 50) -> pd.DataFrame:
        conn = get_db_connection()
        query = "SELECT * FROM knowledge WHERE 1=1"
        params = []
        if workspace_id:
            query += _adapt_sql(" AND workspace_id=?")
            params.append(workspace_id)
        if status:
            query += _adapt_sql(" AND status=?")
            params.append(status)
        if platform:
            query += _adapt_sql(" AND platform=?")
            params.append(platform)
        query += " ORDER BY id DESC"
        if limit:
            query += _adapt_sql(" LIMIT ?")
            params.append(limit)
        try:
            return pd.read_sql_query(query, conn, params=params)
        except Exception as e:
            logger.error(f"Loi truy van knowledge: {e}", exc_info=True)
            return pd.DataFrame()
        finally:
            conn.close()

    @staticmethod
    def update_status(knowledge_id: int, status: str) -> bool:
        sql = _adapt_sql("UPDATE knowledge SET status=?, updated_at=? WHERE id=?")
        with managed_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (status, datetime.now().isoformat(), knowledge_id))
            return cur.rowcount > 0

    @staticmethod
    def delete(knowledge_id: int) -> bool:
        logger.info(f"[AUDIT] Xoa knowledge ID={knowledge_id}")
        with managed_connection() as conn:
            cur = conn.cursor()
            cur.execute(_adapt_sql("DELETE FROM knowledge WHERE id=?"), (knowledge_id,))
            return cur.rowcount > 0

    @staticmethod
    def search(keyword: str, workspace_id: int = None, limit: int = 20) -> list:
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            like = f"%{keyword}%"
            if workspace_id:
                sql = _adapt_sql("""
                    SELECT id, title, topic, summary, knowledge_type, ai_tool, platform, status, created_at
                    FROM knowledge WHERE workspace_id=? AND (title LIKE ? OR topic LIKE ? OR content LIKE ?)
                    ORDER BY id DESC LIMIT ?
                """)
                cur.execute(sql, (workspace_id, like, like, like, limit))
            else:
                sql = _adapt_sql("""
                    SELECT id, title, topic, summary, knowledge_type, ai_tool, platform, status, created_at
                    FROM knowledge WHERE title LIKE ? OR topic LIKE ? OR content LIKE ?
                    ORDER BY id DESC LIMIT ?
                """)
                cur.execute(sql, (like, like, like, limit))
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
        finally:
            conn.close()
