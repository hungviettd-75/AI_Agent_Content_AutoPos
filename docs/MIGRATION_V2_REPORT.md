# Báo cáo Nâng cấp Schema V2 (13 Entity)

**Thời gian:** 2026-07-11 15:22:09
**Database Engine:** `SQLITE`

## Kết quả Khởi tạo
- **Trạng thái:** Thành công ✅
- **Số bảng đã xác minh:** 14/14 bảng (gồm cả bảng phụ `workspace_members`)

## Tài nguyên mặc định được khởi tạo
- **User quản trị mặc định:** `admin@hungvietai.com` (Role: `super_admin`)
- **Workspace mặc định:** `Default Workspace` (Slug: `default-workspace`)
- **Company mặc định:** `Hung Viet AI` (Industry: `AI & Automation Service`)
- **Brand Profile mặc định:** Tone: `casual`, Target: `[CEO, Sales, Chủ Shop, Freelancer, AI Specialist]`

## Dữ liệu chuyển đổi (Migration)
- **Bài viết tiếp thị (posts) cũ:** Đã gán/migrate `118/118` dòng cũ sang default workspace và thêm đầy đủ cấu trúc mới.
- **Bài viết tri thức (knowledge_posts) cũ:** Đã chuyển đổi `0/0` sang bảng `knowledge` mới (Bảng cũ đã xóa thành công).

## Hướng dẫn sử dụng
Cơ sở dữ liệu đã sẵn sàng chạy với 13 bảng mới và tương thích ngược với các thao tác CRUD hiện tại.
