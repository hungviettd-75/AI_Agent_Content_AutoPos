# PHÂN TÍCH RỦI RO & KHẢ NĂNG BẢO TRÌ (RISK_ANALYSIS.md)

Tài liệu này xác định các rủi ro kỹ thuật hiện tại của hệ thống và đề xuất giải pháp cải thiện nhằm đảm bảo khả năng mở rộng.

---

## 1. Rủi Ro Kỹ Thuật (Technical Risks)

### 1.1. Rò Rỉ Khóa API Bảo Mật (Secret Exposure)
*   **Chi tiết rủi ro**: Trong file khởi chạy `AI_Agent_Content_AutoPost.bat` dòng số 9 đang lưu trữ cứng một khóa API Gemini (`set GEMINI_API_KEY=AIzaSyDK__Lqiic8FT00-X7OB2tcybw-zvsMvys`). Nếu đưa mã nguồn này lên các nền tảng công khai (như GitHub), khóa API sẽ bị lộ ngay lập tức.
*   **Mức độ**: 🚨 Rất cao (Critical)
*   **Giải pháp xử lý**: Loại bỏ việc gán cứng giá trị API Key trong file `.bat`. Thay thế hoàn toàn bằng việc đọc file cấu hình `.env` (đã có thư viện `dotenv` hỗ trợ trong code Python).

### 1.2. Phụ Thuộc Đồng Bộ Vào API Bên Ngoài (Synchronous External API Calls)
*   **Chi tiết rủi ro**: Việc đăng bài lên mạng xã hội (Facebook, Zalo, LinkedIn) và gọi API Gemini sinh nội dung đang được thực hiện một cách đồng bộ (Synchronous) trực tiếp trong luồng giao diện chính của Streamlit. Nếu một trong các API phản hồi chậm hoặc bị treo, giao diện Streamlit sẽ bị đơ (frozen) hoặc gây ra timeout cho người dùng.
*   **Mức độ**: ⚠️ Trung bình
*   **Giải pháp xử lý**: Áp dụng cơ chế xử lý bất đồng bộ (Asynchronous) hoặc hàng đợi tác vụ (Task Queue như Celery / Redis) để xử lý việc đăng bài ngầm dưới background.

### 1.3. Cơ Chế Sửa Lỗi JSON Chưa Thật Sự Tối Ưu (Fragile JSON Repair Logic)
*   **Chi tiết rủi ro**: Hàm `parse_weekly_plan_json` dựa vào việc gọi lại Gemini thêm một lần nữa để "sửa" (repair) chuỗi JSON bị lỗi. Phương pháp này có độ trễ lớn và không đảm bảo 100% thành công nếu mô hình AI tiếp tục trả về chuỗi JSON sai định dạng.
*   **Mức độ**: ⚠️ Trung bình
*   **Giải pháp xử lý**: Sử dụng tính năng **Structured Outputs** của Gemini (truyền tham số `response_schema` vào cấu hình mô hình) để ép buộc Gemini trả về đúng định dạng JSON mong muốn mà không cần lọc văn bản thủ công hay chạy vòng lặp sửa lỗi.

---

## 2. Điểm Nghẽn Vận Hành & Khả Năng Bảo Trì (Maintainability Bottlenecks)

### 2.1. Mã Nguồn Streamlit Quá Dài (Monolithic Codebase)
*   **Chi tiết rủi ro**: File `AI_Agent_Content_AutoPost.py` hiện tại dài hơn 1740 dòng code. Việc gộp chung giao diện Streamlit, thiết lập kết nối cơ sở dữ liệu SQLite, logic xuất file PDF/Word và định dạng gọi API xã hội vào cùng một file làm tăng độ phức tạp, rất khó kiểm thử tự động (Unit Test) và dễ phát sinh lỗi khi cập nhật.
*   **Mức độ**: ⚠️ Cao
*   **Giải pháp xử lý**: Thực hiện tái cấu trúc chia tách mã nguồn (Refactoring) theo mô hình **MVC** hoặc tách biệt rõ ràng các lớp:
    *   `src/ui/`: Chứa giao diện Streamlit.
    *   `src/services/`: Logic tạo tài liệu, tích hợp mạng xã hội.
    *   `src/database/`: Quản lý SQLite.

### 2.2. SQLite Bị Khóa Ghi Đồng Thời (Database Locking)
*   **Chi tiết rủi ro**: SQLite hỗ trợ ghi đồng thời kém. Nếu ứng dụng được mở rộng cho nhiều người dùng truy cập cùng lúc, việc tranh chấp tài nguyên ghi vào file `content_manager.db` có thể gây ra lỗi `database is locked`.
*   **Mức độ**: 📉 Thấp (chỉ xảy ra khi nhiều người dùng đồng thời)
*   **Giải pháp xử lý**: Giữ nguyên SQLite cho chạy cục bộ (Single User). Nếu chuyển đổi sang mô hình ứng dụng SaaS, cần thay thế bằng **PostgreSQL**.
