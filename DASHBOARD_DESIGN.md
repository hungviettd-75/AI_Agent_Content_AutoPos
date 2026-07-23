# 📊 DASHBOARD DESIGN — HỆ THỐNG QUẢN TRỊ NỘI DUNG AI AUTOMATION

Tài liệu này đặc tả thiết kế chi tiết của **Dashboard tổng quan hoàn toàn mới** cho ứng dụng **AI_Agent_Content_AutoPos**. Dashboard được xây dựng để cung cấp cái nhìn toàn diện, trực quan cho Marketer và Quản trị viên dựa trên dữ liệu thời gian thực từ cơ sở dữ liệu Schema V2 mà **không sử dụng dữ liệu giả (fake data)**. Nếu cơ sở dữ liệu trống, hệ thống sẽ tự động hiển thị **Empty State** tương tác sinh động hướng dẫn người dùng tạo tài nguyên.

---

## 🎨 1. Bố Cục Giao Diện (Grid Layout & Architecture)

Dashboard sử dụng hệ thống lưới 12-cột linh hoạt của Streamlit (`st.columns`), tối ưu hóa trải nghiệm thị giác theo luồng từ trên xuống dưới, từ trái qua phải:

```
┌────────────────────────────────────────────────────────────────────────┐
│  [Workspace Info Header]                                               │
├────────────────────────────────────────────────────────────────────────┤
│  [KPI 1: Posts]   │  [KPI 2: Engage]  │  [KPI 3: Scheduled] │ [KPI 4: Budget]  │
├──────────────────────────────────────┬─────────────────────────────────┤
│                                      │                                 │
│    [Performance Chart (8 Cols)]      │    [AI Cost Summary (4 Cols)]   │
│                                      │                                 │
├──────────────────────────────────────┼─────────────────────────────────┤
│                                      │                                 │
│    [Calendar View (6 Cols)]          │    [Pending Approvals (6 Cols)] │
│                                      │                                 │
├──────────────────────────────────────┼─────────────────────────────────┤
│                                      │                                 │
│    [Publishing Queue (4 Cols)]       │    [Campaign Summary (4 Cols)]  │
│    [Trending Topics (4 Cols)]        │    [Recent Activities (4 Cols)] │
│                                      │                                 │
└──────────────────────────────────────┴─────────────────────────────────┘
```

---

## ⚙️ 2. Chi Tiết 10 Thành Phần & Truy Vấn Cơ Sở Dữ Liệu Thực Tế

### 2.1. Workspace Information
- **Vị trí**: Header đầu trang.
- **Mục tiêu**: Hiển thị thông tin Workspace hiện tại, gói dịch vụ (`plan`), số thành viên hoạt động và hạn mức sử dụng tháng.
- **Truy vấn SQL thực tế**:
  ```sql
  SELECT w.*, 
         (SELECT COUNT(*) FROM workspace_members WHERE workspace_id = w.id) as total_members,
         (SELECT COUNT(*) FROM posts WHERE workspace_id = w.id AND strftime('%Y-%m', published_at) = strftime('%Y-%m', 'now')) as monthly_posts
  FROM workspaces w
  WHERE w.id = ?
  ```

### 2.2. KPI Cards
- **Vị trí**: Hàng ngang thứ nhất.
- **KPIs**:
  1. **Tổng số bài đã đăng**: Số lượng bài viết có `status = 'published'` trong tháng hiện tại.
  2. **Tỷ lệ tương tác trung bình**: `AVG(engagement_rate)` từ bảng `analytics`.
  3. **Bài đăng chờ xuất bản**: Số bài có lịch đăng tương lai trong bảng `schedules` với `status = 'pending'`.
  4. **Tổng ngân sách chiến dịch active**: `SUM(budget)` của các chiến dịch có `status = 'active'`.
- **Truy vấn SQL thực tế**:
  ```sql
  -- Tổng số bài đăng & Ngân sách active
  SELECT COUNT(id) as total_published FROM posts WHERE workspace_id = ? AND status = 'published';
  SELECT SUM(budget) as active_budget FROM campaigns WHERE workspace_id = ? AND status = 'active';
  
  -- Tương tác trung bình
  SELECT AVG(engagement_rate) as avg_er FROM analytics WHERE workspace_id = ?;
  
  -- Lịch đăng chờ xử lý
  SELECT COUNT(id) as total_pending_sched FROM schedules WHERE workspace_id = ? AND status = 'pending';
  ```

### 2.3. Performance Chart
- **Vị trí**: Hàng thứ 2, chiếm 8/12 cột.
- **Mục tiêu**: Biểu đồ đường (Line chart) thể hiện tương tác (`likes`, `comments`, `shares`, `clicks`) theo ngày (`metric_date`).
- **Truy vấn SQL thực tế**:
  ```sql
  SELECT metric_date, SUM(likes) as likes, SUM(comments) as comments, SUM(shares) as shares
  FROM analytics
  WHERE workspace_id = ? AND metric_date >= date('now', '-30 days')
  GROUP BY metric_date
  ORDER BY metric_date ASC;
  ```

### 2.4. AI Cost Summary
- **Vị trí**: Hàng thứ 2, chiếm 4/12 cột.
- **Mục tiêu**: Thống kê tổng số token đã dùng, chi phí tích lũy dạng USD và số lần gọi AI.
- **Truy vấn SQL thực tế**:
  ```sql
  SELECT provider, SUM(total_tokens) as total_tokens, SUM(cost) as total_cost, COUNT(*) as calls
  FROM ai_logs
  WHERE workspace_id = ?
  GROUP BY provider;
  ```

### 2.5. Calendar (Lịch Đăng Bài)
- **Vị trí**: Hàng thứ 3, chiếm 6/12 cột.
- **Mục tiêu**: Hiển thị mật độ phân phối bài đăng theo ngày trong tháng hiện tại (Sử dụng Streamlit Calendar component hoặc Heatmap).
- **Truy vấn SQL thực tế**:
  ```sql
  SELECT date(scheduled_at) as scheduled_date, COUNT(*) as post_count
  FROM schedules
  WHERE workspace_id = ? AND scheduled_at >= date('now', 'start of month')
  GROUP BY date(scheduled_at);
  ```

### 2.6. Pending Approval (Danh Sách Chờ Phê Duyệt)
- **Vị trí**: Hàng thứ 3, chiếm 6/12 cột.
- **Mục tiêu**: Danh sách bài viết đang chờ duyệt để xuất bản (Phù hợp cho Editor theo dõi, Admin thao tác nhanh).
- **Truy vấn SQL thực tế**:
  ```sql
  SELECT a.id as approval_id, p.id as post_id, p.title, p.platform, a.requested_at
  FROM approvals a
  JOIN posts p ON a.post_id = p.id
  WHERE a.workspace_id = ? AND a.status = 'pending'
  ORDER BY a.requested_at DESC
  LIMIT 5;
  ```

### 2.7. Publishing Queue (Hàng Đợi Xuất Bản)
- **Vị trí**: Hàng thứ 4, chiếm 4/12 cột.
- **Mục tiêu**: 5 bài đăng sắp tới thời gian xuất bản.
- **Truy vấn SQL thực tế**:
  ```sql
  SELECT s.scheduled_at, p.title, p.platform
  FROM schedules s
  JOIN posts p ON s.post_id = p.id
  WHERE s.workspace_id = ? AND s.status = 'pending' AND s.scheduled_at >= datetime('now')
  ORDER BY s.scheduled_at ASC
  LIMIT 5;
  ```

### 2.8. Campaign Summary
- **Vị trí**: Hàng thứ 4, chiếm 4/12 cột.
- **Mục tiêu**: Danh sách các chiến dịch cùng số lượng bài viết đã tạo.
- **Truy vấn SQL thực tế**:
  ```sql
  SELECT c.name, c.status, COUNT(p.id) as post_count
  FROM campaigns c
  LEFT JOIN posts p ON p.campaign_id = c.id
  WHERE c.workspace_id = ?
  GROUP BY c.id
  ORDER BY post_count DESC
  LIMIT 5;
  ```

### 2.9. Trending Topics
- **Vị trí**: Hàng thứ 4, chiếm 4/12 cột.
- **Mục tiêu**: Tổng hợp chủ đề/từ khóa phổ biến nhất được ghi nhận trong kho tri thức hoặc trend service.
- **Truy vấn SQL thực tế**:
  ```sql
  SELECT tags, COUNT(*) as topic_count
  FROM knowledge
  WHERE workspace_id = ? AND tags IS NOT NULL AND tags != ''
  GROUP BY tags
  ORDER BY topic_count DESC
  LIMIT 5;
  ```

### 2.10. Recent Activity (Nhật Ký Kiểm Toán)
- **Vị trí**: Hàng thứ 4, chiếm 4/12 cột.
- **Mục tiêu**: Hiển thị 5 hoạt động gần nhất của người dùng trong Workspace.
- **Truy vấn SQL thực tế**:
  ```sql
  SELECT timestamp, user_email, action, description
  FROM audit_logs
  WHERE workspace_id = ?
  ORDER BY timestamp DESC
  LIMIT 5;
  ```

---

## 🕳️ 3. Thiết Kế Trạng Thái Trống (Empty State)

Khi cơ sở dữ liệu của một thành phần chưa có thông tin (Ví dụ: Workspace mới tạo), hệ thống sẽ hiển thị **Empty State** trực quan bằng các hộp thông báo thiết kế cao cấp:

1. **KPI Cards Trống**: Hiển thị `0` hoặc `- -` đi kèm dòng hướng dẫn: *"Chưa có dữ liệu bài viết. Hãy bắt đầu tạo bài đầu tiên!"*
2. **Biểu Đồ Trống (Performance Chart Empty)**:
   - Hiển thị một khung placeholder đồ họa xám nhạt với hiệu ứng gradient.
   - Text gợi ý: *"Không tìm thấy dữ liệu hiệu suất trong 30 ngày qua. Biểu đồ sẽ hiển thị ngay khi bài viết đầu tiên của bạn được đăng và nhận tương tác."*
   - Nút kêu gọi hành động (CTA): `"Tạo bài viết AI ngay"` liên kết chuyển sang Tab `Content Studio`.
3. **Phê duyệt Trống**:
   - Hiển thị thông báo: 🟢 *"Hộp thư phê duyệt sạch sẽ! Hiện không có bài đăng nào cần duyệt."*
4. **Hàng đợi trống**:
   - Hiển thị: 📅 *"Hàng đợi trống. Hãy lập lịch bài đăng hoặc thiết lập workflow tự động."*

---

## 🔐 4. Phân Quyền Vai Trò Trên Dashboard (RBAC Map)

| Thành phần Dashboard | Super Admin | Admin | Editor | Viewer |
|---|:---:|:---:|:---:|:---:|
| **Workspace Info** | ✅ Toàn quyền | ✅ Toàn quyền | 👁️ Chỉ xem | 👁️ Chỉ xem |
| **KPI Cards** | ✅ Toàn quyền | ✅ Toàn quyền | 👁️ Chỉ xem | 👁️ Chỉ xem |
| **Performance Chart**| ✅ Xem báo cáo | ✅ Xem báo cáo | ✅ Xem báo cáo | ✅ Xem báo cáo |
| **AI Cost Summary** | ✅ Xem chi tiết | ✅ Xem chi tiết | ❌ Ẩn | ❌ Ẩn |
| **Calendar** | ✅ Xem lịch | ✅ Xem lịch | ✅ Xem lịch | ✅ Xem lịch |
| **Pending Approval** | ⚡ Phê duyệt nhanh | ⚡ Phê duyệt nhanh | 👁️ Theo dõi | ❌ Ẩn |
| **Publishing Queue** | ✅ Quản lý | ✅ Quản lý | ✅ Xem | ✅ Xem |
| **Campaign Summary** | ✅ Xem | ✅ Xem | ✅ Xem | ✅ Xem |
| **Trending Topics** | ✅ Xem | ✅ Xem | ✅ Xem | ✅ Xem |
| **Recent Activity** | 🔎 Xem chi tiết | 🔎 Xem chi tiết | ❌ Ẩn | ❌ Ẩn |

---

## 💻 5. Mã Nguồn Streamlit Thực Tế Tích Hợp (Dashboard Component)

Dưới đây là file Python tích hợp giao diện hoàn chỉnh, sử dụng trực tiếp kết nối DB và các class có sẵn, đảm bảo xử lý Empty State hoàn chỉnh.

```python
# Save as: ui/tab_dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
from database.connection import get_db_connection
from database.models.approvals import ApprovalModel
from database.models.ai_cost import AICostModel

def fetch_db_data(query, params=()):
    """Tiện ích thực thi truy vấn an toàn, trả về DataFrame."""
    conn = get_db_connection()
    try:
        df = pd.read_sql_query(query, conn, params=params)
        return df
    except Exception as e:
        st.error(f"Lỗi truy vấn cơ sở dữ liệu: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def render_dashboard(workspace_id: int, user_role: str):
    st.markdown("## 📊 Dashboard Tổng Quan")
    
    # 1. WORKSPACE INFORMATION
    ws_df = fetch_db_data("""
        SELECT name, plan, max_users, max_posts_per_month 
        FROM workspaces WHERE id = ?
    """, (workspace_id,))
    
    if not ws_df.empty:
        ws = ws_df.iloc[0]
        st.info(f"🏢 **Workspace**: {ws['name']} | **Gói dịch vụ**: {ws['plan'].upper()} | **Giới hạn tháng**: {ws['max_posts_per_month']} bài đăng")
    else:
        st.warning("⚠️ Không tìm thấy thông tin không gian làm việc.")
        return

    # 2. KPI CARDS
    st.markdown("### 🔑 Chỉ số chính (KPIs)")
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    
    # Query dữ liệu thực tế
    posts_stat = fetch_db_data("SELECT COUNT(*) as cnt FROM posts WHERE workspace_id = ? AND status = 'published'", (workspace_id,))
    pending_sched = fetch_db_data("SELECT COUNT(*) as cnt FROM schedules WHERE workspace_id = ? AND status = 'pending'", (workspace_id,))
    er_stat = fetch_db_data("SELECT AVG(engagement_rate) as er FROM analytics WHERE workspace_id = ?", (workspace_id,))
    budget_stat = fetch_db_data("SELECT SUM(budget) as budget FROM campaigns WHERE workspace_id = ? AND status = 'active'", (workspace_id,))
    
    val_posts = posts_stat.iloc[0]['cnt'] if not posts_stat.empty else 0
    val_sched = pending_sched.iloc[0]['cnt'] if not pending_sched.empty else 0
    val_er = round(er_stat.iloc[0]['er'], 2) if not er_stat.empty and er_stat.iloc[0]['er'] is not None else None
    val_budget = budget_stat.iloc[0]['budget'] if not budget_stat.empty and budget_stat.iloc[0]['budget'] is not None else 0
    
    # Render KPI
    with kpi_col1:
        st.metric(label="Bài đã xuất bản", value=val_posts if val_posts > 0 else "0")
    with kpi_col2:
        st.metric(label="Tương tác trung bình", value=f"{val_er}%" if val_er is not None else "- -")
    with kpi_col3:
        st.metric(label="Hàng đợi xuất bản", value=val_sched if val_sched > 0 else "0")
    with kpi_col4:
        st.metric(label="Ngân sách active", value=f"${val_budget:,.2f}" if val_budget > 0 else "$0.00")

    # 3. PERFORMANCE CHART & AI COST SUMMARY
    st.markdown("---")
    chart_col, ai_col = st.columns([2, 1])
    
    with chart_col:
        st.markdown("#### 📉 Biểu đồ hiệu năng (30 ngày)")
        perf_df = fetch_db_data("""
            SELECT metric_date, SUM(likes) as Likes, SUM(comments) as Comments, SUM(shares) as Shares
            FROM analytics
            WHERE workspace_id = ? AND metric_date >= date('now', '-30 days')
            GROUP BY metric_date ORDER BY metric_date ASC
        """, (workspace_id,))
        
        if perf_df.empty:
            # EMPTY STATE CHART
            st.markdown(
                """
                <div style='background-color:#f0f2f6; border-radius:10px; padding:30px; text-align:center;'>
                    <h5 style='color:#555;'>📉 Chưa có dữ liệu tương tác</h5>
                    <p style='color:#777;'>Biểu đồ hiệu năng sẽ xuất hiện ở đây khi bài đăng của bạn ghi nhận lượt thích/bình luận thực tế.</p>
                </div>
                """, unsafe_check_html=True
            )
        else:
            fig = px.line(perf_df, x='metric_date', y=['Likes', 'Comments', 'Shares'], 
                          title="Tương tác mạng xã hội theo thời gian", labels={"value": "Lượt", "metric_date": "Ngày"})
            st.plotly_chart(fig, use_container_width=True)

    with ai_col:
        st.markdown("#### 🤖 Chi phí Gemini & AI")
        if user_role not in ["super_admin", "admin"]:
            st.warning("🔒 Yêu cầu quyền Admin để xem thông tin chi phí.")
        else:
            ai_df = fetch_db_data("""
                SELECT provider, SUM(total_tokens) as tokens, SUM(cost) as cost 
                FROM ai_logs WHERE workspace_id = ? GROUP BY provider
            """, (workspace_id,))
            
            if ai_df.empty:
                # EMPTY STATE AI COST
                st.info("💡 Chưa có hóa đơn sử dụng AI. Toàn bộ cuộc gọi API sinh nội dung sẽ được liệt kê tại đây.")
            else:
                for _, row in ai_df.iterrows():
                    st.metric(label=f"Nhà cung cấp {row['provider']}", 
                              value=f"${row['cost']:.4f}", 
                              help=f"Tổng tokens tiêu thụ: {row['tokens']:,}")

    # 4. CALENDAR & PENDING APPROVALS
    st.markdown("---")
    cal_col, app_col = st.columns(2)
    
    with cal_col:
        st.markdown("#### 📅 Lịch phân bổ đăng bài")
        cal_df = fetch_db_data("""
            SELECT date(scheduled_at) as date, COUNT(*) as count 
            FROM schedules 
            WHERE workspace_id = ? AND scheduled_at >= date('now', 'start of month')
            GROUP BY date
        """, (workspace_id,))
        
        if cal_df.empty:
            st.markdown("ℹ️ *Không có lịch đăng nào được đặt cho tháng này.*")
        else:
            st.write(cal_df) # Định dạng bảng lịch cơ bản

    with app_col:
        st.markdown("#### 🔏 Phê duyệt chờ xử lý")
        pending_apps = ApprovalModel.get_pending_by_workspace(workspace_id)
        
        if not pending_apps:
            st.success("🟢 Hộp thư phê duyệt trống! Tất cả nội dung đã được xử lý.")
        else:
            for app in pending_apps[:5]:
                st.write(f"📝 **{app['title']}** ({app['platform'].upper()})")
                st.caption(f"Yêu cầu lúc: {app['requested_at']}")
                # Cho phép Admin duyệt nhanh trực tiếp trên Dashboard
                if user_role in ["super_admin", "admin"]:
                    app_id = app['id']
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("Duyệt", key=f"appr_{app_id}"):
                            ApprovalModel.respond(app_id, "approved")
                            st.rerun()
                    with c2:
                        if st.button("Từ chối", key=f"rej_{app_id}"):
                            ApprovalModel.respond(app_id, "rejected")
                            st.rerun()

    # 5. QUEUES & SUMMARIES & TRENDS
    st.markdown("---")
    q_col, camp_col, trend_col, act_col = st.columns(4)
    
    with q_col:
        st.markdown("##### 🚀 Hàng đợi đăng bài")
        q_df = fetch_db_data("""
            SELECT s.scheduled_at, p.title, p.platform
            FROM schedules s
            JOIN posts p ON s.post_id = p.id
            WHERE s.workspace_id = ? AND s.status = 'pending' AND s.scheduled_at >= datetime('now')
            ORDER BY s.scheduled_at ASC LIMIT 5
        """, (workspace_id,))
        
        if q_df.empty:
            st.caption("📅 *Hàng đợi xuất bản hiện tại đang trống.*")
        else:
            for _, row in q_df.iterrows():
                st.write(f"• **{row['title'][:20]}...** ({row['platform']})")
                st.caption(f"Lên lịch: {row['scheduled_at']}")

    with camp_col:
        st.markdown("##### 🏁 Tóm tắt Chiến dịch")
        camp_df = fetch_db_data("""
            SELECT c.name, COUNT(p.id) as posts
            FROM campaigns c
            LEFT JOIN posts p ON p.campaign_id = c.id
            WHERE c.workspace_id = ? GROUP BY c.id LIMIT 5
        """, (workspace_id,))
        
        if camp_df.empty:
            st.caption("🏁 *Chưa thiết lập chiến dịch marketing.*")
        else:
            for _, row in camp_df.iterrows():
                st.write(f"• **{row['name']}**")
                st.caption(f"Tổng bài viết: {row['posts']}")

    with trend_col:
        st.markdown("##### 🔥 Xu hướng Hot")
        trend_df = fetch_db_data("""
            SELECT tags, COUNT(*) as cnt 
            FROM knowledge 
            WHERE workspace_id = ? AND tags IS NOT NULL AND tags != '' 
            GROUP BY tags ORDER BY cnt DESC LIMIT 5
        """, (workspace_id,))
        
        if trend_df.empty:
            st.caption("🔥 *Chưa lưu trữ xu hướng/chủ đề nổi bật.*")
        else:
            for _, row in trend_df.iterrows():
                st.write(f"🏷️ **{row['tags']}** ({row['cnt']} bài)")

    with act_col:
        st.markdown("##### 🕵️ Hoạt động gần đây")
        if user_role not in ["super_admin", "admin"]:
            st.caption("🔒 *Yêu cầu quyền quản trị.*")
        else:
            act_df = fetch_db_data("""
                SELECT timestamp, user_email, action 
                FROM audit_logs WHERE workspace_id = ? 
                ORDER BY timestamp DESC LIMIT 5
            """, (workspace_id,))
            
            if act_df.empty:
                st.caption("💬 *Chưa ghi nhận hoạt động nào.*")
            else:
                for _, row in act_df.iterrows():
                    st.write(f"• **{row['user_email'].split('@')[0]}**: {row['action']}")
                    st.caption(f"{row['timestamp']}")
```
