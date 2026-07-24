"""database/repositories/audit_repository.py
=============================================
Repository truy vấn bảng audit_logs.
Không chứa SQL trực tiếp trong UI — tuân thủ Repository Pattern.
"""

import json
import pandas as pd
from datetime import datetime
from database.connection import get_db_connection, _adapt_sql, _is_postgres
from config.config import logger


class AuditRepository:

    @staticmethod
    def _require_workspace(workspace_id: int | None) -> None:
        if workspace_id is None:
            raise ValueError("workspace_id is required")

    @staticmethod
    def get_logs(
        workspace_id: int | None = None,
        user_email: str | None = None,
        action: str | None = None,
        entity_type: str | None = None,
        limit: int = 200,
    ) -> pd.DataFrame:
        """
        Lấy danh sách audit log có lọc theo workspace / email / action / entity_type.
        Trả về DataFrame sắp xếp mới nhất trước.
        """
        AuditRepository._require_workspace(workspace_id)
        sql = """
            SELECT
                id,
                timestamp,
                user_email,
                action,
                entity_type,
                entity_id,
                description,
                old_value,
                new_value,
                workspace_id,
                ip_address
            FROM audit_logs
            WHERE 1=1
        """
        params = []

        sql += _adapt_sql(" AND workspace_id = ?")
        params.append(workspace_id)

        if user_email:
            sql += _adapt_sql(" AND user_email LIKE ?")
            params.append(f"%{user_email}%")

        if action:
            sql += _adapt_sql(" AND action = ?")
            params.append(action)

        if entity_type:
            sql += _adapt_sql(" AND entity_type = ?")
            params.append(entity_type)

        sql += " ORDER BY id DESC"
        sql += _adapt_sql(" LIMIT ?")
        params.append(limit)

        conn = get_db_connection()
        try:
            df = pd.read_sql_query(sql, conn, params=params)
            return df
        except Exception as e:
            logger.error(f"AuditRepository.get_logs lỗi: {e}", exc_info=True)
            return pd.DataFrame()
        finally:
            conn.close()

    @staticmethod
    def get_summary(workspace_id: int | None = None) -> dict:
        """
        Thống kê nhanh: tổng log, số hành động theo loại.
        """
        AuditRepository._require_workspace(workspace_id)
        sql = "SELECT action, COUNT(*) as cnt FROM audit_logs WHERE 1=1"
        sql += _adapt_sql(" AND workspace_id = ?")
        params = [workspace_id]
        sql += " GROUP BY action ORDER BY cnt DESC"

        conn = get_db_connection()
        try:
            df = pd.read_sql_query(sql, conn, params=params)
            return df.set_index("action")["cnt"].to_dict() if not df.empty else {}
        except Exception as e:
            logger.error(f"AuditRepository.get_summary lỗi: {e}")
            return {}
        finally:
            conn.close()

    @staticmethod
    def get_recent_by_user(user_id: int, limit: int = 50) -> pd.DataFrame:
        """Lấy log gần đây của một user cụ thể."""
        sql = _adapt_sql("""
            SELECT timestamp, action, description, workspace_id
            FROM audit_logs
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
        """)
        conn = get_db_connection()
        try:
            df = pd.read_sql_query(sql, conn, params=[user_id, limit])
            return df
        except Exception as e:
            logger.error(f"AuditRepository.get_recent_by_user lỗi: {e}")
            return pd.DataFrame()
        finally:
            conn.close()
