import streamlit as st
import pandas as pd
import json
from datetime import datetime
from database.repositories import WeeklyScheduleRepository
from core.doc_exporter import get_plan_items, export_plan_to_word
from services.content_service import create_weekly_plan
from core.rbac import get_role_display, render_role_badge

def render_tab_plan(gemini_key, workspace_id: int = None, role="editor"):
    st.header("Lộ trình nội dung 7 ngày")
    
    role = (role or "editor").lower()
    state_key = f"current_plan_{workspace_id}"
    if state_key not in st.session_state:
        latest = WeeklyScheduleRepository.get_latest_weekly_schedule(workspace_id)
        if latest:
            st.session_state[state_key] = latest

    # Xác định quyền tạo kế hoạch (lấy từ core/rbac)
    # viewer không tạo được. Các role khác đều có thể tạo.
    st.markdown(render_role_badge(role), unsafe_allow_html=True)

    if role == "viewer":
        st.info("💡 Bạn có quyền Người xem (Viewer) tại Workspace này. Bạn chỉ có thể xem lộ trình hiện tại mà không thể tạo hoặc chỉnh sửa lộ trình mới.")
    else:
        col_btn1, col_btn2 = st.columns([1, 4])

        if col_btn1.button("🔄 Gợi ý kế hoạch mặc định"):
            with st.spinner("AI đang tạo kế hoạch..."):
                try:
                    # Gọi qua Service Layer
                    plan = create_weekly_plan(api_key=gemini_key)
                    st.session_state[state_key] = plan
                    
                    # Lưu vào DB
                    WeeklyScheduleRepository.add_weekly_schedule(
                        week_start=datetime.now().strftime("%Y-%m-%d"),
                        plan_json=json.dumps(plan, ensure_ascii=False),
                        workspace_id=workspace_id
                    )
                except Exception as e:
                    st.error(f"Lỗi khi tạo lịch: {e}")

        with st.form("weekly_plan_form"):
            weekly_topic = st.text_area(
                "Chủ đề chính của tuần",
                placeholder="Ví dụ: Cách sử dụng ChatGPT hiệu quả cho CEO"
            )
            form_col1, form_col2 = st.columns(2)
            with form_col1:
                weekly_target = st.selectbox("Đối tượng mục tiêu", [
                    "CEO",
                    "Chủ doanh nghiệp",
                    "Nhà quản lý",
                    "Nhân viên văn phòng",
                    "Sales",
                    "Marketing",
                    "Developer",
                    "Freelancer",
                    "Người mới bắt đầu",
                    "Chuyên gia AI"
                ])
                weekly_days = st.selectbox("Số ngày lên lịch", [7, 14, 30])
            with form_col2:
                weekly_goal = st.selectbox("Mục tiêu nội dung", [
                    "Chia sẻ kiến thức",
                    "Xây dựng thương hiệu cá nhân",
                    "Tạo khách hàng tiềm năng",
                    "Tăng tương tác",
                    "Giáo dục thị trường",
                    "Quảng bá dịch vụ"
                ])
                weekly_style = st.selectbox("Phong cách nội dung", [
                    "Dễ hiểu cho người mới",
                    "Chuyên sâu cho chuyên gia",
                    "Thực chiến kinh nghiệm",
                    "Case study doanh nghiệp",
                    "So sánh công cụ",
                    "Hướng dẫn từng bước",
                    "Sai lầm thường gặp"
                ])

            weekly_submit = st.form_submit_button("🔄 Tạo lịch theo chủ đề")

            if weekly_submit:
                if not weekly_topic or not weekly_topic.strip():
                    st.warning("Vui lòng nhập chủ đề chính cho kế hoạch tuần.")
                else:
                    with st.spinner("AI đang tạo lịch theo chủ đề..."):
                        try:
                            # Gọi qua Service Layer
                            plan = create_weekly_plan(
                                topic=weekly_topic,
                                target=weekly_target,
                                goal=weekly_goal,
                                days=weekly_days,
                                style=weekly_style,
                                api_key=gemini_key
                            )
                            
                            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            plan_record = {
                                "meta": {
                                    "topic": weekly_topic,
                                    "target": weekly_target,
                                    "goal": weekly_goal,
                                    "days": weekly_days,
                                    "style": weekly_style,
                                    "created_at": created_at,
                                },
                                "items": plan,
                            }
                            st.session_state[state_key] = plan_record
                            
                            WeeklyScheduleRepository.add_weekly_schedule(
                                week_start=datetime.now().strftime("%Y-%m-%d"),
                                plan_json=json.dumps(plan_record, ensure_ascii=False),
                                workspace_id=workspace_id
                            )
                        except Exception as e:
                            st.error(f"Lỗi khi tạo lịch theo chủ đề: {e}")
                        
    if state_key in st.session_state:
        plan_items = get_plan_items(st.session_state[state_key])
        df_plan = pd.DataFrame(plan_items)
        supported_plan_columns = [
            "day", "topic", "target", "goal", "format", "angle", "hook", "cta"
        ]
        visible_plan_columns = [col for col in supported_plan_columns if col in df_plan.columns]
        if visible_plan_columns:
            df_plan = df_plan[visible_plan_columns]
        st.dataframe(df_plan, use_container_width=True, hide_index=True)
        st.info("💡 Mẹo: Bạn có thể copy chủ đề từng ngày để dán vào tab Tạo Content.")

        st.divider()
        col_word, _ = st.columns([1, 3])
        with col_word:
            word_bytes = export_plan_to_word(st.session_state[state_key])
            if word_bytes:
                st.download_button(
                    "📄 Xuất kế hoạch tuần (Word)",
                    data=word_bytes,
                    file_name=f"Ke_Hoach_Tuan_{datetime.now().strftime('%d%m%Y')}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
    else:
        st.write("Chưa có kế hoạch tuần này. Hãy nhấn nút để AI gợi ý.")
