"""Migration for AI Content Strategy Center tables.

The migration is intentionally non-destructive: ``up`` only creates new
tables/indexes when missing, and ``down`` only drops the tables introduced here.
It supports SQLite and PostgreSQL through the active DB engine.
"""

from database.connection import get_db_connection, _is_postgres, ensure_columns


TABLES = [
    "lead_magnet_calendar_items",
    "content_generation_jobs",
    "content_strategy_kpis",
    "content_calendar_items",
    "content_format_variants",
    "content_angles",
    "content_subtopics",
    "content_pillars",
    "lead_magnets",
    "business_goals",
    "audience_personas",
    "content_strategy_versions",
    "content_strategies",
]


SQLITE_TABLES = [
    """CREATE TABLE IF NOT EXISTS content_strategies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workspace_id INTEGER NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
        company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
        campaign_id INTEGER REFERENCES campaigns(id) ON DELETE SET NULL,
        project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL,
        name TEXT NOT NULL,
        description TEXT,
        strategy_type TEXT NOT NULL DEFAULT 'content',
        status TEXT NOT NULL DEFAULT 'draft',
        start_date TEXT,
        end_date TEXT,
        metadata TEXT,
        version INTEGER NOT NULL DEFAULT 1,
        sort_order INTEGER NOT NULL DEFAULT 0,
        created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
        updated_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
        archived_at TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now')),
        deleted_at TEXT,
        UNIQUE(workspace_id, company_id, name)
    )""",
    """CREATE TABLE IF NOT EXISTS content_strategy_versions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workspace_id INTEGER NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
        company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
        strategy_id INTEGER NOT NULL REFERENCES content_strategies(id) ON DELETE CASCADE,
        version INTEGER NOT NULL,
        snapshot TEXT NOT NULL,
        notes TEXT,
        created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
        created_at TEXT DEFAULT (datetime('now')),
        UNIQUE(strategy_id, version)
    )""",
    """CREATE TABLE IF NOT EXISTS audience_personas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workspace_id INTEGER NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
        company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
        strategy_id INTEGER NOT NULL REFERENCES content_strategies(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        segment TEXT,
        description TEXT,
        pain_points TEXT,
        goals TEXT,
        preferred_channels TEXT,
        status TEXT NOT NULL DEFAULT 'active',
        sort_order INTEGER NOT NULL DEFAULT 0,
        created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
        updated_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now')),
        deleted_at TEXT,
        UNIQUE(strategy_id, name)
    )""",
    """CREATE TABLE IF NOT EXISTS business_goals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workspace_id INTEGER NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
        company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
        strategy_id INTEGER NOT NULL REFERENCES content_strategies(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        description TEXT,
        target_metric TEXT,
        target_value REAL,
        timeframe TEXT,
        status TEXT NOT NULL DEFAULT 'active',
        sort_order INTEGER NOT NULL DEFAULT 0,
        created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
        updated_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now')),
        deleted_at TEXT,
        UNIQUE(strategy_id, name)
    )""",
    """CREATE TABLE IF NOT EXISTS content_pillars (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workspace_id INTEGER NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
        company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
        strategy_id INTEGER NOT NULL REFERENCES content_strategies(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        slug TEXT NOT NULL,
        description TEXT,
        objective TEXT,
        status TEXT NOT NULL DEFAULT 'active',
        sort_order INTEGER NOT NULL DEFAULT 0,
        created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
        updated_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now')),
        deleted_at TEXT,
        UNIQUE(strategy_id, slug)
    )""",
    """CREATE TABLE IF NOT EXISTS content_subtopics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workspace_id INTEGER NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
        company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
        strategy_id INTEGER NOT NULL REFERENCES content_strategies(id) ON DELETE CASCADE,
        pillar_id INTEGER NOT NULL REFERENCES content_pillars(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        slug TEXT NOT NULL,
        description TEXT,
        status TEXT NOT NULL DEFAULT 'active',
        sort_order INTEGER NOT NULL DEFAULT 0,
        created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
        updated_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now')),
        deleted_at TEXT,
        UNIQUE(pillar_id, slug)
    )""",
    """CREATE TABLE IF NOT EXISTS content_angles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workspace_id INTEGER NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
        company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
        strategy_id INTEGER NOT NULL REFERENCES content_strategies(id) ON DELETE CASCADE,
        pillar_id INTEGER NOT NULL REFERENCES content_pillars(id) ON DELETE CASCADE,
        subtopic_id INTEGER REFERENCES content_subtopics(id) ON DELETE SET NULL,
        title TEXT NOT NULL,
        slug TEXT NOT NULL,
        description TEXT,
        hook TEXT,
        cta TEXT,
        status TEXT NOT NULL DEFAULT 'active',
        sort_order INTEGER NOT NULL DEFAULT 0,
        created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
        updated_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now')),
        deleted_at TEXT,
        UNIQUE(strategy_id, slug)
    )""",
    """CREATE TABLE IF NOT EXISTS content_format_variants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workspace_id INTEGER NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
        company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
        strategy_id INTEGER NOT NULL REFERENCES content_strategies(id) ON DELETE CASCADE,
        angle_id INTEGER REFERENCES content_angles(id) ON DELETE CASCADE,
        platform TEXT NOT NULL DEFAULT 'facebook',
        format_type TEXT NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        specs TEXT,
        status TEXT NOT NULL DEFAULT 'active',
        sort_order INTEGER NOT NULL DEFAULT 0,
        created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
        updated_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now')),
        deleted_at TEXT,
        UNIQUE(strategy_id, angle_id, platform, format_type)
    )""",
    """CREATE TABLE IF NOT EXISTS content_calendar_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workspace_id INTEGER NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
        company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
        strategy_id INTEGER NOT NULL REFERENCES content_strategies(id) ON DELETE CASCADE,
        pillar_id INTEGER REFERENCES content_pillars(id) ON DELETE SET NULL,
        subtopic_id INTEGER REFERENCES content_subtopics(id) ON DELETE SET NULL,
        angle_id INTEGER REFERENCES content_angles(id) ON DELETE SET NULL,
        format_variant_id INTEGER REFERENCES content_format_variants(id) ON DELETE SET NULL,
        campaign_id INTEGER REFERENCES campaigns(id) ON DELETE SET NULL,
        post_id INTEGER REFERENCES posts(id) ON DELETE SET NULL,
        schedule_id INTEGER REFERENCES schedules(id) ON DELETE SET NULL,
        title TEXT NOT NULL,
        brief TEXT,
        platform TEXT NOT NULL DEFAULT 'facebook',
        content_type TEXT,
        planned_date TEXT,
        scheduled_at TEXT,
        status TEXT NOT NULL DEFAULT 'draft',
        metadata TEXT,
        sort_order INTEGER NOT NULL DEFAULT 0,
        created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
        updated_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now')),
        deleted_at TEXT,
        UNIQUE(strategy_id, planned_date, platform, title)
    )""",
    """CREATE TABLE IF NOT EXISTS content_strategy_kpis (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workspace_id INTEGER NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
        company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
        strategy_id INTEGER NOT NULL REFERENCES content_strategies(id) ON DELETE CASCADE,
        calendar_item_id INTEGER REFERENCES content_calendar_items(id) ON DELETE CASCADE,
        analytics_id INTEGER REFERENCES analytics(id) ON DELETE SET NULL,
        metric_name TEXT NOT NULL,
        target_value REAL,
        actual_value REAL,
        unit TEXT,
        status TEXT NOT NULL DEFAULT 'tracking',
        sort_order INTEGER NOT NULL DEFAULT 0,
        created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
        updated_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now')),
        deleted_at TEXT,
        UNIQUE(strategy_id, calendar_item_id, metric_name)
    )""",
    """CREATE TABLE IF NOT EXISTS lead_magnets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workspace_id INTEGER NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
        company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
        strategy_id INTEGER NOT NULL REFERENCES content_strategies(id) ON DELETE CASCADE,
        pillar_id INTEGER REFERENCES content_pillars(id) ON DELETE SET NULL,
        name TEXT NOT NULL,
        description TEXT,
        asset_type TEXT,
        offer_url TEXT,
        status TEXT NOT NULL DEFAULT 'draft',
        sort_order INTEGER NOT NULL DEFAULT 0,
        created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
        updated_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now')),
        deleted_at TEXT,
        UNIQUE(strategy_id, name)
    )""",
    """CREATE TABLE IF NOT EXISTS content_generation_jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workspace_id INTEGER NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
        company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
        strategy_id INTEGER REFERENCES content_strategies(id) ON DELETE CASCADE,
        prompt_version_id INTEGER REFERENCES prompt_versions(id) ON DELETE SET NULL,
        learning_insight_id INTEGER REFERENCES learning_insights(id) ON DELETE SET NULL,
        job_type TEXT NOT NULL DEFAULT 'strategy_generation',
        provider TEXT,
        model_name TEXT,
        status TEXT NOT NULL DEFAULT 'queued',
        input_summary TEXT,
        output_summary TEXT,
        request_metadata TEXT,
        validation_errors TEXT,
        error_message TEXT,
        started_at TEXT,
        completed_at TEXT,
        sort_order INTEGER NOT NULL DEFAULT 0,
        created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
        updated_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now')),
        deleted_at TEXT
    )""",
]


POSTGRESQL_TABLES = [
    stmt.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
    .replace("metadata TEXT", "metadata JSONB")
    .replace("snapshot TEXT NOT NULL", "snapshot JSONB NOT NULL")
    .replace("pain_points TEXT", "pain_points JSONB")
    .replace("goals TEXT", "goals JSONB")
    .replace("preferred_channels TEXT", "preferred_channels JSONB")
    .replace("specs TEXT", "specs JSONB")
    .replace("request_metadata TEXT", "request_metadata JSONB")
    .replace("validation_errors TEXT", "validation_errors JSONB")
    .replace("created_at TEXT DEFAULT (datetime('now'))", "created_at TIMESTAMPTZ DEFAULT NOW()")
    .replace("updated_at TEXT DEFAULT (datetime('now'))", "updated_at TIMESTAMPTZ DEFAULT NOW()")
    for stmt in SQLITE_TABLES
]


EXTRA_COLUMNS = {
    "campaigns": {
        "company_id": "INTEGER REFERENCES companies(id) ON DELETE CASCADE",
        "target_personas": "TEXT",
        "business_goals": "TEXT",
        "pillars": "TEXT",
        "key_message": "TEXT",
        "offer": "TEXT",
        "cta": "TEXT",
        "owner": "TEXT",
        "kpi": "TEXT",
        "metadata": "TEXT",
        "is_template": "INTEGER DEFAULT 0",
        "template_name": "TEXT",
    },
    "lead_magnets": {
        "type": "TEXT",
        "target_persona": "TEXT",
        "pain_point": "TEXT",
        "value_proposition": "TEXT",
        "cta": "TEXT",
        "destination_url": "TEXT",
        "campaign_id": "INTEGER REFERENCES campaigns(id) ON DELETE SET NULL",
        "funnel_stage": "TEXT",
        "asset_reference": "TEXT",
        "metadata": "TEXT",
    },
    "content_subtopics": {
        "target_persona": "TEXT",
        "business_goal": "TEXT",
        "intent": "TEXT",
        "funnel_stage": "TEXT",
        "priority": "TEXT",
        "trend_classification": "TEXT",
        "suggested_channels": "TEXT",
        "source": "TEXT DEFAULT 'manual'",
        "metadata": "TEXT",
    },
    "content_angles": {
        "category": "TEXT",
        "core_insight": "TEXT",
        "intended_emotion": "TEXT",
        "target_persona": "TEXT",
        "funnel_stage": "TEXT",
        "cta_type": "TEXT",
        "evidence_requirement": "TEXT",
        "trend_classification": "TEXT",
        "priority": "TEXT",
        "risk_level": "TEXT",
        "source": "TEXT DEFAULT 'manual'",
        "metadata": "TEXT",
    },
    "content_strategy_kpis": {
        "scope_level": "TEXT DEFAULT 'strategy'",
        "campaign_id": "INTEGER REFERENCES campaigns(id) ON DELETE SET NULL",
        "platform": "TEXT",
        "baseline_value": "REAL",
        "period": "TEXT",
        "data_source": "TEXT",
        "owner": "TEXT",
        "metadata": "TEXT",
    },
    "content_calendar_items": {
        "approval_status": "TEXT",
        "publishing_status": "TEXT",
    },
    "content_format_variants": {
        "target_length": "TEXT",
        "tone_override": "TEXT",
        "cta": "TEXT",
        "visual_requirement": "TEXT",
        "hook_style": "TEXT",
        "publishing_objective": "TEXT",
        "repurposing_source": "TEXT",
        "priority": "TEXT",
        "publishing_enabled": "INTEGER DEFAULT 0",
        "production_effort": "TEXT",
        "adaptation_guidance": "TEXT",
        "brief": "TEXT",
        "metadata": "TEXT",
    },
    "learning_insights": {
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
    },}

SQLITE_EXTRA_TABLES = [
    """CREATE TABLE IF NOT EXISTS lead_magnet_calendar_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workspace_id INTEGER NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
        company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
        strategy_id INTEGER NOT NULL REFERENCES content_strategies(id) ON DELETE CASCADE,
        lead_magnet_id INTEGER NOT NULL REFERENCES lead_magnets(id) ON DELETE CASCADE,
        calendar_item_id INTEGER NOT NULL REFERENCES content_calendar_items(id) ON DELETE CASCADE,
        created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
        created_at TEXT DEFAULT (datetime('now')),
        UNIQUE(lead_magnet_id, calendar_item_id)
    )""",
]

POSTGRESQL_EXTRA_TABLES = [
    stmt.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
    .replace("created_at TEXT DEFAULT (datetime('now'))", "created_at TIMESTAMPTZ DEFAULT NOW()")
    for stmt in SQLITE_EXTRA_TABLES
]

POSTGRES_EXTRA_COLUMNS = {
    table: {
        name: col_type.replace("TEXT", "JSONB") if name == "metadata" else col_type
        for name, col_type in columns.items()
    }
    for table, columns in EXTRA_COLUMNS.items()
}

INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_content_strategies_tenant ON content_strategies(workspace_id, company_id, status)",
    "CREATE INDEX IF NOT EXISTS idx_strategy_versions_strategy ON content_strategy_versions(strategy_id, version)",
    "CREATE INDEX IF NOT EXISTS idx_audience_personas_strategy ON audience_personas(strategy_id, sort_order)",
    "CREATE INDEX IF NOT EXISTS idx_business_goals_strategy ON business_goals(strategy_id, sort_order)",
    "CREATE INDEX IF NOT EXISTS idx_content_pillars_strategy ON content_pillars(strategy_id, sort_order)",
    "CREATE INDEX IF NOT EXISTS idx_content_subtopics_pillar ON content_subtopics(pillar_id, sort_order)",
    "CREATE INDEX IF NOT EXISTS idx_content_angles_strategy ON content_angles(strategy_id, sort_order)",
    "CREATE INDEX IF NOT EXISTS idx_content_formats_strategy ON content_format_variants(strategy_id, sort_order)",
    "CREATE INDEX IF NOT EXISTS idx_calendar_strategy_date ON content_calendar_items(strategy_id, planned_date, status)",
    "CREATE INDEX IF NOT EXISTS idx_calendar_workspace_company ON content_calendar_items(workspace_id, company_id, planned_date)",
    "CREATE INDEX IF NOT EXISTS idx_strategy_kpis_strategy ON content_strategy_kpis(strategy_id, metric_name)",
    "CREATE INDEX IF NOT EXISTS idx_lead_magnets_strategy ON lead_magnets(strategy_id, status)",
    "CREATE INDEX IF NOT EXISTS idx_lead_magnets_campaign ON lead_magnets(workspace_id, company_id, campaign_id)",
    "CREATE INDEX IF NOT EXISTS idx_lead_magnet_calendar ON lead_magnet_calendar_items(workspace_id, company_id, strategy_id)",
    "CREATE INDEX IF NOT EXISTS idx_generation_jobs_strategy ON content_generation_jobs(strategy_id, status)",
    "CREATE INDEX IF NOT EXISTS idx_learning_strategy_status ON learning_insights(workspace_id, company_id, strategy_id, status)",
]


def up(conn=None, engine=None):
    owns_connection = conn is None
    conn = conn or get_db_connection()
    engine = engine or ("postgresql" if _is_postgres() else "sqlite")
    try:
        cur = conn.cursor()
        if engine != "postgresql":
            cur.execute("PRAGMA foreign_keys = ON")
        for stmt in POSTGRESQL_TABLES if engine == "postgresql" else SQLITE_TABLES:
            cur.execute(stmt)
        for stmt in POSTGRESQL_EXTRA_TABLES if engine == "postgresql" else SQLITE_EXTRA_TABLES:
            cur.execute(stmt)
        for table, columns in (POSTGRES_EXTRA_COLUMNS if engine == "postgresql" else EXTRA_COLUMNS).items():
            ensure_columns(cur, table, columns)
        for stmt in INDEXES:
            cur.execute(stmt)
        conn.commit()
    finally:
        if owns_connection:
            conn.close()


def down(conn=None, engine=None):
    owns_connection = conn is None
    conn = conn or get_db_connection()
    engine = engine or ("postgresql" if _is_postgres() else "sqlite")
    try:
        cur = conn.cursor()
        if engine != "postgresql":
            cur.execute("PRAGMA foreign_keys = OFF")
        for table in TABLES:
            cur.execute(f"DROP TABLE IF EXISTS {table}")
        conn.commit()
    finally:
        if owns_connection:
            conn.close()








