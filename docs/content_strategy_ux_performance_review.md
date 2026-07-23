# AI Content Strategy Center UX and Performance Review

Date: 2026-07-20
Scope: UX, session state, performance, error handling, and accessibility for the existing Streamlit AI Content Strategy Center. No new business capability was added.

## Current Flow Before Changes

- `app/main.py` authenticates the user, resolves `active_workspace_id`, and renders `render_tab_content_planning_wizard` for the Content Planning wizard page.
- `ui/tab_content_planning_wizard.py` selects a company inside the active workspace, keeps wizard draft state under a workspace/company-scoped session key, and renders the step wizard.
- Draft creation, opening, saving, duplication, archive, restore, activation, AI generation, publishing readiness, and handoff are routed through `ContentStrategyService`.
- `ContentStrategyService` validates workspace/company context, calls generation services where needed, and persists through `ContentStrategyRepository`.
- `ContentStrategyRepository` requires `workspace_id` and `company_id` in public methods and checks tenant ownership before writes.

## Findings Fixed

### UX and Accessibility

Before:
- Progress showed the current step only; users could not scan which steps were complete or blocked.
- Autosave visibility only said the draft was persisted, without a last-saved timestamp.
- Destructive actions like archive, restore, delete persona/goal/pillar/subtopic/angle/format/calendar items executed after one click.
- AI and database errors were often displayed as raw provider/database text without next-step guidance.

After:
- Added a step completion status table with status, action, and first blocking issue per step.
- Added explicit autosave captions: not created, pending changes, loaded from saved draft, or saved timestamp.
- Added confirmation checkboxes before destructive archive, restore, and delete actions.
- Added friendly error guidance for Gemini 429, Gemini 503, timeout, invalid JSON, database locked, lost connection, invalid workspace, permission denied, publishing configuration missing, and session-expired style failures.
- Status is conveyed with text labels and guidance, not only color.

### Session State

Before:
- Wizard draft state was workspace/company-scoped, but helper `current_*_for_strategy` values were global and logout did not clear wizard state.
- Company select widget key was not workspace-scoped, creating risk of stale selection after switching tenants.
- Action buttons did not consistently guard against rapid duplicate clicks.

After:
- Added `clear_content_strategy_session_state()` and call it on logout and workspace switch.
- Made company selector key workspace-scoped.
- Added in-state action guard for open, save, duplicate, archive, and restore actions.

### Performance

Before:
- Strategy picker loaded all strategies for a company every rerun.
- Repository `list_strategies` had no `limit/offset` parameters.
- `get_strategy(..., include_children=True)` loaded soft-deleted children from child tables.

After:
- Added optional repository/service pagination with `limit` and `offset` while preserving old callers.
- UI strategy picker now pages strategies at 10/25/50 per page.
- Child loading now filters `deleted_at IS NULL` for soft-delete-aware child tables.

### Error Handling

Before:
- Retryability covered Gemini 429/503/timeout but not database locked or lost connection.
- UI error messages exposed raw operational wording without enough retry guidance.

After:
- Expanded retry classification for database lock and lost/interrupted connection cases.
- Standardized UI messages with action guidance and retryability wording.
- Existing sensitive value redaction remains in service error handling.

## Bottleneck Before/After

| Area | Before | After | Impact |
| --- | --- | --- | --- |
| Strategy picker | Loaded every strategy on every rerun | Paged with `limit/offset`, default 25 | Lower DB/read and render cost for large strategy lists |
| Deleted children | Soft-deleted rows were loaded with full strategy | Filters deleted children | Less noise, fewer rows rendered, correct state recovery |
| Repeated actions | Save/archive/restore/open could be clicked rapidly | Guarded by loading/action state | Reduces duplicate operations during Streamlit reruns |
| Autosave visibility | Persisted message only | Last-saved timestamp and dirty state | Easier recovery and less user uncertainty |

## Database Impact

- No destructive schema change.
- No migration required.
- Repository signatures are backwards compatible.
- Existing indexes remain compatible with the new `LIMIT/OFFSET` strategy list query.
- Tenant filters continue to require `workspace_id` and `company_id`.

## Security Impact

- No API key, token, or JWT logging added.
- Error display continues to use sanitized messages and friendlier guidance.
- Logout and workspace switch now clear Content Strategy session state, reducing cross-tenant/stale-data risk.
- UI still does not call Gemini directly; generation remains behind `ContentStrategyService`.

## Tests Updated

- Wizard helper tests for autosave captions, step completion rows, friendly errors, retry classification, and service pagination.
- Repository tests for `limit/offset` strategy listing and soft-deleted calendar children being excluded from loaded strategy data.

## Manual Verification Steps

1. Log in, open Content Planning Wizard, create a new strategy, type required Business Context fields, and confirm autosave caption changes from draft not created to pending/saved.
2. Switch workspace and verify the previous strategy/company state is not shown.
3. Log out and log back in; verify the previous Content Strategy session state is cleared.
4. Create more than 25 strategies and verify Next/Previous strategy pagination works.
5. Try archive/restore/delete actions and confirm they remain disabled until the confirmation checkbox is selected.
6. Trigger an AI generation failure with a mocked 429/503/timeout and verify the error gives retry guidance.
7. Toggle Streamlit light/dark mode and scan labels, warnings, errors, and table text for readable contrast.
8. Resize within Streamlit-supported widths and verify controls remain usable without overlapping text.

## Known Issues

- Streamlit widget testing is still mostly helper-level; visual UX should be manually verified in the running app.
- Long in-memory draft sections such as generated calendars are still held in Streamlit session state until persisted; calendar row rendering is paged, but generation itself remains synchronous.
- No new database index was added because the existing tenant/status and calendar indexes match the changed queries.

## Recommended Next Task

Run a focused Streamlit visual QA pass for the wizard in light and dark mode, then address any layout-specific issues found with screenshots.
