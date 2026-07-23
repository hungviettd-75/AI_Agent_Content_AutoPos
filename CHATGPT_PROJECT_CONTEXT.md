# Tom tat du an: AI_Agent_Content_AutoPos / Apex AI

Day la ung dung Python dung Streamlit, ten hien thi la **Apex AI - Marketing Intelligence Platform**. Muc tieu cua du an la tu dong hoa quy trinh marketing noi dung bang AI: lap ke hoach noi dung, tao bai viet, quan ly thuong hieu, kiem duyet, dang bai mang xa hoi, phan tich hieu qua va hoc lai tu du lieu.

## Cong nghe chinh

- Frontend/UI: Streamlit
- Backend: Python monolithic app, chia module theo chuc nang
- AI: Google Gemini API, mac dinh model `gemini-2.5-flash`
- Database: SQLite local qua `content_manager.db`, co ho tro tuy chon PostgreSQL
- Xuat tai lieu: PDF bang `fpdf2`, Word bang `python-docx`
- Tich hop mang xa hoi: Facebook Graph API, Zalo OA API, LinkedIn API
- Config: `.env`, `python-dotenv`

## Cau truc chinh

- `app/main.py`: entrypoint Streamlit, xu ly login/register, workspace, sidebar API config, routing tab.
- `ui/`: cac tab giao dien nhu Content Planning, Content Studio, Knowledge Center, Brand Identity, Thumbnail Studio, Publishing, Analytics, A/B Testing, Billing, System Monitor, Admin.
- `services/`: logic nghiep vu va tich hop AI/API, gom Gemini, content, copywriting, fact check, trend, monitoring, thumbnail, visual intelligence.
- `database/`: ket noi DB, schema, models, repositories.
- `core/`: xac thuc, JWT, RBAC, audit log, export tai lieu, parser tai lieu.
- `agents/`: prompt templates va framework prompt.
- `workflow/`: scheduler va learning engine.
- `analytics/`: tinh diem viral va chi so phan tich.
- `social/`: publishers cho Facebook, Zalo, LinkedIn.
- `docs/` va cac file `.md`: tai lieu kien truc, UI, thumbnail, creative engine, analytics, migration.

## Tinh nang chinh

1. Dang nhap/dang ky nguoi dung, luu session bang JWT cookie.
2. Multi-tenant workspace: moi user co the thuoc nhieu workspace.
3. RBAC/phan quyen theo vai tro: owner, ceo, admin, manager, marketing, editor, viewer, super_admin.
4. Content Planning Wizard: tao ke hoach noi dung bang AI.
5. Content Studio Workspace: tao, chinh sua, quan ly noi dung.
6. Knowledge Center va Company Brain: luu tri thuc noi bo, kien thuc AI, du lieu doanh nghiep.
7. Brand Identity: quan ly tone of voice, mau sac, guideline, CTA, mission, vision.
8. Fact Check: kiem tra thong tin bang AI.
9. Thumbnail Studio va Thumbnail Analytics: tao/quan ly/danh gia thumbnail.
10. Publishing Agent: len lich va dang bai len Facebook, Zalo OA, LinkedIn.
11. Workflow Engine: tu dong hoa quy trinh marketing.
12. Approval Flow: duyet bai truoc khi xuat ban.
13. Analytics Agent, Learning Loop, A/B Testing: do hieu qua, rut insight, toi uu noi dung.
14. AI Cost Center, Billing & Quota: theo doi chi phi AI va quota.
15. Audit Log va System Monitor: giam sat he thong, ghi lich su thao tac.

## Database

Schema V2 gom cac bang chinh:

- `users`
- `workspaces`
- `workspace_members`
- `companies`
- `brand`
- `projects`
- `campaigns`
- `posts`
- `assets`
- `knowledge`
- `schedules`
- `approvals`
- `prompt_versions`
- `analytics`
- `learning_insights`
- ngoai ra co `audit_logs`

Database mac dinh la SQLite, nhung code co lop tuong thich de chuyen sang PostgreSQL qua bien `DB_ENGINE`.

## AI/Gemini

File `services/gemini_client.py` boc logic goi Gemini. Co:

- client Gemini moi `google.genai`, fallback sang `google.generativeai`
- ham tao content text
- ham tao weekly plan dang JSON
- co che lam sach JSON tu AI
- workflow sua JSON neu AI tra ve sai dinh dang
- tuy chon bat Google Search Tool cho research mode

## Cach chay

```bash
pip install -r requirements.txt
streamlit run app/main.py
```

Hoac tren Windows co the chay file:

```bash
AI_Agent_Content_AutoPost.bat
```

Can cau hinh `.env` cho cac key nhu:

- `GEMINI_API_KEY`
- `FACEBOOK_ACCESS_TOKEN`
- `FACEBOOK_PAGE_ID`
- `ZALO_OA_ACCESS_TOKEN`
- `LINKEDIN_ACCESS_TOKEN`
- `DB_ENGINE`

## Ghi chu ky thuat

Du an hien la monolithic Streamlit app nhung da duoc tach module tuong doi ro: UI, services, database, core, workflow, agents. Mot so tai lieu `.md` bi loi encoding tieng Viet, nhung code chinh van doc duoc. Thu muc hien tai khong co git repository kha dung khi kiem tra bang `git status`.

## Goi y cach hoi ChatGPT tiep

- Hay review kien truc du an nay va chi ra rui ro lon nhat.
- Hay de xuat roadmap nang cap thanh SaaS production.
- Hay tim cac diem can refactor trong ung dung Streamlit monolithic nay.
- Hay de xuat chien luoc bao mat cho app co AI API key va social access token.
- Hay thiet ke test plan cho cac module AI, publishing va database.
