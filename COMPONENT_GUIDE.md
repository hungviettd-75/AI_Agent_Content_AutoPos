# 🎨 Apex AI — Component & UI/UX Standardization Guide
> **Dự án**: AI_Agent_Content_AutoPos (Apex AI Portal)  
> **Phiên bản**: 2.0.0 — Production Ready  
> **Ngày**: 12-07-2026  
> **Tài liệu**: Hướng dẫn chuẩn hóa và tái sử dụng toàn bộ Component của hệ thống.  

---

## 🛠️ 1. Nguyên Tắc Thiết Kế (Design System Principles)

Toàn bộ giao diện của Apex AI Portal được xây dựng dựa trên các design tokens định nghĩa tập trung tại [ui/theme.py](file:///e:/Save%20APP/AI_Agent_Content_AutoPos/ui/theme.py) và cấu trúc CSS toàn cục tại [ui/design_system.py](file:///e:/Save%20APP/AI_Agent_Content_AutoPos/ui/design_system.py). 

### Quy tắc cốt lõi:
1. **Không Hardcode màu sắc/kích thước**: Luôn sử dụng alias từ class `C` (Colors), `T` (Typography), `S` (Spacing), `R` (Radius), `SH` (Shadow), `A` (Animation).
2. **Layout linh hoạt**: Tận dụng hệ thống `st.columns()` kết hợp với HTML/CSS nhúng thông qua `unsafe_allow_html=True` để tạo giao diện premium, responsive.
3. **Giữ nguyên nghiệp vụ logic**: Việc chuẩn hóa Component chỉ cải thiện lớp giao diện (Presentation Layer) mà không được thay đổi các hàm xử lý logic (Business Logic Layer) bên dưới.

---

## 🧱 2. Thư Viện Components Chuẩn Hóa

### 2.1 Buttons
Các nút bấm được định nghĩa trong [ui/components/buttons.py](file:///e:/Save%20APP/AI_Agent_Content_AutoPos/ui/components/buttons.py) hỗ trợ 4 trạng thái ngữ cảnh chính với hiệu ứng hover nâng nhẹ `translateY(-1px)`.

```python
from ui.components.buttons import render_button

# 1. Nút Primary (Kêu gọi hành động chính: Đăng bài, Tạo bài, Phân tích)
if render_button("Sáng tạo nội dung", action_type="primary", key="btn_create"):
    do_something()

# 2. Nút Secondary (Hành động phụ: Xem chi tiết, Nháp, Quay lại)
if render_button("Lưu nháp", action_type="secondary", key="btn_draft"):
    do_something()

# 3. Nút Success (Phê duyệt tối cao, Kết nối thành công)
if render_button("Phê duyệt", action_type="success", key="btn_approve"):
    do_something()

# 4. Nút Danger (Xóa, Hủy, Vô hiệu hóa tài khoản)
if render_button("Xóa bài viết", action_type="danger", key="btn_delete"):
    do_something()
```

---

### 2.2 Cards & KPI Cards
Định nghĩa trong [ui/components/cards.py](file:///e:/Save%20APP/AI_Agent_Content_AutoPos/ui/components/cards.py). Sử dụng shadow dịu và bo góc `R.LG` (12px) hoặc `R.XL` (16px) cho card tổng quan.

```python
from ui.components.cards import render_card, render_kpi_card

# Card thông tin chung
render_card(
    title="🤖 Cấu hình AI Agent",
    subtitle="Phiên bản mô hình: gemini-2.0-flash",
    content_html="<p>Hệ thống tự động sử dụng cấu hình giọng điệu đã thiết lập trong Company Brain.</p>",
    footer_html="Uptime: 99.7%"
)

# Thẻ chỉ số (KPI Card) có hiển thị xu hướng tăng/giảm phần trăm
render_kpi_card(
    label="Tổng số Reach",
    value="1.2M",
    icon="👤",
    delta_pct=12.4,
    trend_up=True
)
```

---

### 2.3 Forms
Chuẩn hóa cấu trúc Form nhập liệu bằng Container Form có viền nhẹ và nền Canvas trắng sữa. Luôn sử dụng CSS từ `[data-testid="stForm"]` trong `DesignSystem.get_global_css()`.

```python
# Mẫu Form chuẩn hóa trong Streamlit
with st.form("campaign_creation_form"):
    st.markdown("<h5>🆕 Tạo chiến dịch mới</h5>", unsafe_allow_html=True)
    campaign_name = st.text_input("Tên chiến dịch", placeholder="Ví dụ: Chiến dịch ra mắt sản phẩm A")
    budget = st.number_input("Ngân sách (VND)", min_value=0, step=100000)
    
    # Nút submit chuẩn của Form
    submitted = st.form_submit_button("🚀 Kích hoạt chiến dịch")
    if submitted:
        st.success(f"Chiến dịch '{campaign_name}' đã được khởi tạo thành công!")
```

---

### 2.4 Tables & DataFrames
Các bảng dữ liệu được bo góc thông qua CSS selector `[data-testid="stDataFrame"]` và có shadow dịu nhẹ để phân tách với nền.

```python
# Tận dụng st.dataframe với cấu hình cột linh hoạt
st.dataframe(
    df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Trạng thái": st.column_config.SelectboxColumn(
            options=["Draft", "Pending", "Published"]
        ),
        "Link bài đăng": st.column_config.LinkColumn()
    }
)
```

---

### 2.5 Dialogs (Modal & Confirm)
Vì Streamlit chạy tuyến tính (linear-execution), chúng ta xây dựng hộp thoại xác nhận bằng cách tận dụng `st.columns` trong một `st.expander` hoặc Container nổi độc lập ở Danger Zone.

```python
# Dialog xác nhận hành động nguy hiểm ở Danger Zone
with st.expander("💀 Xóa Workspace", expanded=False):
    st.write("Hành động này không thể hoàn tác. Toàn bộ dữ liệu thành viên sẽ bị xóa sạch.")
    confirm_text = st.text_input("Nhập tên Workspace để xác nhận:")
    if st.button("Xác nhận xóa vĩnh viễn", type="secondary"):
        if confirm_text == "MyWorkspace":
            st.error("Đã thực hiện xóa Workspace.")
```

---

### 2.6 Badges
Định nghĩa trong [ui/components/badge.py](file:///e:/Save%20APP/AI_Agent_Content_AutoPos/ui/components/badge.py). Badge trả về chuỗi HTML để nhúng nội dòng trong bảng, danh sách, hay đoạn văn markdown.

```python
from ui.components.badge import render_badge, render_status_badge

# Badge trạng thái thủ công
st.markdown(f"Trạng thái thanh toán: {render_badge('Đã thanh toán', 'success')}", unsafe_allow_html=True)

# Tự động chọn màu theo nội dung trạng thái
st.markdown(f"Phê duyệt: {render_status_badge('pending_ceo_approval')}", unsafe_allow_html=True)
```

---

### 2.7 Charts
Chuẩn hóa chiều cao biểu đồ ở mức **240px** cho các biểu đồ đôi (cột song song) và sử dụng gradient hoặc color tone lấy từ `C.PRIMARY` và `C.SECONDARY` để tạo cảm giác hài hòa.

```python
col1, col2 = st.columns(2)
with col1:
    st.markdown("##### 📡 Lượt tiếp cận (Reach)")
    st.area_chart(df_reach, height=240) # Chiều cao tiêu chuẩn 240px

with col2:
    st.markdown("##### 🎯 Khách hàng tiềm năng (Leads)")
    st.bar_chart(df_leads, height=240)
```

---

### 2.8 Alerts & Notifications
Thay thế các cảnh báo thô mặc định của hệ thống bằng alert sang trọng có bo góc `R.LG` và icon tương ứng tại [ui/components/alerts.py](file:///e:/Save%20APP/AI_Agent_Content_AutoPos/ui/components/alerts.py).

```python
from ui.components.alerts import render_alert

# Hiển thị Alert chuyên nghiệp
render_alert("Gemini API Key đang hoạt động ổn định.", alert_type="success")
render_alert("Hạn mức Token AI của bạn đã sử dụng vượt quá 80%.", alert_type="warning")
render_alert("Lỗi kết nối tới tài khoản TikTok Business.", alert_type="danger")
```

---

### 2.9 Loading States (Spinners & Skeletons)
Hỗ trợ trải nghiệm người dùng tối đa khi AI Agent đang sinh nội dung dài hoặc đang gọi API thông qua [ui/components/loading.py](file:///e:/Save%20APP/AI_Agent_Content_AutoPos/ui/components/loading.py).

```python
from ui.components.loading import render_loading, render_skeleton

# Spinner loading kèm text
render_loading("AI đang viết bài theo công thức AIDA...")

# Skeleton loading giả lập cấu trúc UI đang tải
render_skeleton(height="20px", width="100%")
render_skeleton(height="120px", width="100%")
```

---

### 2.10 Empty States
Hiển thị màn hình trống thân thiện với icon lớn và thông tin gợi ý hành động khi chưa có dữ liệu tại [ui/components/empty_state.py](file:///e:/Save%20APP/AI_Agent_Content_AutoPos/ui/components/empty_state.py).

```python
from ui.components.empty_state import render_empty_state

# Hiển thị khi chưa có bài viết nháp nào
render_empty_state(
    title="Chưa có bài viết nháp",
    message="Hãy truy cập tab 'Tạo & Đăng bài' để AI viết bài đăng đầu tiên cho bạn.",
    icon="📝"
)
```

---

## 🎨 3. Cấu Trúc Bố Cục (Layout & Spacing)

### 3.1 Sidebar
- **Thiết kế**: Sidebar tối giản, màu nền tối (Dark Slate `#0a0f1e` hoặc `#0f172a`), phân tách rõ ràng với khu vực nội dung chính.
- **Hành động nhanh (Quick Actions)**: Nằm ở phần dưới sidebar, sử dụng nút phẳng nhỏ gọn.

### 3.2 Header
- **Breadcrumb**: Luôn hiển thị vị trí đường dẫn hiện tại (ví dụ: `Workspace: AI Content Agency / Dashboard`).
- **Notification Badge**: Hiển thị số lượng thông báo chờ xử lý (ví dụ: bài viết chờ duyệt) trên icon 🔔.

### 3.3 Spacing, Padding & Margin (8pt Grid System)
Hệ thống khoảng cách được chia hết cho 8 hoặc 4 để đảm bảo tỷ lệ hoàn hảo:
- `SP_1` (4px): Khoảng cách cực nhỏ giữa nhãn (label) và trường nhập liệu (input).
- `SP_2` (8px): Khoảng cách nhỏ giữa các dòng dữ liệu.
- `SP_3` (12px): Padding của các component trung bình.
- `SP_4` (16px): Khoảng cách thông thường giữa các khối nội dung.
- `SP_6` (24px) và `SP_12` (48px): Padding chính của các form, container và Empty State.

---

## ✨ 4. Hiệu Ứng Động (Hover, Transition & Animations)

```css
/* Hiệu ứng mượt mà cho toàn bộ các nút bấm và thẻ thông tin */
.stButton > button, .kpi-card, .stTextInput input, .stTabs button {
    transition: all 0.2s ease-in-out !important;
}

/* Hiệu ứng nổi lên nhẹ khi hover vào thẻ KPI */
.kpi-card:hover {
    transform: translateY(-3px) !important;
    box-shadow: 0 10px 25px rgba(0,0,0,0.1) !important;
}

/* Hiệu ứng nhấn nút */
.stButton > button:active {
    transform: translateY(1px) !important;
}
```

---

## 🚀 5. Lộ Trình Tích Hợp (Integration Steps)

Để áp dụng quy chuẩn thiết kế này vào toàn bộ các tab của dự án:
1. Nhúng đoạn CSS toàn cục ở hàm khởi tạo của `AI_Agent_Content_AutoPost.py`:
   ```python
   from ui.design_system import DesignSystem
   DesignSystem.inject_styles()
   ```
2. Import các component tương ứng từ thư mục `ui/components/` khi vẽ giao diện thay thế cho các thành phần Streamlit thuần.
3. Sử dụng các biến màu từ `ui/theme.py` để tô màu cho các biểu đồ hoặc bảng số liệu tùy chỉnh.
4. Tuyệt đối duy trì cấu trúc dữ liệu và logic nghiệp vụ cũ của các file model/service trong quá trình cải tiến UI.
