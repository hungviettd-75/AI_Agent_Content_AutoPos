"""database/models/billing.py — DAO quản lý Subscription, Quota, Invoice cho Workspaces."""
import json
from datetime import datetime, timedelta
import random
from database.connection import managed_connection, get_db_connection, _adapt_sql, _is_postgres
from config.config import logger

class BillingModel:

    PLANS = {
        "free": {"name": "Free Plan", "price": 0, "max_users": 3, "max_posts": 30, "ai_tokens": 100_000},
        "pro": {"name": "Pro Plan", "price": 29, "max_users": 10, "max_posts": 300, "ai_tokens": 2_000_000},
        "agency": {"name": "Agency Plan", "price": 99, "max_users": 50, "max_posts": 2000, "ai_tokens": 15_000_000}
    }

    @staticmethod
    def ensure_tables():
        """Tao bang invoices dung cu phap cho SQLite va PostgreSQL."""
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            if _is_postgres():
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS invoices (
                        id             SERIAL PRIMARY KEY,
                        workspace_id   INTEGER NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
                        invoice_no     TEXT UNIQUE NOT NULL,
                        plan           TEXT NOT NULL,
                        amount         NUMERIC(12,2) NOT NULL,
                        status         TEXT NOT NULL DEFAULT 'paid',
                        billing_date   TEXT NOT NULL,
                        payment_method TEXT DEFAULT 'Credit Card',
                        pdf_url        TEXT
                    )
                """)
            else:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS invoices (
                        id             INTEGER PRIMARY KEY AUTOINCREMENT,
                        workspace_id   INTEGER NOT NULL,
                        invoice_no     TEXT UNIQUE NOT NULL,
                        plan           TEXT NOT NULL,
                        amount         REAL NOT NULL,
                        status         TEXT NOT NULL DEFAULT 'paid',
                        billing_date   TEXT NOT NULL,
                        payment_method TEXT DEFAULT 'Credit Card',
                        pdf_url        TEXT
                    )
                """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_invoices_workspace ON invoices(workspace_id)")
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"[BILLING] Khong the khoi tao bang invoices: {e}", exc_info=True)
        finally:
            conn.close()

    @staticmethod
    def get_workspace_plan_details(workspace_id: int) -> dict:
        """Lấy thông tin chi tiết gói cước và quota hiện tại của Workspace."""
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute(_adapt_sql("SELECT plan FROM workspaces WHERE id = ?"), (workspace_id,))
            row = cur.fetchone()
            plan_code = row[0].lower() if row else "free"
        except Exception:
            plan_code = "free"
        finally:
            conn.close()

        # Đếm số lượng thực tế đã dùng trong tháng này
        now = datetime.now()
        start_of_month = datetime(now.year, now.month, 1).strftime("%Y-%m-%d")
        
        # 1. Đếm số bài viết đã đăng / tạo trong tháng
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute(_adapt_sql("SELECT COUNT(*) FROM posts WHERE workspace_id = ? AND created_at >= ?"), (workspace_id, start_of_month))
            posts_used = cur.fetchone()[0]
        except Exception:
            posts_used = 0
        finally:
            conn.close()

        # 2. Đếm số tokens AI đã tiêu dùng trong tháng
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute(_adapt_sql("SELECT SUM(total_tokens) FROM ai_logs WHERE workspace_id = ? AND created_at >= ?"), (workspace_id, start_of_month))
            val = cur.fetchone()[0]
            tokens_used = val if val else 0
        except Exception:
            tokens_used = 0
        finally:
            conn.close()

        # 3. Đếm số thành viên nhóm
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute(_adapt_sql("SELECT COUNT(*) FROM workspace_members WHERE workspace_id = ?"), (workspace_id,))
            users_used = cur.fetchone()[0]
        except Exception:
            users_used = 1
        finally:
            conn.close()

        plan_limit = BillingModel.PLANS.get(plan_code, BillingModel.PLANS["free"])
        
        return {
            "plan_code": plan_code,
            "plan_name": plan_limit["name"],
            "price": plan_limit["price"],
            "quota": {
                "users": {"used": users_used, "max": plan_limit["max_users"]},
                "posts": {"used": posts_used, "max": plan_limit["max_posts"]},
                "tokens": {"used": tokens_used, "max": plan_limit["ai_tokens"]}
            }
        }

    @staticmethod
    def update_plan(workspace_id: int, plan: str) -> bool:
        """Nâng cấp hoặc thay đổi gói cước của Workspace."""
        if plan not in BillingModel.PLANS:
            return False
        sql = _adapt_sql("UPDATE workspaces SET plan = ? WHERE id = ?")
        with managed_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (plan, workspace_id))
            return cur.rowcount > 0

    @staticmethod
    def get_invoices(workspace_id: int) -> list:
        """Lấy danh sách hóa đơn thanh toán của Workspace."""
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                _adapt_sql("SELECT * FROM invoices WHERE workspace_id = ? ORDER BY billing_date DESC"),
                (workspace_id,)
            )
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def create_invoice(workspace_id: int, plan: str, amount: float, method: str = "Credit Card") -> bool:
        """Tạo hóa đơn thanh toán mới."""
        inv_no = f"INV-{datetime.now().strftime('%Y%M')}-{random.randint(1000, 9999)}"
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        sql = _adapt_sql("""
            INSERT INTO invoices (workspace_id, invoice_no, plan, amount, status, billing_date, payment_method)
            VALUES (?,?,?,?,'paid',?,?)
        """)
        with managed_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (workspace_id, inv_no, plan, amount, date_str, method))
            return cur.rowcount > 0
            
    @staticmethod
    def generate_mock_invoices(workspace_id: int, plan: str):
        """Tạo dữ liệu hóa đơn ảo cho lịch sử giao dịch."""
        plan_meta = BillingModel.PLANS.get(plan, BillingModel.PLANS["free"])
        price = plan_meta["price"]
        if price == 0:
            return
        
        now = datetime.now()
        for i in range(3): # Tạo hóa đơn cho 3 tháng qua
            bill_date = (now - timedelta(days=i*30)).strftime("%Y-%m-%d %H:%M")
            inv_no = f"INV-{now.year}{now.month - i:02d}-{random.randint(1000, 9999)}"
            sql = _adapt_sql("""
                INSERT INTO invoices (workspace_id, invoice_no, plan, amount, status, billing_date, payment_method)
                VALUES (?,?,?,?,'paid',?,?)
            """)
            with managed_connection() as conn:
                cur = conn.cursor()
                try:
                    cur.execute(sql, (workspace_id, inv_no, plan, price, bill_date, "Credit Card (Visa)"))
                except Exception:
                    pass
