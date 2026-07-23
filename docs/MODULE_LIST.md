# DANH SÁCH CÁC MODULE (MODULE_LIST.md)

Dưới đây là bảng phân tích chi tiết chức năng, vị trí và vai trò của từng thành phần trong dự án.

---

## 1. Các Module Thành Phần Kịch Bản & Nội Dung (Engine Modules)

### 1.1. Case Study Engine
*   **Đường dẫn**: [case_study_engine.py](file:///e:/Save%20APP/AI_Agent_Content_AutoPos/case_study_engine.py)
*   **Hàm chính**: `generate_ai_case_study(industry, company_size, problem, ai_tool)`
*   **Chức năng**:
    *   Lưu trữ metadata về cấu hình doanh nghiệp (`COMPANY_SIZE_PROFILES`) và ngành nghề (`INDUSTRY_CONTEXT`).
    *   Lắp ráp văn bản markdown hoàn chỉnh cho một Case Study thực tế.

### 1.2. Comparison Engine
*   **Đường dẫn**: [comparison_engine.py](file:///e:/Save%20APP/AI_Agent_Content_AutoPos/comparison_engine.py)
*   **Hàm chính**: `generate_comparison_table(tools, criteria)`, `generate_full_comparison_markdown()`
*   **Chức năng**:
    *   Định nghĩa dữ liệu so sánh điểm mạnh/yếu của 10 công cụ AI phổ biến theo các tiêu chí thực tế.
    *   Xây dựng bảng dữ liệu dạng Markdown.

### 1.3. Knowledge Content Planner
*   **Đường dẫn**: [knowledge_planner.py](file:///e:/Save%20APP/AI_Agent_Content_AutoPos/knowledge_planner.py)
*   **Hàm chính**: `generate_30_day_knowledge_plan(start_date)`, `generate_30_day_knowledge_plan_json(...)`
*   **Chức năng**:
    *   Xây dựng kho ý tưởng nội dung (`TOPIC_BANK`) và mục tiêu truyền tải (`GOALS`).
    *   Tự động sinh mảng JSON chứa kế hoạch phân bổ bài đăng 30 ngày.

### 1.4. Knowledge Reels Script Generator
*   **Đường dẫn**: [knowledge_reels_engine.py](file:///e:/Save%20APP/AI_Agent_Content_AutoPos/knowledge_reels_engine.py)
*   **Hàm chính**: `generate_knowledge_reels_script(...)`, `generate_reels_prompt(...)`
*   **Chức năng**:
    *   Tạo khung kịch bản phân cảnh video ngắn cho TikTok/Reels.
    *   Sinh câu lệnh prompt hướng dẫn AI tạo kịch bản.

### 1.5. Prompt Framework Engine
*   **Đường dẫn**: [prompt_framework_engine.py](file:///e:/Save%20APP/AI_Agent_Content_AutoPos/prompt_framework_engine.py)
*   **Hàm chính**: `build_prompt_framework(...)`, `generate_tool_prompt_framework(...)`
*   **Chức năng**:
    *   Chuẩn hóa cấu trúc viết câu lệnh Prompt.
    *   Lưu trữ các ví dụ mẫu cụ thể cho từng công cụ AI lớn.

---

## 2. Module Điều Hướng Chính (Orchestration & UI Module)

### 2.1. Main Streamlit Controller
*   **Đường dẫn**: [AI_Agent_Content_AutoPost.py](file:///e:/Save%20APP/AI_Agent_Content_AutoPos/AI_Agent_Content_AutoPost.py)
*   **Các thành phần chính**:
    *   **Giao diện**: Layout Streamlit với 3 Tabs (`tab_plan`, `tab_create`, `tab_history`).
    *   **Database Utility**: `init_db()`, `get_db_connection()`, `save_knowledge_post()`, `get_knowledge_posts()`.
    *   **Document Exporter**: `export_post_to_pdf()`, `export_knowledge_to_pdf()`, `export_knowledge_to_docx()`, `export_plan_to_word()`.
    *   **Social Poster**: `post_to_facebook()`, `post_to_zalo_oa()`, `post_to_linkedin()`.
    *   **AI Generator**: `get_weekly_plan()`, `generate_ai_knowledge_content()`.
