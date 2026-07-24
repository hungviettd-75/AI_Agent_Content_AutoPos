"""
database/schema.py
==================
Dinh nghia toan bo DDL (CREATE TABLE, INDEX) cho Schema V2.
Ho tro ca SQLite va PostgreSQL qua lop tuong thich.

Su dung:
    from database.schema import create_all_tables
    create_all_tables(conn, engine="sqlite")  # hoac "postgresql"
"""

from config.config import logger


# ============================================================
# SQLITE DDL
# ============================================================

SQLITE_DDL = [

    # ----------------------------------------------------------
    # 1. users
    # ----------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS users (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        email         TEXT    UNIQUE NOT NULL,
        username      TEXT    UNIQUE NOT NULL,
        password_hash TEXT    NOT NULL,
        full_name     TEXT,
        avatar_url    TEXT,
        role          TEXT    NOT NULL DEFAULT 'editor',
        is_active     INTEGER NOT NULL DEFAULT 1,
        created_at    TEXT    DEFAULT (datetime('now')),
        updated_at    TEXT    DEFAULT (datetime('now')),
        last_login_at TEXT
    )""",

    # ----------------------------------------------------------
    # 2. workspaces
    # ----------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS workspaces (
        id                   INTEGER PRIMARY KEY AUTOINCREMENT,
        name                 TEXT    NOT NULL,
        slug                 TEXT    UNIQUE NOT NULL,
        owner_id             INTEGER REFERENCES users(id) ON DELETE SET NULL,
        plan                 TEXT    NOT NULL DEFAULT 'free',
        max_users            INTEGER NOT NULL DEFAULT 5,
        max_posts_per_month  INTEGER NOT NULL DEFAULT 100,
        is_active            INTEGER NOT NULL DEFAULT 1,
        created_at           TEXT    DEFAULT (datetime('now')),
        updated_at           TEXT    DEFAULT (datetime('now'))
    )""",

    # ----------------------------------------------------------
    # 2b. workspace_members (junction)
    # ----------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS workspace_members (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        workspace_id INTEGER NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
        user_id      INTEGER NOT NULL REFERENCES users(id)      ON DELETE CASCADE,
        role         TEXT    NOT NULL DEFAULT 'editor',
        invited_at   TEXT    DEFAULT (datetime('now')),
        joined_at    TEXT,
        UNIQUE(workspace_id, user_id)
    )""",

    # ----------------------------------------------------------
    # 3. companies
    # ----------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS companies (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        workspace_id INTEGER REFERENCES workspaces(id) ON DELETE CASCADE,
        name         TEXT    NOT NULL,
        industry     TEXT,
        size         TEXT,
        website      TEXT,
        description  TEXT,
        logo_url     TEXT,
        products     TEXT,
        target_customers TEXT,
        created_at   TEXT    DEFAULT (datetime('now')),
        updated_at   TEXT    DEFAULT (datetime('now'))
    )""",

    # ----------------------------------------------------------
    # 4. brand
    # ----------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS brand (
        id                INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id        INTEGER REFERENCES companies(id) ON DELETE CASCADE,
        workspace_id      INTEGER REFERENCES workspaces(id) ON DELETE CASCADE,
        tone_of_voice     TEXT    DEFAULT 'casual',
        target_audiences  TEXT,
        brand_colors      TEXT,
        logo_url          TEXT,
        tagline           TEXT,
        brand_guidelines  TEXT,
        blacklist_words   TEXT,
        cta               TEXT,
        vision            TEXT,
        mission           TEXT,
        keywords          TEXT,
        created_at        TEXT    DEFAULT (datetime('now')),
        updated_at        TEXT    DEFAULT (datetime('now'))
    )""",

    # ----------------------------------------------------------
    # 5. projects
    # ----------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS projects (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        workspace_id INTEGER REFERENCES workspaces(id) ON DELETE CASCADE,
        company_id   INTEGER REFERENCES companies(id)  ON DELETE SET NULL,
        name         TEXT    NOT NULL,
        description  TEXT,
        status       TEXT    NOT NULL DEFAULT 'active',
        start_date   TEXT,
        end_date     TEXT,
        created_by   INTEGER REFERENCES users(id) ON DELETE SET NULL,
        created_at   TEXT    DEFAULT (datetime('now')),
        updated_at   TEXT    DEFAULT (datetime('now'))
    )""",

    # ----------------------------------------------------------
    # 6. campaigns
    # ----------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS campaigns (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id      INTEGER REFERENCES projects(id)   ON DELETE SET NULL,
        workspace_id    INTEGER REFERENCES workspaces(id) ON DELETE CASCADE,
        name            TEXT    NOT NULL,
        objective       TEXT,
        platforms       TEXT,
        target_audience TEXT,
        budget          REAL    DEFAULT 0,
        start_date      TEXT,
        end_date        TEXT,
        status          TEXT    NOT NULL DEFAULT 'draft',
        created_by      INTEGER REFERENCES users(id) ON DELETE SET NULL,
        created_at      TEXT    DEFAULT (datetime('now')),
        updated_at      TEXT    DEFAULT (datetime('now'))
    )""",

    # ----------------------------------------------------------
    # 7. posts  (CORE â€” mo rong tu bang posts cu)
    # ----------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS posts (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        workspace_id  INTEGER REFERENCES workspaces(id) ON DELETE SET NULL,
        campaign_id   INTEGER REFERENCES campaigns(id)  ON DELETE SET NULL,
        title         TEXT,
        content       TEXT    NOT NULL DEFAULT '',
        platform      TEXT    NOT NULL DEFAULT 'facebook',
        content_type  TEXT    NOT NULL DEFAULT 'marketing_viral',
        status        TEXT    NOT NULL DEFAULT 'draft',
        scheduled_at  TEXT,
        published_at  TEXT,
        viral_score   INTEGER,
        image_prompt  TEXT,
        ai_metadata   TEXT,
        topic         TEXT,
        date          TEXT,
        created_by    INTEGER REFERENCES users(id) ON DELETE SET NULL,
        approved_by   INTEGER REFERENCES users(id) ON DELETE SET NULL,
        created_at    TEXT    DEFAULT (datetime('now')),
        updated_at    TEXT    DEFAULT (datetime('now'))
    )""",

    # ----------------------------------------------------------
    # 8. assets
    # ----------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS assets (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        workspace_id INTEGER REFERENCES workspaces(id) ON DELETE CASCADE,
        post_id      INTEGER REFERENCES posts(id)      ON DELETE SET NULL,
        name         TEXT    NOT NULL,
        file_type    TEXT    NOT NULL DEFAULT 'image',
        url          TEXT    NOT NULL,
        storage_path TEXT,
        size_bytes   INTEGER,
        mime_type    TEXT,
        alt_text     TEXT,
        tags         TEXT,
        uploaded_by  INTEGER REFERENCES users(id) ON DELETE SET NULL,
        created_at   TEXT    DEFAULT (datetime('now'))
    )""",

    # ----------------------------------------------------------
    # 9. knowledge  (nang cap tu knowledge_posts)
    # ----------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS knowledge (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        workspace_id   INTEGER REFERENCES workspaces(id) ON DELETE SET NULL,
        title          TEXT,
        content        TEXT,
        summary        TEXT,
        knowledge_type TEXT,
        ai_tool        TEXT,
        audience       TEXT,
        difficulty     TEXT,
        platform       TEXT,
        tags           TEXT,
        post_id        INTEGER REFERENCES posts(id) ON DELETE SET NULL,
        topic          TEXT,
        date           TEXT,
        status         TEXT    DEFAULT 'draft',
        created_by     INTEGER REFERENCES users(id) ON DELETE SET NULL,
        created_at     TEXT    DEFAULT (datetime('now')),
        updated_at     TEXT    DEFAULT (datetime('now'))
    )""",

    # ----------------------------------------------------------
    # 10. schedules
    # ----------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS schedules (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        workspace_id  INTEGER REFERENCES workspaces(id) ON DELETE CASCADE,
        post_id       INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
        scheduled_at  TEXT    NOT NULL,
        platform      TEXT,
        status        TEXT    NOT NULL DEFAULT 'pending',
        retry_count   INTEGER NOT NULL DEFAULT 0,
        published_at  TEXT,
        error_message TEXT,
        created_by    INTEGER REFERENCES users(id) ON DELETE SET NULL,
        created_at    TEXT    DEFAULT (datetime('now')),
        updated_at    TEXT    DEFAULT (datetime('now'))
    )""",

    # ----------------------------------------------------------
    # 10b. weekly_schedules (legacy weekly planner)
    # ----------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS weekly_schedules (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        week_start   TEXT,
        plan_json    TEXT,
        workspace_id INTEGER REFERENCES workspaces(id) ON DELETE SET NULL,
        created_at   TEXT DEFAULT (datetime('now'))
    )""",
    # ----------------------------------------------------------
    # 11. approvals
    # ----------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS approvals (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id       INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
        workspace_id  INTEGER REFERENCES workspaces(id) ON DELETE CASCADE,
        requested_by  INTEGER REFERENCES users(id) ON DELETE SET NULL,
        approved_by   INTEGER REFERENCES users(id) ON DELETE SET NULL,
        status        TEXT    NOT NULL DEFAULT 'pending',
        notes         TEXT,
        requested_at  TEXT    DEFAULT (datetime('now')),
        responded_at  TEXT
    )""",

    # ----------------------------------------------------------
    # 12. prompt_versions
    # ----------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS prompt_versions (
        id                INTEGER PRIMARY KEY AUTOINCREMENT,
        workspace_id      INTEGER REFERENCES workspaces(id) ON DELETE CASCADE,
        prompt_name       TEXT    NOT NULL,
        version           INTEGER NOT NULL DEFAULT 1,
        content           TEXT    NOT NULL,
        variables         TEXT,
        is_active         INTEGER NOT NULL DEFAULT 1,
        performance_score REAL,
        created_by        INTEGER REFERENCES users(id) ON DELETE SET NULL,
        created_at        TEXT    DEFAULT (datetime('now')),
        UNIQUE(prompt_name, version, workspace_id)
    )""",

    # ----------------------------------------------------------
    # 13. analytics
    # ----------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS analytics (
        id                   INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id              INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
        workspace_id         INTEGER REFERENCES workspaces(id) ON DELETE CASCADE,
        platform             TEXT,
        metric_date          TEXT,
        impressions          INTEGER DEFAULT 0,
        reach                INTEGER DEFAULT 0,
        likes                INTEGER DEFAULT 0,
        comments             INTEGER DEFAULT 0,
        shares               INTEGER DEFAULT 0,
        saves                INTEGER DEFAULT 0,
        clicks               INTEGER DEFAULT 0,
        link_clicks          INTEGER DEFAULT 0,
        engagement_rate      REAL    DEFAULT 0,
        reach_rate           REAL    DEFAULT 0,
        cost_per_engagement  REAL    DEFAULT 0,
        raw_data             TEXT,
        synced_at            TEXT,
        created_at           TEXT    DEFAULT (datetime('now')),
        UNIQUE(post_id, platform, metric_date)
    )""",

    # ----------------------------------------------------------
    # 14. learning_insights  (Learning Loop)
    # ----------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS learning_insights (
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
    )""",

    # ----------------------------------------------------------
    # 15. invoices (Billing & Quota)
    # ----------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS invoices (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        workspace_id   INTEGER NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
        invoice_no     TEXT UNIQUE NOT NULL,
        plan           TEXT NOT NULL,
        amount         REAL NOT NULL,
        status         TEXT NOT NULL DEFAULT 'paid',
        billing_date   TEXT NOT NULL,
        payment_method TEXT DEFAULT 'Credit Card',
        pdf_url        TEXT
    )""",

]


# ----------------------------------------------------------
# SQLITE INDEXES
# ----------------------------------------------------------
SQLITE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_posts_workspace     ON posts(workspace_id)",
    "CREATE INDEX IF NOT EXISTS idx_posts_campaign      ON posts(campaign_id)",
    "CREATE INDEX IF NOT EXISTS idx_posts_status        ON posts(status)",
    "CREATE INDEX IF NOT EXISTS idx_posts_platform      ON posts(platform)",
    "CREATE INDEX IF NOT EXISTS idx_posts_created_at    ON posts(created_at)",
    "CREATE INDEX IF NOT EXISTS idx_knowledge_workspace ON knowledge(workspace_id)",
    "CREATE INDEX IF NOT EXISTS idx_schedules_status    ON schedules(status)",
    "CREATE INDEX IF NOT EXISTS idx_schedules_scheduled ON schedules(scheduled_at)",
    "CREATE INDEX IF NOT EXISTS idx_weekly_schedules_workspace ON weekly_schedules(workspace_id)",
    "CREATE INDEX IF NOT EXISTS idx_analytics_post      ON analytics(post_id)",
    "CREATE INDEX IF NOT EXISTS idx_analytics_date      ON analytics(metric_date)",
    "CREATE INDEX IF NOT EXISTS idx_campaigns_workspace ON campaigns(workspace_id)",
    "CREATE INDEX IF NOT EXISTS idx_approvals_post      ON approvals(post_id)",
    "CREATE INDEX IF NOT EXISTS idx_approvals_status    ON approvals(status)",
    "CREATE INDEX IF NOT EXISTS idx_prompt_name_active  ON prompt_versions(prompt_name, is_active)",
    "CREATE INDEX IF NOT EXISTS idx_learning_workspace  ON learning_insights(workspace_id)",
    "CREATE INDEX IF NOT EXISTS idx_learning_type       ON learning_insights(insight_type, status)",
    "CREATE INDEX IF NOT EXISTS idx_invoices_workspace ON invoices(workspace_id)",
]


# ============================================================
# POSTGRESQL DDL
# ============================================================

POSTGRESQL_DDL = [

    # 1. users
    """CREATE TABLE IF NOT EXISTS users (
        id            SERIAL PRIMARY KEY,
        email         TEXT    UNIQUE NOT NULL,
        username      TEXT    UNIQUE NOT NULL,
        password_hash TEXT    NOT NULL,
        full_name     TEXT,
        avatar_url    TEXT,
        role          TEXT    NOT NULL DEFAULT 'editor',
        is_active     INTEGER NOT NULL DEFAULT 1,
        created_at    TIMESTAMPTZ DEFAULT NOW(),
        updated_at    TIMESTAMPTZ DEFAULT NOW(),
        last_login_at TIMESTAMPTZ
    )""",

    # 2. workspaces
    """CREATE TABLE IF NOT EXISTS workspaces (
        id                   SERIAL PRIMARY KEY,
        name                 TEXT    NOT NULL,
        slug                 TEXT    UNIQUE NOT NULL,
        owner_id             INT     REFERENCES users(id) ON DELETE SET NULL,
        plan                 TEXT    NOT NULL DEFAULT 'free',
        max_users            INT     NOT NULL DEFAULT 5,
        max_posts_per_month  INT     NOT NULL DEFAULT 100,
        is_active            INTEGER NOT NULL DEFAULT 1,
        created_at           TIMESTAMPTZ DEFAULT NOW(),
        updated_at           TIMESTAMPTZ DEFAULT NOW()
    )""",

    # 2b. workspace_members
    """CREATE TABLE IF NOT EXISTS workspace_members (
        id           SERIAL PRIMARY KEY,
        workspace_id INT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
        user_id      INT NOT NULL REFERENCES users(id)      ON DELETE CASCADE,
        role         TEXT NOT NULL DEFAULT 'editor',
        invited_at   TIMESTAMPTZ DEFAULT NOW(),
        joined_at    TIMESTAMPTZ,
        UNIQUE(workspace_id, user_id)
    )""",

    # 3. companies
    """CREATE TABLE IF NOT EXISTS companies (
        id           SERIAL PRIMARY KEY,
        workspace_id INT  REFERENCES workspaces(id) ON DELETE CASCADE,
        name         TEXT NOT NULL,
        industry     TEXT,
        size         TEXT,
        website      TEXT,
        description  TEXT,
        logo_url     TEXT,
        products     TEXT,
        target_customers TEXT,
        created_at   TIMESTAMPTZ DEFAULT NOW(),
        updated_at   TIMESTAMPTZ DEFAULT NOW()
    )""",

    # 4. brand
    """CREATE TABLE IF NOT EXISTS brand (
        id                SERIAL PRIMARY KEY,
        company_id        INT  REFERENCES companies(id)  ON DELETE CASCADE,
        workspace_id      INT  REFERENCES workspaces(id) ON DELETE CASCADE,
        tone_of_voice     TEXT DEFAULT 'casual',
        target_audiences  TEXT,
        brand_colors      TEXT,
        logo_url          TEXT,
        tagline           TEXT,
        brand_guidelines  TEXT,
        blacklist_words   TEXT,
        cta               TEXT,
        vision            TEXT,
        mission           TEXT,
        keywords          TEXT,
        created_at        TIMESTAMPTZ DEFAULT NOW(),
        updated_at        TIMESTAMPTZ DEFAULT NOW()
    )""",

    # 5. projects
    """CREATE TABLE IF NOT EXISTS projects (
        id           SERIAL PRIMARY KEY,
        workspace_id INT  REFERENCES workspaces(id) ON DELETE CASCADE,
        company_id   INT  REFERENCES companies(id)  ON DELETE SET NULL,
        name         TEXT NOT NULL,
        description  TEXT,
        status       TEXT NOT NULL DEFAULT 'active',
        start_date   TEXT,
        end_date     TEXT,
        created_by   INT  REFERENCES users(id) ON DELETE SET NULL,
        created_at   TIMESTAMPTZ DEFAULT NOW(),
        updated_at   TIMESTAMPTZ DEFAULT NOW()
    )""",

    # 6. campaigns
    """CREATE TABLE IF NOT EXISTS campaigns (
        id              SERIAL PRIMARY KEY,
        project_id      INT   REFERENCES projects(id)   ON DELETE SET NULL,
        workspace_id    INT   REFERENCES workspaces(id) ON DELETE CASCADE,
        name            TEXT  NOT NULL,
        objective       TEXT,
        platforms       TEXT,
        target_audience TEXT,
        budget          NUMERIC(12,2) DEFAULT 0,
        start_date      TEXT,
        end_date        TEXT,
        status          TEXT  NOT NULL DEFAULT 'draft',
        created_by      INT   REFERENCES users(id) ON DELETE SET NULL,
        created_at      TIMESTAMPTZ DEFAULT NOW(),
        updated_at      TIMESTAMPTZ DEFAULT NOW()
    )""",

    # 7. posts
    """CREATE TABLE IF NOT EXISTS posts (
        id            SERIAL PRIMARY KEY,
        workspace_id  INT  REFERENCES workspaces(id) ON DELETE SET NULL,
        campaign_id   INT  REFERENCES campaigns(id)  ON DELETE SET NULL,
        title         TEXT,
        content       TEXT NOT NULL DEFAULT '',
        platform      TEXT NOT NULL DEFAULT 'facebook',
        content_type  TEXT NOT NULL DEFAULT 'marketing_viral',
        status        TEXT NOT NULL DEFAULT 'draft',
        scheduled_at  TIMESTAMPTZ,
        published_at  TIMESTAMPTZ,
        viral_score   INT,
        image_prompt  TEXT,
        ai_metadata   TEXT,
        topic         TEXT,
        date          TEXT,
        created_by    INT  REFERENCES users(id) ON DELETE SET NULL,
        approved_by   INT  REFERENCES users(id) ON DELETE SET NULL,
        created_at    TIMESTAMPTZ DEFAULT NOW(),
        updated_at    TIMESTAMPTZ DEFAULT NOW()
    )""",

    # 8. assets
    """CREATE TABLE IF NOT EXISTS assets (
        id           SERIAL PRIMARY KEY,
        workspace_id INT  REFERENCES workspaces(id) ON DELETE CASCADE,
        post_id      INT  REFERENCES posts(id)      ON DELETE SET NULL,
        name         TEXT NOT NULL,
        file_type    TEXT NOT NULL DEFAULT 'image',
        url          TEXT NOT NULL,
        storage_path TEXT,
        size_bytes   BIGINT,
        mime_type    TEXT,
        alt_text     TEXT,
        tags         TEXT,
        uploaded_by  INT  REFERENCES users(id) ON DELETE SET NULL,
        created_at   TIMESTAMPTZ DEFAULT NOW()
    )""",

    # 9. knowledge
    """CREATE TABLE IF NOT EXISTS knowledge (
        id             SERIAL PRIMARY KEY,
        workspace_id   INT  REFERENCES workspaces(id) ON DELETE SET NULL,
        title          TEXT,
        content        TEXT,
        summary        TEXT,
        knowledge_type TEXT,
        ai_tool        TEXT,
        audience       TEXT,
        difficulty     TEXT,
        platform       TEXT,
        tags           TEXT,
        post_id        INT  REFERENCES posts(id) ON DELETE SET NULL,
        topic          TEXT,
        date           TEXT,
        status         TEXT DEFAULT 'draft',
        created_by     INT  REFERENCES users(id) ON DELETE SET NULL,
        created_at     TIMESTAMPTZ DEFAULT NOW(),
        updated_at     TIMESTAMPTZ DEFAULT NOW()
    )""",

    # 10. schedules
    """CREATE TABLE IF NOT EXISTS schedules (
        id            SERIAL PRIMARY KEY,
        workspace_id  INT  REFERENCES workspaces(id)  ON DELETE CASCADE,
        post_id       INT  NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
        scheduled_at  TIMESTAMPTZ NOT NULL,
        platform      TEXT,
        status        TEXT NOT NULL DEFAULT 'pending',
        retry_count   INT  NOT NULL DEFAULT 0,
        published_at  TIMESTAMPTZ,
        error_message TEXT,
        created_by    INT  REFERENCES users(id) ON DELETE SET NULL,
        created_at    TIMESTAMPTZ DEFAULT NOW(),
        updated_at    TIMESTAMPTZ DEFAULT NOW()
    )""",

    # 10b. weekly_schedules (legacy weekly planner)
    """CREATE TABLE IF NOT EXISTS weekly_schedules (
        id           SERIAL PRIMARY KEY,
        week_start   TEXT,
        plan_json    TEXT,
        workspace_id INT REFERENCES workspaces(id) ON DELETE SET NULL,
        created_at   TIMESTAMPTZ DEFAULT NOW()
    )""",
    # 11. approvals
    """CREATE TABLE IF NOT EXISTS approvals (
        id            SERIAL PRIMARY KEY,
        post_id       INT  NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
        workspace_id  INT  REFERENCES workspaces(id)     ON DELETE CASCADE,
        requested_by  INT  REFERENCES users(id) ON DELETE SET NULL,
        approved_by   INT  REFERENCES users(id) ON DELETE SET NULL,
        status        TEXT NOT NULL DEFAULT 'pending',
        notes         TEXT,
        requested_at  TIMESTAMPTZ DEFAULT NOW(),
        responded_at  TIMESTAMPTZ
    )""",

    # 12. prompt_versions
    """CREATE TABLE IF NOT EXISTS prompt_versions (
        id                SERIAL PRIMARY KEY,
        workspace_id      INT  REFERENCES workspaces(id) ON DELETE CASCADE,
        prompt_name       TEXT NOT NULL,
        version           INT  NOT NULL DEFAULT 1,
        content           TEXT NOT NULL,
        variables         TEXT,
        is_active         INTEGER NOT NULL DEFAULT 1,
        performance_score NUMERIC(4,2),
        created_by        INT  REFERENCES users(id) ON DELETE SET NULL,
        created_at        TIMESTAMPTZ DEFAULT NOW(),
        UNIQUE(prompt_name, version, workspace_id)
    )""",

    # 13. analytics
    """CREATE TABLE IF NOT EXISTS analytics (
        id                   SERIAL PRIMARY KEY,
        post_id              INT  NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
        workspace_id         INT  REFERENCES workspaces(id)     ON DELETE CASCADE,
        platform             TEXT,
        metric_date          DATE,
        impressions          INT     DEFAULT 0,
        reach                INT     DEFAULT 0,
        likes                INT     DEFAULT 0,
        comments             INT     DEFAULT 0,
        shares               INT     DEFAULT 0,
        saves                INT     DEFAULT 0,
        clicks               INT     DEFAULT 0,
        link_clicks          INT     DEFAULT 0,
        engagement_rate      NUMERIC(6,4) DEFAULT 0,
        reach_rate           NUMERIC(6,4) DEFAULT 0,
        cost_per_engagement  NUMERIC(10,4) DEFAULT 0,
        raw_data             TEXT,
        synced_at            TIMESTAMPTZ,
        created_at           TIMESTAMPTZ DEFAULT NOW(),
        UNIQUE(post_id, platform, metric_date)
    )""",

    # 15. invoices (Billing & Quota)
    """CREATE TABLE IF NOT EXISTS invoices (
        id             SERIAL PRIMARY KEY,
        workspace_id   INT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
        invoice_no     TEXT UNIQUE NOT NULL,
        plan           TEXT NOT NULL,
        amount         NUMERIC(12,2) NOT NULL,
        status         TEXT NOT NULL DEFAULT 'paid',
        billing_date   TEXT NOT NULL,
        payment_method TEXT DEFAULT 'Credit Card',
        pdf_url        TEXT
    )""",

]

POSTGRESQL_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_posts_workspace    ON posts(workspace_id)",
    "CREATE INDEX IF NOT EXISTS idx_posts_campaign     ON posts(campaign_id)",
    "CREATE INDEX IF NOT EXISTS idx_posts_status       ON posts(status)",
    "CREATE INDEX IF NOT EXISTS idx_posts_platform     ON posts(platform)",
    "CREATE INDEX IF NOT EXISTS idx_posts_created_at   ON posts(created_at)",
    "CREATE INDEX IF NOT EXISTS idx_knowledge_workspace ON knowledge(workspace_id)",
    "CREATE INDEX IF NOT EXISTS idx_schedules_status    ON schedules(status)",
    "CREATE INDEX IF NOT EXISTS idx_schedules_scheduled ON schedules(scheduled_at)",
    "CREATE INDEX IF NOT EXISTS idx_weekly_schedules_workspace ON weekly_schedules(workspace_id)",
    "CREATE INDEX IF NOT EXISTS idx_analytics_post      ON analytics(post_id)",
    "CREATE INDEX IF NOT EXISTS idx_analytics_date      ON analytics(metric_date)",
    "CREATE INDEX IF NOT EXISTS idx_campaigns_workspace ON campaigns(workspace_id)",
    "CREATE INDEX IF NOT EXISTS idx_approvals_post      ON approvals(post_id)",
    "CREATE INDEX IF NOT EXISTS idx_approvals_status    ON approvals(status)",
    "CREATE INDEX IF NOT EXISTS idx_prompt_name_active  ON prompt_versions(prompt_name, is_active)",
    "CREATE INDEX IF NOT EXISTS idx_invoices_workspace ON invoices(workspace_id)",
]

# Danh sach ten bang theo thu tu tao (phu thuoc)
TABLE_ORDER = [
    "users", "workspaces", "workspace_members",
    "companies", "brand", "projects", "campaigns",
    "posts", "assets", "knowledge",
    "schedules", "weekly_schedules", "approvals", "prompt_versions", "analytics",
    "learning_insights", "invoices",
]


# ============================================================
# PUBLIC API
# ============================================================

def create_all_tables(conn, engine: str = "sqlite"):
    """
    Tao toan bo 14 bang (13 entity + workspace_members) tren connection da cho.
    engine: "sqlite" hoac "postgresql"
    """
    ddl_list  = POSTGRESQL_DDL  if engine == "postgresql" else SQLITE_DDL
    idx_list  = POSTGRESQL_INDEXES if engine == "postgresql" else SQLITE_INDEXES

    cur = conn.cursor()
    lock_key = 2026072301
    use_pg_lock = engine == "postgresql"

    try:
        if use_pg_lock:
            logger.info("[SCHEMA] Dang khoa advisory lock PostgreSQL de tranh tao schema song song...")
            cur.execute("SELECT pg_advisory_lock(%s)", (lock_key,))

        logger.info(f"[SCHEMA] Bat dau tao {len(ddl_list)} bang ({engine.upper()})...")

        for stmt in ddl_list:
            # Lay ten bang tu dong dau DDL
            table_name = stmt.strip().split("EXISTS")[-1].strip().split("(")[0].strip()
            try:
                cur.execute(stmt)
                logger.debug(f"[SCHEMA] OK: {table_name}")
            except Exception as e:
                logger.error(f"[SCHEMA] LOI tao bang {table_name}: {e}")
                raise

        conn.commit()

        logger.info(f"[SCHEMA] Tao {len(idx_list)} index...")
        for stmt in idx_list:
            try:
                if engine == "postgresql":
                    cur.execute("SAVEPOINT schema_index")
                cur.execute(stmt)
                if engine == "postgresql":
                    cur.execute("RELEASE SAVEPOINT schema_index")
            except Exception as e:
                logger.warning(f"[SCHEMA] Khong the tao index: {e}")
                if engine == "postgresql":
                    cur.execute("ROLLBACK TO SAVEPOINT schema_index")
                    cur.execute("RELEASE SAVEPOINT schema_index")

        conn.commit()
        logger.info("[SCHEMA] Hoan tat tao toan bo bang va index.")
    except Exception:
        conn.rollback()
        raise
    finally:
        if use_pg_lock:
            try:
                cur.execute("SELECT pg_advisory_unlock(%s)", (lock_key,))
                conn.commit()
            except Exception as e:
                logger.warning(f"[SCHEMA] Khong the mo advisory lock PostgreSQL: {e}")
                conn.rollback()


def verify_tables(conn, engine: str = "sqlite") -> dict:
    """
    Kiem tra xem tat ca bang da duoc tao hay chua.
    Returns dict: {table_name: exists (bool)}
    """
    cur = conn.cursor()
    result = {}

    for table in TABLE_ORDER:
        try:
            if engine == "postgresql":
                cur.execute(
                    "SELECT COUNT(*) FROM information_schema.tables "
                    "WHERE table_name = %s AND table_schema = 'public'",
                    (table,)
                )
            else:
                cur.execute(
                    "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?",
                    (table,)
                )
            count = cur.fetchone()[0]
            result[table] = count > 0
        except Exception:
            result[table] = False

    return result


# ============================================================
# CLI: chay truc tiep de tao DB test
# ============================================================
if __name__ == "__main__":
    import sys
    import os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

    from database.connection import get_db_connection, _is_postgres
    from config.settings import DB_ENGINE

    print("=" * 55)
    print(f"  Schema V2 â€” Tao bang ({DB_ENGINE.upper()})")
    print("=" * 55)

    conn = get_db_connection()
    create_all_tables(conn, engine=DB_ENGINE)

    print("\n  Ket qua xac minh:")
    report = verify_tables(conn, engine=DB_ENGINE)
    all_ok = True
    for table, exists in report.items():
        icon = "OK" if exists else "THIEU"
        print(f"  [{icon:5}] {table}")
        if not exists:
            all_ok = False

    conn.close()
    print()
    if all_ok:
        print("  => Tat ca bang da tao thanh cong!")
    else:
        print("  => CO BANG CHUA DUOC TAO. Kiem tra log.")
        sys.exit(1)

