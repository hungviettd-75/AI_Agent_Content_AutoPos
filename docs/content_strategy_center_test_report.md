# AI Content Strategy Center Test Report

Ngay nghiem thu: 2026-07-20

## Current State

`Content Planning Wizard` da duoc nang cap thanh `AI Content Strategy Center` tren cung route Streamlit cu. UI hien title moi, chon company theo workspace, va luu state theo key `content_strategy_center_state_{workspace_id}_{company_id}`.

Flow hien tai:

1. `app/main.py` xac thuc user, chon workspace, roi render `ui/tab_content_planning_wizard.py`.
2. Wizard chon company trong workspace va goi `ContentStrategyService`.
3. Service xu ly draft, AI generation, validation, audit, cost logging va repository persistence.
4. `ContentStrategyRepository` bat buoc co `workspace_id` va `company_id` cho strategy data.
5. Migration `database/migrations/content_strategy_center.py` tao bang strategy normalized va index tenant.

## Scope Review

Tai lieu da doi chieu:

- `docs/content_strategy_center_assessment.md`
- `docs/content_strategy_center_architecture.md`
- `docs/content_strategy_database.md`
- `docs/content_strategy_ai_pipeline.md`
- `docs/content_strategy_wizard.md`

Code da doi chieu:

- `app/main.py`
- `ui/tab_content_planning_wizard.py`
- `services/content_strategy_service.py`
- `services/content_strategy_validation.py`
- `agents/content_strategy_prompts.py`
- `database/migrations/content_strategy_center.py`
- `database/repositories/content_strategy_repository.py`
- `database/repositories/content_strategy_generation_repository.py`
- `database/models/content_strategy.py`
- `tests/test_content_strategy_*.py`

## Test Summary

Tong so test chay: 123

Passed: 122

Failed: 1

Skipped: 0

Strategy Center focused tests: 76 passed, 0 failed.

Compile check: passed for `app`, `ui`, `services`, `database`, `core`, `agents`, `tests`.

## Commands Executed

```powershell
python -m unittest tests.test_content_strategy_repository tests.test_content_strategy_ai_service tests.test_content_strategy_wizard tests.test_content_strategy_subtopics_angles tests.test_content_strategy_calendar tests.test_content_strategy_campaigns_lead_magnets tests.test_content_strategy_kpi_publishing tests.test_content_strategy_learning_loop
```

Result: `Ran 76 tests ... OK`

```powershell
python -m compileall app ui services database core agents tests
```

Result: success.

```powershell
python -m unittest discover -s tests -p "test_*.py"
```

Result: `Ran 123 tests`, `FAILED (failures=1)`.

## End-To-End Coverage

Automated service/repository coverage confirms:

- Create strategy.
- Load company/brand context.
- Generate valid AI strategy from mocked provider response.
- Validate JSON object, markdown-wrapped JSON, missing fields, wrong types, duplicates.
- Retry timeout/429/503 style failures and repair malformed JSON.
- Persist strategy, goals, pillars, subtopics, angles, formats, calendar, lead magnets, KPIs, generation jobs.
- Create 30-day and 365-day calendar data through calendar tests.
- Create campaign and link calendar items.
- Link lead magnet to calendar items.
- Set KPI and connect publishing/schedule behavior.
- Read analytics and create learning insights.
- Create and restore strategy versions.
- Reject cross-workspace/company reads and writes.

Manual Streamlit click-through was not executed in this run. The UAT checklist in `docs/content_strategy_center_uat_checklist.md` must be completed before final production sign-off.

## Regression Result

Critical modules checked by compile and existing tests:

- Login/register: compile pass; no dedicated full auth test found.
- Workspace switching: covered by Strategy Center workspace/company isolation tests and app compile.
- Brand Identity: covered by wizard/service tests and compile.
- Content Studio: compile pass; no dedicated test found in this run.
- Knowledge Center: compile pass; context-loading paths covered indirectly.
- Publishing: Strategy Center publishing/KPI test passed; legacy publishing compile pass.
- Approval Flow: Strategy Center approval/schedule paths covered; legacy approval compile pass.
- Analytics: Strategy Center learning loop tests passed.
- Billing/Quota: compile pass; AI cost logging covered in service code path.
- Audit Log: repository/service writes audit events; tests exercise audited creates.
- Existing weekly plan: compile pass; not deeply exercised by Strategy Center tests.
- SQLite startup: passed repeatedly in test setup.
- PostgreSQL compatibility layer: SQL adapter/migration DDL reviewed; no live PostgreSQL DB was available.

## Security Result

Passed automated/reviewed:

- Workspace isolation.
- Company isolation.
- IDOR protection for strategy, children, campaign, lead magnet, KPI, calendar item, version restore.
- Viewer UI restrictions are present through disabled edit/lifecycle actions.
- Cross-tenant object access blocked by repository `_require_*` checks.
- Strategy session state scoped by workspace/company.
- API key/token/JWT redaction path exists through `_safe_error_message()`.
- Audit events include `workspace_id` and safe payload summaries.

Open security cautions:

- Legacy `services/gemini_client.py` still logs first 300 chars of generic prompts. Strategy Center uses its own service path, but this remains a general sensitive-log risk for older flows.
- Full manual role matrix was not click-tested in Streamlit.

## AI Result

Covered:

- Valid response.
- Invalid JSON.
- Markdown-wrapped JSON.
- Missing fields.
- Duplicate content.
- Timeout.
- 429 retry.
- 503 retry.
- JSON repair.
- Partial regeneration.
- Resume/batch behavior for subtopics and angles.
- Cost recording path through `AICostModel`.

Not fully proven:

- Live Gemini behavior was not called; tests use mocks to avoid external dependency.
- Provider quota dashboards were not manually verified.

## Database Result

Covered:

- Clean SQLite migration.
- Idempotent migration.
- Foreign keys and cascade behavior.
- Index presence by migration review.
- Transactions and rollback.
- Version restore.
- Batch insert.
- Tenant-filtered reads/writes.

Not fully proven:

- Existing production database migration dry-run was not executed against a copy of production data.
- Live PostgreSQL migration was not executed.
- High-concurrency write load was not stress-tested beyond application-level transaction tests.

## Known Issues

| Severity | Area | Issue | Status |
|---|---|---|---|
| Medium | Regression | `tests/test_thumbnail_features.py::test_thumbnail_analytics_crud` failed because `summary.total_impressions` was lower than expected. | Open |
| Medium | UAT | Manual Streamlit click-through for the full 25-step flow was not executed in this run. | Open |
| Low | PostgreSQL | PostgreSQL compatibility reviewed by DDL/adapter, but no live PostgreSQL DB test was run. | Open |
| Low | Legacy AI logging | Generic Gemini client logs prompt snippets for older flows. | Open |

Critical issues: 0

High issues: 0

Medium issues: 2

Low issues: 2

## Files Changed

- `docs/content_strategy_center_test_report.md`
- `docs/content_strategy_center_uat_checklist.md`
- `docs/content_strategy_center_migration_guide.md`
- `docs/content_strategy_center_rollback_guide.md`
- `docs/content_strategy_center_release_notes.md`

## Migration Required

Run:

```python
from database.migrations.content_strategy_center import up
up(engine="sqlite")
```

For PostgreSQL, run the same migration with `engine="postgresql"` after configuring `DB_ENGINE=postgresql` and connection settings.

## Configuration Required

- `GEMINI_API_KEY` for live AI generation.
- Existing database config in `.env`.
- PostgreSQL variables only when using PostgreSQL.
- Social publishing tokens only for live publishing.

## Rollback

Use `docs/content_strategy_center_rollback_guide.md`.

Technical rollback:

```python
from database.migrations.content_strategy_center import down
down(engine="sqlite")
```

## Go/No-Go Recommendation

Recommendation: Conditional Go for staging/UAT, No-Go for production sign-off until:

- Full Streamlit UAT checklist is completed.
- The thumbnail analytics regression is triaged or explicitly accepted as unrelated.
- PostgreSQL migration is run against a staging PostgreSQL database if PostgreSQL is a supported production target.

Do not label this Production Ready yet.
