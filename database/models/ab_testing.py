"""database/models/ab_testing.py — DAO cho hệ thống A/B Testing."""
from datetime import datetime
from database.connection import managed_connection, get_db_connection, _adapt_sql, _is_postgres
from config.config import logger


class ABTestModel:
    """Quản lý A/B Tests: tạo test, thêm variant, ghi kết quả, tuyên bố winner."""

    VALID_TEST_TYPES = {"prompt", "headline", "cta", "full_post", "subject_line", "angle"}
    VALID_STATUS     = {"draft", "running", "paused", "completed", "archived"}

    # ── INIT: Tự tạo bảng nếu chưa có ─────────────────────────────
    @staticmethod
    def ensure_tables():
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            if _is_postgres():
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS ab_tests (
                        id           SERIAL PRIMARY KEY,
                        workspace_id INTEGER REFERENCES workspaces(id) ON DELETE CASCADE,
                        name         TEXT NOT NULL,
                        test_type    TEXT NOT NULL DEFAULT 'prompt',
                        topic        TEXT,
                        platform     TEXT,
                        description  TEXT,
                        status       TEXT NOT NULL DEFAULT 'draft',
                        winner_id    INTEGER,
                        created_by   INTEGER,
                        created_at   TIMESTAMPTZ DEFAULT NOW(),
                        started_at   TIMESTAMPTZ,
                        completed_at TIMESTAMPTZ
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS ab_variants (
                        id           SERIAL PRIMARY KEY,
                        test_id      INTEGER NOT NULL REFERENCES ab_tests(id) ON DELETE CASCADE,
                        label        TEXT NOT NULL,
                        variant_type TEXT NOT NULL DEFAULT 'A',
                        content      TEXT NOT NULL,
                        prompt_used  TEXT,
                        impressions  INTEGER DEFAULT 0,
                        clicks       INTEGER DEFAULT 0,
                        conversions  INTEGER DEFAULT 0,
                        leads        INTEGER DEFAULT 0,
                        revenue      INTEGER DEFAULT 0,
                        score        NUMERIC(12,4) DEFAULT 0,
                        notes        TEXT,
                        created_at   TIMESTAMPTZ DEFAULT NOW()
                    )
                """)
            else:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS ab_tests (
                        id           INTEGER PRIMARY KEY AUTOINCREMENT,
                        workspace_id INTEGER,
                        name         TEXT NOT NULL,
                        test_type    TEXT NOT NULL DEFAULT 'prompt',
                        topic        TEXT,
                        platform     TEXT,
                        description  TEXT,
                        status       TEXT NOT NULL DEFAULT 'draft',
                        winner_id    INTEGER,
                        created_by   INTEGER,
                        created_at   TEXT DEFAULT (datetime('now')),
                        started_at   TEXT,
                        completed_at TEXT
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS ab_variants (
                        id           INTEGER PRIMARY KEY AUTOINCREMENT,
                        test_id      INTEGER NOT NULL,
                        label        TEXT NOT NULL,
                        variant_type TEXT NOT NULL DEFAULT 'A',
                        content      TEXT NOT NULL,
                        prompt_used  TEXT,
                        impressions  INTEGER DEFAULT 0,
                        clicks       INTEGER DEFAULT 0,
                        conversions  INTEGER DEFAULT 0,
                        leads        INTEGER DEFAULT 0,
                        revenue      INTEGER DEFAULT 0,
                        score        REAL DEFAULT 0,
                        notes        TEXT,
                        created_at   TEXT DEFAULT (datetime('now'))
                    )
                """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_ab_variants_test ON ab_variants(test_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_ab_tests_workspace ON ab_tests(workspace_id)")
            conn.commit()
        except Exception:
            conn.rollback()
            logger.exception("[AB_TESTING] Could not ensure A/B testing tables")
            raise
        finally:
            conn.close()

    # --- CREATE TEST ────────────────────────────────────────────────
    @staticmethod
    def create_test(workspace_id: int, name: str, test_type: str = "prompt",
                    topic: str = "", platform: str = "", description: str = "",
                    created_by: int = None) -> int:
        ABTestModel.ensure_tables()
        sql = _adapt_sql("""
            INSERT INTO ab_tests (workspace_id, name, test_type, topic, platform, description, status, created_at)
            VALUES (?,?,?,?,?,?,'draft',?)
        """)
        now = datetime.now().isoformat()
        with managed_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (workspace_id, name, test_type, topic, platform, description, now))
            if _is_postgres():
                cur.execute("SELECT lastval()")
                return cur.fetchone()[0]
            return cur.lastrowid

    # ── ADD VARIANT ────────────────────────────────────────────────
    @staticmethod
    def add_variant(test_id: int, label: str, content: str,
                    variant_type: str = "A", prompt_used: str = "") -> int:
        ABTestModel.ensure_tables()
        sql = _adapt_sql("""
            INSERT INTO ab_variants (test_id, label, variant_type, content, prompt_used, created_at)
            VALUES (?,?,?,?,?,?)
        """)
        now = datetime.now().isoformat()
        with managed_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (test_id, label, variant_type, content, prompt_used, now))
            if _is_postgres():
                cur.execute("SELECT lastval()")
                return cur.fetchone()[0]
            return cur.lastrowid

    # ── UPDATE VARIANT METRICS ──────────────────────────────────────
    @staticmethod
    def update_variant_metrics(variant_id: int, impressions: int = 0,
                               clicks: int = 0, conversions: int = 0,
                               leads: int = 0, revenue: int = 0, notes: str = "") -> bool:
        ABTestModel.ensure_tables()
        ctr   = (clicks / impressions * 100) if impressions > 0 else 0
        cvr   = (conversions / clicks * 100) if clicks > 0 else 0
        score = (ctr * 0.3) + (cvr * 0.5) + (leads * 2) + (revenue / 1_000_000)
        sql = _adapt_sql("""
            UPDATE ab_variants SET impressions=?, clicks=?, conversions=?,
            leads=?, revenue=?, score=?, notes=? WHERE id=?
        """)
        with managed_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (impressions, clicks, conversions, leads, revenue, score, notes, variant_id))
            return cur.rowcount > 0

    # ── UPDATE TEST STATUS ─────────────────────────────────────────
    @staticmethod
    def update_test_status(test_id: int, status: str, winner_id: int = None) -> bool:
        ABTestModel.ensure_tables()
        now = datetime.now().isoformat()
        if status == "running":
            sql = _adapt_sql("UPDATE ab_tests SET status=?, started_at=? WHERE id=?")
            params = (status, now, test_id)
        elif status == "completed":
            sql = _adapt_sql("UPDATE ab_tests SET status=?, winner_id=?, completed_at=? WHERE id=?")
            params = (status, winner_id, now, test_id)
        else:
            sql = _adapt_sql("UPDATE ab_tests SET status=? WHERE id=?")
            params = (status, test_id)
        with managed_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            return cur.rowcount > 0

    # ── GET TEST ──────────────────────────────────────────────────
    @staticmethod
    def get_test(test_id: int) -> dict:
        ABTestModel.ensure_tables()
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute(_adapt_sql("SELECT * FROM ab_tests WHERE id=?"), (test_id,))
            cols = [d[0] for d in cur.description]
            row  = cur.fetchone()
            return dict(zip(cols, row)) if row else {}
        finally:
            conn.close()

    # ── LIST TESTS ────────────────────────────────────────────────
    @staticmethod
    def list_tests(workspace_id: int, status: str = None, limit: int = 50) -> list:
        ABTestModel.ensure_tables()
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            q = "SELECT * FROM ab_tests WHERE workspace_id=?"
            p = [workspace_id]
            if status:
                q += _adapt_sql(" AND status=?")
                p.append(status)
            q += " ORDER BY created_at DESC"
            if limit:
                q += _adapt_sql(" LIMIT ?")
                p.append(limit)
            cur.execute(_adapt_sql(q), p)
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]
        finally:
            conn.close()

    # ── GET VARIANTS ──────────────────────────────────────────────
    @staticmethod
    def get_variants(test_id: int) -> list:
        ABTestModel.ensure_tables()
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                _adapt_sql("SELECT * FROM ab_variants WHERE test_id=? ORDER BY variant_type ASC"),
                (test_id,)
            )
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]
        finally:
            conn.close()

    # ── DELETE TEST + VARIANTS ────────────────────────────────────
    @staticmethod
    def delete_test(test_id: int) -> bool:
        ABTestModel.ensure_tables()
        with managed_connection() as conn:
            cur = conn.cursor()
            cur.execute(_adapt_sql("DELETE FROM ab_variants WHERE test_id=?"), (test_id,))
            cur.execute(_adapt_sql("DELETE FROM ab_tests WHERE id=?"), (test_id,))
            return cur.rowcount > 0

    # ── STATS ─────────────────────────────────────────────────────
    @staticmethod
    def get_test_stats(workspace_id: int) -> dict:
        ABTestModel.ensure_tables()
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                _adapt_sql("SELECT status, COUNT(*) FROM ab_tests WHERE workspace_id=? GROUP BY status"),
                (workspace_id,)
            )
            return {row[0]: row[1] for row in cur.fetchall()}
        finally:
            conn.close()
