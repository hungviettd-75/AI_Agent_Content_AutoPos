# AI Content Strategy Center Release Notes

Ngay tao: 2026-07-20

## Summary

The existing `Content Planning Wizard` route now hosts the `AI Content Strategy Center`. The upgrade keeps the Streamlit monolith and existing navigation pattern while adding normalized strategy persistence, tenant-scoped repositories, AI output validation, version restore, campaign/lead magnet/KPI/calendar integrations, and documented migration/rollback procedures.

## What Changed

- Added Strategy Center wizard shell under existing content planning route.
- Added workspace/company-scoped session state.
- Added business context, brand identity, persona, goals, pillars, subtopics, angles, formats, calendar, campaign, lead magnet, KPI, publishing, analytics, learning, and version flows.
- Added service layer so Strategy Center UI calls `ContentStrategyService` instead of Gemini directly.
- Added JSON parser/validator for object-root strategy outputs.
- Added retry/repair handling for malformed AI responses and transient provider errors.
- Added normalized database tables for strategies and child entities.
- Added strategy version snapshots and restore behavior.
- Added audit-safe payload summaries for Strategy Center events.
- Added migration, rollback, architecture, database, AI pipeline, wizard, test, UAT, and release documentation.

## Security Notes

- Strategy data is scoped by `workspace_id` and `company_id`.
- Repository methods validate tenant ownership before read/write.
- Viewer role is read-only in the wizard UI.
- Strategy Center errors use safe messages and do not expose API keys, access tokens, or JWTs.
- Audit payloads record counts/flags rather than raw sensitive business context.

## AI Notes

- Live Gemini calls are behind `ContentStrategyService`.
- Invalid JSON and validation failures trigger one repair attempt.
- Timeout, 429, and 503 style failures are retryable.
- The service records AI cost estimates through `AICostModel` when possible.
- No fake data fallback is used for failed AI generation.

## Database Notes

Migration:

- `database/migrations/content_strategy_center.py`

Run:

```powershell
python -c "from database.migrations.content_strategy_center import up; up(engine='sqlite')"
```

Rollback:

```powershell
python -c "from database.migrations.content_strategy_center import down; down(engine='sqlite')"
```

For PostgreSQL, use `engine='postgresql'` with PostgreSQL environment configured.

## Test Result

Focused Strategy Center tests:

- 76 passed.
- 0 failed.

Full discovered test suite:

- 123 total.
- 122 passed.
- 1 failed.

Known failing regression:

- `tests/test_thumbnail_features.py::test_thumbnail_analytics_crud`
- Failure: `summary.total_impressions` lower than expected.
- Severity: Medium.

## Known Issues

- Manual Streamlit UAT checklist is still pending.
- PostgreSQL live migration was not executed in this run.
- Legacy generic Gemini client still logs prompt snippets for older flows.
- Thumbnail analytics regression needs triage or explicit acceptance as unrelated.

## Release Recommendation

Conditional Go for staging/UAT.

No-Go for production sign-off until manual UAT is complete and the thumbnail analytics regression is triaged or accepted.

Do not call this Production Ready yet.
