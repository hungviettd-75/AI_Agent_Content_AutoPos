"""database/models/assets.py — CRUD cho bang assets (media files)."""
import json
from datetime import datetime
from database.connection import managed_connection, get_db_connection, _adapt_sql, _is_postgres
from config.config import logger


class AssetModel:

    VALID_TYPES = {"image", "video", "document", "audio"}

    @staticmethod
    def create(workspace_id: int, name: str, url: str,
               file_type: str = "image", post_id: int = None,
               storage_path: str = "", size_bytes: int = 0,
               mime_type: str = "", alt_text: str = "",
               tags: list = None, uploaded_by: int = None) -> int:
        now = datetime.now().isoformat()
        sql = _adapt_sql("""
            INSERT INTO assets (workspace_id, post_id, name, file_type, url, storage_path,
                                size_bytes, mime_type, alt_text, tags, uploaded_by, created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """)
        logger.info(f"[AUDIT] Upload asset: {name} (type={file_type})")
        with managed_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (
                workspace_id, post_id, name, file_type, url, storage_path,
                size_bytes, mime_type, alt_text,
                json.dumps(tags or [], ensure_ascii=False),
                uploaded_by, now
            ))
            if _is_postgres():
                cur.execute("SELECT lastval()")
                return cur.fetchone()[0]
            return cur.lastrowid

    @staticmethod
    def get_by_id(asset_id: int) -> dict:
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute(_adapt_sql("SELECT * FROM assets WHERE id=?"), (asset_id,))
            row = cur.fetchone()
            if not row:
                return {}
            data = dict(row)
            # tags có thể là list (cũ) hoặc dict (mới từ thumbnail service)
            raw_tags = data.get("tags") or ""
            try:
                parsed = json.loads(raw_tags) if raw_tags else {}
            except Exception:
                parsed = {}
            data["tags"] = parsed
            return data
        finally:
            conn.close()

    @staticmethod
    def list_by_workspace(workspace_id: int, file_type: str = None) -> list:
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            if file_type:
                cur.execute(
                    _adapt_sql("SELECT * FROM assets WHERE workspace_id=? AND file_type=? ORDER BY created_at DESC"),
                    (workspace_id, file_type)
                )
            else:
                cur.execute(
                    _adapt_sql("SELECT * FROM assets WHERE workspace_id=? ORDER BY created_at DESC"),
                    (workspace_id,)
                )
            cols = [d[0] for d in cur.description]
            rows = []
            for row in cur.fetchall():
                data = dict(zip(cols, row))
                # tags có thể là list (cũ) hoặc dict (mới)
                raw = data.get("tags") or ""
                try:
                    data["tags"] = json.loads(raw) if raw else {}
                except Exception:
                    data["tags"] = {}
                rows.append(data)
            return rows
        finally:
            conn.close()

    @staticmethod
    def list_by_post(post_id: int) -> list:
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                _adapt_sql("SELECT * FROM assets WHERE post_id=? ORDER BY created_at"),
                (post_id,)
            )
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def attach_to_post(asset_id: int, post_id: int) -> bool:
        with managed_connection() as conn:
            cur = conn.cursor()
            cur.execute(_adapt_sql("UPDATE assets SET post_id=? WHERE id=?"), (post_id, asset_id))
            return cur.rowcount > 0

    @staticmethod
    def delete(asset_id: int) -> bool:
        logger.info(f"[AUDIT] Xoa asset ID={asset_id}")
        with managed_connection() as conn:
            cur = conn.cursor()
            cur.execute(_adapt_sql("DELETE FROM assets WHERE id=?"), (asset_id,))
            return cur.rowcount > 0
