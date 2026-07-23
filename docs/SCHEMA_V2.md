# Tài liệu Schema V2 — AI-Agent Marketing

Tài liệu này mô tả chi tiết 13 Entity chính (14 bảng thực tế) của hệ thống cơ sở dữ liệu **AI-Agent Marketing** sau khi nâng cấp lên phiên bản V2.

---

## 1. Sơ đồ quan hệ thực thể (ERD)

```
users (1) ─────────── (N) workspace_members (N) ─────────── (1) workspaces (1)
  │                                                               │
  │                                                ┌──────────────┼──────────────┐
  │                                               (1)            (1)            (1)
  │                                            companies      projects        brand
  │                                                │              │
  │                                               (1)            (1)
  │                                            campaigns ─────────┘
  │                                                │
  │                                               (1)
  │                                        ┌───────┴───────┐
  │                                       (N)             (N)
  │                                      posts         knowledge
  │                                       │
  │                    ┌──────────────────┼──────────────────┐
  │                   (1)                (N)                (N)
  │                schedules          approvals          analytics
  │
  └── (N) prompt_versions
```

---

## 2. Danh sách các bảng và chi tiết các trường

### 2.1. `users` — Người dùng
Lưu trữ thông tin tài khoản người dùng, vai trò hệ thống, và mật khẩu đã hash.
- **id** (`INTEGER/SERIAL` PK): ID người dùng.
- **email** (`TEXT` UNIQUE): Địa chỉ email.
- **username** (`TEXT` UNIQUE): Tên tài khoản.
- **password_hash** (`TEXT`): Chuỗi mật khẩu đã băm (SHA-256 kèm salt).
- **full_name** (`TEXT`): Họ và tên đầy đủ.
- **avatar_url** (`TEXT`): Link ảnh đại diện.
- **role** (`TEXT`): Vai trò (`super_admin`, `admin`, `editor`, `viewer`).
- **is_active** (`INTEGER/BOOLEAN`): Trạng thái hoạt động.
- **created_at** / **updated_at** / **last_login_at** (`TEXT/TIMESTAMPTZ`).

### 2.2. `workspaces` — Không gian làm việc
Hỗ trợ mô hình **Multi-tenant** để phân vùng tài nguyên độc lập.
- **id** (`INTEGER/SERIAL` PK): ID workspace.
- **name** (`TEXT`): Tên không gian làm việc.
- **slug** (`TEXT` UNIQUE): Đường dẫn URL thân thiện (ví dụ: `default-workspace`).
- **owner_id** (`INTEGER` FK → `users.id`): Người sở hữu.
- **plan** (`TEXT`): Gói dịch vụ (`free`, `pro`, `enterprise`).
- **max_users** / **max_posts_per_month** (`INTEGER`): Giới hạn hệ thống.
- **is_active** (`INTEGER/BOOLEAN`).

### 2.3. `workspace_members` — Thành viên Workspace
Bảng trung gian thể hiện quan hệ Nhiều-Nhiều giữa Users và Workspaces.
- **workspace_id** (`INTEGER` FK → `workspaces.id`).
- **user_id** (`INTEGER` FK → `users.id`).
- **role** (`TEXT`): Vai trò của thành viên trong workspace này (`admin`, `editor`, `viewer`).

### 2.4. `companies` — Công ty
Thông tin doanh nghiệp/khách hàng cần làm content.
- **id** (`INTEGER/SERIAL` PK).
- **workspace_id** (`INTEGER` FK → `workspaces.id`).
- **name** (`TEXT`): Tên doanh nghiệp (ví dụ: `Hung Viet AI`).
- **industry** / **size** / **website** / **description** / **logo_url** (`TEXT`).

### 2.5. `brand` — Nhận diện thương hiệu
Lưu trữ các chỉ dẫn viết content AI, Tone of voice, đối tượng mục tiêu, và từ cấm.
- **id** (`INTEGER/SERIAL` PK).
- **company_id** (`INTEGER` FK → `companies.id`).
- **workspace_id** (`INTEGER` FK → `workspaces.id`).
- **tone_of_voice** (`TEXT`): Giọng văn chủ đạo (`formal`, `casual`, `educational`,...).
- **target_audiences** (`TEXT/JSONB`): Danh sách đối tượng mục tiêu (JSON Array).
- **brand_colors** (`TEXT/JSONB`): Bảng màu thương hiệu.
- **brand_guidelines** (`TEXT`): Tài liệu markdown chỉ dẫn viết content.
- **blacklist_words** (`TEXT/JSONB`): Danh sách từ ngữ cấm sử dụng (JSON Array).

### 2.6. `projects` — Dự án
- **id** (`INTEGER/SERIAL` PK).
- **workspace_id** (`INTEGER` FK → `workspaces.id`).
- **company_id** (`INTEGER` FK → `companies.id`).
- **name** / **description** / **status** / **start_date** / **end_date** (`TEXT`).

### 2.7. `campaigns` — Chiến dịch marketing
- **id** (`INTEGER/SERIAL` PK).
- **project_id** (`INTEGER` FK → `projects.id`).
- **workspace_id** (`INTEGER` FK → `workspaces.id`).
- **name** / **objective** / **target_audience** / **status** (`TEXT`).
- **platforms** (`TEXT/JSONB`): Các mạng xã hội mục tiêu (ví dụ: `["facebook", "zalo"]`).
- **budget** (`REAL/NUMERIC`).

### 2.8. `posts` — Bài đăng
Lưu trữ toàn bộ nội dung tiếp thị tạo bởi AI, điểm số, và trạng thái phê duyệt.
- **id** (`INTEGER/SERIAL` PK).
- **workspace_id** (`INTEGER` FK → `workspaces.id`).
- **campaign_id** (`INTEGER` FK → `campaigns.id`).
- **title** / **content** / **platform** / **content_type** / **status** (`TEXT`).
- **scheduled_at** / **published_at** (`TEXT/TIMESTAMPTZ`).
- **viral_score** (`INTEGER`): Điểm viral (1-10).
- **image_prompt** (`TEXT`): Prompt gợi ý sinh ảnh.
- **ai_metadata** (`TEXT/JSONB`): Metadata của AI (tokens, model, cost).

### 2.9. `assets` — Tài nguyên media
Lưu trữ thông tin hình ảnh/video đi kèm bài viết.
- **id** (`INTEGER/SERIAL` PK).
- **workspace_id** (`INTEGER` FK → `workspaces.id`).
- **post_id** (`INTEGER` FK → `posts.id`): Bài viết liên kết.
- **name** / **file_type** / **url** / **storage_path** / **mime_type** (`TEXT`).
- **size_bytes** (`INTEGER`).
- **tags** (`TEXT/JSONB`).

### 2.10. `knowledge` — Kho tri thức AI
Phiên bản nâng cấp của `knowledge_posts` cũ.
- **id** (`INTEGER/SERIAL` PK).
- **workspace_id** (`INTEGER` FK → `workspaces.id`).
- **title** / **content** / **summary** / **knowledge_type** / **ai_tool** / **audience** / **difficulty** / **platform** / **status** (`TEXT`).
- **post_id** (`INTEGER` FK → `posts.id`).
- **tags** (`TEXT/JSONB`).

### 2.11. `schedules` — Lịch đăng bài
- **id** (`INTEGER/SERIAL` PK).
- **workspace_id** (`INTEGER` FK → `workspaces.id`).
- **post_id** (`INTEGER` FK → `posts.id`).
- **scheduled_at** (`TEXT/TIMESTAMPTZ`): Thời gian đăng dự kiến.
- **status** (`TEXT`): `pending`, `processing`, `published`, `failed`, `cancelled`.
- **retry_count** (`INTEGER`): Số lần thử lại nếu thất bại.
- **error_message** (`TEXT`).

### 2.12. `approvals` — Phê duyệt bài viết
- **id** (`INTEGER/SERIAL` PK).
- **post_id** (`INTEGER` FK → `posts.id`).
- **workspace_id** (`INTEGER` FK → `workspaces.id`).
- **requested_by** / **approved_by** (`INTEGER` FK → `users.id`).
- **status** (`TEXT`): `pending`, `approved`, `rejected`, `revision_requested`.
- **notes** (`TEXT`): Lý do phản hồi.

### 2.13. `prompt_versions` — Phiên bản Prompt AI
Theo dõi hiệu năng và quản lý lịch sử thay đổi prompt AI.
- **id** (`INTEGER/SERIAL` PK).
- **workspace_id** (`INTEGER` FK → `workspaces.id`): Cấu hình per workspace (NULL = Global).
- **prompt_name** (`TEXT`): Tên prompt (ví dụ: `viral_marketing`).
- **version** (`INTEGER`): Phiên bản tự tăng.
- **content** (`TEXT`): Nội dung prompt thô.
- **variables** (`TEXT/JSONB`): Các biến sử dụng.
- **is_active** (`INTEGER/BOOLEAN`): Phiên bản đang chạy.
- **performance_score** (`REAL`): Điểm viral trung bình của các bài sử dụng prompt này.

### 2.14. `analytics` — Phân tích hiệu suất bài viết
Thống kê tương tác theo ngày của bài viết đã đăng.
- **id** (`INTEGER/SERIAL` PK).
- **post_id** (`INTEGER` FK → `posts.id`).
- **workspace_id** (`INTEGER` FK → `workspaces.id`).
- **platform** / **metric_date** (`TEXT`): Nền tảng và ngày thống kê (YYYY-MM-DD).
- **impressions** / **reach** / **likes** / **comments** / **shares** / **saves** / **clicks** / **link_clicks** (`INTEGER`).
- **engagement_rate** / **reach_rate** (`REAL`): Tỷ lệ tương tác/reach (%).
- **raw_data** (`TEXT/JSONB`): Dữ liệu gốc từ API.
