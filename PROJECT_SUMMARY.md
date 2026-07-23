# 📋 TÓM TẮT DỰ ÁN — AI_Agent_Content_AutoPos

> **Ngày tạo**: 2026-07-12  
> **Tác giả tóm tắt**: Antigravity AI Assistant  
> **Phiên bản hiện tại**: V2 (sau tái cấu trúc)

---

## 1. 🎯 Tổng Quan Dự Án

**AI_Agent_Content_AutoPost** là một ứng dụng **AI Marketing Automation** chạy trên nền tảng **Streamlit**, được thiết kế để giúp các doanh nghiệp và marketer tự động hóa toàn bộ quy trình tạo, lập lịch và đăng bài nội dung lên mạng xã hội với sự hỗ trợ của trí tuệ nhân tạo.

### Mục tiêu cốt lõi
- **Tự động sinh nội dung** marketing chất lượng cao bằng AI (Google Gemini)
- **Lập kế hoạch nội dung** tuần/tháng một cách thông minh
- **Tự động đăng bài** lên Facebook, Zalo OA và LinkedIn
- **Chia sẻ kiến thức AI** dưới dạng bài viết giáo dục chuyên sâu
- **Quản lý nhiều khách hàng/thương hiệu** theo mô hình Multi-tenant Workspace

---

## 2. 🏗️ Kiến Trúc Hệ Thống

### Kiểu kiến trúc
**Monolithic Application** với phân tách module rõ ràng theo chức năng.

```
┌─────────────────────────────────────────────────────┐
│              Streamlit Web UI (app/main.py)          │
│         21 tabs giao diện chức năng chuyên biệt      │
└──────────────────────┬──────────────────────────────┘
                       │
         ┌─────────────┼──────────────┐
         ▼             ▼              ▼
   ┌──────────┐  ┌──────────┐  ┌──────────────┐
   │  Services│  │ Database │  │    Core /    │
   │  (AI/API)│  │  Models  │  │   Workflow   │
   └────┬─────┘  └────┬─────┘  └──────┬───────┘
        │              │               │
        ▼              ▼               ▼
   ┌──────────┐  ┌──────────┐  ┌──────────────┐
   │  Google  │  │ SQLite / │  │   Agents /   │
   │  Gemini  │  │Postgres  │  │  Knowledge   │
   │   API    │  │    DB    │  │   Engines    │
   └──────────┘  └──────────┘  └──────────────┘
        │
        ▼
   ┌──────────────────────────────┐
   │   Mạng xã hội tích hợp      │
   │  Facebook │ Zalo OA │ LinkedIn│
   └──────────────────────────────┘
```

### Công nghệ sử dụng

| Thành phần | Công nghệ |
|-----------|-----------|
| **Framework UI** | Streamlit ≥ 1.35.0 |
| **AI Engine** | Google Gemini API (model: `gemini-2.5-flash`) |
| **Database chính** | SQLite 3 (local) |
| **Database tùy chọn** | PostgreSQL (cho môi trường SaaS) |
| **Xuất tài liệu** | FPDF2 (PDF) + python-docx (Word) |
| **Mạng xã hội** | Facebook Graph API, Zalo OA API, LinkedIn UGC API |
| **HTTP Client** | requests ≥ 2.31.0 |
| **Xử lý dữ liệu** | pandas ≥ 2.0.0 |
| **Cấu hình** | python-dotenv ≥ 1.0.0 |
| **Ngôn ngữ** | Python 3.x |

---

## 3. 📁 Cấu Trúc Thư Mục

```
AI_Agent_Content_AutoPos/
│
├── app/                          # Điểm khởi chạy chính
│   └── main.py                   # File Streamlit chính (41 KB)
│
├── config/                       # Cấu hình hệ thống
│   ├── config.py                 # Logger, settings object
│   ├── constants.py              # Hằng số toàn cục (AI tools, topic bank...)
│   ├── logging.py                # Cấu hình logging
│   └── settings.py               # Biến môi trường (.env loader)
│
├── database/                     # Lớp truy cập dữ liệu
│   ├── connection.py             # Kết nối DB (SQLite/PostgreSQL dual-support)
│   ├── schema.py                 # Định nghĩa schema V2 (14 bảng)
│   ├── migrate_v2.py             # Script migration V2
│   ├── migrate_to_postgres.py    # Script chuyển SQLite → PostgreSQL
│   ├── models/                   # Các CRUD Model class
│   │   ├── __init__.py           # Export 13 model classes
│   │   ├── users.py              # UserModel
│   │   ├── workspaces.py         # WorkspaceModel + MemberModel
│   │   ├── companies.py          # CompanyModel
│   │   ├── brand.py              # BrandModel
│   │   ├── projects.py           # ProjectModel
│   │   ├── campaigns.py          # CampaignModel
│   │   ├── posts.py              # PostModel
│   │   ├── assets.py             # AssetModel
│   │   ├── knowledge.py          # KnowledgeModel
│   │   ├── schedules.py          # ScheduleModel
│   │   ├── approvals.py          # ApprovalModel
│   │   ├── prompt_versions.py    # PromptVersionModel
│   │   ├── analytics.py          # AnalyticsModel
│   │   ├── ab_testing.py         # ABTestingModel
│   │   ├── ai_cost.py            # AICostModel
│   │   ├── billing.py            # BillingModel
│   │   └── learning_insights.py  # LearningInsightModel
│   └── repositories/             # Repository pattern (query nâng cao)
│       ├── audit_repository.py
│       ├── knowledge_repository.py
│       ├── post_repository.py
│       └── weekly_schedule_repository.py
│
├── services/                     # Tích hợp API bên ngoài
│   ├── gemini_client.py          # Google Gemini AI client
│   ├── content_service.py        # Dịch vụ tạo nội dung
│   ├── automation_service.py     # Dịch vụ tự động hóa
│   ├── brand_voice_engine.py     # Engine giọng thương hiệu
│   ├── chat_service.py           # Chat service
│   ├── copywriting_service.py    # Dịch vụ viết content
│   ├── fact_check_service.py     # Kiểm tra thông tin thực tế
│   ├── monitoring_service.py     # Giám sát hệ thống
│   ├── trend_service.py          # Phân tích xu hướng
│   └── vector_service.py         # Vector search service
│
├── agents/                       # AI Prompt & Framework
│   ├── prompt_templates.py       # Template prompt hệ thống (24 KB)
│   ├── copywriting_prompts.py    # Prompt copywriting chuyên biệt
│   └── framework.py              # Cấu trúc khung Prompt
│
├── core/                         # Tiện ích hệ thống
│   ├── audit_logger.py           # Ghi log kiểm toán
│   ├── auth.py                   # Xác thực người dùng
│   ├── doc_exporter.py           # Xuất PDF/Word (20 KB)
│   ├── document_parser.py        # Phân tích tài liệu
│   └── rbac.py                   # Phân quyền theo vai trò (RBAC)
│
├── social/                       # Tích hợp mạng xã hội
│   └── publishers.py             # Facebook, Zalo OA, LinkedIn API
│
├── workflow/                     # Workflow & Lịch trình
│   ├── scheduler.py              # Lập lịch nội dung 30 ngày
│   └── learning_engine.py        # Engine học máy từ dữ liệu (18 KB)
│
├── analytics/                    # Phân tích dữ liệu
│   └── (viral_score, metrics)
│
├── ui/                           # Các tab giao diện (21 tab)
│   ├── tab_plan.py               # Tab lên lịch tuần
│   ├── tab_create.py             # Tab tạo & đăng bài (18 KB)
│   ├── tab_history.py            # Tab lịch sử bài viết
│   ├── tab_campaign.py           # Tab chiến dịch
│   ├── tab_analytics.py          # Tab phân tích (24 KB)
│   ├── tab_ab_testing.py         # Tab A/B Testing (31 KB)
│   ├── tab_workflow.py           # Tab workflow tự động (21 KB)
│   ├── tab_publishing.py         # Tab lịch đăng bài (17 KB)
│   ├── tab_knowledge.py          # Tab kho tri thức (15 KB)
│   ├── tab_copywriting.py        # Tab copywriting AI
│   ├── tab_learning.py           # Tab học máy & insights
│   ├── tab_brand.py              # Tab nhận diện thương hiệu
│   ├── tab_approval.py           # Tab phê duyệt nội dung
│   ├── tab_factcheck.py          # Tab kiểm tra thực tế
│   ├── tab_trend.py              # Tab xu hướng
│   ├── tab_monitoring.py         # Tab giám sát hệ thống
│   ├── tab_planning.py           # Tab lập kế hoạch
│   ├── tab_company_brain.py      # Tab tri thức doanh nghiệp
│   ├── tab_ai_cost.py            # Tab theo dõi chi phí AI
│   ├── tab_billing.py            # Tab thanh toán
│   └── tab_audit.py              # Tab nhật ký kiểm toán
│
├── knowledge/                    # Kho tri thức & Engine
│   └── (case study, comparison, reels engines)
│
├── docs/                         # Tài liệu kỹ thuật
│   ├── PROJECT_ARCHITECTURE.md   # Kiến trúc dự án
│   ├── MODULE_LIST.md            # Danh sách module
│   ├── SCHEMA_V2.md              # Schema cơ sở dữ liệu V2
│   ├── MASTER_UPGRADE_PLAN.md    # Kế hoạch nâng cấp
│   ├── DEPENDENCY_GRAPH.md       # Đồ thị phụ thuộc
│   ├── RISK_ANALYSIS.md          # Phân tích rủi ro
│   └── MIGRATION_V2_REPORT.md    # Báo cáo migration
│
├── tests/                        # Unit tests
├── .env                          # Biến môi trường (API Keys)
├── requirements.txt              # Danh sách thư viện
├── REFACTOR_REPORT.md            # Báo cáo tái cấu trúc
└── content_manager.db            # Database SQLite (~3 MB)
```

---

## 4. 🗃️ Mô Hình Dữ Liệu (Schema V2)

Hệ thống sử dụng **14 bảng dữ liệu** tổ chức theo mô hình Multi-tenant:

```
users (1) ──── (N) workspace_members ──── (1) workspaces
                                               │
                              ┌───────────────┼──────────────┐
                           companies        projects        brand
                              │                │
                           campaigns ─────────┘
                              │
                    ┌─────────┴─────────┐
                  posts             knowledge
                    │
          ┌─────────┼──────────┐
       schedules  approvals  analytics
```

### Bảng dữ liệu chi tiết

| Bảng | Mô tả | Trường quan trọng |
|------|-------|-------------------|
| `users` | Tài khoản người dùng | email, role (super_admin/admin/editor/viewer), password_hash |
| `workspaces` | Không gian làm việc | name, slug, plan (free/pro/enterprise), max_users |
| `workspace_members` | Thành viên Workspace | workspace_id, user_id, role |
| `companies` | Thông tin doanh nghiệp | name, industry, size, website |
| `brand` | Nhận diện thương hiệu | tone_of_voice, target_audiences, blacklist_words, brand_guidelines |
| `projects` | Dự án marketing | name, status, start_date, end_date |
| `campaigns` | Chiến dịch | name, objective, platforms (JSON), budget |
| `posts` | Bài đăng | content, platform, status, viral_score (1-10), image_prompt |
| `assets` | Tài nguyên media | name, file_type, url, size_bytes |
| `knowledge` | Kho tri thức AI | title, knowledge_type, audience, difficulty, ai_tool |
| `schedules` | Lịch đăng bài | scheduled_at, status (pending/published/failed), retry_count |
| `approvals` | Phê duyệt | status (pending/approved/rejected), notes |
| `prompt_versions` | Phiên bản Prompt | prompt_name, version, content, performance_score |
| `analytics` | Phân tích hiệu suất | impressions, reach, likes, comments, engagement_rate |

### Hỗ trợ dual database
- **SQLite**: Mặc định cho chạy local/single user
- **PostgreSQL**: Tùy chọn khi deploy SaaS (set `DB_ENGINE=postgresql` trong `.env`)

---

## 5. 🤖 AI & Prompt System

### AI Engine
- **Model**: Google Gemini `gemini-2.5-flash`
- **SDK**: `google-genai` (mới) với fallback sang `google.generativeai`
- **Tính năng nổi bật**:
  - Hỗ trợ Google Search Tool (research mode)
  - Tự động sửa lỗi JSON (JSON Repair Workflow)
  - Kiểm tra cấu trúc dữ liệu trả về

### Loại nội dung AI tạo ra
1. **Marketing Viral** — Bài đăng quảng cáo lan truyền cao
2. **AI Knowledge Sharing** — Bài giáo dục về AI (Tutorial, Tips, Case Study, Comparison, Deep Dive...)

### Kho chủ đề (Topic Bank)
- **AI Basics** (6 chủ đề): Nền tảng AI cho người mới
- **Prompt Engineering** (6 chủ đề): Kỹ thuật viết prompt hiệu quả
- **AI Tools** (6 chủ đề): So sánh và đánh giá công cụ AI
- **Case Study** (5 chủ đề): Tình huống triển khai thực tế
- **Automation** (4 chủ đề): Tự động hóa quy trình
- **Future Trends** (3 chủ đề): Xu hướng AI tương lai

### 11 AI Tools được tích hợp so sánh
`ChatGPT` · `Claude` · `Gemini` · `Cursor` · `Codex` · `Windsurf` · `n8n` · `Make` · `MCP` · `Lovable` · `Bolt`

---

## 6. 📱 Giao Diện Người Dùng (21 Tabs)

| Tab | File | Chức năng |
|-----|------|-----------|
| Lên lịch tuần | `tab_plan.py` | Tạo kế hoạch content 7 ngày bằng AI |
| Tạo & Đăng bài | `tab_create.py` | Tạo bài viết và đăng trực tiếp |
| Lịch sử | `tab_history.py` | Xem & xuất lịch sử bài viết |
| Chiến dịch | `tab_campaign.py` | Quản lý campaign marketing |
| Phân tích | `tab_analytics.py` | Dashboard phân tích hiệu suất |
| A/B Testing | `tab_ab_testing.py` | So sánh hiệu quả nội dung |
| Workflow | `tab_workflow.py` | Quy trình tự động hóa |
| Lịch đăng | `tab_publishing.py` | Lập lịch đăng bài tương lai |
| Tri thức | `tab_knowledge.py` | Kho tri thức AI & quản lý |
| Copywriting | `tab_copywriting.py` | Viết copy chuyên nghiệp |
| Học máy | `tab_learning.py` | AI học từ hiệu suất bài đăng |
| Thương hiệu | `tab_brand.py` | Quản lý nhận diện thương hiệu |
| Phê duyệt | `tab_approval.py` | Quy trình duyệt nội dung |
| Fact Check | `tab_factcheck.py` | Kiểm tra độ chính xác |
| Xu hướng | `tab_trend.py` | Trending topics & insights |
| Giám sát | `tab_monitoring.py` | Theo dõi hệ thống real-time |
| Kế hoạch | `tab_planning.py` | Lập kế hoạch dài hạn |
| Company Brain | `tab_company_brain.py` | Tri thức nội bộ doanh nghiệp |
| Chi phí AI | `tab_ai_cost.py` | Theo dõi chi phí API |
| Thanh toán | `tab_billing.py` | Quản lý gói dịch vụ |
| Kiểm toán | `tab_audit.py` | Nhật ký hoạt động hệ thống |

---

## 7. 🔗 Tích Hợp Mạng Xã Hội

| Nền tảng | Endpoint API | Phương thức |
|---------|-------------|-------------|
| **Facebook** | `/feed` (Graph API) | POST với Page Access Token |
| **Zalo OA** | `/oa/message` | POST Broadcast Message |
| **LinkedIn** | `/ugcPosts` | POST dạng PUBLISHED |

---

## 8. 📤 Xuất Tài Liệu

| Định dạng | Thư viện | Chức năng |
|-----------|---------|-----------|
| **PDF** | fpdf2 ≥ 2.7.0 | Xuất bài viết, báo cáo, kế hoạch |
| **Word (.docx)** | python-docx ≥ 1.1.0 | Xuất kế hoạch tuần, bài viết |
| **CSV** | pandas | Xuất dữ liệu phân tích |

---

## 9. 🔐 Bảo Mật & Phân Quyền

### Xác thực
- Mật khẩu được băm bằng **SHA-256 + Salt**
- Quản lý session qua Streamlit State

### Phân quyền RBAC (Role-Based Access Control)
| Vai trò | Quyền hạn |
|---------|-----------|
| `super_admin` | Toàn quyền hệ thống |
| `admin` | Quản lý workspace, user |
| `editor` | Tạo, chỉnh sửa nội dung |
| `viewer` | Chỉ đọc |

### Cấu hình bảo mật
- API Keys lưu trong file `.env` (không commit lên Git)
- Hỗ trợ biến môi trường cho toàn bộ thông tin nhạy cảm

---

## 10. 🚀 Lộ Trình Phát Triển (Roadmap)

### Giai đoạn 1 — Bảo mật & Tối ưu AI *(Hiện tại)*
- [x] Bảo mật API Key qua `.env`
- [x] Tích hợp Gemini JSON Repair Workflow
- [ ] Triển khai Gemini Structured Outputs (Pydantic Schema)

### Giai đoạn 2 — Tái cấu trúc kiến trúc *(Hoàn thành)*
- [x] Tách module: UI / Database / Services / Core
- [x] Nâng cấp Schema V2 (14 bảng, Multi-tenant)
- [x] Hỗ trợ dual database SQLite + PostgreSQL
- [ ] Xử lý Async cho tác vụ đăng bài (Threading/Queue)

### Giai đoạn 3 — Kiểm thử & Đóng gói *(Kế hoạch)*
- [ ] Viết Unit Tests với pytest cho các Engine
- [ ] Đóng gói Docker + docker-compose
- [ ] Deploy Demo trên server

---

## 11. ⚠️ Rủi Ro Kỹ Thuật Đã Xác Định

| Rủi ro | Mức độ | Trạng thái |
|--------|--------|-----------|
| API Key bị lộ trong file `.bat` | 🚨 Rất cao | Cần khắc phục |
| Gọi API đồng bộ gây treo UI Streamlit | ⚠️ Trung bình | Kế hoạch dùng Threading |
| JSON Repair Logic không ổn định | ⚠️ Trung bình | Kế hoạch dùng Structured Outputs |
| SQLite bị khóa khi nhiều user | 📉 Thấp | Chuyển PostgreSQL khi scale |
| File code đơn lẻ >1700 dòng | ⚠️ Cao | ✅ Đã giải quyết (tái cấu trúc) |

---

## 12. 📦 Cài Đặt & Khởi Chạy

```bash
# 1. Cài đặt thư viện
pip install -r requirements.txt

# 2. Tạo file cấu hình
cp .env.example .env
# Điền API Keys vào file .env

# 3. Khởi chạy ứng dụng
streamlit run app/main.py

# Hoặc dùng file bat (Windows)
AI_Agent_Content_AutoPost.bat
```

### Biến môi trường cần thiết (`.env`)
```env
GEMINI_API_KEY=your_gemini_api_key
FACEBOOK_ACCESS_TOKEN=your_fb_token
FACEBOOK_PAGE_ID=your_page_id
ZALO_OA_ACCESS_TOKEN=your_zalo_token
LINKEDIN_ACCESS_TOKEN=your_linkedin_token
DB_ENGINE=sqlite   # hoặc postgresql
```

---

## 13. 📊 Thống Kê Dự Án

| Chỉ số | Giá trị |
|--------|---------|
| **Tổng số file Python** | ~60+ files |
| **Số tab giao diện** | 21 tabs |
| **Số bảng database** | 14 bảng (Schema V2) |
| **Số Model CRUD class** | 13 classes |
| **Số service tích hợp** | 10 services |
| **Kích thước database** | ~3 MB (content_manager.db) |
| **Nền tảng MXH hỗ trợ** | 3 (Facebook, Zalo, LinkedIn) |
| **Công cụ AI so sánh** | 11 tools |
| **Chủ đề nội dung** | 30+ topics trong Topic Bank |

---

*File này được tạo tự động bởi AI Assistant. Cập nhật lần cuối: 2026-07-12*
