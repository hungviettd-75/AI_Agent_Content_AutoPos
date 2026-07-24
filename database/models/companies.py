"""database/models/companies.py — CRUD cho bang companies."""
from datetime import datetime
from database.connection import managed_connection, get_db_connection, _adapt_sql, _is_postgres
from config.config import logger


class CompanyModel:

    @staticmethod
    def create(workspace_id: int, name: str, industry: str = "",
               size: str = "small", website: str = "", description: str = "",
               logo_url: str = "", products: str = "", target_customers: str = "") -> int:
        now = datetime.now().isoformat()
        sql = _adapt_sql("""
            INSERT INTO companies (workspace_id, name, industry, size, website, description, logo_url, products, target_customers, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """)
        logger.info(f"[AUDIT] Tao cong ty: {name} trong workspace {workspace_id}")
        with managed_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (workspace_id, name, industry, size, website, description, logo_url, products, target_customers, now, now))
            if _is_postgres():
                cur.execute("SELECT lastval()")
                return cur.fetchone()[0]
            return cur.lastrowid

    @staticmethod
    def get_by_id(company_id: int, workspace_id: int = None) -> dict:
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            if workspace_id is not None:
                cur.execute(_adapt_sql("SELECT * FROM companies WHERE id=? AND workspace_id=?"), (company_id, workspace_id))
            else:
                cur.execute(_adapt_sql("SELECT * FROM companies WHERE id=?"), (company_id,))
            row = cur.fetchone()
            return dict(row) if row else {}
        finally:
            conn.close()

    @staticmethod
    def list_by_workspace(workspace_id: int) -> list:
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute(_adapt_sql("SELECT * FROM companies WHERE workspace_id=? ORDER BY name"), (workspace_id,))
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def get_by_workspace(workspace_id: int) -> dict:
        """Lay thong tin cong ty dau tien cua workspace, hoac tu dong tao moi neu chua co."""
        companies = CompanyModel.list_by_workspace(workspace_id)
        if companies:
            return companies[0]
            
        # Tạo mặc định
        c_id = CompanyModel.create(workspace_id=workspace_id, name="Công ty mặc định")
        return CompanyModel.get_by_id(c_id, workspace_id=workspace_id)

    @staticmethod
    def upsert(workspace_id: int, **kwargs) -> int:
        """Tao moi hoac cap nhat thong tin cong ty cua workspace."""
        existing = CompanyModel.get_by_workspace(workspace_id)
        if existing:
            CompanyModel.update(existing["id"], workspace_id=workspace_id, **kwargs)
            return existing["id"]
        else:
            return CompanyModel.create(workspace_id=workspace_id, **kwargs)

    @staticmethod
    def update(company_id: int, **kwargs) -> bool:
        workspace_id = kwargs.pop("workspace_id", None)
        allowed = {"name", "industry", "size", "website", "description", "logo_url", "products", "target_customers"}
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        if not fields:
            return False
        fields["updated_at"] = datetime.now().isoformat()
        set_clause = ", ".join([f"{k}=?" for k in fields])
        sql = f"UPDATE companies SET {set_clause} WHERE id=?"
        params = [*fields.values(), company_id]
        if workspace_id is not None:
            sql += " AND workspace_id=?"
            params.append(workspace_id)
        with managed_connection() as conn:
            cur = conn.cursor()
            cur.execute(_adapt_sql(sql), params)
            return cur.rowcount > 0

    @staticmethod
    def delete(company_id: int, workspace_id: int = None) -> bool:
        logger.info(f"[AUDIT] Xoa cong ty ID={company_id}")
        with managed_connection() as conn:
            cur = conn.cursor()
            if workspace_id is not None:
                cur.execute(_adapt_sql("DELETE FROM companies WHERE id=? AND workspace_id=?"), (company_id, workspace_id))
            else:
                cur.execute(_adapt_sql("DELETE FROM companies WHERE id=?"), (company_id,))
            return cur.rowcount > 0
