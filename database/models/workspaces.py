"""database/models/workspaces.py — CRUD cho workspaces + workspace_members."""
import re
from datetime import datetime
from database.connection import managed_connection, get_db_connection, _adapt_sql, _is_postgres
from config.config import logger
from core.rbac import normalize_role


def _slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_-]+", "-", slug)
    return slug[:60]


class WorkspaceModel:

    @staticmethod
    def create(name: str, owner_id: int = None, plan: str = "free") -> int:
        slug_base = _slugify(name)
        slug = slug_base
        # Them suffix neu trung
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute(_adapt_sql("SELECT COUNT(*) FROM workspaces WHERE slug=?"), (slug,))
            if cur.fetchone()[0] > 0:
                slug = f"{slug_base}-{int(datetime.now().timestamp())}"
        finally:
            conn.close()

        now = datetime.now().isoformat()
        sql = _adapt_sql("""
            INSERT INTO workspaces (name, slug, owner_id, plan, is_active, created_at, updated_at)
            VALUES (?,?,?,?,1,?,?)
        """)
        logger.info(f"[AUDIT] Tao workspace: {name}")
        with managed_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (name, slug, owner_id, plan, now, now))
            if _is_postgres():
                cur.execute("SELECT lastval()")
                return cur.fetchone()[0]
            return cur.lastrowid

    @staticmethod
    def get_by_id(ws_id: int) -> dict:
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute(_adapt_sql("SELECT * FROM workspaces WHERE id=?"), (ws_id,))
            row = cur.fetchone()
            return dict(row) if row else {}
        finally:
            conn.close()

    @staticmethod
    def list_by_user(user_id: int) -> list:
        """Lay danh sach workspace ma user la thanh vien."""
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            sql = _adapt_sql("""
                SELECT w.*, wm.role as member_role
                FROM workspaces w
                JOIN workspace_members wm ON w.id = wm.workspace_id
                WHERE wm.user_id = ? AND w.is_active = 1
                ORDER BY w.created_at DESC
            """)
            cur.execute(sql, (user_id,))
            cols = [d[0] for d in cur.description]
            workspaces = [dict(zip(cols, row)) for row in cur.fetchall()]
            for workspace in workspaces:
                workspace["member_role"] = normalize_role(workspace.get("member_role"))
            return workspaces
        finally:
            conn.close()

    @staticmethod
    def add_member(workspace_id: int, user_id: int, role: str = "editor") -> bool:
        role = normalize_role(role)
        now = datetime.now().isoformat()
        sql = _adapt_sql("""
            INSERT INTO workspace_members (workspace_id, user_id, role, invited_at, joined_at)
            VALUES (?,?,?,?,?)
        """)
        try:
            with managed_connection() as conn:
                conn.cursor().execute(sql, (workspace_id, user_id, role, now, now))
            logger.info(f"[AUDIT] Them user {user_id} vao workspace {workspace_id} role={role}")
            return True
        except Exception as e:
            logger.warning(f"Khong the them member: {e}")
            return False

    @staticmethod
    def remove_member(workspace_id: int, user_id: int) -> bool:
        sql = _adapt_sql("DELETE FROM workspace_members WHERE workspace_id=? AND user_id=?")
        with managed_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (workspace_id, user_id))
            return cur.rowcount > 0

    @staticmethod
    def get_members(workspace_id: int) -> list:
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            sql = _adapt_sql("""
                SELECT u.id, u.email, u.username, u.full_name, u.avatar_url, wm.role, wm.joined_at
                FROM workspace_members wm
                JOIN users u ON u.id = wm.user_id
                WHERE wm.workspace_id = ?
                ORDER BY wm.joined_at
            """)
            cur.execute(sql, (workspace_id,))
            cols = [d[0] for d in cur.description]
            members = [dict(zip(cols, row)) for row in cur.fetchall()]
            for member in members:
                member["role"] = normalize_role(member.get("role"))
            return members
        finally:
            conn.close()

    @staticmethod
    def update_member_role(workspace_id: int, user_id: int, new_role: str) -> bool:
        """Cập nhật vai trò của một thành viên trong Workspace."""
        new_role = normalize_role(new_role)
        from config.config import logger
        sql = _adapt_sql("UPDATE workspace_members SET role=? WHERE workspace_id=? AND user_id=?")
        try:
            with managed_connection() as conn:
                cur = conn.cursor()
                cur.execute(sql, (new_role, workspace_id, user_id))
                changed = cur.rowcount > 0
            if changed:
                logger.info(f"[AUDIT] Doi role user {user_id} trong WS {workspace_id} -> {new_role}")
            return changed
        except Exception as e:
            from config.config import logger as _log
            _log.warning(f"update_member_role loi: {e}")
            return False

    @staticmethod
    def update(ws_id: int, **kwargs) -> bool:
        allowed = {"name", "plan", "max_users", "max_posts_per_month", "is_active"}
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        if not fields:
            return False
        fields["updated_at"] = datetime.now().isoformat()
        set_clause = ", ".join([f"{k}=?" for k in fields])
        sql = _adapt_sql(f"UPDATE workspaces SET {set_clause} WHERE id=?")
        with managed_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (*fields.values(), ws_id))
            return cur.rowcount > 0
