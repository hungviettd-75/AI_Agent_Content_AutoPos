# 💡 UI_IMPROVEMENT.md — Đề Xuất Cải Thiện Trải Nghiệm Người Dùng (UX)
> **Hệ thống**: AI_Agent_Content_AutoPos (Apex AI Portal)  
> **Phiên bản đề xuất**: 2.1.0  
> **Ngày**: 12-07-2026  

---

## 🚀 Đề Xuất Cải Tiến Trải Nghiệm & Giao Diện Người Dùng

### 1. IMP-01: Thêm nút chuyển nhanh chế độ Light/Dark Mode trong Sidebar
- **Mô tả cải tiến**: Thêm một công tắc chuyển đổi (toggle switch) nhỏ ở góc dưới sidebar để người dùng chuyển đổi nhanh giao diện tối (Dark Mode) cho toàn bộ ứng dụng, thay vì chỉ áp dụng riêng cho Admin Panel.
- **Giá trị mang lại**: Cải thiện đáng kể độ thân thiện với mắt khi sử dụng ứng dụng vào ban đêm. Giảm mỏi mắt cho người dùng vận hành hệ thống liên tục.
- **Cách triển khai (Không đổi business logic)**:
  - Lưu trạng thái giao diện vào `st.session_state["theme_mode"] = "light" | "dark"`.
  - Thay đổi biến màu `C.BG_APP` và `C.BG_CARD` động dựa trên trạng thái session này trước khi gọi `DesignSystem.inject_styles()`.

---

### 2. IMP-02: Bổ sung hiệu ứng chuyển động mượt (Fade-In Animation) khi chuyển đổi tab
- **Mô tả cải tiến**: Khi người dùng nhấn chuyển đổi giữa các mục trên cây thư mục (Tree Navigation), nội dung bên phải hiển thị ngay lập tức gây cảm giác đột ngột. Thêm hiệu ứng chuyển động mờ dần (Fade-In) sẽ giúp trải nghiệm mượt mà hơn.
- **Giá trị mang lại**: Tạo cảm giác ứng dụng phản hồi nhanh, hiện đại và cao cấp giống như các ứng dụng Single Page Application (SPA) viết bằng React/NextJS.
- **Cách triển khai**:
  - Nhúng class CSS animation vào vùng chứa nội dung chính trong `ui/design_system.py`:
    ```css
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(4px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .block-container {
        animation: fadeIn 0.3s ease-out-in;
    }
    ```
