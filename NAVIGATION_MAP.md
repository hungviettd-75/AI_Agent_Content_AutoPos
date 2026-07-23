# 🗺️ NAVIGATION MAP — AI_Agent_Content_AutoPos

Tài liệu này định nghĩa cấu trúc menu điều hướng mới cho ứng dụng **AI_Agent_Content_AutoPos** chạy trên Streamlit. Toàn bộ 21 tab chức năng hiện tại được tổ chức lại thành **7 nhóm Accordion** chính trên Sidebar, hỗ trợ hiển thị Badge động và phân quyền chi tiết theo vai trò (RBAC).

---

## 🛠️ Quy Tắc Hiển Thị & Phân Quyền (RBAC)

Hệ thống phân quyền dựa trên 4 vai trò cốt lõi trong `core/rbac.py`:
- `super_admin`: Toàn quyền hệ thống.
- `admin`: Quản lý workspace, thành viên và cấu hình dự án.
- `editor`: Tạo nội dung, chỉnh sửa, gửi yêu cầu phê duyệt và đăng bài.
- `viewer`: Chỉ xem báo cáo, lịch đăng bài và lịch sử.

---

## 🧭 Bản Đồ Điều Hướng (7 Nhóm Chức Năng)

### 1. 📊 Dashboard
*Nhóm hiển thị tổng quan trạng thái vận hành của hệ thống.*
- **Icon Accordion**: `📊`

| Tên chức năng | File UI | Mô tả ngắn | Badge | Quyền truy cập (RBAC) |
|---|---|---|---|---|
| Giám sát | [tab_monitoring.py](file:///e:/Save%20APP/AI_Agent_Content_AutoPos/ui/tab_monitoring.py) | Theo dõi hệ thống real-time, trạng thái API | `Live` | `super_admin`, `admin` |
| Chi phí AI | [tab_ai_cost.py](file:///e:/Save%20APP/AI_Agent_Content_AutoPos/ui/tab_ai_cost.py) | Thống kê chi phí API và tokens sử dụng | `$ USD` | `super_admin`, `admin` |

---

### 2. 🗓️ Content Planning
*Lên kế hoạch, nghiên cứu từ khóa/xu hướng và chiến dịch truyền thông.*
- **Icon Accordion**: `🗓️`

| Tên chức năng | File UI | Mô tả ngắn | Badge | Quyền truy cập (RBAC) |
|---|---|---|---|---|
| Lên lịch tuần | [tab_plan.py](file:///e:/Save%20APP/AI_Agent_Content_AutoPos/ui/tab_plan.py) | Tạo kế hoạch nội dung 7 ngày bằng Gemini AI | `7-Days` | `super_admin`, `admin`, `editor` |
| Kế hoạch | [tab_planning.py](file:///e:/Save%20APP/AI_Agent_Content_AutoPos/ui/tab_planning.py) | Lập kế hoạch nội dung dài hạn (tháng/quý) | `Planning` | `super_admin`, `admin`, `editor` |
| Chiến dịch | [tab_campaign.py](file:///e:/Save%20APP/AI_Agent_Content_AutoPos/ui/tab_campaign.py) | Quản lý các chiến dịch marketing lớn | `Active` | `super_admin`, `admin`, `editor` |
| Xu hướng | [tab_trend.py](file:///e:/Save%20APP/AI_Agent_Content_AutoPos/ui/tab_trend.py) | Phân tích xu hướng MXH mới nhất | `Trending` | Tất cả vai trò |

---

### 3. 🎨 Content Studio
*Không gian sáng tạo, tối ưu hóa và biên tập nội dung.*
- **Icon Accordion**: `🎨`

| Tên chức năng | File UI | Mô tả ngắn | Badge | Quyền truy cập (RBAC) |
|---|---|---|---|---|
| Tạo & Đăng bài | [tab_create.py](file:///e:/Save%20APP/AI_Agent_Content_AutoPos/ui/tab_create.py) | Tạo bài viết AI nhanh và đăng trực tiếp lên mạng xã hội | `AI Powered` | `super_admin`, `admin`, `editor` |
| Copywriting | [tab_copywriting.py](file:///e:/Save%20APP/AI_Agent_Content_AutoPos/ui/tab_copywriting.py) | Viết bài quảng cáo chuyên sâu theo các công thức AIDA/PAS | `Pro` | `super_admin`, `admin`, `editor` |
| Tri thức | [tab_knowledge.py](file:///e:/Save%20APP/AI_Agent_Content_AutoPos/ui/tab_knowledge.py) | Quản lý kho bài học, case study, so sánh công cụ AI | `Library` | Tất cả vai trò |
| Company Brain | [tab_company_brain.py](file:///e:/Save%20APP/AI_Agent_Content_AutoPos/ui/tab_company_brain.py) | Tri thức nội bộ doanh nghiệp giúp AI viết đúng thương hiệu | `Brain` | `super_admin`, `admin` |
| Fact Check | [tab_factcheck.py](file:///e:/Save%20APP/AI_Agent_Content_AutoPos/ui/tab_factcheck.py) | Tự động kiểm chứng thông tin chính xác bằng Search Tool | `Shield` | `super_admin`, `admin`, `editor` |
| Thương hiệu | [tab_brand.py](file:///e:/Save%20APP/AI_Agent_Content_AutoPos/ui/tab_brand.py) | Quản lý Guideline nhận diện thương hiệu, giọng nói (Voice) | `Identity` | `super_admin`, `admin`, `editor` |

---

### 4. 🔏 Approval
*Quy trình phê duyệt và kiểm tra chất lượng nội dung trước khi xuất bản.*
- **Icon Accordion**: `🔏`

| Tên chức năng | File UI | Mô tả ngắn | Badge | Quyền truy cập (RBAC) |
|---|---|---|---|---|
| Phê duyệt | [tab_approval.py](file:///e:/Save%20APP/AI_Agent_Content_AutoPos/ui/tab_approval.py) | Duyệt bài viết chờ đăng từ các Editor | `Pending` | `super_admin`, `admin` (Duyệt), `editor` (Theo dõi) |

---

### 5. 🚀 Publishing
*Quản lý lịch xuất bản, quy trình tự động hóa đăng bài và lịch sử.*
- **Icon Accordion**: `🚀`

| Tên chức năng | File UI | Mô tả ngắn | Badge | Quyền truy cập (RBAC) |
|---|---|---|---|---|
| Lịch đăng | [tab_publishing.py](file:///e:/Save%20APP/AI_Agent_Content_AutoPos/ui/tab_publishing.py) | Xem và chỉnh sửa lịch đăng bài tương lai | `Calendar` | Tất cả vai trò |
| Lịch sử | [tab_history.py](file:///e:/Save%20APP/AI_Agent_Content_AutoPos/ui/tab_history.py) | Xem, tải về báo cáo PDF/Word các bài đăng cũ | `Archive` | Tất cả vai trò |
| Workflow | [tab_workflow.py](file:///e:/Save%20APP/AI_Agent_Content_AutoPos/ui/tab_workflow.py) | Lập cấu hình tự động đăng bài theo luồng sự kiện | `Auto` | `super_admin`, `admin` |

---

### 6. 📈 Analytics
*Theo dõi hiệu suất truyền thông và tối ưu hóa nội dung.*
- **Icon Accordion**: `📈`

| Tên chức năng | File UI | Mô tả ngắn | Badge | Quyền truy cập (RBAC) |
|---|---|---|---|---|
| Phân tích | [tab_analytics.py](file:///e:/Save%20APP/AI_Agent_Content_AutoPos/ui/tab_analytics.py) | Thống kê lượng tương tác, Reach, Impressions chi tiết | `Stats` | Tất cả vai trò |
| A/B Testing | [tab_ab_testing.py](file:///e:/Save%20APP/AI_Agent_Content_AutoPos/ui/tab_ab_testing.py) | Thử nghiệm, so sánh hiệu quả giữa các phiên bản bài viết | `Split` | `super_admin`, `admin`, `editor` |
| Học máy | [tab_learning.py](file:///e:/Save%20APP/AI_Agent_Content_AutoPos/ui/tab_learning.py) | AI tự rút ra insights để tối ưu hóa hiệu suất bài đăng tiếp theo | `Insight` | `super_admin`, `admin` |

---

### 7. ⚙️ Administration
*Quản lý hệ thống, thanh toán và nhật ký kiểm toán.*
- **Icon Accordion**: `⚙️`

| Tên chức năng | File UI | Mô tả ngắn | Badge | Quyền truy cập (RBAC) |
|---|---|---|---|---|
| Thanh toán | [tab_billing.py](file:///e:/Save%20APP/AI_Agent_Content_AutoPos/ui/tab_billing.py) | Quản lý gói cước dịch vụ và hóa đơn | `Billing` | `super_admin`, `admin` |
| Kiểm toán | [tab_audit.py](file:///e:/Save%20APP/AI_Agent_Content_AutoPos/ui/tab_audit.py) | Xem lịch sử thao tác của các thành viên (Audit logs) | `Logs` | `super_admin` |

---

## 🎨 Trải Nghiệm Giao Diện Sidebar Accordion (Streamlit Design)

Sử dụng cấu trúc `st.expander` trong Streamlit để tạo giao diện Accordion mượt mà, hỗ trợ style CSS tùy chỉnh để làm nổi bật badge:

```python
import streamlit as st

def render_sidebar(user_role):
    st.sidebar.title("🤖 AutoPost Navigator")
    
    # 1. Nhóm Dashboard
    with st.sidebar.expander("📊 Dashboard", expanded=True):
        if user_role in ["super_admin", "admin"]:
            if st.button("🔴 Giám sát [Live]"):
                st.session_state.current_tab = "monitoring"
            if st.button("💵 Chi phí AI [$ USD]"):
                st.session_state.current_tab = "ai_cost"
                
    # 2. Nhóm Content Planning
    with st.sidebar.expander("🗓️ Content Planning", expanded=False):
        if user_role in ["super_admin", "admin", "editor"]:
            if st.button("📅 Lên lịch tuần [7-Days]"):
                st.session_state.current_tab = "plan"
            if st.button("📋 Kế hoạch [Planning]"):
                st.session_state.current_tab = "planning"
            if st.button("🏁 Chiến dịch [Active]"):
                st.session_state.current_tab = "campaign"
        if st.button("🔥 Xu hướng [Trending]"):
            st.session_state.current_tab = "trend"
            
    # 3. Nhóm Content Studio
    with st.sidebar.expander("🎨 Content Studio", expanded=False):
        if user_role in ["super_admin", "admin", "editor"]:
            if st.button("✨ Tạo & Đăng bài [AI Powered]"):
                st.session_state.current_tab = "create"
            if st.button("✍️ Copywriting [Pro]"):
                st.session_state.current_tab = "copywriting"
        if st.button("📚 Tri thức [Library]"):
            st.session_state.current_tab = "knowledge"
        if user_role in ["super_admin", "admin"]:
            if st.button("🧠 Company Brain [Brain]"):
                st.session_state.current_tab = "company_brain"
        if user_role in ["super_admin", "admin", "editor"]:
            if st.button("🛡️ Fact Check [Shield]"):
                st.session_state.current_tab = "factcheck"
            if st.button("🎗️ Thương hiệu [Identity]"):
                st.session_state.current_tab = "brand"

    # 4. Nhóm Approval
    with st.sidebar.expander("🔏 Approval", expanded=False):
        # Editor xem trạng thái, Admin/Super Admin duyệt
        if user_role in ["super_admin", "admin", "editor"]:
            # Giả định lấy số bài viết chờ duyệt từ db
            pending_count = get_pending_approval_count() 
            if st.button(f"📥 Phê duyệt [{pending_count} Pending]"):
                st.session_state.current_tab = "approval"

    # 5. Nhóm Publishing
    with st.sidebar.expander("🚀 Publishing", expanded=False):
        if st.button("📆 Lịch đăng [Calendar]"):
            st.session_state.current_tab = "publishing"
        if st.button("📜 Lịch sử [Archive]"):
            st.session_state.current_tab = "history"
        if user_role in ["super_admin", "admin"]:
            if st.button("⚙️ Workflow [Auto]"):
                st.session_state.current_tab = "workflow"

    # 6. Nhóm Analytics
    with st.sidebar.expander("📈 Analytics", expanded=False):
        if st.button("📊 Phân tích [Stats]"):
            st.session_state.current_tab = "analytics"
        if user_role in ["super_admin", "admin", "editor"]:
            if st.button("🧪 A/B Testing [Split]"):
                st.session_state.current_tab = "ab_testing"
        if user_role in ["super_admin", "admin"]:
            if st.button("💡 Học máy [Insight]"):
                st.session_state.current_tab = "learning"

    # 7. Nhóm Administration
    with st.sidebar.expander("⚙️ Administration", expanded=False):
        if user_role in ["super_admin", "admin"]:
            if st.button("💳 Thanh toán [Billing]"):
                st.session_state.current_tab = "billing"
        if user_role == "super_admin":
            if st.button("🕵️ Kiểm toán [Logs]"):
                st.session_state.current_tab = "audit"
```
