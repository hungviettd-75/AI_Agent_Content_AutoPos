"""database/models/posts.py — CRUD cho bang posts (schema V2)."""
import json
import pandas as pd
from datetime import datetime
from database.connection import managed_connection, get_db_connection, _adapt_sql, _is_postgres
from config.config import logger


class PostModel:

    VALID_STATUS   = {"draft", "pending_approval", "pending_manager_approval", "pending_ceo_approval", "approved", "published", "failed", "archived"}
    VALID_PLATFORM = {"facebook","zalo","linkedin","all"}
    VALID_TYPES    = {"marketing_viral","ai_knowledge","case_study","reels"}

    @staticmethod
    def create(content: str, platform: str = "facebook",
               content_type: str = "marketing_viral",
               topic: str = "", title: str = "",
               status: str = "draft", campaign_id: int = None,
               workspace_id: int = None, viral_score: int = None,
               image_prompt: str = "", ai_metadata: dict = None,
               created_by: int = None) -> int:
        now = datetime.now().isoformat()
        sql = _adapt_sql("""
            INSERT INTO posts (workspace_id, campaign_id, title, content, platform,
                               content_type, status, viral_score, image_prompt,
                               ai_metadata, topic, date, created_by, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """)
        logger.info(f"[AUDIT] Tao post moi (platform={platform}, type={content_type})")
        with managed_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (
                workspace_id, campaign_id, title, content, platform,
                content_type, status, viral_score, image_prompt,
                json.dumps(ai_metadata or {}, ensure_ascii=False),
                topic, now, created_by, now, now
            ))
            if _is_postgres():
                cur.execute("SELECT lastval()")
                return cur.fetchone()[0]
            return cur.lastrowid

    @staticmethod
    def get_by_id(post_id: int) -> dict:
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute(_adapt_sql("SELECT * FROM posts WHERE id=?"), (post_id,))
            row = cur.fetchone()
            if not row:
                return {}
            data = dict(row)
            try:
                data["ai_metadata"] = json.loads(data.get("ai_metadata") or "{}")
            except Exception:
                pass
            return data
        finally:
            conn.close()

    @staticmethod
    def list_by_workspace(workspace_id: int, status: str = None,
                          platform: str = None, limit: int = 50,
                          offset: int = 0) -> pd.DataFrame:
        conn = get_db_connection()
        query = "SELECT * FROM posts WHERE 1=1"
        params = []
        if workspace_id:
            query += _adapt_sql(" AND workspace_id=?")
            params.append(workspace_id)
        if status:
            query += _adapt_sql(" AND status=?")
            params.append(status)
        if platform and platform != "all":
            query += _adapt_sql(" AND platform=?")
            params.append(platform)
        query += " ORDER BY created_at DESC"
        if limit:
            query += _adapt_sql(" LIMIT ?")
            params.append(limit)
        if offset:
            query += _adapt_sql(" OFFSET ?")
            params.append(offset)
        try:
            return pd.read_sql_query(query, conn, params=params)
        except Exception as e:
            logger.error(f"Loi truy van posts: {e}", exc_info=True)
            return pd.DataFrame()
        finally:
            conn.close()

    @staticmethod
    def list_by_campaign(campaign_id: int) -> pd.DataFrame:
        conn = get_db_connection()
        try:
            return pd.read_sql_query(
                _adapt_sql("SELECT * FROM posts WHERE campaign_id=? ORDER BY created_at DESC"),
                conn, params=(campaign_id,)
            )
        finally:
            conn.close()

    @staticmethod
    def update_status(post_id: int, status: str, approved_by: int = None) -> bool:
        now = datetime.now().isoformat()
        if approved_by:
            sql = _adapt_sql("UPDATE posts SET status=?, approved_by=?, updated_at=? WHERE id=?")
            params = (status, approved_by, now, post_id)
        else:
            sql = _adapt_sql("UPDATE posts SET status=?, updated_at=? WHERE id=?")
            params = (status, now, post_id)
        logger.info(f"[AUDIT] Cap nhat trang thai post ID={post_id} -> {status}")
        with managed_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            return cur.rowcount > 0

    @staticmethod
    def update(post_id: int, **kwargs) -> bool:
        allowed = {"title","content","platform","content_type","status",
                   "viral_score","image_prompt","campaign_id","scheduled_at","published_at"}
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        if not fields:
            return False
        fields["updated_at"] = datetime.now().isoformat()
        set_clause = ", ".join([f"{k}=?" for k in fields])
        sql = _adapt_sql(f"UPDATE posts SET {set_clause} WHERE id=?")
        with managed_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (*fields.values(), post_id))
            return cur.rowcount > 0

    @staticmethod
    def delete(post_id: int) -> bool:
        logger.info(f"[AUDIT] Xoa post ID={post_id}")
        with managed_connection() as conn:
            cur = conn.cursor()
            cur.execute(_adapt_sql("DELETE FROM posts WHERE id=?"), (post_id,))
            return cur.rowcount > 0

    @staticmethod
    def count_by_workspace(workspace_id: int, status: str = None) -> int:
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            if status:
                cur.execute(_adapt_sql("SELECT COUNT(*) FROM posts WHERE workspace_id=? AND status=?"), (workspace_id, status))
            else:
                cur.execute(_adapt_sql("SELECT COUNT(*) FROM posts WHERE workspace_id=?"), (workspace_id,))
            return cur.fetchone()[0]
        finally:
            conn.close()
