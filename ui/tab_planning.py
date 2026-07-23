import streamlit as st
import json
import pandas as pd
from services.gemini_client import generate_with_gemini, clean_ai_json_text

_PLANNING_CSS = """
<style>
.plan-header {
    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 50%, #1d4ed8 100%);
    border-radius: 16px;
    padding: 1.5rem 2rem;
    margin-bottom: 1.8rem;
    color: white;
    text-align: center;
}
.plan-header h2 { color: white !important; margin: 0 0 0.3rem 0; font-size: 1.6rem; }
.plan-header p { color: rgba(255,255,255,0.85); margin: 0; font-size: 0.95rem; }

.task-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 1rem;
    margin-bottom: 0.8rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.02);
}
.assignee-badge {
    background-color: #eff6ff;
    color: #1d4ed8;
    padding: 2px 8px;
    border-radius: 99px;
    font-size: 0.75rem;
    font-weight: 700;
}
.phase-badge {
    background-color: #f3f4f6;
    color: #374151;
    padding: 2px 8px;
    border-radius: 99px;
    font-size: 0.75rem;
    font-weight: 600;
}
</style>
"""

def generate_campaign_tasks(goal: str, target: str, duration: int, style: str, api_key: str):
    """Gọi Gemini AI để chia nhỏ công việc dựa trên mục tiêu."""
    prompt = f"""
    Bạn là một Project Manager & AI Planning Specialist. 
    Hãy chia nhỏ mục tiêu chiến dịch marketing sau đây thành một danh sách công việc (task list) chi tiết, phân chia theo các giai đoạn rõ ràng.
    
    Thông tin chiến dịch:
    - Mục tiêu lớn: "{goal}"
    - Đối tượng mục tiêu: {target}
    - Thời gian triển khai: {duration} ngày
    - Phong cách thực hiện: {style}
    
    Yêu cầu trả về định dạng JSON Array chứa các Object công việc. Mỗi Object bắt buộc có cấu trúc sau:
    [
      {{
        "task_id": 1,
        "task_name": "Tên công việc cụ thể",
        "phase": "Tên giai đoạn (ví dụ: Chuẩn bị, Triển khai, Nghiệm thu)",
        "assignee": "Vai trò thực hiện (ví dụ: Designer, Copywriter, Manager, Editor)",
        "duration": "Thời gian hoàn thành (ví dụ: 2 ngày)",
        "checklist": [
          "Công việc chi tiết 1",
          "Công việc chi tiết 2",
          "Công việc chi tiết 3"
        ]
      }}
    ]
    
    Lưu ý: Chỉ trả về mảng JSON thuan tuy, khong bao gom markdown codeblock, khong co loi giai thich. Chia nho tu 5 den 8 công việc chính, mỗi công việc co 2-4 checklist con.
    """
    
    raw_text = generate_with_gemini(prompt, api_key=api_key)
    clean_json = clean_ai_json_text(raw_text)
    
    # Try parsing and repairing if necessary
    try:
        tasks = json.loads(clean_json)
        return tasks
    except Exception as e:
        # Fallback repair prompt
        repair_prompt = f"""
        Hãy sửa lỗi định dạng đoạn text sau đây thành một mảng JSON Array hợp lệ.
        Mỗi object chứa các thuộc tính: task_id, task_name, phase, assignee, duration, checklist.
        
        Text lỗi cần sửa:
        {clean_json}
        """
        repaired_text = generate_with_gemini(repair_prompt, api_key=api_key)
        repaired_json = clean_ai_json_text(repaired_text)
        return json.loads(repaired_json)

def render_tab_planning(gemini_key: str = "", workspace_id: int = 1, role: str = "editor"):
    st.markdown(_PLANNING_CSS, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="plan-header">
        <h2>📋 Planning Engine – AI Tự Chia Task</h2>
        <p>Phân rã mục tiêu chiến dịch lớn thành các nhiệm vụ cụ thể theo từng giai đoạn và vai trò</p>
    </div>
    """, unsafe_allow_html=True)
    
    # --- PHẦN 1: FORM THIẾT LẬP ---
    with st.form("planning_engine_form"):
        goal_input = st.text_area(
            "🎯 Nhập mục tiêu chiến dịch lớn của bạn:",
            placeholder="Ví dụ: Ra mắt dòng trà sữa hạt mới ít ngọt cho giới văn phòng tại Quận 1"
        )
        
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            target_audience = st.selectbox("Đối tượng mục tiêu:", [
                "Giới văn phòng, công sở",
                "Học sinh, sinh viên",
                "Chủ doanh nghiệp, CEO",
                "Các bà mẹ bỉm sữa",
                "Người tập gym, thể thao",
                "Developer, kỹ sư công nghệ"
            ])
            campaign_duration = st.slider("Thời gian chạy chiến dịch (ngày):", min_value=7, max_value=90, value=30)
            
        with col_c2:
            campaign_style = st.selectbox("Phong cách chiến dịch:", [
                "Viral Marketing (Lan truyền rộng rãi)",
                "Educating (Giáo dục khách hàng về sản phẩm)",
                "Direct Sales (Tập trung chuyển đổi mua hàng)",
                "Branding (Định vị và gia tăng nhận diện thương hiệu)"
            ])
            
        btn_plan = st.form_submit_button("🤖 AI tự chia task ngay", use_container_width=True)
        
    if btn_plan:
        if not goal_input:
            st.warning("Vui lòng nhập mục tiêu lớn của chiến dịch!")
            return
        if not gemini_key:
            st.error("⚠️ Vui lòng nhập Gemini API Key ở thanh bên trái!")
            return
            
        with st.spinner("AI đang nghiên cứu chiến dịch và tự động phân chia các đầu việc..."):
            try:
                tasks_data = generate_campaign_tasks(
                    goal=goal_input,
                    target=target_audience,
                    duration=campaign_duration,
                    style=campaign_style,
                    api_key=gemini_key
                )
                
                # Lưu vào session state
                state_key = f"planning_tasks_{workspace_id}"
                st.session_state[state_key] = tasks_data
                # Khởi tạo trạng thái các checklist
                st.session_state[f"checklist_states_{workspace_id}"] = {}
                st.success("🎉 Đã lập lộ trình công việc thành công!")
            except Exception as e:
                st.error(f"Lỗi phân rã công việc: {e}")
                
    # --- PHẦN 2: HIỂN THỊ LỘ TRÌNH TASK ---
    state_key = f"planning_tasks_{workspace_id}"
    tasks = st.session_state.get(state_key, [])
    
    if tasks:
        st.write("")
        st.subheader("📋 Bảng phân công công việc chi tiết")
        
        # Thống kê tiến độ dự án
        checklist_states = st.session_state.get(f"checklist_states_{workspace_id}", {})
        
        total_checklist_items = 0
        completed_checklist_items = 0
        
        for task in tasks:
            t_id = task["task_id"]
            for sub_idx, _ in enumerate(task.get("checklist", [])):
                total_checklist_items += 1
                key = f"task_{t_id}_sub_{sub_idx}"
                if checklist_states.get(key, False):
                    completed_checklist_items += 1
                    
        progress_pct = (completed_checklist_items / total_checklist_items) if total_checklist_items > 0 else 0.0
        
        st.markdown(f"**📈 Tiến độ hoàn thành chiến dịch: {completed_checklist_items}/{total_checklist_items} tiểu mục ({progress_pct*100:.1f}%)**")
        st.progress(progress_pct)
        
        st.write("")
        
        # Hiển thị các task
        # Gom nhóm theo phase
        phases = {}
        for task in tasks:
            phase_name = task.get("phase", "Chung")
            if phase_name not in phases:
                phases[phase_name] = []
            phases[phase_name].append(task)
            
        for phase_name, phase_tasks in phases.items():
            st.markdown(f"#### 🏷️ Giai đoạn: {phase_name}")
            
            for task in phase_tasks:
                t_id = task["task_id"]
                with st.expander(f"📌 {task['task_name']}"):
                    col_info1, col_info2 = st.columns(2)
                    with col_info1:
                        st.markdown(f"👤 **Vai trò:** <span class='assignee-badge'>{task.get('assignee', 'Chưa rõ')}</span>", unsafe_allow_html=True)
                    with col_info2:
                        st.markdown(f"⏱️ **Thời hạn:** `{task.get('duration', 'N/A')}`")
                        
                    st.write("")
                    st.markdown("**Checklist con cần làm:**")
                    
                    for sub_idx, sub_item in enumerate(task.get("checklist", [])):
                        key = f"task_{t_id}_sub_{sub_idx}"
                        # Checkbox tương tác lưu vào state
                        is_checked = st.checkbox(
                            sub_item,
                            value=checklist_states.get(key, False),
                            key=f"chk_{workspace_id}_{t_id}_{sub_idx}"
                        )
                        if is_checked != checklist_states.get(key, False):
                            checklist_states[key] = is_checked
                            st.session_state[f"checklist_states_{workspace_id}"] = checklist_states
                            st.rerun()
                            
            st.write("")
            
        # Nút xuất CSV danh sách công việc
        flat_tasks = []
        for task in tasks:
            for sub_item in task.get("checklist", []):
                flat_tasks.append({
                    "Giai đoạn": task.get("phase"),
                    "Công việc chính": task.get("task_name"),
                    "Người thực hiện": task.get("assignee"),
                    "Thời hạn": task.get("duration"),
                    "Đầu việc nhỏ": sub_item
                })
        df_flat = pd.DataFrame(flat_tasks)
        csv_bytes = df_flat.to_csv(index=False).encode('utf-8-sig')
        
        st.download_button(
            "📊 Tải danh sách công việc (CSV)",
            data=csv_bytes,
            file_name=f"Lộ_Trình_Chiến_Dịch_{workspace_id}.csv",
            mime="text/csv"
        )
    else:
        st.markdown("""
        <div style='text-align:center;padding:3rem 1rem;color:#94a3b8;'>
            <div style='font-size:3.5rem;margin-bottom:1rem;'>📋</div>
            <div style='font-size:1.1rem;font-weight:600;color:#64748b;margin-bottom:0.5rem;'>
                Chưa có kế hoạch nào được tạo
            </div>
            <div style='font-size:0.9rem;'>
                Nhập mục tiêu chiến dịch của bạn ở biểu mẫu bên trên để AI tự động chia nhỏ công việc.
            </div>
        </div>
        """, unsafe_allow_html=True)
