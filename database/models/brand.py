"""database/models/brand.py — CRUD cho bang brand (nhan dien thuong hieu)."""
import json
from datetime import datetime
from database.connection import managed_connection, get_db_connection, _adapt_sql, _is_postgres
from config.config import logger


class BrandModel:

    @staticmethod
    def create(workspace_id: int, company_id: int = None,
               tone_of_voice: str = "casual",
               target_audiences: list = None,
               brand_colors: dict = None,
               logo_url: str = "", tagline: str = "",
               brand_guidelines: str = "",
               blacklist_words: list = None,
               cta: str = "", vision: str = "",
               mission: str = "", keywords: list = None) -> int:
        now = datetime.now().isoformat()
        sql = _adapt_sql("""
            INSERT INTO brand (company_id, workspace_id, tone_of_voice, target_audiences,
                               brand_colors, logo_url, tagline, brand_guidelines, blacklist_words,
                               cta, vision, mission, keywords,
                               created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """)
        logger.info(f"[AUDIT] Tao brand cho workspace {workspace_id}")
        with managed_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (
                company_id, workspace_id, tone_of_voice,
                json.dumps(target_audiences or [], ensure_ascii=False),
                json.dumps(brand_colors or {}, ensure_ascii=False),
                logo_url, tagline, brand_guidelines,
                json.dumps(blacklist_words or [], ensure_ascii=False),
                cta, vision, mission,
                json.dumps(keywords or [], ensure_ascii=False),
                now, now
            ))
            if _is_postgres():
                cur.execute("SELECT lastval()")
                return cur.fetchone()[0]
            return cur.lastrowid

    @staticmethod
    def get_by_workspace(workspace_id: int) -> dict:
        """Lay brand profile cua workspace (moi workspace co 1 brand)."""
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                _adapt_sql("SELECT * FROM brand WHERE workspace_id=? ORDER BY id DESC LIMIT 1"),
                (workspace_id,)
            )
            row = cur.fetchone()
            if not row:
                return {}
            data = dict(row)
            # Parse JSON fields
            for field in ("target_audiences", "brand_colors", "blacklist_words", "keywords"):
                try:
                    data[field] = json.loads(data.get(field) or "[]")
                except Exception:
                    pass
            return data
        finally:
            conn.close()

    @staticmethod
    def upsert(workspace_id: int, **kwargs) -> int:
        """Tao moi hoac cap nhat brand profile cua workspace."""
        existing = BrandModel.get_by_workspace(workspace_id)
        if existing:
            BrandModel.update(existing["id"], workspace_id=workspace_id, **kwargs)
            return existing["id"]
        else:
            return BrandModel.create(workspace_id=workspace_id, **kwargs)

    @staticmethod
    def update(brand_id: int, **kwargs) -> bool:
        workspace_id = kwargs.pop("workspace_id", None)
        allowed = {"tone_of_voice", "target_audiences", "brand_colors",
                   "logo_url", "tagline", "brand_guidelines", "blacklist_words",
                   "cta", "vision", "mission", "keywords"}
        fields = {}
        for k, v in kwargs.items():
            if k not in allowed:
                continue
            if isinstance(v, (list, dict)):
                fields[k] = json.dumps(v, ensure_ascii=False)
            else:
                fields[k] = v
        if not fields:
            return False
        fields["updated_at"] = datetime.now().isoformat()
        set_clause = ", ".join([f"{k}=?" for k in fields])
        sql = f"UPDATE brand SET {set_clause} WHERE id=?"
        params = [*fields.values(), brand_id]
        if workspace_id is not None:
            sql += " AND workspace_id=?"
            params.append(workspace_id)
        with managed_connection() as conn:
            cur = conn.cursor()
            cur.execute(_adapt_sql(sql), params)
            return cur.rowcount > 0

    @staticmethod
    def get_blacklist(workspace_id: int) -> list:
        """Tra ve danh sach tu cam cua workspace."""
        brand = BrandModel.get_by_workspace(workspace_id)
        return brand.get("blacklist_words", []) if brand else []
