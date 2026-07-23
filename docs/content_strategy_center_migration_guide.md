# AI Content Strategy Center Migration Guide

Ngay tao: 2026-07-20

## Overview

This migration adds normalized persistence for AI Content Strategy Center. It is non-destructive: it creates new tables and indexes and adds compatible nullable columns to existing integration tables.

Migration file:

- `database/migrations/content_strategy_center.py`

Primary functions:

- `up(conn=None, engine=None)`
- `down(conn=None, engine=None)`

## Tables Added

- `content_strategies`
- `content_strategy_versions`
- `audience_personas`
- `business_goals`
- `content_pillars`
- `content_subtopics`
- `content_angles`
- `content_format_variants`
- `content_calendar_items`
- `content_strategy_kpis`
- `lead_magnets`
- `lead_magnet_calendar_items`
- `content_generation_jobs`

## Existing Tables Extended

The migration uses `ensure_columns()` to add compatible columns when missing:

- `campaigns`
- `lead_magnets`
- `content_subtopics`
- `content_angles`
- `content_strategy_kpis`
- `content_calendar_items`
- `content_format_variants`
- `learning_insights`

## Before Migration

1. Back up the database.
2. Confirm the app can start on the current version.
3. Record current `DB_ENGINE` and DB path/connection settings.
4. Stop write traffic if this is a shared environment.
5. Run the focused Strategy Center tests against a clean local SQLite database.

## SQLite Migration

From project root:

```powershell
python -c "from database.migrations.content_strategy_center import up; up(engine='sqlite')"
```

Then start the app and confirm:

- Strategy Center opens.
- Company selector loads.
- New draft can be created and saved.
- Existing modules still open.

## PostgreSQL Migration

Set the project environment for PostgreSQL first.

Then run:

```powershell
python -c "from database.migrations.content_strategy_center import up; up(engine='postgresql')"
```

Verify:

- JSON fields are created as JSONB where supported.
- Index creation succeeds.
- Existing tables still contain their previous data.
- Strategy reads/writes use `%s` placeholders through `_adapt_sql()`.

## Existing Database Migration

For an existing database:

1. Create a database backup.
2. Run `up()`.
3. Run smoke test for login, workspace switch, Brand Identity, Content Studio, Publishing, Analytics, Audit.
4. Create one Strategy Center draft in a non-production workspace.
5. Restore a strategy version to confirm snapshot behavior.

The migration does not automatically convert legacy `weekly_schedules` into content strategies.

## Data Integrity Rules

- Every strategy table row must have `workspace_id`.
- Every strategy table row must have `company_id`.
- Child rows must reference a strategy from the same workspace/company.
- Campaign, lead magnet, KPI, calendar, post, schedule links must be tenant-validated.
- JSON metadata must be serialized/deserialized through repository helpers.

## Validation Commands

```powershell
python -m unittest tests.test_content_strategy_repository tests.test_content_strategy_ai_service tests.test_content_strategy_wizard tests.test_content_strategy_subtopics_angles tests.test_content_strategy_calendar tests.test_content_strategy_campaigns_lead_magnets tests.test_content_strategy_kpi_publishing tests.test_content_strategy_learning_loop
```

Expected result:

```text
Ran 76 tests
OK
```

```powershell
python -m compileall app ui services database core agents tests
```

Expected result: no compile errors.

## Migration Impact

Database impact:

- Adds new Strategy Center tables.
- Adds nullable compatibility columns to existing integration tables.
- Does not delete or rewrite existing data.

Application impact:

- Existing navigation route remains compatible.
- Strategy Center data is normalized and scoped by workspace/company.
- Legacy weekly plan flow is not migrated automatically.

## Rollback Reference

Rollback instructions are in:

- `docs/content_strategy_center_rollback_guide.md`
