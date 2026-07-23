"""core/audit_logger.py
=======================
Module ghi Audit Log tập trung cho mọi hành động quan trọng trong hệ thống.
Mỗi bản ghi lưu: ai làm (user_id, email), lúc nào (timestamp), làm gì (action, description).
"""

import json
from datetime import datetime
from database.connection import managed_connection, _adapt_sql, _is_postgres
from config.config import logger


# -----------------------------------------------------------------------
# Hằng số hành động (action constants)
# -----------------------------------------------------------------------
class AuditAction:
    # Auth
    LOGIN             = "LOGIN"
    LOGOUT            = "LOGOUT"
    REGISTER          = "REGISTER"
    LOGIN_FAILED      = "LOGIN_FAILED"

    # Bài viết
    CREATE_POST       = "CREATE_POST"
    AUTO_POST         = "AUTO_POST"
    DELETE_POST       = "DELETE_POST"

    # Kế hoạch tuần
    CREATE_PLAN       = "CREATE_PLAN"

    # AI Knowledge
    CREATE_KNOWLEDGE  = "CREATE_KNOWLEDGE"

    # Workspace
    CREATE_WORKSPACE  = "CREATE_WORKSPACE"
    ADD_MEMBER        = "ADD_MEMBER"
    REMOVE_MEMBER     = "REMOVE_MEMBER"
    CHANGE_ROLE       = "CHANGE_ROLE"

    # Hệ thống
    SYSTEM            = "SYSTEM"


# -----------------------------------------------------------------------
# Hàm ghi log chính
# -----------------------------------------------------------------------
def log_action(
    action: str,
    user_id: int | None = None,
    user_email: str = "",
    workspace_id: int | None = None,
    entity_type: str = "",
    entity_id: int | str | None = None,
    description: str = "",
    old_value: dict | str | None = None,
    new_value: dict | str | None = None,
    ip_address: str = "",
) -> bool:
    """
    Ghi một bản ghi audit log vào cơ sở dữ liệu.

    Args:
        action      : Loại hành động (dùng AuditAction constants)
        user_id     : ID người thực hiện (None = hệ thống)
        user_email  : Email người thực hiện
        workspace_id: ID workspace liên quan (None nếu toàn cục)
        entity_type : Loại đối tượng bị ảnh hưởng (post, member, workspace, auth...)
        entity_id   : ID đối tượng bị ảnh hưởng
        description : Mô tả chi tiết bằng tiếng Việt
        old_value   : Giá trị cũ trước khi thay đổi (dict hoặc string)
        new_value   : Giá trị mới sau khi thay đổi (dict hoặc string)
        ip_address  : Địa chỉ IP (optional)

    Returns:
        True nếu ghi thành công, False nếu có lỗi.
    """
    try:
        now = datetime.now().isoformat()

        def _serialize(val):
            if val is None:
                return None
            if isinstance(val, dict):
                return json.dumps(val, ensure_ascii=False)
            return str(val)

        sql = _adapt_sql("""
            INSERT INTO audit_logs
                (timestamp, user_id, user_email, workspace_id,
                 action, entity_type, entity_id,
                 description, old_value, new_value, ip_address)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """)

        with managed_connection() as conn:
            conn.cursor().execute(sql, (
                now,
                user_id,
                user_email or "",
                workspace_id,
                action,
                entity_type or "",
                str(entity_id) if entity_id is not None else None,
                description or "",
                _serialize(old_value),
                _serialize(new_value),
                ip_address or "",
            ))

        logger.debug(f"[AUDIT] {action} | user={user_email or user_id} | {description[:80]}")
        return True

    except Exception as e:
        # Audit log KHÔNG được làm crash ứng dụng chính
        logger.warning(f"[AUDIT WARNING] Không thể ghi audit log: {e}")
        return False


# -----------------------------------------------------------------------
# Shortcut helpers — gọi gọn hơn ở các điểm tích hợp
# -----------------------------------------------------------------------
def log_login(user_id: int, user_email: str):
    log_action(AuditAction.LOGIN, user_id=user_id, user_email=user_email,
               entity_type="auth", description=f"Đăng nhập thành công: {user_email}")

def log_login_failed(user_email: str):
    log_action(AuditAction.LOGIN_FAILED, user_email=user_email,
               entity_type="auth", description=f"Đăng nhập thất bại: {user_email}")

def log_logout(user_id: int, user_email: str):
    log_action(AuditAction.LOGOUT, user_id=user_id, user_email=user_email,
               entity_type="auth", description=f"Đăng xuất: {user_email}")

def log_register(user_id: int, user_email: str, role: str):
    log_action(AuditAction.REGISTER, user_id=user_id, user_email=user_email,
               entity_type="auth",
               description=f"Đăng ký tài khoản mới: {user_email} với vai trò {role.upper()}")

def log_create_post(user_id: int, user_email: str, workspace_id: int,
                    platform: str, topic: str, post_id=None):
    log_action(AuditAction.CREATE_POST, user_id=user_id, user_email=user_email,
               workspace_id=workspace_id, entity_type="post", entity_id=post_id,
               description=f"Tạo bài viết [{platform}] - Chủ đề: {topic[:80]}")

def log_auto_post(user_id: int, user_email: str, workspace_id: int,
                  platform: str, topic: str, status: str):
    log_action(AuditAction.AUTO_POST, user_id=user_id, user_email=user_email,
               workspace_id=workspace_id, entity_type="post",
               description=f"Tự động đăng [{platform}] - {topic[:60]} → {status}")

def log_create_plan(user_id: int, user_email: str, workspace_id: int, topic: str):
    log_action(AuditAction.CREATE_PLAN, user_id=user_id, user_email=user_email,
               workspace_id=workspace_id, entity_type="plan",
               description=f"Tạo kế hoạch tuần - Chủ đề: {topic[:80]}")

def log_create_workspace(user_id: int, user_email: str, ws_id: int, ws_name: str):
    log_action(AuditAction.CREATE_WORKSPACE, user_id=user_id, user_email=user_email,
               workspace_id=ws_id, entity_type="workspace", entity_id=ws_id,
               description=f"Tạo Workspace mới: '{ws_name}'")

def log_add_member(actor_id: int, actor_email: str, workspace_id: int,
                   target_email: str, role: str):
    log_action(AuditAction.ADD_MEMBER, user_id=actor_id, user_email=actor_email,
               workspace_id=workspace_id, entity_type="member",
               description=f"Thêm thành viên '{target_email}' vào Workspace với vai trò {role.upper()}",
               new_value={"email": target_email, "role": role})

def log_remove_member(actor_id: int, actor_email: str, workspace_id: int,
                      target_email: str):
    log_action(AuditAction.REMOVE_MEMBER, user_id=actor_id, user_email=actor_email,
               workspace_id=workspace_id, entity_type="member",
               description=f"Xóa thành viên '{target_email}' khỏi Workspace",
               old_value={"email": target_email})

def log_change_role(actor_id: int, actor_email: str, workspace_id: int,
                    target_email: str, old_role: str, new_role: str):
    log_action(AuditAction.CHANGE_ROLE, user_id=actor_id, user_email=actor_email,
               workspace_id=workspace_id, entity_type="member",
               description=f"Đổi vai trò '{target_email}': {old_role.upper()} → {new_role.upper()}",
               old_value={"email": target_email, "role": old_role},
               new_value={"email": target_email, "role": new_role})
