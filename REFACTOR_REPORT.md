# BÁO CÁO TÁI CẤU TRÚC DỰ ÁN (REFACTOR_REPORT.md)

Tài liệu này báo cáo chi tiết cấu trúc phân vùng mới của dự án **AI-Agent Marketing** sau khi tái cấu trúc nhằm mục đích chia nhỏ file nguyên khối `AI_Agent_Content_AutoPost.py` và các module engine độc lập vào các thư mục chuyên biệt.

---

## 1. Bản Đồ Cấu Trúc Thư Mục Mới (New Project Directory Layout)

Dưới đây là sơ đồ tổ chức thư mục của dự án sau khi phân tách:

```
AI_Agent_Content_AutoPost/
├── app/
│   └── main.py                 # File khởi chạy chính Streamlit (Gốc: AI_Agent_Content_AutoPost.py)
├── config/
│   └── settings.py             # Cấu hình biến môi trường, đường dẫn database
├── database/
│   └── connection.py           # Thiết lập SQLite, tạo bảng, hàm CRUD
├── social/
│   └── publishers.py           # Tích hợp đăng bài (Facebook, Zalo, LinkedIn)
├── services/
│   └── gemini_client.py        # Client kết nối Gemini AI API & tự sửa JSON
├── core/
│   └── doc_exporter.py         # Hàm phụ trợ tiện ích: xuất PDF, xuất Word (.docx)
├── agents/
│   ├── prompt_templates.py     # Prompt hệ thống & các câu lệnh mẫu
│   └── framework.py            # Cấu trúc khung Prompt (Gốc: prompt_framework_engine.py)
├── knowledge/
│   ├── case_study.py           # Engine sinh Case Study (Gốc: case_study_engine.py)
│   ├── comparison.py           # Engine lập bảng so sánh (Gốc: comparison_engine.py)
│   └── reels.py                # Engine sinh kịch bản Reels (Gốc: knowledge_reels_engine.py)
├── workflow/
│   └── scheduler.py            # Lên lịch trình nội dung 30 ngày (Gốc: knowledge_planner.py)
├── analytics/
│   └── viral_score.py          # Logic trích xuất điểm số & lý do lan truyền
├── ui/
│   ├── tab_plan.py             # Tab Lên lịch tuần
│   ├── tab_create.py           # Tab Tạo & Đăng Bài
│   └── tab_history.py          # Tab Lịch sử bài viết
├── REFACTOR_REPORT.md          # Báo cáo này
└── content_manager.db          # Cơ sở dữ liệu SQLite
```

---

## 2. Chi Tiết Phân Chia Từng Module

### 2.1. Module `config/` (Cấu hình)
*   **Mục tiêu**: Độc lập hóa cấu hình hệ thống khỏi code chạy.
*   **Nội dung**: File `settings.py` chịu trách nhiệm nạp các khóa bí mật (`GEMINI_API_KEY`, các Access Tokens) từ file `.env` sử dụng thư viện `python-dotenv`. Cách tiếp cận này giúp bảo mật mã nguồn khi đưa lên các hệ thống quản lý phiên bản (Git).

### 2.2. Module `database/` (Cơ sở dữ liệu)
*   **Mục tiêu**: Tách biệt logic truy cập dữ liệu (Data Access Object).
*   **Nội dung**: File `connection.py` tập hợp toàn bộ các hàm SQLite như `init_db()`, `get_db_connection()`, các hàm lưu bài đăng và cập nhật trạng thái. Lớp UI Streamlit chỉ cần import các hàm này thay vì tự viết các câu lệnh SQL sống.

### 2.3. Module `social/` (Đăng bài mạng xã hội)
*   **Mục tiêu**: Quản lý độc lập kênh truyền thông mạng xã hội.
*   **Nội dung**: Gom các hàm gọi API REST: `post_to_facebook()`, `post_to_zalo_oa()`, `post_to_linkedin()` vào `publishers.py`. Dễ dàng nâng cấp hoặc thay thế API của các bên này mà không ảnh hưởng tới logic nghiệp vụ khác.

### 2.4. Module `services/` (Tích hợp API AI)
*   **Mục tiêu**: Tạo lớp trừu tượng kết nối AI.
*   **Nội dung**: `gemini_client.py` xử lý cấu hình model, thiết lập tham số nhiệt độ (temperature) và các hàm bổ sung lớp sửa định dạng JSON (JSON validation/repair).

### 2.5. Module `core/` (Hàm dùng chung)
*   **Mục tiêu**: Phục vụ các tiện ích kỹ thuật.
*   **Nội dung**: Đóng gói các hàm liên quan đến thư viện `FPDF` và `python-docx` phục vụ xuất tài liệu Tiếng Việt không bị lỗi định dạng font chữ vào file `doc_exporter.py`.

### 2.6. Module `agents/` (Thiết kế prompt)
*   **Mục tiêu**: Quản lý tập trung tài nguyên tri thức của Agent.
*   **Nội dung**: Tách toàn bộ các văn bản prompt dài hàng trăm dòng ra khỏi code UI. Chuyển chúng thành các hằng số hoặc template trong `prompt_templates.py`. Module `framework.py` chứa logic cấu trúc prompt của `prompt_framework_engine.py`.

### 2.7. Module `knowledge/` (Trích xuất tri thức)
*   **Mục tiêu**: Đóng gói logic sinh nội dung giáo dục.
*   **Nội dung**: Chuyển đổi mã nguồn từ các file engine cũ (`case_study_engine.py`, `comparison_engine.py`, `knowledge_reels_engine.py`) vào các file tương ứng trong thư mục `knowledge/`.

### 2.8. Module `workflow/` (Lịch trình)
*   **Mục tiêu**: Điều phối kế hoạch nội dung dài hạn.
*   **Nội dung**: Chuyển các hàm tính toán lịch đăng bài 30 ngày từ `knowledge_planner.py` cũ vào `scheduler.py`.

### 2.9. Module `analytics/` (Phân tích chỉ số)
*   **Mục tiêu**: Đánh giá hiệu suất nội dung.
*   **Nội dung**: Chứa logic xử lý trích xuất điểm số lan truyền và lý do chấm điểm từ văn bản phản hồi của AI.

### 2.1.0. Module `ui/` (Giao diện người dùng)
*   **Mục tiêu**: Tối giản hóa file chạy chính Streamlit.
*   **Nội dung**: Chia nhỏ giao diện thành 3 file độc lập: `tab_plan.py` (Lên lịch tuần), `tab_create.py` (Tạo & Đăng Bài), và `tab_history.py` (Lịch sử). Việc này giúp chỉnh sửa giao diện một tab không ảnh hưởng đến tab khác.

### 2.1.1. Module `app/` (Điểm khởi chạy)
*   **Mục tiêu**: Điểm vào của chương trình (Entry Point).
*   **Nội dung**: File `main.py` chỉ làm nhiệm vụ import cấu hình, thiết lập tiêu đề trang, áp dụng CSS tùy biến và render layout sidebar cùng các tab giao diện.

---

## 3. Lợi Ích Sau Khi Tái Cấu Trúc
1.  **Tính dễ đọc (Readability)**: Không còn file code khổng lồ >1700 dòng, lập trình viên dễ dàng tìm thấy nơi cần sửa lỗi.
2.  **Tính dễ kiểm thử (Testability)**: Các hàm logic nghiệp vụ (DB, API, Document Exporter) hoàn toàn tách khỏi giao diện Streamlit, cho phép chạy Unit Test tự động cực kỳ đơn giản.
3.  **Tính an toàn (Security)**: Thông tin bảo mật được chuyển ra ngoài file chạy, đảm bảo an toàn tuyệt đối.
