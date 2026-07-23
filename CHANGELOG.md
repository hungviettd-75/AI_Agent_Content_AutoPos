# 📝 CHANGELOG — NHẬT KÝ THAY ĐỔI CẬP NHẬT KIẾN TRÚC

> **Phiên bản hiện tại**: 2.0-Alpha  
> **Dự án**: AI_Agent_Content_AutoPos  
> **Người biên soạn**: Principal Software Architect & Product Owner  

---

## [2.0.0-Alpha] — 2026-07-12

### 🚀 Tính Năng Mới Thêm (Added)
*   **Creative Strategy Engine (`CREATIVE_STRATEGY_ENGINE.md`)**: Ra mắt Tầng chiến lược hình ảnh trung gian (Visual Strategy Middleware) tự động phân tích ngữ nghĩa 6 trục cốt lõi của bài viết để định hình hướng đi cho Concept hình ảnh.
*   **Adaptive Creative Engine (`ADAPTIVE_CREATIVE_ENGINE.md`)**: Cơ chế tự động quyết định giữ lại, loại bỏ, hoặc lai tạo (Merge/Blend) chéo các Design Tokens giữa các concept thành phần để sinh ra concept lai động (Hybrid Concept) mà không bị giới hạn trong thư viện tĩnh.
*   **Creative Strategy Mapping (`CREATIVE_STRATEGY_MAPPING.md`)**: Đặc tả dòng chảy quyết định tự động ánh xạ định dạng nội dung (Content Category) sang ý tưởng sáng tạo tương ứng phù hợp nhất.
*   **Creative Concept Library (`CREATIVE_CONCEPT_LIBRARY.md`)**: Xây dựng thư viện chuẩn hóa gồm **33 khái niệm sáng tạo** chuyên sâu cho thiết kế hình ảnh marketing.
*   **Creative Scoring Engine (`CREATIVE_SCORING_ENGINE.md`)**: Bộ chấm điểm 10 tiêu chí hiệu năng tăng trưởng (Relevance, CTR Potential, Business Value,...) dựa trên phương pháp trung bình nhân có trọng số để xếp hạng và trích xuất Top 3 Concept tối ưu.

### 🛠️ Cải Tiến Hệ Thống (Improved)
*   **Tích hợp Auto-Trigger cho Editor**: Nâng cấp luồng xử lý trong `ui/tab_content_studio_workspace.py` và `services/content_service.py` để tự động kích hoạt Creative Concept Engine phân tích bài viết ngay sau khi soạn thảo xong mà không cần bấm thêm nút thủ công.
*   **Metadata mở rộng động**: Sử dụng trường `assets.tags` (kiểu dữ liệu JSON) trong database để lưu trữ toàn bộ trạng thái vòng đời sáng tạo (lifecycle, scores, approved_by) mà không làm thay đổi hay phá vỡ cấu trúc cơ sở dữ liệu hiện có.

### 🧪 Hoạt Động Kiểm Thử (Tested)
*   **Kiểm thử tự động**: Xác nhận vượt qua $8/8$ bài test tự động (`tests/test_new_features.py` và `tests/test_thumbnail_features.py`) kiểm tra luồng xử lý của Learning Insights, A/B Testing, Cost Logging, Spec Retrieval, Analytics, Heatmap và Template Stats.

---
*Changelog được cập nhật chính thức vào mã nguồn dự án.*
