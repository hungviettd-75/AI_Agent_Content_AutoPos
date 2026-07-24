"""
database/models/thumbnail_analytics.py
=======================================
Model CRUD cho Thumbnail Analytics, Heatmap và Template Stats.
Module MỚI — Không sửa đổi analytics.py hiện có.
"""

import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from database.connection import managed_connection, get_db_connection, _adapt_sql, _is_postgres
from config.config import logger


def _as_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value: Any, default: int = 0) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return default


class ThumbnailAnalyticsModel:
    """CRUD và query nâng cao cho thumbnail_analytics, thumbnail_heatmap, thumbnail_template_stats."""

    @staticmethod
    def ensure_tables():
        """Tao bang thumbnail analytics dung cu phap cho SQLite va PostgreSQL."""
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            id_type = "SERIAL PRIMARY KEY" if _is_postgres() else "INTEGER PRIMARY KEY AUTOINCREMENT"
            ts_default = "TIMESTAMPTZ DEFAULT NOW()" if _is_postgres() else "TEXT DEFAULT (datetime('now'))"
            real_type = "NUMERIC(12,4)" if _is_postgres() else "REAL"
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS thumbnail_analytics (
                    id                  {id_type},
                    workspace_id        INTEGER NOT NULL,
                    asset_id            INTEGER NOT NULL,
                    post_id             INTEGER,
                    campaign_id         INTEGER,
                    ab_test_id          INTEGER,
                    ab_variant_id       INTEGER,
                    platform            TEXT NOT NULL,
                    template_id         TEXT,
                    brand_status        TEXT DEFAULT 'unknown',
                    aspect_ratio        TEXT,
                    style_tag           TEXT,
                    thumbnail_url       TEXT,
                    impressions         INTEGER DEFAULT 0,
                    reach               INTEGER DEFAULT 0,
                    clicks              INTEGER DEFAULT 0,
                    thumbnail_clicks    INTEGER DEFAULT 0,
                    saves               INTEGER DEFAULT 0,
                    shares              INTEGER DEFAULT 0,
                    comments            INTEGER DEFAULT 0,
                    likes               INTEGER DEFAULT 0,
                    video_plays         INTEGER DEFAULT 0,
                    link_clicks         INTEGER DEFAULT 0,
                    ctr                 {real_type} DEFAULT 0.0,
                    engagement_rate     {real_type} DEFAULT 0.0,
                    save_rate           {real_type} DEFAULT 0.0,
                    share_rate          {real_type} DEFAULT 0.0,
                    virality_score      {real_type} DEFAULT 0.0,
                    thumbnail_score     {real_type} DEFAULT 0.0,
                    score_breakdown     TEXT,
                    period_start        TEXT NOT NULL,
                    period_end          TEXT NOT NULL,
                    granularity         TEXT DEFAULT 'daily',
                    collected_at        {ts_default},
                    source              TEXT DEFAULT 'manual'
                )
            """)
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS thumbnail_heatmap (
                    id               {id_type},
                    workspace_id     INTEGER NOT NULL,
                    asset_id         INTEGER NOT NULL,
                    x_norm           {real_type} NOT NULL,
                    y_norm           {real_type} NOT NULL,
                    zone_label       TEXT,
                    attention_score  {real_type} DEFAULT 0.0,
                    interaction_type TEXT DEFAULT 'view',
                    device_type      TEXT DEFAULT 'mobile',
                    session_count    INTEGER DEFAULT 1,
                    recorded_at      {ts_default}
                )
            """)
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS thumbnail_template_stats (
                    id                  {id_type},
                    workspace_id        INTEGER NOT NULL,
                    template_id         TEXT NOT NULL,
                    template_name       TEXT,
                    template_category   TEXT,
                    platform            TEXT,
                    usage_count         INTEGER DEFAULT 0,
                    avg_ctr             {real_type} DEFAULT 0.0,
                    avg_engagement      {real_type} DEFAULT 0.0,
                    avg_reach           INTEGER DEFAULT 0,
                    avg_saves           {real_type} DEFAULT 0.0,
                    avg_shares          {real_type} DEFAULT 0.0,
                    total_impressions   INTEGER DEFAULT 0,
                    win_rate            {real_type} DEFAULT 0.0,
                    rank_score          {real_type} DEFAULT 0.0,
                    rank_position       INTEGER DEFAULT 0,
                    last_used_at        TEXT,
                    updated_at          {ts_default},
                    UNIQUE (workspace_id, template_id, platform)
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_thumb_analytics_workspace ON thumbnail_analytics(workspace_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_thumb_analytics_asset ON thumbnail_analytics(asset_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_heatmap_asset ON thumbnail_heatmap(asset_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_tmpl_stats_workspace ON thumbnail_template_stats(workspace_id)")
            conn.commit()
            logger.info("[ThumbnailAnalytics] ensured thumbnail analytics tables.")
        except Exception:
            conn.rollback()
            logger.exception("[ThumbnailAnalytics] Could not ensure thumbnail analytics tables")
            raise
        finally:
            conn.close()

    @staticmethod
    def record(workspace_id: int, asset_id: int, platform: str,
               period_start: str, period_end: str,
               impressions: int = 0, reach: int = 0,
               clicks: int = 0, saves: int = 0,
               shares: int = 0, likes: int = 0,
               comments: int = 0, post_id: int = None,
               ab_test_id: int = None, ab_variant_id: int = None,
               template_id: str = None, brand_status: str = 'unknown',
               aspect_ratio: str = None, style_tag: str = None,
               thumbnail_url: str = None, source: str = 'manual') -> int:
        """Ghi nhận một bản ghi phân tích thumbnail."""
        ctr = (clicks / impressions * 100) if impressions > 0 else 0.0
        engagement = (likes + comments + shares + saves) / max(reach, 1) * 100
        save_rate  = saves / max(reach, 1) * 100
        share_rate = shares / max(reach, 1) * 100
        virality   = (shares * 3 + saves * 2 + comments) / max(reach, 1) * 100

        # Tính điểm score
        ctr_pts = min(ctr / 5.0, 1.0) * 30
        eng_pts = min(engagement / 10.0, 1.0) * 25
        reach_pts = min(reach / 1000.0, 1.0) * 20
        save_pts = min(save_rate / 3.0, 1.0) * 15
        share_pts = min(share_rate / 2.0, 1.0) * 10
        score = ctr_pts + eng_pts + reach_pts + save_pts + share_pts

        ThumbnailAnalyticsModel.ensure_tables()

        score_breakdown = json.dumps({
            'ctr_pts': round(ctr_pts, 2),
            'eng_pts': round(eng_pts, 2),
            'reach_pts': round(reach_pts, 2),
            'save_pts': round(save_pts, 2),
            'share_pts': round(share_pts, 2),
        })

        sql = _adapt_sql("""
            INSERT INTO thumbnail_analytics (
                workspace_id, asset_id, post_id, ab_test_id, ab_variant_id,
                platform, template_id, brand_status, aspect_ratio, style_tag, thumbnail_url,
                impressions, reach, clicks, saves, shares, likes, comments,
                ctr, engagement_rate, save_rate, share_rate, virality_score,
                thumbnail_score, score_breakdown, period_start, period_end, source, collected_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """)
        now = datetime.now().isoformat()
        with managed_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (
                workspace_id, asset_id, post_id, ab_test_id, ab_variant_id,
                platform, template_id, brand_status, aspect_ratio, style_tag, thumbnail_url,
                impressions, reach, clicks, saves, shares, likes, comments,
                round(ctr, 4), round(engagement, 4), round(save_rate, 4),
                round(share_rate, 4), round(virality, 4),
                round(score, 2), score_breakdown, period_start, period_end, source, now
            ))
            if _is_postgres():
                cur.execute("SELECT lastval()")
                return cur.fetchone()[0]
            return cur.lastrowid

    @staticmethod
    def get_by_asset(asset_id: int, workspace_id: int, days: int = 30) -> list:
        ThumbnailAnalyticsModel.ensure_tables()
        since = (datetime.now() - timedelta(days=days)).isoformat()
        sql = _adapt_sql("""
            SELECT * FROM thumbnail_analytics
            WHERE asset_id=? AND workspace_id=? AND period_start >= ?
            ORDER BY period_start DESC
        """)
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute(sql, (asset_id, workspace_id, since))
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def get_workspace_summary(workspace_id: int, days: int = 30) -> dict:
        ThumbnailAnalyticsModel.ensure_tables()
        since = (datetime.now() - timedelta(days=days)).isoformat()
        sql = _adapt_sql("""
            SELECT
                COUNT(DISTINCT asset_id)        AS total_thumbnails,
                COALESCE(SUM(impressions), 0)   AS total_impressions,
                COALESCE(SUM(reach), 0)         AS total_reach,
                COALESCE(SUM(clicks), 0)        AS total_clicks,
                COALESCE(AVG(ctr), 0)           AS avg_ctr,
                COALESCE(AVG(engagement_rate),0) AS avg_engagement,
                COALESCE(AVG(save_rate), 0)     AS avg_save_rate,
                COALESCE(AVG(share_rate), 0)    AS avg_share_rate,
                COALESCE(AVG(thumbnail_score),0) AS avg_score,
                COALESCE(MAX(thumbnail_score),0) AS max_score
            FROM thumbnail_analytics
            WHERE workspace_id=? AND period_start >= ?
        """)
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute(sql, (workspace_id, since))
            cols = [d[0] for d in cur.description]
            row = cur.fetchone()
            res = dict(zip(cols, row)) if row else {}

            for key in ("total_thumbnails", "total_impressions", "total_reach", "total_clicks"):
                res[key] = _as_int(res.get(key))
            for key in ("avg_ctr", "avg_engagement", "avg_save_rate", "avg_share_rate", "avg_score", "max_score"):
                res[key] = _as_float(res.get(key))

            # Delta gia lap cho UI. PostgreSQL returns NUMERIC averages as Decimal,
            # so keep every derived metric as a plain float for Streamlit formatting.
            res["new_this_week"] = res["total_thumbnails"]
            res["ctr_delta"] = 0.15
            res["score_delta"] = 2.4
            res["max_ctr"] = res["avg_ctr"] * 1.5
            return res
        finally:
            conn.close()

    @staticmethod
    def get_platform_breakdown(workspace_id: int, days: int = 30) -> list:
        ThumbnailAnalyticsModel.ensure_tables()
        since = (datetime.now() - timedelta(days=days)).isoformat()
        sql = _adapt_sql("""
            SELECT
                platform,
                COUNT(DISTINCT asset_id) AS thumbnail_count,
                AVG(ctr)                 AS avg_ctr,
                AVG(engagement_rate)     AS avg_engagement,
                AVG(thumbnail_score)     AS avg_score,
                SUM(impressions)         AS total_impressions,
                SUM(reach)               AS total_reach
            FROM thumbnail_analytics
            WHERE workspace_id=? AND period_start >= ?
            GROUP BY platform
            ORDER BY avg_score DESC
        """)
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute(sql, (workspace_id, since))
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def get_top_thumbnails(workspace_id: int, limit: int = 10, platform: str = None, days: int = 30) -> list:
        ThumbnailAnalyticsModel.ensure_tables()
        since = (datetime.now() - timedelta(days=days)).isoformat()
        q = """
            SELECT ta.*, a.name, a.url
            FROM thumbnail_analytics ta
            LEFT JOIN assets a ON a.id = ta.asset_id
            WHERE ta.workspace_id=? AND ta.period_start >= ?
        """
        params = [workspace_id, since]
        if platform:
            q += " AND ta.platform=?"
            params.append(platform)
        q += " ORDER BY ta.thumbnail_score DESC LIMIT ?"
        params.append(limit)

        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute(_adapt_sql(q), params)
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]
        finally:
            conn.close()

    # --- Heatmap Helpers ---
    @staticmethod
    def record_heatmap_click(workspace_id: int, asset_id: int, x_norm: float, y_norm: float, zone_label: str, attention_score: float = 0.5):
        ThumbnailAnalyticsModel.ensure_tables()
        sql = _adapt_sql("""
            INSERT INTO thumbnail_heatmap (workspace_id, asset_id, x_norm, y_norm, zone_label, attention_score, recorded_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """)
        now = datetime.now().isoformat()
        with managed_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (workspace_id, asset_id, x_norm, y_norm, zone_label, attention_score, now))
            return cur.rowcount > 0

    @staticmethod
    def get_heatmap_by_asset(asset_id: int, workspace_id: int) -> list:
        ThumbnailAnalyticsModel.ensure_tables()
        sql = _adapt_sql("SELECT * FROM thumbnail_heatmap WHERE asset_id=? AND workspace_id=?")
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute(sql, (asset_id, workspace_id))
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]
        finally:
            conn.close()

    # --- Template stats ---
    @staticmethod
    def increment_template_usage(workspace_id: int, template_id: str, platform: str, template_name: str, template_category: str):
        ThumbnailAnalyticsModel.ensure_tables()
        sql_check = _adapt_sql("SELECT id, usage_count FROM thumbnail_template_stats WHERE workspace_id=? AND template_id=? AND platform=?")
        conn = get_db_connection()
        row = None
        try:
            cur = conn.cursor()
            cur.execute(sql_check, (workspace_id, template_id, platform))
            row = cur.fetchone()
        finally:
            conn.close()
        
        now = datetime.now().isoformat()
        if row:
            sql_update = _adapt_sql("UPDATE thumbnail_template_stats SET usage_count=usage_count+1, last_used_at=?, updated_at=? WHERE id=? AND workspace_id=?")
            with managed_connection() as conn:
                cur = conn.cursor()
                cur.execute(sql_update, (now, now, row[0], workspace_id))
                return True
        else:
            sql_insert = _adapt_sql("""
                INSERT INTO thumbnail_template_stats (workspace_id, template_id, template_name, template_category, platform, usage_count, last_used_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 1, ?, ?)
            """)
            with managed_connection() as conn:
                cur = conn.cursor()
                cur.execute(sql_insert, (workspace_id, template_id, template_name, template_category, platform, now, now))
                return True

    @staticmethod
    def list_templates(workspace_id: int) -> list:
        ThumbnailAnalyticsModel.ensure_tables()
        sql = _adapt_sql("SELECT * FROM thumbnail_template_stats WHERE workspace_id=? ORDER BY rank_score DESC")
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute(sql, (workspace_id,))
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]
        finally:
            conn.close()
