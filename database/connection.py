"""
database/connection.py
======================
Module káº¿t ná»‘i cÆ¡ sá»Ÿ dá»¯ liá»‡u vá»›i há»— trá»£ Dual-Mode:
  - SQLite  (DB_ENGINE=sqlite  - máº·c Ä‘á»‹nh / dev)
  - PostgreSQL (DB_ENGINE=postgresql - production)

Táº¥t cáº£ hÃ m public giá»¯ nguyÃªn interface Ä‘á»ƒ khÃ´ng thay Ä‘á»•i cÃ¡c module khÃ¡c.
"""

import sqlite3
import pandas as pd
from datetime import datetime
from contextlib import contextmanager
from urllib.parse import parse_qs, unquote, urlsplit
from config.config import logger
from config.settings import DB_ENGINE, DB_PATH, PG_DSN

# ============================================================
# INTERNAL: Connection helpers
# ============================================================

def _redact_dsn(dsn: str) -> str:
    text = str(dsn or "")
    if "@" in text:
        return "***@" + text.rsplit("@", 1)[-1]
    if "password=" in text.lower():
        return "keyword-dsn-with-password"
    return text or "<empty>"


def _pg_kwargs_from_url(dsn: str) -> dict:
    parsed = urlsplit(dsn.strip())
    query = parse_qs(parsed.query)
    kwargs = {
        "host": parsed.hostname,
        "dbname": unquote(parsed.path.lstrip("/")) if parsed.path else None,
        "user": unquote(parsed.username or "") or None,
        "password": unquote(parsed.password or "") or None,
        "port": parsed.port,
    }
    if query.get("sslmode"):
        kwargs["sslmode"] = query["sslmode"][0]
    return {key: value for key, value in kwargs.items() if value not in (None, "")}


def _connect_pg(psycopg2, cursor_factory):
    dsn = str(PG_DSN or "").strip()
    try:
        return psycopg2.connect(dsn, cursor_factory=cursor_factory)
    except psycopg2.ProgrammingError as exc:
        if dsn.startswith(("postgresql://", "postgres://")):
            try:
                kwargs = _pg_kwargs_from_url(dsn)
                if kwargs.get("host") and kwargs.get("dbname"):
                    return psycopg2.connect(cursor_factory=cursor_factory, **kwargs)
            except Exception:
                pass
        raise RuntimeError(
            "Invalid PostgreSQL connection string. In Streamlit secrets, set PG_DSN or DATABASE_URL "
            "to a valid Postgres URL, or use PG_HOST/PG_PORT/PG_NAME/PG_USER/PG_PASSWORD. "
            "If the password contains special characters, prefer separate PG_* secrets."
        ) from exc

def _is_postgres() -> bool:
    return DB_ENGINE == "postgresql"


def _get_pg_connection():
    """Tao ket noi PostgreSQL/Neon voi cursor gan tuong thich SQLite."""
    try:
        import psycopg2
        import psycopg2.extras

        class CompatibleDictCursor(psycopg2.extras.DictCursor):
            @property
            def lastrowid(self):
                self.execute("SELECT lastval()")
                row = self.fetchone()
                return row[0] if row else None

        conn = _connect_pg(psycopg2, CompatibleDictCursor)
        conn.autocommit = False
        return conn
    except ImportError:
        logger.error("Thiáº¿u thÆ° viá»‡n psycopg2. HÃ£y cháº¡y: pip install psycopg2-binary")
        raise
    except Exception as e:
        logger.error(f"Khong the ket noi PostgreSQL tai {_redact_dsn(PG_DSN)}: {e}", exc_info=True)
        raise


def _get_sqlite_connection():
    """Táº¡o káº¿t ná»‘i SQLite."""
    logger.debug(f"Äang káº¿t ná»‘i tá»›i SQLite: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_db_connection():
    """
    Tráº£ vá» káº¿t ná»‘i database theo DB_ENGINE Ä‘Æ°á»£c cáº¥u hÃ¬nh.
    Caller cÃ³ trÃ¡ch nhiá»‡m Ä‘Ã³ng connection sau khi dÃ¹ng xong.
    """
    if _is_postgres():
        logger.debug(f"Dang ket noi toi PostgreSQL ({_redact_dsn(PG_DSN)})")
        return _get_pg_connection()
    else:
        return _get_sqlite_connection()


@contextmanager
def managed_connection():
    """Context manager tá»± Ä‘á»™ng Ä‘Ã³ng connection vÃ  rollback khi cÃ³ lá»—i."""
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ============================================================
# INTERNAL: SQL adapter (SQLite dÃ¹ng ?, PostgreSQL dÃ¹ng %s)
# ============================================================

def _placeholder(n: int = 1) -> str:
    """Tráº£ vá» placeholder phÃ¹ há»£p vá»›i engine Ä‘ang dÃ¹ng."""
    ph = "%s" if _is_postgres() else "?"
    return ", ".join([ph] * n)


def _adapt_sql(sql: str) -> str:
    """Chuyá»ƒn Ä‘á»•i SQL dÃ¹ng ? sang %s náº¿u lÃ  PostgreSQL."""
    if _is_postgres():
        return sql.replace("?", "%s")
    return sql


# ============================================================
# SCHEMA: Táº¡o / Cáº­p nháº­t báº£ng
# ============================================================

def _ensure_columns_sqlite(cursor, table_name: str, columns: dict):
    cursor.execute(f"PRAGMA table_info({table_name})")
    existing = {row[1] for row in cursor.fetchall()}
    for col_name, col_type in columns.items():
        if col_name not in existing:
            logger.info(f"SQLite: ThÃªm cá»™t '{col_name}' ({col_type}) vÃ o báº£ng '{table_name}'")
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}")


def _ensure_columns_postgres(cursor, table_name: str, columns: dict):
    cursor.execute(
        """SELECT column_name FROM information_schema.columns
           WHERE table_name = %s""",
        (table_name,)
    )
    existing = {row[0] for row in cursor.fetchall()}
    for col_name, col_type in columns.items():
        if col_name not in existing:
            logger.info(f"PostgreSQL: ThÃªm cá»™t '{col_name}' ({col_type}) vÃ o báº£ng '{table_name}'")
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}")


def ensure_columns(cursor, table_name: str, columns: dict):
    if _is_postgres():
        _ensure_columns_postgres(cursor, table_name, columns)
    else:
        _ensure_columns_sqlite(cursor, table_name, columns)



def _load_create_all_tables():
    """Load schema creator reliably on Streamlit Cloud and local runs."""
    try:
        from .schema import create_all_tables
        return create_all_tables
    except ModuleNotFoundError as exc:
        logger.warning(f"Relative import database.schema failed, trying file import: {exc}")

        import importlib.util
        from pathlib import Path

        schema_path = Path(__file__).resolve().with_name("schema.py")
        if not schema_path.exists():
            raise ModuleNotFoundError(
                f"database/schema.py was not found at deploy path: {schema_path}"
            ) from exc

        spec = importlib.util.spec_from_file_location("database_schema_fallback", schema_path)
        if spec is None or spec.loader is None:
            raise ModuleNotFoundError(
                f"Could not load database/schema.py from deploy path: {schema_path}"
            ) from exc

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.create_all_tables
def init_db():
    """Khá»Ÿi táº¡o toÃ n bá»™ 14 báº£ng cá»§a Schema V2 (SQLite hoáº·c PostgreSQL)."""
    logger.info(f"Äang khá»Ÿi táº¡o cÆ¡ sá»Ÿ dá»¯ liá»‡u Schema V2 ({DB_ENGINE.upper()})...")
    create_all_tables = _load_create_all_tables()
    
    conn = get_db_connection()
    try:
        create_all_tables(conn, engine=DB_ENGINE)
        cur = conn.cursor()

        # --- Báº£ng audit_logs ---
        if _is_postgres():
            cur.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id          SERIAL PRIMARY KEY,
                    timestamp   TEXT NOT NULL,
                    user_id     INTEGER,
                    user_email  TEXT DEFAULT '',
                    workspace_id INTEGER,
                    action      TEXT NOT NULL,
                    entity_type TEXT DEFAULT '',
                    entity_id   TEXT,
                    description TEXT DEFAULT '',
                    old_value   TEXT,
                    new_value   TEXT,
                    ip_address  TEXT DEFAULT ''
                )
            """)
        else:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp   TEXT NOT NULL,
                    user_id     INTEGER,
                    user_email  TEXT DEFAULT '',
                    workspace_id INTEGER,
                    action      TEXT NOT NULL,
                    entity_type TEXT DEFAULT '',
                    entity_id   TEXT,
                    description TEXT DEFAULT '',
                    old_value   TEXT,
                    new_value   TEXT,
                    ip_address  TEXT DEFAULT ''
                )
            """)

        # --- Äáº£m báº£o cá»™t embedding tá»“n táº¡i trong báº£ng knowledge ---
        ensure_columns(cur, "knowledge", {
            "embedding": "TEXT",
            "folder": "TEXT",
            "collection": "TEXT",
            "version": "TEXT"
        })

        # --- Äáº£m báº£o cÃ¡c cá»™t má»›i tá»“n táº¡i trong báº£ng brand ---
        ensure_columns(cur, "brand", {
            "cta": "TEXT",
            "vision": "TEXT",
            "mission": "TEXT",
            "keywords": "TEXT"
        })

        # --- Äáº£m báº£o cÃ¡c cá»™t má»›i tá»“n táº¡i trong báº£ng companies ---
        ensure_columns(cur, "companies", {
            "products": "TEXT",
            "target_customers": "TEXT"
        })

        # --- Tuong thich nguoc: tao/bo sung weekly_schedules neu thieu ---
        if _is_postgres():
            cur.execute("""
                CREATE TABLE IF NOT EXISTS weekly_schedules (
                    id           SERIAL PRIMARY KEY,
                    week_start   TEXT,
                    plan_json    TEXT,
                    workspace_id INT REFERENCES workspaces(id) ON DELETE SET NULL,
                    created_at   TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            cur.execute("ALTER TABLE weekly_schedules ADD COLUMN IF NOT EXISTS workspace_id INT")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_weekly_schedules_workspace ON weekly_schedules(workspace_id)")
        else:
            try:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS weekly_schedules (
                        id           INTEGER PRIMARY KEY AUTOINCREMENT,
                        week_start   TEXT,
                        plan_json    TEXT,
                        workspace_id INTEGER REFERENCES workspaces(id) ON DELETE SET NULL,
                        created_at   TEXT DEFAULT (datetime('now'))
                    )
                """)
                cur.execute("PRAGMA table_info(weekly_schedules)")
                cols = {row[1] for row in cur.fetchall()}
                if cols and "workspace_id" not in cols:
                    logger.info("SQLite: Them cot 'workspace_id' vao bang 'weekly_schedules'")
                    cur.execute("ALTER TABLE weekly_schedules ADD COLUMN workspace_id INTEGER")
            except Exception as e:
                logger.warning(f"Khong the tao/kiem tra/bo sung weekly_schedules: {e}")

        # --- Learning Loop: Tu tao bang learning_insights neu chua co ---
        if _is_postgres():
            cur.execute("""
                CREATE TABLE IF NOT EXISTS learning_insights (
                    id               SERIAL PRIMARY KEY,
                    workspace_id     INTEGER REFERENCES workspaces(id) ON DELETE CASCADE,
                    insight_type     TEXT    NOT NULL DEFAULT 'content_pattern',
                    platform         TEXT,
                    content_type     TEXT,
                    title            TEXT    NOT NULL,
                    description      TEXT,
                    recommendation   TEXT,
                    data_snapshot    TEXT,
                    avg_reach        REAL    DEFAULT 0,
                    avg_ctr          REAL    DEFAULT 0,
                    avg_er           REAL    DEFAULT 0,
                    avg_leads        REAL    DEFAULT 0,
                    avg_roi          REAL    DEFAULT 0,
                    sample_size      INTEGER DEFAULT 0,
                    confidence       REAL    DEFAULT 0,
                    applied_count    INTEGER DEFAULT 0,
                    status           TEXT    NOT NULL DEFAULT 'new',
                    generated_at     TIMESTAMPTZ DEFAULT NOW(),
                    applied_at       TEXT,
                    expires_at       TEXT
                )
            """)
        else:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS learning_insights (
                    id               INTEGER PRIMARY KEY AUTOINCREMENT,
                    workspace_id     INTEGER REFERENCES workspaces(id) ON DELETE CASCADE,
                    insight_type     TEXT    NOT NULL DEFAULT 'content_pattern',
                    platform         TEXT,
                    content_type     TEXT,
                    title            TEXT    NOT NULL,
                    description      TEXT,
                    recommendation   TEXT,
                    data_snapshot    TEXT,
                    avg_reach        REAL    DEFAULT 0,
                    avg_ctr          REAL    DEFAULT 0,
                    avg_er           REAL    DEFAULT 0,
                    avg_leads        REAL    DEFAULT 0,
                    avg_roi          REAL    DEFAULT 0,
                    sample_size      INTEGER DEFAULT 0,
                    confidence       REAL    DEFAULT 0,
                    applied_count    INTEGER DEFAULT 0,
                    status           TEXT    NOT NULL DEFAULT 'new',
                    generated_at     TEXT    DEFAULT (datetime('now')),
                    applied_at       TEXT,
                    expires_at       TEXT
                )
            """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_learning_workspace ON learning_insights(workspace_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_learning_type ON learning_insights(insight_type, status)")

        try:
            from database.migrations.content_strategy_center import up as migrate_content_strategy_center
            migrate_content_strategy_center(conn=conn, engine=DB_ENGINE)
        except Exception as e:
            logger.error(f"Khong the migrate AI Content Strategy Center: {e}", exc_info=True)
            raise

        ensure_columns(cur, "learning_insights", {
            "company_id": "INTEGER REFERENCES companies(id) ON DELETE CASCADE",
            "strategy_id": "INTEGER REFERENCES content_strategies(id) ON DELETE SET NULL",
            "evidence_period": "TEXT",
            "metric": "TEXT",
            "observation": "TEXT",
            "confidence_level": "TEXT",
            "affected_pillar": "TEXT",
            "affected_subtopic": "TEXT",
            "affected_platform": "TEXT",
            "affected_dimensions": "TEXT",
            "data_quality": "TEXT",
            "accepted_by": "INTEGER REFERENCES users(id) ON DELETE SET NULL",
            "accepted_at": "TEXT",
            "rejected_by": "INTEGER REFERENCES users(id) ON DELETE SET NULL",
            "rejected_at": "TEXT",
            "rejection_reason": "TEXT",
            "applied_version_id": "INTEGER REFERENCES content_strategy_versions(id) ON DELETE SET NULL",
        })
        logger.info("[SCHEMA] ÄÃ£ xÃ¡c minh báº£ng learning_insights (Learning Loop).")

        # Billing is optional UI, but production must self-heal its invoice table
        # before the Billing & Quota page reads from it.
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
        logger.info("[SCHEMA] Da xac minh bang invoices (Billing & Quota).")

        if _is_postgres():
            cur.execute("""
                CREATE TABLE IF NOT EXISTS ai_logs (
                    id                SERIAL PRIMARY KEY,
                    workspace_id      INTEGER REFERENCES workspaces(id) ON DELETE CASCADE,
                    provider          TEXT NOT NULL,
                    model_name        TEXT NOT NULL,
                    prompt_tokens     INTEGER DEFAULT 0,
                    completion_tokens INTEGER DEFAULT 0,
                    total_tokens      INTEGER DEFAULT 0,
                    cost              NUMERIC(12,6) DEFAULT 0.0,
                    latency_ms        INTEGER DEFAULT 0,
                    feature           TEXT,
                    status            TEXT NOT NULL DEFAULT 'success',
                    created_at        TIMESTAMPTZ DEFAULT NOW()
                )
            """)
        else:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS ai_logs (
                    id                INTEGER PRIMARY KEY AUTOINCREMENT,
                    workspace_id      INTEGER,
                    provider          TEXT NOT NULL,
                    model_name        TEXT NOT NULL,
                    prompt_tokens     INTEGER DEFAULT 0,
                    completion_tokens INTEGER DEFAULT 0,
                    total_tokens      INTEGER DEFAULT 0,
                    cost              REAL DEFAULT 0.0,
                    latency_ms        INTEGER DEFAULT 0,
                    feature           TEXT,
                    status            TEXT NOT NULL DEFAULT 'success',
                    created_at        TEXT DEFAULT (datetime('now'))
                )
            """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_ai_logs_workspace ON ai_logs(workspace_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_ai_logs_provider ON ai_logs(provider)")
        logger.info("[SCHEMA] Da xac minh bang ai_logs (AI Cost Center).")

        conn.commit()
    finally:
        conn.close()
    
    logger.info("CÆ¡ sá»Ÿ dá»¯ liá»‡u Schema V2 Ä‘Ã£ khá»Ÿi táº¡o / xÃ¡c minh thÃ nh cÃ´ng.")




# ============================================================
# PUBLIC API: Knowledge Posts
# ============================================================

def build_content_summary(content, max_length: int = 220) -> str:
    clean_content = " ".join(str(content or "").split())
    if len(clean_content) <= max_length:
        return clean_content
    return clean_content[:max_length].rsplit(" ", 1)[0] + "..."


def save_knowledge_post(
    date=None, platform="", topic="", audience="",
    tool_name="", knowledge_type="", difficulty="",
    content="", summary="", status="Draft"
):
    if not date:
        date = datetime.now().strftime("%d/%m/%Y %H:%M")
    if not summary:
        summary = build_content_summary(content)

    logger.info(f"[AUDIT] Ghi bÃ i viáº¿t AI Knowledge vÃ o DB ({DB_ENGINE}). Chá»§ Ä‘á»: {topic[:50]}")
    sql = _adapt_sql("""INSERT INTO knowledge_posts
        (date, platform, topic, audience, tool_name, knowledge_type, difficulty, content, summary, status)
        VALUES (?,?,?,?,?,?,?,?,?,?)""")

    with managed_connection() as conn:
        c = conn.cursor()
        c.execute(sql, (date, platform, topic, audience, tool_name, knowledge_type, difficulty, content, summary, status))
        if _is_postgres():
            c.execute("SELECT lastval()")
            new_id = c.fetchone()[0]
        else:
            new_id = c.lastrowid
        logger.debug(f"ÄÃ£ lÆ°u bÃ i viáº¿t AI Knowledge, ID má»›i: {new_id}")
        return new_id


def get_knowledge_posts(status=None, platform=None, limit=None):
    logger.debug(f"Truy váº¥n danh sÃ¡ch bÃ i viáº¿t AI Knowledge (status={status}, platform={platform}, limit={limit})")
    query = "SELECT * FROM knowledge_posts"
    filters, params = [], []

    if status:
        filters.append(_adapt_sql("status = ?"))
        params.append(status)
    if platform:
        filters.append(_adapt_sql("platform = ?"))
        params.append(platform)
    if filters:
        query += " WHERE " + " AND ".join(filters)
    query += " ORDER BY id DESC"
    if limit:
        query += _adapt_sql(" LIMIT ?")
        params.append(limit)

    conn = get_db_connection()
    try:
        if _is_postgres():
            import psycopg2.extras
            df = pd.read_sql_query(query, conn, params=params)
        else:
            df = pd.read_sql_query(query, conn, params=params)
        return df
    except Exception as e:
        logger.error(f"Lá»—i truy váº¥n knowledge_posts: {e}", exc_info=True)
        return pd.DataFrame()
    finally:
        conn.close()


def delete_knowledge_post(post_id) -> bool:
    logger.info(f"[AUDIT] XÃ³a bÃ i viáº¿t AI Knowledge ID={post_id} khá»i DB ({DB_ENGINE})")
    sql = _adapt_sql("DELETE FROM knowledge_posts WHERE id = ?")
    with managed_connection() as conn:
        c = conn.cursor()
        c.execute(sql, (post_id,))
        deleted = c.rowcount > 0
        if deleted:
            logger.info(f"ÄÃ£ xÃ³a thÃ nh cÃ´ng bÃ i viáº¿t AI Knowledge ID={post_id}")
        else:
            logger.warning(f"KhÃ´ng tÃ¬m tháº¥y bÃ i viáº¿t Ä‘á»ƒ xÃ³a vá»›i ID={post_id}")
        return deleted

