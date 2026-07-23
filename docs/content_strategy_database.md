# AI Content Strategy Center Database

This task adds normalized persistence for the AI Content Strategy Center. It does
not change the Streamlit UI and does not rewrite existing content planning flows.

## Current Flow

- Core schema is created from `database/schema.py` through `database.connection.init_db()`.
- Existing models use static CRUD helpers and `database.connection._adapt_sql()` for SQLite/PostgreSQL placeholders.
- Existing repositories are thin wrappers, but strategy data now uses a repository with tenant checks because every read/write must be scoped by `workspace_id` and `company_id`.
- Existing tables remain reusable integration points: `campaigns`, `posts`, `schedules`, `analytics`, `learning_insights`, `brand`, `companies`, `projects`, `knowledge`, `prompt_versions`, and `audit_logs`.

## Migration

Migration file:

- `database/migrations/content_strategy_center.py`

Public functions:

- `up(conn=None, engine=None)`
- `down(conn=None, engine=None)`

The migration is idempotent because every table and index uses `CREATE ... IF NOT EXISTS`.
Rollback drops only the tables introduced by this migration, in dependency order.

## New Tables

- `content_strategies`: strategy root scoped by workspace/company, with optional links to project/campaign.
- `content_strategy_versions`: version snapshots for restore.
- `audience_personas`: normalized personas per strategy.
- `business_goals`: measurable strategy goals.
- `content_pillars`: top-level content pillars.
- `content_subtopics`: pillar subtopics.
- `content_angles`: content angles linked to pillar/subtopic.
- `content_format_variants`: platform/format variants.
- `content_calendar_items`: normalized content calendar items linked to pillars, angles, posts, and schedules.
- `content_strategy_kpis`: strategy/calendar item KPI tracking with optional analytics link.
- `lead_magnets`: strategy lead magnet offers.
- `content_generation_jobs`: AI generation run metadata linked to prompt versions and learning insights.

## Tenant Rules

Repository methods require both `workspace_id` and `company_id`.

- A company must belong to the workspace before a strategy can be created.
- Strategy reads require matching `id`, `workspace_id`, and `company_id`.
- Child writes verify that the parent strategy and referenced pillar/subtopic/angle belong to the same tenant.
- Calendar item reads and writes are filtered by `workspace_id`, `company_id`, and `strategy_id`.

## JSON Usage

The strategy structure is not stored as one JSON blob. Pillars, subtopics,
angles, formats, and calendar items are normalized in separate tables.

JSON/TEXT fields are limited to flexible metadata:

- strategy `metadata`
- version `snapshot`
- persona arrays such as `pain_points`
- format `specs`
- generation job `request_metadata` and `validation_errors`
- calendar item `metadata`

SQLite stores JSON as `TEXT`; PostgreSQL DDL maps supported fields to `JSONB`.
The repository serializes/deserializes these fields consistently.

## Constraints And Indexes

Important constraints:

- `content_strategies`: `UNIQUE(workspace_id, company_id, name)`
- `content_strategy_versions`: `UNIQUE(strategy_id, version)`
- `content_pillars`: `UNIQUE(strategy_id, slug)`
- `content_subtopics`: `UNIQUE(pillar_id, slug)`
- `content_angles`: `UNIQUE(strategy_id, slug)`
- `content_calendar_items`: `UNIQUE(strategy_id, planned_date, platform, title)`

Important indexes:

- tenant/status index on `content_strategies`
- strategy/order indexes on personas, goals, pillars, angles, formats
- pillar/order index on subtopics
- strategy/date/status and tenant/date indexes on calendar items
- strategy indexes on KPIs, lead magnets, and generation jobs

## Repository API

Implemented in `database/repositories/content_strategy_repository.py`:

- `create_strategy()`
- `get_strategy()`
- `list_strategies()`
- `update_strategy()`
- `archive_strategy()`
- `create_pillar()`
- `update_pillar()`
- `reorder_pillars()`
- `create_subtopic()`
- `create_angles_batch()`
- `create_calendar_items_batch()`
- `list_calendar_items()`
- `update_calendar_item()`
- `delete_calendar_item()`
- `create_strategy_version()`
- `restore_strategy_version()`

## Rollback

Call `database.migrations.content_strategy_center.down()`.

Rollback drops only the new strategy tables. It does not modify existing
`campaigns`, `posts`, `schedules`, `analytics`, `learning_insights`,
`companies`, `brand`, `knowledge`, `prompt_versions`, or `audit_logs`.

