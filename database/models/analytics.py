"""database/models/analytics.py — CRUD cho bang analytics (hieu suat bai dang)."""
import json
from datetime import datetime
from database.connection import managed_connection, get_db_connection, _adapt_sql, _is_postgres
from config.config import logger

class AnalyticsModel:

    @staticmethod
    def upsert(post_id: int, platform: str, metric_date: str,
               impressions: int = 0, reach: int = 0, likes: int = 0,
               comments: int = 0, shares: int = 0, saves: int = 0,
               clicks: int = 0, link_clicks: int = 0,
               raw_data: dict = None, workspace_id: int = None) -> bool:
        """Ghi nhận hoặc cập nhật số liệu thống kê hiệu quả bài đăng của ngày cụ thể."""
        now = datetime.now().isoformat()
        
        # Tính toán rates cơ bản
        engagement_rate = 0.0
        interactions = likes + comments + shares + saves + clicks
        if reach > 0:
            engagement_rate = round((interactions / reach) * 100, 4)
        elif impressions > 0:
            engagement_rate = round((interactions / impressions) * 100, 4)
            
        reach_rate = 0.0
        if impressions > 0:
            reach_rate = round((reach / impressions) * 100, 4)

        raw_str = json.dumps(raw_data or {}, ensure_ascii=False)

        # Chế độ UPSERT cho cả SQLite và PostgreSQL
        if _is_postgres():
            sql = """
                INSERT INTO analytics (
                    post_id, workspace_id, platform, metric_date, impressions, reach,
                    likes, comments, shares, saves, clicks, link_clicks,
                    engagement_rate, reach_rate, raw_data, synced_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (post_id, platform, metric_date) DO UPDATE SET
                    impressions = EXCLUDED.impressions,
                    reach = EXCLUDED.reach,
                    likes = EXCLUDED.likes,
                    comments = EXCLUDED.comments,
                    shares = EXCLUDED.shares,
                    saves = EXCLUDED.saves,
                    clicks = EXCLUDED.clicks,
                    link_clicks = EXCLUDED.link_clicks,
                    engagement_rate = EXCLUDED.engagement_rate,
                    reach_rate = EXCLUDED.reach_rate,
                    raw_data = EXCLUDED.raw_data,
                    synced_at = EXCLUDED.synced_at
            """
        else:
            sql = """
                INSERT INTO analytics (
                    post_id, workspace_id, platform, metric_date, impressions, reach,
                    likes, comments, shares, saves, clicks, link_clicks,
                    engagement_rate, reach_rate, raw_data, synced_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(post_id, platform, metric_date) DO UPDATE SET
                    impressions = excluded.impressions,
                    reach = excluded.reach,
                    likes = excluded.likes,
                    comments = excluded.comments,
                    shares = excluded.shares,
                    saves = excluded.saves,
                    clicks = excluded.clicks,
                    link_clicks = excluded.link_clicks,
                    engagement_rate = excluded.engagement_rate,
                    reach_rate = excluded.reach_rate,
                    raw_data = excluded.raw_data,
                    synced_at = excluded.synced_at
            """
            
        sql = _adapt_sql(sql)
        logger.info(f"[AUDIT] Upsert analytics cho post_id={post_id} date={metric_date}")
        with managed_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (
                post_id, workspace_id, platform, metric_date, impressions, reach,
                likes, comments, shares, saves, clicks, link_clicks,
                engagement_rate, reach_rate, raw_str, now
            ))
            return cur.rowcount > 0

    @staticmethod
    def get_by_post(post_id: int, workspace_id: int = None) -> list:
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            if workspace_id is not None:
                cur.execute(
                    _adapt_sql("SELECT * FROM analytics WHERE post_id=? AND workspace_id=? ORDER BY metric_date ASC"),
                    (post_id, workspace_id)
                )
            else:
                cur.execute(
                    _adapt_sql("SELECT * FROM analytics WHERE post_id=? ORDER BY metric_date ASC"),
                    (post_id,)
                )
            cols = [d[0] for d in cur.description]
            rows = []
            for row in cur.fetchall():
                data = dict(zip(cols, row))
                try:
                    data["raw_data"] = json.loads(data.get("raw_data") or "{}")
                except Exception:
                    pass
                rows.append(data)
            return rows
        finally:
            conn.close()

    @staticmethod
    def get_summary_by_workspace(workspace_id: int, start_date: str = None, end_date: str = None) -> dict:
        """Tính tổng số tương tác, reach, impressions trong thời gian qua."""
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            query = """
                SELECT 
                    SUM(impressions) as total_impressions,
                    SUM(reach) as total_reach,
                    SUM(likes) as total_likes,
                    SUM(comments) as total_comments,
                    SUM(shares) as total_shares,
                    SUM(saves) as total_saves,
                    SUM(clicks) as total_clicks
                FROM analytics WHERE workspace_id = ?
            """
            params = [workspace_id]
            if start_date:
                query += _adapt_sql(" AND metric_date >= ?")
                params.append(start_date)
            if end_date:
                query += _adapt_sql(" AND metric_date <= ?")
                params.append(end_date)
                
            cur.execute(query, params)
            row = cur.fetchone()
            if not row or row[0] is None:
                return {
                    "impressions": 0, "reach": 0, "likes": 0, "comments": 0,
                    "shares": 0, "saves": 0, "clicks": 0
                }
            return {
                "impressions": row[0],
                "reach": row[1],
                "likes": row[2],
                "comments": row[3],
                "shares": row[4],
                "saves": row[5],
                "clicks": row[6]
            }
        finally:
            conn.close()
