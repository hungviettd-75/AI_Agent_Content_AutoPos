# AI Content Strategy Center Rollback Guide

Ngay tao: 2026-07-20

## Rollback Decision Criteria

Rollback if any of these occur in staging or production:

- Strategy Center exposes cross-tenant data.
- Login/workspace switching is broken.
- Existing Content Studio, Publishing, Approval, or Analytics cannot open.
- Migration fails and leaves database in an unknown state.
- AI generation failures cause data loss or unhandled crashes.

## Immediate Safe Rollback

1. Disable or hide the Strategy Center route in navigation if needed.
2. Keep the existing `Content Planning (Wizard)` route name stable.
3. Stop live Strategy Center usage.
4. Preserve database backup and current logs for investigation.

## Database Rollback

Run only after confirming that newly created Strategy Center data can be discarded or has been exported.

SQLite:

```powershell
python -c "from database.migrations.content_strategy_center import down; down(engine='sqlite')"
```

PostgreSQL:

```powershell
python -c "from database.migrations.content_strategy_center import down; down(engine='postgresql')"
```

The rollback drops only tables introduced by the Strategy Center migration:

- `lead_magnet_calendar_items`
- `content_generation_jobs`
- `content_strategy_kpis`
- `content_calendar_items`
- `content_format_variants`
- `content_angles`
- `content_subtopics`
- `content_pillars`
- `lead_magnets`
- `business_goals`
- `audience_personas`
- `content_strategy_versions`
- `content_strategies`

## What Rollback Does Not Undo

The migration rollback does not remove compatibility columns added to existing tables, including:

- `campaigns`
- `learning_insights`
- content strategy child-table extension columns if the tables remain

These nullable columns are intentionally left in place to avoid destructive schema changes.

## Version Restore Instead Of Rollback

For bad strategy edits, prefer restoring a previous strategy version:

1. Open AI Content Strategy Center.
2. Select the affected workspace/company.
3. Open the strategy.
4. Choose the prior version.
5. Confirm `Restore Version`.

This restores the strategy root and child rows from `content_strategy_versions` without removing the module.

## AI Rollback

If AI generation is unstable:

- Disable live generation controls operationally.
- Keep manual strategy editing available.
- Keep existing weekly plan and Content Studio workflows available.
- Do not insert fake fallback strategy data.

## Publishing Rollback

If created schedules are wrong:

1. Cancel or unschedule unpublished items through Publishing/Approval tools.
2. Keep already published posts as records; do not delete them silently.
3. Archive the affected strategy instead of deleting production history.

## Post-Rollback Verification

Run:

```powershell
python -m compileall app ui services database core agents tests
```

Then manually verify:

- Login/register.
- Workspace switching.
- Brand Identity.
- Content Studio.
- Publishing.
- Approval Flow.
- Analytics.
- Audit Log.
- Existing weekly plan.

## Recovery

To re-enable Strategy Center after fixes:

1. Restore from backup if database rollback was destructive to strategy data.
2. Re-run `database.migrations.content_strategy_center.up()`.
3. Run the Strategy Center automated tests.
4. Complete the UAT checklist.
