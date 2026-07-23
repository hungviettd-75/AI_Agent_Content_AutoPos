"""
database/models/users.py
=========================
CRUD operations cho bang `users`.
"""
import hashlib
import secrets
from datetime import datetime
from database.connection import managed_connection, get_db_connection, _adapt_sql, _is_postgres
from config.config import logger


def _hash_password(password: str) -> str:
    """Hash mat khau bang SHA-256 + salt don gian. Production: dung bcrypt."""
    salt = secrets.token_hex(16)
    hashed = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}${hashed}"


def _verify_password(password: str, password_hash: str) -> bool:
    """Xac minh mat khau."""
    try:
        salt, hashed = password_hash.split("$", 1)
        return hashlib.sha256((salt + password).encode()).hexdigest() == hashed
    except Exception:
        return False


class UserModel:
    """CRUD cho bang users."""

    @staticmethod
    def create(email: str, username: str, password: str,
               full_name: str = "", role: str = "editor") -> int:
        """Tao user moi. Tra ve ID vua tao."""
        logger.info(f"[AUDIT] Tao user moi: {username} ({email})")
        password_hash = _hash_password(password)
        now = datetime.now().isoformat()
        sql = _adapt_sql("""
            INSERT INTO users (email, username, password_hash, full_name, role, is_active, created_at, updated_at)
            VALUES (?,?,?,?,?,1,?,?)
        """)
        with managed_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (email, username, password_hash, full_name, role, now, now))
            if _is_postgres():
                cur.execute("SELECT lastval()")
                return cur.fetchone()[0]
            return cur.lastrowid

    @staticmethod
    def get_by_id(user_id: int) -> dict:
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute(_adapt_sql("SELECT * FROM users WHERE id = ?"), (user_id,))
            row = cur.fetchone()
            return dict(row) if row else {}
        finally:
            conn.close()

    @staticmethod
    def get_by_email(email: str) -> dict:
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute(_adapt_sql("SELECT * FROM users WHERE email = ?"), (email,))
            row = cur.fetchone()
            return dict(row) if row else {}
        finally:
            conn.close()

    @staticmethod
    def authenticate(email: str, password: str) -> dict:
        """Xac thuc va tra ve user neu thanh cong, {} neu that bai."""
        user = UserModel.get_by_email(email)
        if not user:
            return {}
        if not _verify_password(password, user.get("password_hash", "")):
            return {}
        # Cap nhat last_login_at
        sql = _adapt_sql("UPDATE users SET last_login_at=? WHERE id=?")
        with managed_connection() as conn:
            conn.cursor().execute(sql, (datetime.now().isoformat(), user["id"]))
        logger.info(f"[AUDIT] User xac thuc thanh cong: {email}")
        return {k: v for k, v in user.items() if k != "password_hash"}

    @staticmethod
    def update(user_id: int, **kwargs) -> bool:
        allowed = {"full_name", "avatar_url", "role", "is_active"}
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        if not fields:
            return False
        fields["updated_at"] = datetime.now().isoformat()
        set_clause = ", ".join([f"{k}=?" for k in fields])
        sql = _adapt_sql(f"UPDATE users SET {set_clause} WHERE id=?")
        with managed_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (*fields.values(), user_id))
            return cur.rowcount > 0

    @staticmethod
    def list_all(active_only: bool = True) -> list:
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            if active_only:
                cur.execute(_adapt_sql("SELECT id,email,username,full_name,role,is_active,created_at FROM users WHERE is_active=?"), (1,))
            else:
                cur.execute("SELECT id,email,username,full_name,role,is_active,created_at FROM users")
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
        finally:
            conn.close()
