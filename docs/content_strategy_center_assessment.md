# AI Content Strategy Center Assessment

Pham vi task nay chi la assessment cho viec nang cap `Content Planning Wizard` thanh `AI Content Strategy Center`. Chua trien khai chuc nang moi, chua doi schema, chua refactor code nghiep vu.

## 1. Current Architecture

Ung dung hien la Streamlit monolithic, chia theo layer:

- Entry point/UI routing: `app/main.py`.
- UI tabs: `ui/tab_content_planning_wizard.py`, `ui/tab_campaign.py`, `ui/tab_brand.py`, `ui/tab_company_brain.py`, `ui/tab_knowledge.py`, `ui/tab_publishing.py`.
- Service AI/content: `services/content_service.py`, `services/gemini_client.py`, `services/trend_service.py`.
- Prompt templates: `agents/prompt_templates.py`.
- Repository/model/database: `database/repositories/weekly_schedule_repository.py`, `database/repositories/knowledge_repository.py`, `database/models/*.py`, `database/schema.py`, `database/connection.py`.
- Export/helper: `core/doc_exporter.py`.

Content Planning Wizard hien tai:

- UI chinh nam tai `ui/tab_content_planning_wizard.py`, function `render_tab_content_planning_wizard()` dong 115.
- Route/tab duoc import trong `app/main.py` dong 24 va render khi `active_page == "🗓️ Content Planning (Wizard)"` tai dong 591-592.
- Tab mac dinh duoc khai bao trong `ui/nav_config.py`, `DEFAULT_NAV` dong 10 va nhom nav dong 16-17.
- `workspace_id` duoc lay tu `st.session_state['active_workspace_id']` trong `app/main.py` dong 484-489, gan vao `ws_id` dong 589, roi truyen xuong wizard dong 592.
- Gemini API key duoc nhap o sidebar trong `app/main.py` dong 535 va truyen vao UI tab.

## 2. Existing Content Planning Flow

Flow weekly plan hien tai:

1. `app/main.py:591-592` goi `render_tab_content_planning_wizard(gemini_key, workspace_id=ws_id, role=active_ws_role)`.
2. `ui/tab_content_planning_wizard.py:115` khoi tao wizard state theo `workspace_id`.
3. Step 1 cua wizard cho user chon method. Method weekly la `"📅 Lên lịch tuần"` trong `ui/tab_content_planning_wizard.py`.
4. Khi submit weekly, UI goi `create_weekly_plan()` tai `ui/tab_content_planning_wizard.py:251`.
5. `services/content_service.py:6` tao prompt bang `get_weekly_plan_prompt()` va goi `generate_weekly_plan_json()` tai dong 16.
6. `agents/prompt_templates.py:1` tao prompt yeu cau Gemini tra ve JSON Array voi field `day`, `topic`, `target`, `goal`, `format`, `angle`, `hook`, `cta` tai dong 10-20 va 38-48.
7. `services/gemini_client.py:119` goi Gemini, lam sach JSON bang `clean_ai_json_text()` dong 78, parse bang `json.loads()`, validate bang `validate_weekly_plan_items()` dong 89.
8. Neu JSON loi, `generate_weekly_plan_json()` dung repair prompt tai `services/gemini_client.py:137-151`, goi lai model, parse lai, validate lai dong 152-156.
9. UI tao `plan_record` gom `meta` va `items`, luu vao `st.session_state[temp_output_key]` trong `ui/tab_content_planning_wizard.py:251-269`.
10. Step 2 hien thi bang plan qua `get_plan_items()` tai `ui/tab_content_planning_wizard.py:441` va `core/doc_exporter.py:21`.
11. Neu user bam luu mot item weekly vao draft, UI goi truc tiep `PostModel.create()` tai `ui/tab_content_planning_wizard.py:476`.
12. Step 3 doc posts bang `PostModel.list_by_workspace()` tai `ui/tab_content_planning_wizard.py:609`, hien calendar mockup theo `created_at`, va export Word bang `export_plan_to_word()` tai dong 649.

Luu y quan trong: weekly plan chinh khong tu dong luu vao bang `weekly_schedules` sau khi Gemini sinh xong. `WeeklyScheduleRepository.add_weekly_schedule()` chi duoc dung trong nhanh `Planning Engine` khi user bam luu task draft tai `ui/tab_content_planning_wizard.py:510`, khong phai weekly method.

## 3. Existing Files and Responsibilities

- `ui/tab_content_planning_wizard.py`
  - `render_tab_content_planning_wizard()` dong 115: UI wizard 3 buoc, quan ly session state theo workspace, goi service va hien thi ket qua.
  - Dong 251: goi `create_weekly_plan()` cho weekly plan.
  - Dong 441: parse `plan_record` de hien thi bang/preview.
  - Dong 476, 559, 589: luu draft post bang `PostModel.create()`.
  - Dong 510: luu Planning Engine task draft vao `weekly_schedules`.
  - Dong 554 va 588: goi `generate_with_gemini()` truc tiep tu UI cho Campaign Engine detail post va Trend Agent draft.
  - Dong 609: doc posts trong workspace cho review/calendar.

- `services/content_service.py`
  - `create_weekly_plan()` dong 6: service chinh cho weekly plan, tao prompt va goi `generate_weekly_plan_json()`.
  - `generate_marketing_or_knowledge_content()` dong 23: service sinh bai viet co RAG, Brand/Company Memory, Learning Loop, Brand Voice Engine. Day la component co the tai su dung, nhung hien weekly wizard chua goi no.

- `services/gemini_client.py`
  - `get_gemini_client()` dong 28: tao Gemini client, ho tro SDK moi va fallback SDK cu.
  - `generate_with_gemini()` dong 105: ham goi text generation chung.
  - `generate_weekly_plan_json()` dong 119: ham rieng cho weekly plan JSON, co repair workflow.
  - `clean_ai_json_text()` dong 78: loai markdown code block va cat chuoi tu `[` den `]`.
  - `validate_weekly_plan_items()` dong 89: chi validate list/object, chua validate required keys, type, so ngay, hoac duplicate.

- `agents/prompt_templates.py`
  - `get_weekly_plan_prompt()` dong 1: prompt hien tai tao ke hoach noi dung dang JSON Array.
  - `get_viral_marketing_prompt()` dong 142 va `get_ai_knowledge_sharing_prompt()` dong 53: prompt sinh noi dung bai viet, dang duoc service content dung.

- `database/repositories/weekly_schedule_repository.py`
  - `WeeklyScheduleRepository.add_weekly_schedule()` dong 7: insert `week_start`, `plan_json`, `workspace_id`.
  - `WeeklyScheduleRepository.get_latest_weekly_schedule()` dong 24: doc plan moi nhat, co filter workspace neu co `workspace_id`.

- `database/models/posts.py`
  - `PostModel.create()` dong 12: tao draft/published post, co `workspace_id`, `campaign_id`, `created_by`.
  - `PostModel.list_by_workspace()` dong 63: list posts theo workspace/status/platform.

- `database/models/schedules.py`
  - `ScheduleModel.create()` dong 12: tao lich dang bai co `workspace_id`.
  - `ScheduleModel.list_by_workspace()` dong 90: list schedules theo workspace.

- `database/models/brand.py`
  - `BrandModel.get_by_workspace()` dong 47 va `BrandModel.upsert()` dong 71: doc/ghi brand profile theo workspace.

- `database/models/companies.py`
  - `CompanyModel.get_by_workspace()` dong 50: lay company dau tien cua workspace hoac tao default neu chua co.
  - `CompanyModel.upsert()` dong 61: doc/ghi company theo workspace.

- `database/models/knowledge.py`
  - `KnowledgeModel.create()` dong 12: luu knowledge item theo workspace.
  - `KnowledgeModel.search()` dong 104: search knowledge co filter workspace.

- `database/repositories/knowledge_repository.py`
  - `save_knowledge_post()` dong 5 va `get_knowledge_posts()` dong 37: repository layer cho Knowledge Center.

- `database/models/campaigns.py`
  - `CampaignModel.create()` dong 13 va `CampaignModel.list_by_workspace()` dong 58: model campaign theo workspace.

- `database/schema.py`
  - Dinh nghia Schema V2 cho SQLite va PostgreSQL. Cac bang lien quan: `companies`, `brand`, `campaigns`, `posts`, `knowledge`, `schedules`, `prompt_versions`, `analytics`.
  - Khong thay `weekly_schedules` trong `SQLITE_DDL`/`POSTGRESQL_DDL`; bang nay duoc xu ly boi migration/backward compatibility.

- `database/connection.py`
  - `_is_postgres()` dong 22 va `_adapt_sql()` dong 86: compatibility layer SQLite/PostgreSQL.
  - `init_db()` dong 127: goi schema V2 va them compatibility column `workspace_id` cho `weekly_schedules` dong 194-211.

## 4. Reusable Components

- Wizard shell/state:
  - `render_tab_content_planning_wizard()` co san flow 3 buoc, state key theo `workspace_id`, preview, draft save, export.
- Weekly AI service:
  - `create_weekly_plan()` co san separation UI -> service -> Gemini JSON parser.
- Gemini client:
  - `generate_weekly_plan_json()`, `clean_ai_json_text()`, `validate_weekly_plan_items()`, `generate_with_gemini()`.
- Prompt template:
  - `get_weekly_plan_prompt()` co contract field ro cho plan items.
- Content memory/RAG:
  - `generate_marketing_or_knowledge_content()` da tich hop Brand, Company, Knowledge RAG, Learning Loop, Brand Voice Engine.
- Data models:
  - `PostModel`, `ScheduleModel`, `CampaignModel`, `BrandModel`, `CompanyModel`, `KnowledgeModel`.
- Export:
  - `core/doc_exporter.py:get_plan_items()` va `export_plan_to_word()`.
- Multi-tenant routing:
  - `app/main.py` da co active workspace selector va truyen `workspace_id` xuong tabs.

## 5. Technical Gaps

- Weekly plan generated by `create_weekly_plan()` chua nhan `workspace_id`/`company_id`, nen khong the lay Brand Identity, Company Brain, Knowledge Center, Campaign context trong weekly prompt.
- `generate_weekly_plan_json()` chi validate list/object, chua enforce required keys, data type, length theo `days`, hoac unknown fields.
- `clean_ai_json_text()` chi cat JSON array bang bracket `[`/`]`; khong ho tro object root, nested markdown phuc tap, hoac explanatory text co `[` khac.
- UI wizard goi Gemini truc tiep trong mot so nhanh:
  - Campaign detail post: `ui/tab_content_planning_wizard.py:554`.
  - Trend draft: `ui/tab_content_planning_wizard.py:588`.
  Dieu nay vi pham target rule "khong goi Gemini truc tiep tu UI" neu mo rong tuong lai.
- UI wizard goi truc tiep model database `PostModel.create()` tai dong 476, 559, 589 thay vi repository/service abstraction.
- Weekly plan khong luu full plan vao database mac dinh. `weekly_schedules` chi duoc dung cho Planning Engine task draft.
- Step 3 calendar dung `posts.created_at` de hien thi, khong dung `posts.scheduled_at` hoac bang `schedules`; do do chua phan anh lich dang that.
- `role` moi chi duoc render/truyen, nhung wizard khong thay check permission de chan viewer tao plan/draft.
- Company Brain UI truyen `marketing_strategy` va `sales_guideline` vao `CompanyModel.upsert()` trong `ui/tab_company_brain.py`, nhung `CompanyModel.update()` chi allow `name`, `industry`, `size`, `website`, `description`, `logo_url`, `products`, `target_customers`; cac field nay khong duoc persist theo model hien tai.

## 6. Database Gaps

- `weekly_schedules` khong nam trong `database/schema.py` Schema V2. No xuat hien trong `database/migrate_to_postgres.py:118` voi cot `week_start`, `plan_json`; `workspace_id` duoc bo sung compatibility trong `database/connection.py:194-211`.
- `weekly_schedules` chua co `company_id`, `campaign_id`, `created_by`, `status`, `version`, `plan_type`, `created_at`, `updated_at`.
- `weekly_schedules.plan_json` la TEXT o migration, phu hop SQLite/PostgreSQL, nhung chua co typed JSONB cho PostgreSQL. Neu muon giu compatibility, nen tiep tuc dung TEXT + json serialize, hoac them abstraction serialize/deserialize ro rang.
- Schema V2 co `prompt_versions`, nhung weekly prompt hardcoded trong `agents/prompt_templates.py`, chua luu version prompt su dung de tao plan.
- `posts` co `campaign_id`, `scheduled_at`, `ai_metadata`; wizard save draft chua gan `campaign_id`, `created_by`, `ai_metadata` co plan metadata.
- `schedules` da co bang rieng cho lich dang, nhung wizard review/calendar chua tao/doc schedules cho weekly plan.
- `company_id` ton tai trong `companies`, `brand`, `projects`; weekly plan flow hien tai khong xu ly `company_id`.
- Can dam bao moi bang moi neu them sau nay co filter `workspace_id` bat buoc va `company_id` nullable/foreign key khi context can gan company.

SQLite/PostgreSQL compatibility:

- Nen tiep tuc dung `_adapt_sql()` cho placeholder, `managed_connection()` cho commit/rollback.
- Voi cot JSON, SQLite nen dung TEXT; PostgreSQL co the dung JSONB nhung repository phai serialize/deserialize thong nhat.
- Date/time hien co dang TEXT o SQLite va TIMESTAMPTZ o PostgreSQL trong Schema V2; plan schedule nen dung service normalize ISO datetime.
- `lastrowid`/`lastval()` pattern dang duoc dung trong `PostModel.create()`, `ScheduleModel.create()`, `WeeklyScheduleRepository.add_weekly_schedule()`.

## 7. Security and Multi-tenant Risks

- `workspace_id`:
  - Duoc xac dinh o `app/main.py:484-489`, truyen vao wizard `app/main.py:592`.
  - State key wizard co suffix `workspace_id`, giam rui ro leak state giua workspace.
  - Database reads/writes lien quan posts/schedules/knowledge/brand/company da co `workspace_id` o model/repository.
  - Rui ro: `WeeklyScheduleRepository.get_latest_weekly_schedule(workspace_id=None)` co fallback doc latest global neu caller khong truyen workspace. Target moi nen tranh goi voi `None`.

- `company_id`:
  - Hien weekly flow khong nhan hoac truyen `company_id`.
  - `CompanyModel.get_by_workspace()` tra company dau tien trong workspace; khong co UI chon company cho wizard.
  - Neu target co multi-company trong mot workspace, can them chon/lien ket `company_id` ro rang.

- API keys/secrets:
  - Gemini key duoc nhap password field trong `app/main.py:535`.
  - `services/gemini_client.py:107-108` log 300 ky tu dau cua prompt; prompt co the chua thong tin nhay cam tu Company Brain/Knowledge neu sau nay tich hop. Nen giam log prompt raw khi dua business memory vao.
  - Khong thay log API key trong `gemini_client.py`, nhung can tiep tuc cam log token/API key.

- Permissions:
  - Wizard nhan `role`, nhung chua enforce viewer read-only. Day la regression/security risk neu Strategy Center co save/create/update nhieu hon.

## 8. Refactoring Recommendations

Khong nen viet lai ung dung hoac tach microservices. Nen refactor nho theo kien truc Streamlit hien tai:

1. Tao service-level facade cho strategy planning, vi du trong `services/content_service.py` hoac module service moi trong `services/`, de UI chi goi service.
2. Mo rong `create_weekly_plan()` de nhan `workspace_id`, `company_id=None`, `campaign_id=None`, `created_by=None`, nhung giu backward compatibility.
3. Tach build context:
   - `BrandModel.get_by_workspace()`
   - `CompanyModel.get_by_workspace()` hoac by company_id neu them.
   - `KnowledgeRepository.get_knowledge_posts()` / semantic search logic tu `generate_marketing_or_knowledge_content()`.
   - `CampaignModel.get_by_id()` / `list_by_workspace()`.
4. Tach JSON schema validator cho plan item, validate required keys va normalize output truoc khi save.
5. Dua cac goi Gemini truc tiep trong `ui/tab_content_planning_wizard.py:554` va `:588` sang service.
6. Dua draft post creation trong wizard sang service/repository wrapper de enforce `workspace_id`, `created_by`, `campaign_id`, audit, metadata.
7. Dung `ScheduleModel` cho calendar/schedule thay vi mock calendar theo `created_at`.
8. Neu can luu full strategy plan, them migration co rollback cho bang/cot moi; khong sua schema pha huy.

## 9. Proposed Target Architecture

Target van la Streamlit monolith co layer ro:

```text
app/main.py
  -> ui/tab_content_planning_wizard.py (doi ten/hien thi thanh Strategy Center sau)
    -> services/content_strategy_service.py hoac services/content_service.py
      -> agents/prompt_templates.py
      -> services/gemini_client.py
      -> parser/validator JSON
      -> database repositories/models
    -> UI review/export/schedule controls
```

Dependency map hien tai:

```text
app/main.py
  -> ui.nav_config.DEFAULT_NAV/get_nav_groups
  -> ui.top_navigation_tabs.render_top_navigation_tabs
  -> ui.tab_content_planning_wizard.render_tab_content_planning_wizard

ui.tab_content_planning_wizard
  -> services.content_service.create_weekly_plan
  -> services.gemini_client.generate_with_gemini
  -> services.trend_service.analyze_trends
  -> ui.tab_planning.generate_campaign_tasks
  -> ui.tab_campaign.generate_campaign_assets
  -> database.repositories.WeeklyScheduleRepository
  -> database.models.posts.PostModel
  -> core.doc_exporter.get_plan_items/export_plan_to_word

services.content_service.create_weekly_plan
  -> agents.prompt_templates.get_weekly_plan_prompt
  -> services.gemini_client.generate_weekly_plan_json

services.gemini_client.generate_weekly_plan_json
  -> get_gemini_client/_call_model
  -> clean_ai_json_text
  -> json.loads
  -> validate_weekly_plan_items
  -> repair prompt -> _call_model -> clean/parse/validate

database repositories/models
  -> database.connection.get_db_connection/managed_connection/_adapt_sql/_is_postgres
  -> SQLite or PostgreSQL
```

Target data flow:

```text
UI Strategy Center
  -> Strategy Service
  -> Context Loaders (Brand, Company, Knowledge, Campaign, Learning)
  -> Prompt Builder
  -> Gemini Client
  -> JSON Parser/Validator/Repair
  -> Plan Repository + Post/Schedule repositories
  -> UI Review/Calendar/Export
```

## 10. Implementation Backlog

Phase 0 - Safety baseline:

- Viet tests cho `clean_ai_json_text()`, `validate_weekly_plan_items()`, `generate_weekly_plan_json()` voi mocked Gemini.
- Viet tests cho repository workspace filtering cua `WeeklyScheduleRepository`.
- Ghi ro current behavior trong docs va khong doi UI.

Phase 1 - Service boundary:

- Them service facade cho strategy planning.
- Chuyen goi Gemini truc tiep trong wizard sang service.
- Chuyen save draft post sang service wrapper de enforce `workspace_id`, `created_by`, `campaign_id`, `ai_metadata`.

Phase 2 - JSON contract:

- Them validator required fields cho weekly/strategy plan.
- Chuan hoa parser repair flow, error message, va test JSON malformed.
- Can nhac Gemini structured output neu SDK hien tai ho tro, van giu fallback cho compatibility.

Phase 3 - Context integration:

- Dua Brand Identity va Company Brain vao weekly plan prompt.
- Them optional Campaign context.
- Them Knowledge Center/RAG context co gioi han token va filter theo workspace/company.
- Khong log raw context nhay cam.

Phase 4 - Persistence:

- Thiet ke migration non-destructive cho strategy plans hoac mo rong `weekly_schedules`.
- Them `workspace_id` required, optional `company_id`, optional `campaign_id`, `created_by`, `plan_type`, `status`, `prompt_version`, timestamps.
- Ho tro SQLite TEXT JSON va PostgreSQL JSONB/TEXT theo repository abstraction.

Phase 5 - Calendar/schedule:

- Tao post drafts tu plan items co metadata.
- Tao optional schedules bang `ScheduleModel.create()`.
- Step 3 doc `schedules` va `posts.scheduled_at`, khong chi `created_at`.

Phase 6 - UI rename/upgrade:

- Doi nhan hien thi sang AI Content Strategy Center.
- Giu route/tab compatibility ban dau hoac migrate state keys co fallback.
- Them review/edit/approve/schedule ergonomics, van trong Streamlit.

## 11. Dependency Order

1. Tests va current behavior locks.
2. Service boundary cho Gemini va draft creation.
3. Parser/validator hardening.
4. Context loader cho Brand/Company/Knowledge/Campaign.
5. Database migration + repository API.
6. UI wire-up cho persistence va context selectors.
7. Schedule/calendar integration.
8. Rename UX va cleanup deprecated paths.

Khong nen doi UI label, database schema va prompt contract cung luc trong mot PR/task vi regression surface lon.

## 12. Regression Risks

- JSON parsing: thay prompt/validator co the lam weekly plan fail neu Gemini tra text khac format.
- Existing weekly UX: hien tai plan khong auto-save full plan; neu them auto-save co the tao duplicate records.
- Multi-tenant: bat ky call nao thieu `workspace_id` co the doc/ghi cross-workspace, dac biet `WeeklyScheduleRepository.get_latest_weekly_schedule(workspace_id=None)`.
- `company_id`: neu them multi-company selector ma default sai, prompt co the dung sai company brain.
- UI session state: key hien co gan `workspace_id`; doi ten tab/state can migration/fallback de khong mat draft trong session.
- Direct UI Gemini calls: neu refactor khong giu payload/prompt cu, Campaign Engine/Trend Agent trong wizard co the doi output.
- Database compatibility: JSONB PostgreSQL va TEXT SQLite can repository serialize/deserialize; dung SQL syntax rieng co the pha mot engine.
- Calendar: chuyen tu `created_at` sang `scheduled_at`/`schedules` co the lam user thay "mat bai" neu draft chua co schedule.
- Permissions: them enforcement viewer/editor co the thay doi behavior hien tai.
- Logging: tich hop Knowledge/Company vao prompt ma giu `logger.debug(prompt[:300])` co the leak noi dung noi bo vao logs.

## 13. Definition of Done cho toan bo chuong trinh nang cap

- UI hien thi AI Content Strategy Center trong Streamlit, khong phai landing page, va van hoat dong trong navigation hien tai.
- Moi Gemini call tu Strategy Center di qua service layer, khong goi truc tiep tu UI.
- Moi database write/doc du lieu plan/post/schedule di qua repository/model/service layer phu hop, khong query DB truc tiep tu UI neu da co layer.
- Moi du lieu plan/post/schedule/knowledge/campaign duoc filter theo `workspace_id`; `company_id` duoc xu ly ro khi co multi-company.
- Weekly/strategy plan prompt co context Brand Identity, Company Brain, Knowledge Center, Campaign khi user chon/cho phep.
- Parser co validator required fields, test JSON loi, va repair/fallback ro rang.
- Full plan duoc persist non-destructively, co migration va rollback cho SQLite/PostgreSQL.
- Draft posts tao tu plan co `workspace_id`, `created_by`, optional `campaign_id`, `ai_metadata`.
- Calendar/review dung `schedules`/`scheduled_at` thay vi mock theo `created_at`.
- Viewer role khong tao/sua du lieu; editor/manager permissions duoc enforce.
- Khong log API key/token/JWT va khong log raw business knowledge nhay cam.
- Test unit/service/repository/UI smoke lien quan duoc cap nhat va pass tren SQLite; PostgreSQL SQL compatibility duoc verify bang tests hoac dry-run migration.
- Tai lieu van hanh va regression checklist duoc cap nhat.

## Files Analyzed

- `app/main.py`
- `ui/nav_config.py`
- `ui/tab_content_planning_wizard.py`
- `ui/tab_planning.py`
- `ui/tab_campaign.py`
- `ui/tab_brand.py`
- `ui/tab_company_brain.py`
- `ui/tab_knowledge.py`
- `ui/tab_publishing.py`
- `services/content_service.py`
- `services/gemini_client.py`
- `services/trend_service.py`
- `agents/prompt_templates.py`
- `core/doc_exporter.py`
- `database/connection.py`
- `database/schema.py`
- `database/migrate_to_postgres.py`
- `database/repositories/weekly_schedule_repository.py`
- `database/repositories/knowledge_repository.py`
- `database/models/posts.py`
- `database/models/schedules.py`
- `database/models/brand.py`
- `database/models/companies.py`
- `database/models/knowledge.py`
- `database/models/campaigns.py`

## Files Created

- `docs/content_strategy_center_assessment.md`

## Next Task Issues

- Quyet dinh persistence target: mo rong `weekly_schedules` hay tao bang strategy plans moi.
- Thiet ke `company_id` selection/default behavior cho workspace co nhieu company.
- Viet tests baseline cho parser/repository truoc khi refactor.
- Chuyen direct Gemini calls trong wizard sang service.
- Thiet ke migration SQLite/PostgreSQL co rollback.
