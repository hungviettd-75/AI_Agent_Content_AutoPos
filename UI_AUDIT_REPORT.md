# 🔍 UI AUDIT REPORT — APEX AI MARKETING INTELLIGENCE PLATFORM

> **Ngày thực hiện audit**: 2026-07-12
> **Phiên bản đánh giá**: V2 (sau tái cấu trúc)
> **Vai trò kiểm tra**: Senior Product Designer · Senior UX Architect · Streamlit UI Engineer
> **Framework**: Streamlit >= 1.35.0 + Custom CSS (Inline)
> **Phạm vi**: `app/main.py` + 21 files `ui/tab_*.py`

---

## 1. MAN HINH TONG QUAN

### 1.1 Man hinh xac thuc (Unauthenticated)

| # | Man hinh | Mo ta |
|---|----------|--------|
| 1 | **Login Screen** | Split-panel: Brand panel (trai) + Form dang nhap (phai) |
| 2 | **Register Screen** | Cung layout, chuyen doi qua `st.radio` |

### 1.2 Man hinh ung dung chinh (22 page)

| # | Page Name | Tab File | Nhom Nav |
|---|-----------|----------|----------|
| 1 | Len lich tuan | `tab_plan.py` | Content Studio |
| 2 | Tao & Dang Bai | `tab_create.py` | Content Studio |
| 3 | Copywriting | `tab_copywriting.py` | Content Studio |
| 4 | Trend Agent | `tab_trend.py` | Content Studio |
| 5 | Fact Check | `tab_factcheck.py` | Content Studio |
| 6 | Publishing Agent | `tab_publishing.py` | Content Studio |
| 7 | Knowledge Center | `tab_knowledge.py` | Intelligence |
| 8 | Brand Brain | `tab_brand.py` | Intelligence |
| 9 | Company Brain | `tab_company_brain.py` | Intelligence |
| 10 | Learning Loop | `tab_learning.py` | Intelligence |
| 11 | Workflow Engine | `tab_workflow.py` | Automation Engine |
| 12 | Planning Engine | `tab_planning.py` | Automation Engine |
| 13 | Campaign Engine | `tab_campaign.py` | Automation Engine |
| 14 | Quy trinh phe duyet | `tab_approval.py` | Automation Engine |
| 15 | A/B Testing | `tab_ab_testing.py` | Automation Engine |
| 16 | Analytics Agent | `tab_analytics.py` | Data & Analytics |
| 17 | Lich su bai viet | `tab_history.py` | Data & Analytics |
| 18 | AI Cost Center | `tab_ai_cost.py` | Data & Analytics |
| 19 | Billing & Quota | `tab_billing.py` | Data & Analytics |
| 20 | System Monitor | `tab_monitoring.py` | System |
| 21 | Quan ly Workspace | `main.py` (inline) | Admin |
| 22 | Audit Log | `tab_audit.py` | Admin |

---

## 2. DANH SACH 21 TAB GIAO DIEN

| # | Tab Name | File | KB | Custom CSS |
|---|----------|------|----|------------|
| 1 | Len lich tuan | `tab_plan.py` | 7 | Khong |
| 2 | Tao & Dang Bai | `tab_create.py` | 18 | Khong |
| 3 | Lich su bai viet | `tab_history.py` | 5 | Khong |
| 4 | Chien dich | `tab_campaign.py` | 14 | Khong |
| 5 | Phan tich | `tab_analytics.py` | 24 | Co: `_DASHBOARD_CSS` — KPI cards, header, leaderboard |
| 6 | A/B Testing | `tab_ab_testing.py` | 31 | Co: `_AB_CSS` — Variant cards, score bar, status pills |
| 7 | Workflow Engine | `tab_workflow.py` | 21 | Co: `_WORKFLOW_CSS` + HTML5 Drag & Drop iframe |
| 8 | Publishing Agent | `tab_publishing.py` | 17 | Co: `_PUBLISHING_CSS` — Status badge |
| 9 | Knowledge Center | `tab_knowledge.py` | 15 | Khong |
| 10 | Copywriting AI | `tab_copywriting.py` | 15 | Khong |
| 11 | Learning Loop | `tab_learning.py` | 13 | Khong |
| 12 | Brand Brain | `tab_brand.py` | 11 | Khong |
| 13 | Phe duyet | `tab_approval.py` | 12 | Khong |
| 14 | Fact Check | `tab_factcheck.py` | 9 | Khong |
| 15 | Trend Agent | `tab_trend.py` | 9 | Khong |
| 16 | System Monitor | `tab_monitoring.py` | 7 | Co: `_MON_CSS` — Status indicators, alert boxes |
| 17 | Planning Engine | `tab_planning.py` | 11 | Khong |
| 18 | Company Brain | `tab_company_brain.py` | 8 | Khong |
| 19 | AI Cost Center | `tab_ai_cost.py` | 7 | Khong |
| 20 | Billing & Quota | `tab_billing.py` | 9 | Khong |
| 21 | Audit Log | `tab_audit.py` | 8 | Khong |

> **Nhan xet**: 5/21 tab co custom CSS (Analytics, A/B Testing, Workflow, Publishing, Monitoring). 16/21 tab dung Streamlit default — gay inconsistency nghiem trong.

---

## 3. COMPONENT UI DANG SU DUNG

### 3.1 Streamlit Native Components

| Component | Su dung tai | Tan suat |
|-----------|------------|---------|
| `st.sidebar` | `main.py` | Toan cuc |
| `st.button` | Tat ca tab | Rat cao |
| `st.form` + `st.form_submit_button` | 12/21 tab | Cao |
| `st.text_input` | Tat ca tab | Rat cao |
| `st.text_area` | 15/21 tab | Cao |
| `st.selectbox` | Tat ca tab | Rat cao |
| `st.multiselect` | 3/21 tab | Thap |
| `st.radio` | 3/21 tab | Thap |
| `st.checkbox` | 4/21 tab | Thap |
| `st.slider` | `tab_ab_testing.py` | Rat thap |
| `st.number_input` | `tab_ab_testing.py` | Thap |
| `st.date_input` | `tab_publishing.py` | Thap |
| `st.time_input` | `tab_publishing.py` | Thap |
| `st.file_uploader` | `tab_knowledge.py` | Thap |
| `st.dataframe` | 11/21 tab | Cao |
| `st.expander` | 14/21 tab | Cao |
| `st.columns` | Tat ca tab | Rat cao |
| `st.tabs` | KHONG DUNG (da thay bang sidebar nav) | — |
| `st.spinner` | 14/21 tab | Cao |
| `st.success/error/warning/info` | Tat ca tab | Rat cao |
| `st.divider` | 12/21 tab | Cao |
| `st.area_chart/bar_chart/line_chart` | `tab_analytics.py` | Trung binh |
| `st.chat_message` + `st.chat_input` | `tab_create.py` | Thap |
| `st.download_button` | 2 tab | Thap |
| `st.status` | `tab_workflow.py` | Thap |
| `st.components.v1.html` | `tab_workflow.py` | Rat thap |

### 3.2 Custom HTML/CSS Components

| Component | Tab | Mo ta |
|-----------|-----|-------|
| Brand Panel (Login) | `main.py` | Gradient panel gioi thieu san pham |
| Nav Button Group | `main.py` | `.nav-btn` / `.nav-btn-active` sidebar navigation |
| Role Badge | `core/rbac.py` | Pill badge hien thi vai tro nguoi dung |
| Permissions Table | `core/rbac.py` | Bang quyen han mini trong sidebar |
| KPI Cards | `tab_analytics.py` | `.kpi-card` voi top color bar va hover effect |
| Leaderboard Items | `tab_analytics.py` | `.leader-item` voi rank badge vang/bac/dong |
| Platform Badges | `tab_analytics.py` | `.plat-badge` cho FB/LinkedIn/Zalo |
| Variant Cards | `tab_ab_testing.py` | `.variant-wrap` voi gradient header A/B/C/D |
| Score Bar | `tab_ab_testing.py` | Progress bar phan tram diem tong hop |
| Status Pills | `tab_ab_testing.py`, `tab_publishing.py` | `.status-pill` / `.status-badge` |
| Winner Banner | `tab_ab_testing.py` | Green gradient banner thong bao winner |
| Step Cards | `tab_workflow.py` | `.step-card` danh sach buoc workflow |
| Drag & Drop Canvas | `tab_workflow.py` | HTML5 iframe voi JS drag-and-drop (khong sync Streamlit) |
| Status Indicators | `tab_monitoring.py` | Dot mau `.st-green`/`.st-yellow`/`.st-red` |
| Alert Boxes | `tab_monitoring.py` | `.alert-box` canh bao he thong |
| Dark Gradient Headers | 5 tabs | `.db-header`, `.ab-header`, `.wf-header`, `.pub-header`, `.mon-header` |
| Section Titles | `tab_analytics.py`, `tab_ab_testing.py` | `.section-title` voi left border accent |

---

## 4. PHAN TICH CHI TIET CAC THANH PHAN

### 4.1 Navigation

**Co che hien tai:** Custom sidebar navigation: `st.button` + CSS override + `st.session_state['active_nav']`

**Cau truc nav groups:**
- Content Studio (6 items)
- Intelligence (4 items — tat ca icon Brain emoji)
- Automation Engine (5 items)
- Data & Analytics (4 items)
- System (1 item)
- Admin (2 items — role-based)

**Van de phat hien:**

| Muc do | Van de |
|--------|--------|
| CRITICAL | Navigation dua vao `st.button` → moi click **full page reload** (st.rerun). Khong co shallow routing |
| CRITICAL | Khong co URL routing — khong the bookmark, chia se link, su dung browser back/forward |
| HIGH | 22 items nav khong co search/filter |
| HIGH | 4 items nhom Intelligence deu icon emoji nao giong nhau → confusion |
| HIGH | Khong co breadcrumb — user khong biet minh dang o dau |
| MEDIUM | CSS hack `div class='nav-btn'` wrap quanh `st.button` — risk khi Streamlit update |
| MEDIUM | Nav group labels qua nho (0.68rem) — kho doc |
| LOW | Khong co keyboard shortcut |

**Diem tot:** Phan nhom logic ro rang. Active state dung. Role-based visibility hoat dong tot.

---

### 4.2 Sidebar

**Cau truc hien tai:**
```
Sidebar
├── User Info (text + role badges)
├── Permissions Table (mini)
├── Workspace Selector
├── Dang xuat button
├── divider
├── Gemini API Key input  ← SENSITIVE
├── Facebook API expander ← SENSITIVE
├── Zalo OA API expander  ← SENSITIVE
├── LinkedIn API expander ← SENSITIVE
├── divider
└── 22 Navigation Buttons
```

**Van de:**

| Muc do | Van de |
|--------|--------|
| CRITICAL | **API Keys trong Sidebar** — Gemini key, FB token, Zalo token lo ra o primary sidebar area |
| CRITICAL | Sidebar qua tai: user info + permissions + workspace + API config + nav = **cognitive overload** |
| HIGH | Permissions Table luon hien thi trong sidebar — chiem space, khong can thiet xem lien tuc |
| HIGH | API Key expanders o giua User Info va Navigation — khong lien quan, gay mat flow |
| MEDIUM | Khong co user avatar — chi co text |
| LOW | Font size sidebar headings qua nho (0.78rem) |

---

### 4.3 Header

**Van de:**

| Muc do | Van de |
|--------|--------|
| HIGH | **Header inconsistency**: 5/21 tab co custom dark gradient, 16/21 tab dung st.header() — 2 design language song song |
| HIGH | h1 mau `#004ac6` (global) nhung tab headers mau white — CSS conflict |
| HIGH | Global header chiem space tren moi tab du da co sidebar |
| MEDIUM | h2 global mau `#712ae2` nhung tab headers override sang mau khac |
| MEDIUM | Khong co notification bell, sync status tren header |
| LOW | Active page name hien thi 2 lan: sidebar button + h2 |

---

### 4.4 Layout

**Van de:**

| Muc do | Van de |
|--------|--------|
| HIGH | Khong co **breakpoint responsive** — tren man hinh nho (< 1200px) sidebar bi chen ep |
| HIGH | `tab_create.py` qua dai: form + output + chat panel, user phai scroll nhieu |
| MEDIUM | `st.divider()` dung rat nhieu (12/21 tab) — visual separation mo nhat |
| MEDIUM | `st.write("")` spacer hack xuat hien nhieu tab |
| MEDIUM | Khong co **skeleton loading** — chi co st.spinner toan trang |
| LOW | max-width chua set → noi dung qua rong tren ultrawide screen |

---

### 4.5 Card Component

**Van de:**

| Muc do | Van de |
|--------|--------|
| HIGH | **Khong co card component tai su dung** — 6 loai card khac nhau hoan toan (Analytics, A/B, Workflow, Monitoring, Publishing, Knowledge) |
| HIGH | Card style khong nhat quan: border-radius tu 10px den 20px tuy tab |
| MEDIUM | KPI Cards khong co loading state rieng |
| LOW | Hover effects chi co o mot so card |

---

### 4.6 Table Component

**Van de:**

| Muc do | Van de |
|--------|--------|
| HIGH | `st.dataframe()` style override boi global CSS nhung khong dong nhat voi custom HTML tables |
| MEDIUM | Mot so dataframe hien thi cot `id` raw database — khong user-friendly |
| MEDIUM | Khong co pagination native |
| MEDIUM | Mot so tables khong co empty state design |
| LOW | Khong co export-to-CSV button truc tiep tren table |

---

### 4.7 Form Component

**Van de:**

| Muc do | Van de |
|--------|--------|
| CRITICAL | **Form validation rat yeu** — chi check `if not field`, khong co regex validation (email, URL, password strength) |
| HIGH | `label_visibility="collapsed"` tren Login/Register form → label bi an hoan toan, khong accessible |
| HIGH | Khong co **real-time validation** — loi chi hien sau khi submit |
| HIGH | Form `tab_create.py` qua dai (9+ fields) — can chia multi-step wizard |
| MEDIUM | Khong co **required field indicator** (*) |
| MEDIUM | `st.form` khong co auto-save draft — neu reload, toan bo input mat |

---

### 4.8 Button Component

**Van de:**

| Muc do | Van de |
|--------|--------|
| CRITICAL | **Delete without confirmation** — cac nut Xoa thuc thi NGAY LAP TUC khong can xac nhan |
| HIGH | Danger button (xoa) dung `type="primary"` → cung mau blue voi primary action — khong phan biet |
| HIGH | Icon-only buttons (▲ ▼ 🗑️) thieu tooltip/help text — khong accessible |
| MEDIUM | `use_container_width=True` khong nhat quan |
| MEDIUM | `hover: scale(0.98)` — nguoc UX convention (nen scale-up khi hover) |
| LOW | Khong co loading state tren button sau click |

---

### 4.9 Modal & Dialog

**Hien trang:** Streamlit KHONG ho tro native modal/dialog.
- `st.expander()` → thay the accordion
- `st.form()` → thay the dialog
- `st.error()` → thay the confirmation
- Khong co overlay modal thuc su

**Van de:**

| Muc do | Van de |
|--------|--------|
| CRITICAL | Khong co **delete confirmation modal** — xoa du lieu khong the undo |
| CRITICAL | Khong co **preview modal** — xem noi dung bai viet buoc user mo expander, khong clean |
| HIGH | `st.expander` dung voi nhieu muc dich khac nhau: API config, content detail, form, help text |
| MEDIUM | Khong co side drawer/panel |
| LOW | Streamlit 1.35+ co `st.dialog` — CHUA DUOC AP DUNG |

---

### 4.10 Notification System

**Van de:**

| Muc do | Van de |
|--------|--------|
| HIGH | Khong co **toast notification** — `st.success()` render inline, khong phai floating |
| HIGH | Notification khong **tu dong bien mat** — ton tai den khi rerun |
| MEDIUM | `st.info()` dung cho ca thong tin lan empty state — khong phan biet y nghia |
| MEDIUM | Khong co notification history/inbox |
| LOW | `st.status()` tot nhung chi dung o 1 tab |

---

## 5. DANH GIA TONG QUAN

### 5.1 UI Score

| Tieu chi | Diem | Nhan xet |
|----------|------|---------|
| Visual Design | 6/10 | Login screen va 5 tab dep. 16 tab con lai generic Streamlit |
| Color Consistency | 5/10 | Primary palette co nhung 4 mau primary khac nhau giua cac tab CSS |
| Typography | 7/10 | Inter font tot. Nhung h2 global mau purple xung dot voi tab headers trang |
| Iconography | 7/10 | Emoji icons nhat quan. Thieu proper icon library |
| Spacing | 5/10 | 8pt grid o CSS comment nhung khong ap dung nhat quan |
| Animation | 6/10 | Hover transitions muot. Thieu page transition, skeleton loading |
| Dark Mode | 0/10 | Khong co dark mode toggle |

**UI Score: 5.1/10**

### 5.2 UX Score

| Tieu chi | Diem | Nhan xet |
|----------|------|---------|
| Onboarding | 3/10 | Khong co onboarding wizard. User moi khong co guidance |
| Task Flows | 5/10 | Flow tao-dang bai tot. Flow phe duyet phan manh qua 3 tab |
| Navigation Efficiency | 4/10 | 22 items flat, moi click la full reload |
| Cognitive Load | 4/10 | Sidebar qua nhieu thong tin. Form qua phuc tap |
| Error Recovery | 3/10 | Loi hien st.error() khong huong dan sua. Khong co undo |
| Feedback | 5/10 | Spinner tot. AI response ro rang. Thieu progress indication |
| Empty States | 5/10 | Mot so tab co, nhieu tab khong co |
| Mobile | 2/10 | layout=wide hoan toan desktop-first |
| Performance | 5/10 | Moi nav action = full rerun. API calls dong bo blocking UI |

**UX Score: 4.0/10**

### 5.3 Accessibility Score

| Tieu chi | Diem | Nhan xet |
|----------|------|---------|
| Screen Reader | 3/10 | label_visibility=collapsed an labels. Custom HTML khong co ARIA |
| Keyboard Navigation | 4/10 | Streamlit forms co co ban. Custom HTML khong accessible |
| Color Contrast | 6/10 | Primary buttons dat AA. Mot so secondary text (#737686) thap |
| Focus Indicators | 4/10 | Custom nav buttons mat focus ring sau CSS override |
| Alt Text | 2/10 | Emoji buttons khong co aria-label |
| WCAG 2.1 AA | 3/10 | Khong dat o nhieu diem |

**Accessibility Score: 3.7/10**

### 5.4 Consistency Score

| Tieu chi | Diem | Nhan xet |
|----------|------|---------|
| Design Language | 4/10 | 2 design system song song: 5 tab custom CSS vs 16 tab Streamlit default |
| Component Reuse | 3/10 | Khong co shared component library. Moi tab tu viet card/header rieng |
| Color Usage | 4/10 | 4 mau primary khac nhau: #004ac6, #6366f1, #3b82f6, #2563eb |
| Naming Convention | 6/10 | File naming chuan. Nhung 4 nav items cung icon emoji trong nhom Intelligence |
| Interaction Patterns | 4/10 | Form submit patterns khac nhau giua cac tab |
| Error Message Style | 5/10 | Tat ca dung st.error() nhung message format tu do |

**Consistency Score: 4.3/10**

---

## 6. DANH SACH LOI THEO MUC DO

### CRITICAL — Can xu ly ngay

| # | Van de | File | Tac dong |
|---|--------|------|---------|
| C1 | Delete without confirmation: Xoa thanh vien, A/B test, knowledge thuc thi ngay | `main.py`, `tab_ab_testing.py`, `tab_knowledge.py` | Mat du lieu khong the khoi phuc |
| C2 | API Keys exposed in Sidebar: Gemini key, FB token, Zalo token, LinkedIn token | `main.py` | Security risk — shoulder surfing |
| C3 | No URL routing: Khong the bookmark, chia se link, dung browser navigation | `main.py` | Broken navigation mental model |
| C4 | Full page reload on every navigation: st.rerun() tai moi click nav | `main.py` | UX kem, khong co state preservation |
| C5 | No form validation: Register form khong validate email format, password strength | `main.py`, `tab_publishing.py` | Data integrity |
| C6 | label_visibility="collapsed" tren auth forms: Screen reader khong doc duoc labels | `main.py` | WCAG 2.1 Failure |

### HIGH — Uu tien cao

| # | Van de | File | Tac dong |
|---|--------|------|---------|
| H1 | 4 nav items deu icon Brain trong nhom Intelligence | `main.py` | Cognitive confusion |
| H2 | Header inconsistency: 5 tab custom CSS, 16 tab khong co | Multiple | Brand inconsistency |
| H3 | No onboarding flow: User moi khong co guidance sau dang ky | `main.py` | High drop-off |
| H4 | tab_create.py form qua phuc tap: 9+ fields, khong co progressive disclosure | `tab_create.py` | Overwhelm new users |
| H5 | No delete confirmation pattern: st.dialog chua implement | All delete | Data loss risk |
| H6 | Sidebar cognitive overload: user info + permissions + API keys + 22 nav | `main.py` | Focus dilution |
| H7 | No toast/notification system: st.success() khong phai floating toast | All tabs | Poor feedback loop |
| H8 | Permissions table luon visible trong sidebar | `main.py` | Noise, space waste |
| H9 | Danger button cung mau voi primary: ca hai mau blue | Multiple | Accidental destructive action |
| H10 | No mobile responsive layout | Entire app | Khong dung duoc tren mobile/tablet |

### MEDIUM — Backlog thiet ke quan trong

| # | Van de | File |
|---|--------|------|
| M1 | Khong co skeleton loading state | All AI-heavy tabs |
| M2 | st.divider() overused — 12/21 tab | Multiple |
| M3 | Khong co breadcrumb navigation | `main.py` |
| M4 | st.write("") spacer hack | Multiple |
| M5 | hover: scale(0.98) — nguoc UX convention | `main.py` CSS |
| M6 | Khong co st.dialog confirm cho delete | Multiple |
| M7 | Empty state khong nhat quan | Multiple |
| M8 | Icon-only buttons thieu aria-label va tooltip | `tab_workflow.py` |
| M9 | A/B Testing multi-form trong expander — phuc tap | `tab_ab_testing.py` |
| M10 | Khong co dark mode | Entire app |
| M11 | Color contrast thap tren secondary text (#737686) | `main.py` CSS |
| M12 | Drag-and-drop trong iframe khong sync Streamlit state | `tab_workflow.py` |
| M13 | pd.DataFrame dung nhung import khong tuong minh | `tab_publishing.py` |
| M14 | Khong co search/filter cho Navigation | `main.py` |
| M15 | Page title khong cap nhat theo trang dang xem | `main.py` |

### LOW — Nice to have

| # | Van de | File |
|---|--------|------|
| L1 | Khong co keyboard shortcuts | All |
| L2 | Khong co user avatar | `main.py` |
| L3 | Active page name hien thi 2 lan | `main.py` |
| L4 | Khong co page transition animation | All |
| L5 | max-width chua set cho ultrawide screens | `main.py` |
| L6 | Khong co "New" badge cho tinh nang moi | `main.py` |
| L7 | Copyright nam 2024 (outdated) trong login page | `main.py` |
| L8 | Khong co help center / documentation link | `main.py` |
| L9 | Session timeout khong co warning | `main.py` |
| L10 | Khong co "last saved" indicator cho Brand Brain | `tab_brand.py` |

---

## 7. DE XUAT KIEN TRUC UI MOI

### 7.1 Layout Architecture

```
TRUOC (Hien tai):
[Sidebar: User+API Keys+Nav] | [Main: Global Header + Tab Content]

SAU (De xuat):
+------------------------------------------------------------------+
| TOP BAR (64px, fixed)                                             |
| [Logo] [Search] [Workspace] ────────── [Bell] [Settings] [User]  |
+------------------------------------------------------------------+
+--------------+-------------------------------------------------+
| LEFT SIDEBAR | MAIN CONTENT                                    |
| (240px)      |                                                 |
| Collapsible  | [Breadcrumb: Home > Content Studio > Tao bai]   |
| on mobile    | [Page Title H1]     [Context Actions]           |
|              | ────────────────────────────────────────────    |
| NAV GROUPS   | CONTENT SECTIONS (lazy-loaded, scrollable)      |
| icon + text  |                                                 |
| ──────────── |                                                 |
| Settings     |                                                 |
| (bottom)     |                                            [Toast]
+--------------+-------------------------------------------------+
```

### 7.2 Design Tokens (Chuan hoa — 1 nguon duy nhat)

```css
/* === APEX AI DESIGN TOKENS === */

/* Brand Colors */
--color-primary:        #004ac6;   /* Main CTA, links */
--color-primary-hover:  #0053db;
--color-secondary:      #6366f1;   /* AI/Smart features */
--color-accent-green:   #10b981;   /* Success, positive KPI */
--color-danger:         #dc2626;   /* Delete, critical error */
--color-warning:        #f59e0b;   /* Caution */

/* Neutral Scale */
--color-bg:             #f9f9ff;   /* App background */
--color-surface:        #ffffff;   /* Cards, forms */
--color-border:         #e1e8fd;   /* Borders */
--color-text-primary:   #141b2b;
--color-text-secondary: #64748b;
--color-text-muted:     #94a3b8;

/* Sidebar */
--color-sidebar-bg:     #1e293b;
--color-sidebar-text:   #edf0ff;
--color-sidebar-active: linear-gradient(135deg, #004ac6, #2563eb);

/* Spacing (8pt grid) */
--space-1:4px; --space-2:8px; --space-3:12px;
--space-4:16px; --space-6:24px; --space-8:32px;

/* Border Radius */
--radius-sm:6px; --radius-md:10px; --radius-lg:16px; --radius-xl:20px;
```

### 7.3 Shared Component Library

```
ui/
├── components/
│   ├── __init__.py
│   ├── card.py          → render_kpi_card(), render_content_card()
│   ├── header.py        → render_page_header(title, subtitle, actions)
│   ├── table.py         → render_data_table(df, columns, row_actions)
│   ├── badge.py         → render_status_badge(), render_platform_badge()
│   ├── toast.py         → show_success_toast(), show_error_toast()
│   ├── confirm.py       → confirm_delete_dialog(item_name, delete_fn)
│   ├── empty_state.py   → render_empty_state(title, desc, cta)
│   └── form_helpers.py  → validated_text_input(), email_input()
```

### 7.4 Navigation Moi

**Doi ten cac navigation items:**

```
TRUOC (cu):               SAU (moi):
🧠 Intelligence           💡 Intelligence
  🧠 Knowledge Center       📚 Knowledge Center
  🧠 Brand Brain            🎭 Brand Brain
  🧠 Company Brain          🏢 Company Brain
  🧠 Learning Loop          📈 Learning Loop

Settings (an trong sidebar) → ⚙️ Settings Page rieng
API Keys (trong sidebar)   → Chuyen vao Settings Page
```

### 7.5 Key UX Improvements

#### A. Multi-step Wizard cho Content Creation

```
Buoc 1/4 [●○○○]  Chon Platform & Loai noi dung
Buoc 2/4 [○●○○]  Nhap Chu de, Audience & Angle
Buoc 3/4 [○○●○]  AI Config (Research, Knowledge)
Buoc 4/4 [○○○●]  Preview → Dang / Luu nhap / Len lich
```

#### B. Confirmation Dialog (Streamlit 1.35+ st.dialog)

```python
@st.dialog("Xac nhan xoa")
def confirm_delete_dialog(item_name: str, delete_fn: callable):
    st.warning(f"Ban co chac muon xoa '{item_name}'?")
    st.caption("Hanh dong nay khong the hoan tac!")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Xoa", type="primary", use_container_width=True):
            delete_fn()
            st.rerun()
    with col2:
        if st.button("Huy", use_container_width=True):
            st.rerun()
```

#### C. Settings Page rieng (tach API Keys khoi Sidebar)

```
Settings Page:
├── API Configuration (Gemini, Facebook, Zalo, LinkedIn)
├── Workspace Settings (ten, plan, members)
├── Notifications (email alerts, Slack webhook)
└── Appearance (Dark Mode toggle)
```

### 7.6 Lo trinh Cai tien (Roadmap)

| Giai doan | Noi dung | Muc do |
|-----------|----------|--------|
| Phase 1 — Critical Fixes | C1-C6: confirm delete, API settings page, form validation, label accessibility | CRITICAL |
| Phase 2 — Design System | Tao `ui/components/`, chuan hoa Design Tokens, shared `render_page_header()` | HIGH |
| Phase 3 — Navigation | Top bar, collapsible sidebar, doi ten icon trung, Settings page | HIGH |
| Phase 4 — UX Flows | Content creation wizard, onboarding, toast notification, empty states | HIGH |
| Phase 5 — Accessibility | ARIA labels, keyboard nav, color contrast fixes, focus indicators | MEDIUM |
| Phase 6 — Advanced | Dark mode, mobile responsive, URL routing (st.query_params) | LOW |

---

## 8. TOM TAT EXECUTIVE

### Scorecard

| Hang muc | Diem hien tai | Muc tieu sau cai tien |
|----------|:-------------:|:---------------------:|
| UI Design | **5.1/10** | 8.0/10 |
| UX Flow | **4.0/10** | 7.5/10 |
| Accessibility | **3.7/10** | 7.0/10 |
| Consistency | **4.3/10** | 8.5/10 |
| **Tong** | **4.3/10** | **7.8/10** |

### Top 3 Uu tien xu ly ngay (Quick Wins)

| # | Action | Impact |
|---|--------|--------|
| 1 | **C1** — Them `st.dialog` confirm truoc moi action xoa | Ngan mat du lieu khong the khoi phuc |
| 2 | **C2** — Chuyen API Keys ra Settings page rieng, khoi sidebar | Bao mat + giam cognitive overload |
| 3 | **C6** — Khoi phuc labels cho auth forms (bo `label_visibility="collapsed"`) | WCAG compliance |

### Diem manh hien tai

- Login page design chuyen nghiep, split-panel dep
- Analytics dashboard (KPI cards, leaderboard) UX tot
- A/B Testing component design xuat sac — variant cards, score bars
- Workflow Engine drag-and-drop innovative
- RBAC system implement dung huong, role-based visibility hoat dong
- Audit logging system day du
- Inter font + design tokens nen tang san sang mo rong
- Sidebar navigation grouping logic ro rang

---

*Bao cao duoc thuc hien boi AI Assistant (vai tro: Senior Product Designer + Senior UX Architect + Streamlit UI Engineer)*
*Cap nhat lan cuoi: 2026-07-12*
