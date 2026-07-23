# AI Content Strategy Center UAT Checklist

Ngay tao: 2026-07-20

Use this checklist for final manual Streamlit acceptance. Mark each item with Pass, Fail, or N/A and attach evidence where possible.

## Preconditions

- Database backup completed.
- `database.migrations.content_strategy_center.up()` has been run.
- Test user accounts exist for viewer, editor, marketing, manager/admin.
- At least two workspaces and two companies exist.
- Gemini key configured for live AI tests, or mock provider mode documented.

## Main End-To-End Flow

| # | Step | Expected Result | Status |
|---:|---|---|---|
| 1 | User login | User lands in authenticated Streamlit app without session leakage. | Not run |
| 2 | Select workspace/company | Strategy Center company selector shows only companies for active workspace. | Not run |
| 3 | Open AI Content Strategy Center | Existing route opens screen titled `AI Content Strategy Center`. | Not run |
| 4 | Create Strategy | New draft strategy is created with workspace/company scope. | Not run |
| 5 | Enter Business Context | Required fields validate; Save Draft persists draft. | Not run |
| 6 | Read Brand Identity | Existing brand seeds are loaded without overwriting global brand. | Not run |
| 7 | Create Persona | Manual and AI draft personas can be reviewed, edited, confirmed. | Not run |
| 8 | Select Business Goals | Goals persist and validate required fields. | Not run |
| 9 | Generate Content Pillars | AI/manual pillars are generated without placeholder fake data. | Not run |
| 10 | Edit Pillar | Pillar edit persists and version can capture change. | Not run |
| 11 | Generate Subtopics | Batch generation works, partial failures are visible. | Not run |
| 12 | Generate Angles | Batch generation works, retry/resume available. | Not run |
| 13 | Select Formats | Format variants are linked to angles/platforms. | Not run |
| 14 | Create 30-day calendar | Calendar items are created for 30-day range. | Not run |
| 15 | Create 365-day calendar | Calendar generation handles large range without UI hang. | Not run |
| 16 | Create Campaign | Campaign is created in same workspace/company. | Not run |
| 17 | Attach Lead Magnet | Lead magnet links to selected campaign/calendar items. | Not run |
| 18 | Set KPI | KPI is created at strategy/campaign/calendar scope. | Not run |
| 19 | Move post to Content Studio | Draft post is created with strategy metadata and workspace scope. | Not run |
| 20 | Send Approval | Approval request appears in Approval Flow. | Not run |
| 21 | Create Schedule | Schedule row links to post/calendar item. | Not run |
| 22 | Read Analytics | Analytics are read only for active workspace/company. | Not run |
| 23 | Create Learning Insight | Learning insight links to strategy and can be reused. | Not run |
| 24 | Create new Strategy Version | Version snapshot is created and listed. | Not run |
| 25 | Restore previous version | Restore reverts root and children to selected snapshot. | Not run |

## Regression Checklist

| Area | Expected Result | Status |
|---|---|---|
| Login/register | Register and login still work. | Not run |
| Workspace switching | Switching workspace clears Strategy Center state and does not leak data. | Not run |
| Brand Identity | Existing Brand tab can read/write brand data. | Not run |
| Content Studio | Drafts from Strategy Center appear correctly. | Not run |
| Knowledge Center | Knowledge upload/list/search still works by workspace. | Not run |
| Publishing | Existing publishing tab still opens and schedules/publishes supported posts. | Not run |
| Approval Flow | Approval kanban/list still scoped to workspace. | Not run |
| Analytics | Analytics page opens and filters by workspace. | Not run |
| Billing/Quota | Billing and AI cost pages open. | Not run |
| Audit Log | Audit tab shows strategy events without secrets. | Not run |
| Existing weekly plan | Legacy weekly planning flow still generates plan. | Not run |
| SQLite startup | App starts with SQLite after migration. | Automated pass |
| PostgreSQL compatibility | App starts with PostgreSQL staging DB. | Not run |

## Security Checklist

| Area | Expected Result | Status |
|---|---|---|
| Workspace isolation | Workspace A cannot read Strategy Center data from Workspace B. | Automated pass |
| Company isolation | Company A cannot read Strategy Center data from Company B. | Automated pass |
| IDOR | Direct IDs from other tenants return not found/error. | Automated pass |
| Role permissions | Viewer cannot create/edit/save/archive/restore/activate. | Code reviewed; manual pending |
| Cross-tenant links | Campaign, lead magnet, KPI, calendar refs validate tenant. | Automated pass |
| Session leakage | Switching workspace/company changes session key. | Code reviewed; manual pending |
| Sensitive logs | No API key/token/JWT in Strategy Center errors/audit. | Code reviewed |
| Audit completeness | Create/update/generate/link events produce audit rows. | Automated partial pass |

## Acceptance Decision

Final UAT owner:

Date:

Decision: Pending.
