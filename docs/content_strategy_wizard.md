# AI Content Strategy Center Wizard

This document covers the Streamlit wizard shell that upgrades the existing Content Planning Wizard route into the AI Content Strategy Center.

## Current Route

The existing navigation key remains `Content Planning (Wizard)` and is still routed from `app/main.py` to `ui/tab_content_planning_wizard.py`. The displayed screen title is now `AI Content Strategy Center` so existing navigation state is not broken.

## Scope

The first three steps are implemented as structured strategy inputs. The UI never calls Gemini directly; AI persona generation runs through `services/content_strategy_service.py` and returns reviewable drafts only.

## Wizard Steps

1. Business Context
2. Brand Identity
3. Audience Personas
4. Business Goals
5. Content Pillars
6. Subtopics
7. Content Angles
8. Formats and Channels
9. Content Calendar
10. Campaigns and Lead Magnets
11. KPI and Publishing
12. Review and Activate


## Implemented Step 1-3 Behavior

### Step 1: Business Context

Business Context can be entered field by field or loaded from Company Brain. The seed reader prefers the active `companies` row and supplements mission/vision from Brand Identity when available. Upload supports JSON, CSV key/value, and plain text imports. Imported data is merged into the strategy draft and does not update the global company profile.

Captured fields: company name, industry, website, market, business model, products, services, price range, competitive advantages, mission, vision, brand story, current marketing challenges, main competitors, marketing budget range, and available resources.

### Step 2: Brand Identity

Brand Identity can use the existing workspace brand or a strategy-specific customization. Customization is saved inside the strategy draft by default. It is written back to the global Brand Identity only when the user selects the explicit confirmation checkbox and triggers the save action.

Captured fields: tone of voice, personality, writing style, brand keywords, forbidden words, standard CTA, mission, vision, colors, and communication principles.

### Step 3: Audience Personas

The wizard supports multiple personas with add, edit, duplicate, delete, reorder, and completeness validation. AI generation is optional and never runs automatically. AI-generated personas are marked with `ai_generated_draft=true` and `status=draft`; the user must review/edit and confirm before treating them as active.

Captured fields: name, role, industry, company size, demographics if appropriate, goals, pain points, fears, desires, objections, buying triggers, decision authority, preferred channels, preferred content formats, content depth preference, language style, and customer journey stage.

Dedicated customer-data import is not currently backed by a customer repository in this project. The UI can seed from existing Company Brain context and reports when no supported customer-data source exists.

## State Management

Streamlit state is stored under a workspace/company scoped key:

`content_strategy_center_state_{workspace_id}_{company_id}`

The state contains the open `strategy_id`, current `step_index`, draft fields, dirty status, last saved hash, loading status, and the latest UI error. The draft is restored from `content_strategies.metadata.wizard_draft` when a strategy is opened.

## Persistence

Draft data is stored in `content_strategies.metadata.wizard_draft` through `ContentStrategyService.save_draft()`. Business Context, strategy-specific Brand Identity, and Audience Personas are structured objects/lists inside that draft. Autosave updates the current strategy without creating a version. Manual `Save Draft` creates a restore point through `content_strategy_versions`.

## Actions

- New Strategy: resets the local wizard state for a new draft.
- Open Strategy: loads a tenant-scoped strategy and restores draft state.
- Save Draft: persists draft data, writes a sanitized audit log, and creates a version.
- Duplicate Strategy: creates a new draft root with copied metadata.
- Archive Strategy: marks the strategy as archived.
- Restore Version: restores a saved version snapshot.
- Exit Wizard: clears the local wizard state.
- Activate: available on the final step for full-management roles.

## Validation

Each step validates only its own required draft field before moving forward. Steps 1-3 validate structured completeness. Persona validation also checks for unnecessary sensitive-data hints. The final Review and Activate step checks that all previous sections have content. Empty sections render a true empty state and are not marked complete by placeholder data.

## RBAC

Viewer can open and review strategies but cannot edit or save. Editor, Marketing, Manager, and CEO can edit drafts. Owner, Admin, and Super Admin can manage strategy lifecycle actions such as archive, restore, and activate.


## Security and Audit

- All persistence stays behind `ContentStrategyService` and repository/model layers.
- Workspace/company isolation is enforced before reading company seed data or saving strategy data.
- The UI does not call Gemini directly.
- Audit logs are written for strategy draft create/update, global Brand Identity save-back, and AI persona draft generation.
- Audit payloads are sanitized to counts/flags and do not include API keys, tokens, JWTs, or full persona/business sensitive content.
- Persona validation discourages unnecessary sensitive personal data.

## Tenant Isolation

All strategy operations go through `ContentStrategyService`, which uses `ContentStrategyRepository`. Repository methods require `workspace_id` and `company_id` and verify that strategies and companies belong to the active tenant.

## Database Impact

No new schema change is introduced by this task. Step 1-3 data is stored in `content_strategies.metadata.wizard_draft`, scoped by the existing `workspace_id` and `company_id` on `content_strategies`. Global Brand Identity is updated only through `BrandModel.upsert()` after explicit confirmation.

## Manual Verification

1. Log in and open the existing Content Planning Wizard tab.
2. Confirm the screen title reads `AI Content Strategy Center`.
3. Create a company profile if the workspace has none.
4. Click New Strategy, load or enter structured Business Context, then Save Draft.
5. Move through Previous and Next and confirm validation blocks incomplete Business Context, Brand Identity, and Persona records.
6. Add multiple personas, reorder one, refresh the Streamlit page and reopen the saved strategy.
7. Confirm structured Business Context, Brand Identity override, and persona order restore from the saved strategy.
8. Generate persona with AI only when requested; confirm generated rows show as AI drafts before activation.
9. As Viewer, confirm editing and lifecycle buttons are disabled.
10. As Owner/Admin, confirm Duplicate, Archive, Restore Version, Brand save-back confirmation, and Activate are available.

11. Open Content Studio and Publishing tabs to confirm navigation still works.
