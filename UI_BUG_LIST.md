# 🐛 UI_BUG_LIST.md — Danh Sách Lỗi Giao Diện & Biện Pháp Khắc Phục
> **Hệ thống**: AI_Agent_Content_AutoPos (Apex AI Portal)  
> **Ngày phát hiện**: 12-07-2026  
> **Trạng thái**: Chờ duyệt sửa lỗi (Chỉ sửa phần hiển thị UI, không đổi business logic)  

---

## 📌 Danh Sách Lỗi Giao Diện Cần Khắc Phục

### 1. BUG-01: Header Breadcrumb bị tràn chữ trên thiết bị di động (Mobile)
- **Mô tả hiện tượng**: Khi chuyển sang chế độ viewport hẹp (Mobile), phần hiển thị Breadcrumb (`Workspace: AI Content Agency / Dashboard`) bị tràn ra khỏi box trắng, đè lên icon thông báo 🔔.
- **Mức độ nghiêm trọng**: Trung bình (Medium) — Ảnh hưởng đến mỹ quan và khả năng bấm nút của người dùng di động.
- **Nguyên nhân**: Header sử dụng `justify-content: space-between` nhưng không có quy tắc xuống dòng (`flex-wrap: wrap`) hoặc ẩn bớt phần chữ dài (`text-overflow: ellipsis`).
- **Biện pháp khắc phục**: Cập nhật CSS của thẻ chứa breadcrumb trong `ui/header.py`:
  ```css
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  ```

---

### 2. BUG-02: Bảng dữ liệu Analytics bị lệch thanh cuộn ngang (Horizontal Scroll)
- **Mô tả hiện tượng**: Trong tab Analytics, bảng thống kê chi tiết bài đăng khi mở rộng hiển thị quá nhiều cột khiến phần cuối bảng bị khuất, không xuất hiện thanh cuộn ngang tự nhiên trên một số trình duyệt Webkit.
- **Mức độ nghiêm trọng**: Trung bình (Medium) — Khiến người dùng không thể xem được chỉ số ROI (%) ở cột ngoài cùng bên phải.
- **Nguyên nhân**: Thiếu thuộc tính CSS `overflow-x: auto` trên container bao ngoài DataFrame của Streamlit.
- **Biện pháp khắc phục**: Bổ sung selector CSS vào `DesignSystem.get_global_css()` trong `ui/design_system.py`:
  ```css
  [data-testid="stDataFrame"] > div {
      overflow-x: auto !important;
  }
  ```

---

### 3. BUG-03: Trạng thái Hover của Button Danger trong Sidebar bị đè màu nền đỏ
- **Mô tả hiện tượng**: Khi di chuột (hover) vào nút Logout hoặc nút hành động nguy hiểm ở sidebar, màu nền chuyển sang màu đỏ (`C.ERROR`) nhưng màu chữ không chuyển sang trắng hoàn toàn mà bị ám xám do kế thừa style chữ mặc định của sidebar.
- **Mức độ nghiêm trọng**: Thấp (Low) — Lỗi hiển thị tương phản màu sắc chữ.
- **Nguyên nhân**: CSS Selector chưa đủ độ ưu tiên để ghi đè thuộc tính màu chữ (`color`) của Streamlit.
- **Biện pháp khắc phục**: Cập nhật style hover trong `ui/design_system.py`:
  ```css
  [data-testid="stSidebar"] .stButton > button:hover {
      color: #ffffff !important;
  }
  ```
