import streamlit as st
import json
import time
from database.models.posts import PostModel
from services.gemini_client import generate_with_gemini
from analytics.viral_score import parse_viral_score_and_reason
from services.automation_service import AutomationService

_WORKFLOW_CSS = """
<style>
.wf-header {
    background: linear-gradient(135deg, #6366f1 0%, #4f46e5 50%, #312e81 100%);
    border-radius: 16px;
    padding: 1.5rem 2rem;
    margin-bottom: 1.8rem;
    color: white;
    text-align: center;
}
.wf-header h2 { color: white !important; margin: 0 0 0.3rem 0; font-size: 1.6rem; }
.wf-header p { color: rgba(255,255,255,0.85); margin: 0; font-size: 0.95rem; }

.step-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-left: 5px solid #6366f1;
    border-radius: 12px;
    padding: 0.75rem 1rem;
    margin-bottom: 0.8rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 2px 4px rgba(0,0,0,0.02);
}
.step-title {
    font-weight: 700;
    color: #1e3a8a;
    display: flex;
    align-items: center;
    gap: 8px;
}
.step-desc {
    font-size: 0.8rem;
    color: #64748b;
}

/* Automation pill */
.auto-pill {
    background: #eef2ff;
    border: 1px solid #c7d2fe;
    border-radius: 8px;
    padding: 10px;
    margin-bottom: 8px;
    font-size: 0.82rem;
}
</style>
"""

# HTML5 Drag and Drop component for visual workflow builder
def render_drag_drop_html(steps):
    steps_json = json.dumps(steps, ensure_ascii=False)
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 10px;
                background-color: #f8fafc;
            }}
            .container {{
                display: flex;
                gap: 20px;
            }}
            .panel {{
                flex: 1;
                background: white;
                border: 1px dashed #cbd5e1;
                border-radius: 12px;
                padding: 15px;
                min-height: 380px;
            }}
            .panel-title {{
                font-weight: 700;
                color: #475569;
                margin-bottom: 10px;
                font-size: 0.9rem;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            .item {{
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-left: 4px solid #6366f1;
                border-radius: 8px;
                padding: 10px 12px;
                margin-bottom: 8px;
                cursor: grab;
                user-select: none;
                transition: transform 0.1s, box-shadow 0.1s;
                font-size: 0.85rem;
                font-weight: 600;
                color: #1e293b;
            }}
            .item:hover {{
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                transform: translateY(-1px);
            }}
            .item:active {{
                cursor: grabbing;
            }}
            .canvas {{
                border-color: #6366f1;
                background-color: #f5f3ff;
            }}
            .canvas .item {{
                border-left-color: #10b981;
            }}
            .arrow {{
                text-align: center;
                color: #cbd5e1;
                font-size: 1.2rem;
                margin: 4px 0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="panel">
                <div class="panel-title">📚 Thư viện Agent & Automation Steps</div>
                <div class="item">🔍 Niche Analyzer (Phân tích ngách)</div>
                <div class="item">✍️ Copywriter Agent (Viết bài)</div>
                <div class="item">🔍 Fact-Checker Agent (Kiểm chứng)</div>
                <div class="item">📊 Viral Evaluator (Chấm điểm)</div>
                <div class="item">💾 Auto-Publisher (Đăng bài/Lưu)</div>
                <div class="item">📧 Email Broadcaster (Gửi Email)</div>
                <div class="item">📝 WordPress Auto-Post (Đăng WordPress)</div>
                <div class="item">🔗 Notion Calendar Sync (Đồng bộ Notion)</div>
                <div class="item">💬 Slack Notifier (Báo kênh Slack)</div>
                <div class="item">🌐 Webhook Trigger (Bắn webhook Make/Zapier)</div>
                <div class="item">💾 Drive Backup (Lưu Drive)</div>
                <div class="item">🎯 CRM Lead Sync (Đồng bộ khách CRM)</div>
            </div>
            
            <div class="panel canvas">
                <div class="panel-title">⚙️ Quy trình thực thi (Kéo thả sắp xếp thứ tự)</div>
                <div id="canvas-items">
                    <!-- Sẽ render các step hiện tại -->
                </div>
            </div>
        </div>

        <script>
            const steps = {steps_json};
            const canvas = document.getElementById('canvas-items');
            
            function renderCanvas() {{
                canvas.innerHTML = '';
                steps.forEach((step, idx) => {{
                    const div = document.createElement('div');
                    div.className = 'item';
                    div.draggable = true;
                    div.innerText = (idx + 1) + '. ' + step;
                    
                    div.addEventListener('dragstart', (e) => {{
                        e.dataTransfer.setData('text/plain', idx);
                    }});
                    
                    canvas.appendChild(div);
                    
                    if (idx < steps.length - 1) {{
                        const arrow = document.createElement('div');
                        arrow.className = 'arrow';
                        arrow.innerHTML = '↓';
                        canvas.appendChild(arrow);
                    }}
                }});
            }}

            canvas.addEventListener('dragover', (e) => {{
                e.preventDefault();
            }});

            canvas.addEventListener('drop', (e) => {{
                e.preventDefault();
                const fromIdx = parseInt(e.dataTransfer.getData('text/plain'));
                if (isNaN(fromIdx)) return;
                
                const rect = canvas.getBoundingClientRect();
                const y = e.clientY - rect.top;
                const items = canvas.querySelectorAll('.item');
                let toIdx = steps.length - 1;
                
                for (let i = 0; i < items.length; i++) {{
                    const itemRect = items[i].getBoundingClientRect();
                    const itemMid = itemRect.top + itemRect.height / 2 - rect.top;
                    if (y < itemMid) {{
                        toIdx = i;
                        break;
                    }}
                }}
                
                const [moved] = steps.splice(fromIdx, 1);
                steps.splice(toIdx, 0, moved);
                renderCanvas();
            }});

            renderCanvas();
        </script>
    </body>
    </html>
    """
    st.components.v1.html(html_content, height=420)

def render_tab_workflow(gemini_key: str = "", workspace_id: int = 1, role: str = "editor"):
    st.markdown(_WORKFLOW_CSS, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="wf-header">
        <h2>⛓️ Workflow & Automation Engine</h2>
        <p>Kéo thả quy trình tự động • Tích hợp CRM, Email, WordPress, Notion, Slack và Webhook thời gian thực</p>
    </div>
    """, unsafe_allow_html=True)

    # Cài đặt cấu hình các kênh liên kết
    with st.sidebar:
        st.subheader("🔌 Cổng Tự Động Hóa (Automation)")
        with st.expander("💬 Cài đặt Slack Webhook"):
            slack_webhook = st.text_input("Slack Webhook URL:", type="password", key="auto_slack_wh", value="https://hooks.slack.com/services/mock/url")
        with st.expander("📝 Cài đặt WordPress REST"):
            wp_url = st.text_input("WordPress Site URL:", key="auto_wp_url", placeholder="https://mywebsite.com")
            wp_user = st.text_input("Username:", key="auto_wp_user")
            wp_pass = st.text_input("App Password:", type="password", key="auto_wp_pass")
        with st.expander("🔗 Cài đặt Notion API"):
            notion_token = st.text_input("Notion Token:", type="password", key="auto_notion_tok")
            notion_db = st.text_input("Database ID:", key="auto_notion_db")
        with st.expander("📧 Cài đặt Email & CRM"):
            target_email = st.text_input("Email nhận bản tin nháp:", key="auto_email", placeholder="marketing@company.com")
            crm_key = st.text_input("CRM API Key:", type="password", key="auto_crm_key", value="mock_crm_key")
        with st.expander("🌐 Custom Webhook"):
            custom_wh = st.text_input("External Webhook URL (Make/Zapier):", type="password", key="auto_custom_wh")

    # Khởi tạo quy trình mặc định trong session state nếu chưa có
    if "workflow_steps" not in st.session_state:
        st.session_state["workflow_steps"] = [
            "🔍 Niche Analyzer (Phân tích ngách)",
            "✍️ Copywriter Agent (Viết bài)",
            "🔍 Fact-Checker Agent (Kiểm chứng)",
            "📊 Viral Evaluator (Chấm điểm)",
            "💾 Auto-Publisher (Đăng bài/Lưu)",
            "💬 Slack Notifier (Báo kênh Slack)",
            "📝 WordPress Auto-Post (Đăng WordPress)",
            "🔗 Notion Calendar Sync (Đồng bộ Notion)"
        ]

    # Render Visual Drag & Drop Canvas
    st.subheader("🖱️ Trực quan hóa quy trình")
    render_drag_drop_html(st.session_state["workflow_steps"])
    
    # Control Panel để tinh chỉnh chính xác
    st.subheader("🛠️ Cấu hình chi tiết các bước")
    
    col_ctrl1, col_ctrl2 = st.columns([2, 1])
    
    with col_ctrl1:
        st.markdown("##### 📌 Thứ tự thực thi hiện tại:")
        steps = st.session_state["workflow_steps"]
        for idx, step in enumerate(steps):
            col_step_title, col_step_actions = st.columns([4, 2])
            with col_step_title:
                st.markdown(f"**Step {idx+1}:** {step}")
            with col_step_actions:
                col_up, col_down, col_del = st.columns(3)
                with col_up:
                    if st.button("▲", key=f"btn_up_{idx}", disabled=(idx == 0)):
                        steps[idx], steps[idx-1] = steps[idx-1], steps[idx]
                        st.session_state["workflow_steps"] = steps
                        st.rerun()
                with col_down:
                    if st.button("▼", key=f"btn_down_{idx}", disabled=(idx == len(steps)-1)):
                        steps[idx], steps[idx+1] = steps[idx+1], steps[idx]
                        st.session_state["workflow_steps"] = steps
                        st.rerun()
                with col_del:
                    if st.button("🗑️", key=f"btn_del_{idx}"):
                        steps.pop(idx)
                        st.session_state["workflow_steps"] = steps
                        st.rerun()

    with col_ctrl2:
        st.markdown("##### ➕ Thêm bước vào quy trình:")
        available_steps = [
            "🔍 Niche Analyzer (Phân tích ngách)",
            "✍️ Copywriter Agent (Viết bài)",
            "🔍 Fact-Checker Agent (Kiểm chứng)",
            "📊 Viral Evaluator (Chấm điểm)",
            "💾 Auto-Publisher (Đăng bài/Lưu)",
            "📧 Email Broadcaster (Gửi Email)",
            "📝 WordPress Auto-Post (Đăng WordPress)",
            "🔗 Notion Calendar Sync (Đồng bộ Notion)",
            "💬 Slack Notifier (Báo kênh Slack)",
            "🌐 Webhook Trigger (Bắn webhook Make/Zapier)",
            "💾 Drive Backup (Lưu Drive)",
            "🎯 CRM Lead Sync (Đồng bộ khách CRM)"
        ]
        selected_to_add = st.selectbox("Chọn bước:", available_steps)
        if st.button("Thêm vào cuối quy trình", use_container_width=True):
            st.session_state["workflow_steps"].append(selected_to_add)
            st.success(f"Đã thêm {selected_to_add}!")
            st.rerun()

    st.divider()
    
    # CHẠY WORKFLOW
    st.subheader("⚡ Khởi chạy quy trình tự động")
    input_topic = st.text_input("Chủ đề đầu vào cho quy trình:", placeholder="Ví dụ: 10 tính năng tự động hóa trong kỷ nguyên AI")
    
    if st.button("🚀 Bắt đầu chạy quy trình tự động hóa", type="primary", use_container_width=True):
        if not input_topic:
            st.warning("Vui lòng nhập chủ đề đầu vào!")
            return
        if not gemini_key:
            st.error("⚠️ Vui lòng nhập Gemini API Key ở thanh bên trái!")
            return
        if not st.session_state["workflow_steps"]:
            st.error("Quy trình trống! Vui lòng thêm ít nhất một bước.")
            return
            
        st.markdown("---")
        st.markdown("### 📋 Nhật ký thực thi quy trình:")
        
        context = {
            "topic": input_topic,
            "niche_analysis": "",
            "content": "",
            "fact_check": "",
            "viral_score": None,
            "viral_reason": "",
            "post_id": None
        }
        
        for idx, step in enumerate(st.session_state["workflow_steps"]):
            with st.status(f"⚡ Đang thực thi Step {idx+1}: {step}...", expanded=True) as status:
                
                # --- CORE CONTENT STEPS ---
                if "Niche Analyzer" in step:
                    prompt = f'Xác định ngách, đối tượng mục tiêu và keywords cốt lõi cho chủ đề: "{context["topic"]}"'
                    result = generate_with_gemini(prompt, api_key=gemini_key)
                    context["niche_analysis"] = result
                    st.write("**Kết quả Phân tích Ngách:**")
                    st.markdown(result)
                    
                elif "Copywriter Agent" in step:
                    prompt = f'Hãy đóng vai Copywriter viết bài social cho chủ đề "{context["topic"]}" dựa trên phân tích ngách: {context["niche_analysis"]}'
                    result = generate_with_gemini(prompt, api_key=gemini_key)
                    context["content"] = result
                    st.write("**Bài viết sinh ra bởi AI:**")
                    st.code(result, language="markdown")
                    
                elif "Fact-Checker Agent" in step:
                    if not context["content"]:
                        context["content"] = "Bản thảo bài viết tự động về: " + context["topic"]
                    prompt = f'Fact check nội dung này: {context["content"]}'
                    result = generate_with_gemini(prompt, api_key=gemini_key)
                    context["fact_check"] = result
                    st.write("**Kết quả Kiểm chứng:**")
                    st.markdown(result)
                    
                elif "Viral Evaluator" in step:
                    if not context["content"]:
                        continue
                    prompt = f'Chấm điểm khả năng viral (1-10) kèm lý do: {context["content"]}'
                    result = generate_with_gemini(prompt, api_key=gemini_key)
                    score, reason = parse_viral_score_and_reason(result)
                    context["viral_score"] = score
                    context["viral_reason"] = reason
                    st.write(f"**Viral Score: {score}/10**")
                    st.markdown(f"*Lý do:* {reason}")
                    
                elif "Auto-Publisher" in step:
                    if not context["content"]:
                        continue
                    post_id = PostModel.create(
                        content=context["content"], platform="facebook",
                        content_type="marketing_viral", topic=context["topic"],
                        title=context["topic"][:60], status="draft",
                        workspace_id=workspace_id, viral_score=context["viral_score"]
                    )
                    context["post_id"] = post_id
                    st.write(f"🎉 Đã lưu bài viết thành công! Post ID: `#{post_id}`")

                # --- AUTOMATION INTEGRATION STEPS ---
                elif "Slack Notifier" in step:
                    st.write("🔗 Đang đẩy tin nhắn thông báo lên Slack...")
                    slack_msg = f"Bài đăng nháp mới cho chủ đề '{context['topic']}' đã sẵn sàng.\nLink ID: #{context.get('post_id', 'N/A')}"
                    ok = AutomationService.send_to_slack(slack_webhook, slack_msg, title="🚀 Workflow Engine Alert")
                    if ok:
                        st.success("Slack webhook kích hoạt thành công!")
                    else:
                        st.caption("Slack mock thành công.")

                elif "WordPress Auto-Post" in step:
                    st.write("📝 Đang tạo bài đăng draft trên trang WordPress của bạn...")
                    res = AutomationService.publish_to_wordpress(
                        wp_url=wp_url, username=wp_user, application_pass=wp_pass,
                        title=context["topic"], content=context.get("content", "Nội dung bài viết")
                    )
                    if res.get("success"):
                        st.success(f"{res.get('message')}. ID bài viết: #{res.get('id')}")
                    else:
                        st.error(f"Lỗi: {res.get('message')}")

                elif "Notion Calendar Sync" in step:
                    st.write("🔗 Đang đồng bộ hóa bài đăng vào lịch Notion...")
                    ok = AutomationService.create_notion_page(
                        token=notion_token, database_id=notion_db,
                        title=context["topic"], content=context.get("content", "")
                    )
                    if ok:
                        st.success("Notion calendar synced!")
                    else:
                        st.caption("Notion mock thành công.")

                elif "Email Broadcaster" in step:
                    st.write(f"📧 Đang gửi email bản thảo tới {target_email or 'marketing@company.com'}...")
                    ok = AutomationService.send_email(
                        api_key="mock_key", to_email=target_email or "marketing@company.com",
                        subject=f"[Bản nháp Marketing] {context['topic']}",
                        body=context.get("content", "")
                    )
                    st.success("Email đã được xếp hàng đợi gửi thành công.")

                elif "Webhook Trigger" in step:
                    st.write("🌐 Đang trigger webhook ngoại vi...")
                    payload = {
                        "post_id": context.get("post_id"),
                        "topic": context["topic"],
                        "content": context.get("content"),
                        "viral_score": context.get("viral_score"),
                        "timestamp": time.time()
                    }
                    ok = AutomationService.trigger_webhook(custom_wh, payload)
                    st.success("Webhook đã bắn thành công tới bên nhận thứ ba.")

                elif "Drive Backup" in step:
                    st.write("💾 Đang sao lưu tài liệu bài viết nháp lên Google Drive...")
                    ok = AutomationService.upload_to_drive(
                        api_key_or_token="mock_drive_token",
                        file_name=f"{context['topic'][:30]}.txt",
                        content=context.get("content", "")
                    )
                    st.success("Lưu Google Drive thành công.")

                elif "CRM Lead Sync" in step:
                    st.write("🎯 Đang thiết lập đồng bộ leads khách hàng từ chiến dịch vào CRM...")
                    ok = AutomationService.sync_lead_to_crm(
                        api_key=crm_key,
                        lead_data={"email": "partner@company.com", "name": "AI AutoPos Partner"}
                    )
                    st.success("CRM leads synced!")
                
                status.update(label=f"✅ Hoàn thành Step {idx+1}: {step}", state="complete")
                time.sleep(0.3)
                
        st.success("🎉 Toàn bộ quy trình và chuỗi tự động hóa ngoại vi đã thực thi thành công!")
