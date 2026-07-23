import streamlit as st
from services.fact_check_service import fact_check_content, apply_corrected_claims

_FACT_CHECK_CSS = """
<style>
.fact-header {
    background: linear-gradient(135deg, #0d9488 0%, #0f766e 50%, #115e59 100%);
    border-radius: 16px;
    padding: 1.5rem 2rem;
    margin-bottom: 1.8rem;
    color: white;
    text-align: center;
}
.fact-header h2 { color: white !important; margin: 0 0 0.3rem 0; font-size: 1.6rem; }
.fact-header p { color: rgba(255,255,255,0.85); margin: 0; font-size: 0.95rem; }

/* Status styling */
.status-pill {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 99px;
    font-weight: 700;
    font-size: 0.8rem;
    color: white;
    text-transform: uppercase;
}
.status-confirmed { background-color: #10b981; }
.status-needs-review { background-color: #f59e0b; color: #1e293b; }
.status-incorrect { background-color: #ef4444; }
.status-unverifiable { background-color: #6b7280; }

.claim-quote {
    background-color: #f8fafc;
    border-left: 4px solid #cbd5e1;
    padding: 0.75rem 1rem;
    margin: 0.5rem 0;
    font-style: italic;
    color: #334155;
    font-size: 0.95rem;
}
</style>
"""


def _get_status_pill(status: str) -> str:
    """Trả về HTML pill trạng thái."""
    status_lower = status.strip().lower()
    if status_lower == "confirmed":
        return '<span class="status-pill status-confirmed">✅ Xác nhận</span>'
    elif status_lower == "needs_review":
        return '<span class="status-pill status-needs-review">⚠️ Cần xem lại</span>'
    elif status_lower == "incorrect":
        return '<span class="status-pill status-incorrect">❌ Sai lệch</span>'
    return '<span class="status-pill status-unverifiable">🔍 Không thể xác minh</span>'


def render_tab_factcheck(gemini_key: str = "", workspace_id: int = 1, role: str = "editor"):
    """Render giao diện Fact Checking Agent."""
    st.markdown(_FACT_CHECK_CSS, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="fact-header">
        <h2>🔍 Fact Checking Agent – Xác Minh Sự Thật</h2>
        <p>Kiểm tra và xác thực các tuyên bố, số liệu trong bài viết thời gian thực bằng Google Search</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Text area nhập nội dung
    input_text = st.text_area(
        "Nội dung cần kiểm tra fact-check:",
        value=st.session_state.get("factcheck_input_text", ""),
        placeholder="Nhập hoặc dán bài viết của bạn tại đây để kiểm tra các tuyên bố, số liệu thực tế...",
        height=300,
        key="factcheck_input_text_area"
    )
    
    # Lưu vào session_state để không bị mất khi rerun
    if input_text:
        st.session_state["factcheck_input_text"] = input_text
        
    c1, c2 = st.columns([2, 1])
    with c1:
        max_claims = st.slider(
            "Tối đa số tuyên bố muốn kiểm chứng",
            min_value=2, max_value=10, value=5, step=1,
            help="Giới hạn số lượng tuyên bố quan trọng nhất để tối ưu tốc độ và chi phí API."
        )
    with c2:
        st.write("")
        st.write("")
        btn_check = st.button("🔍 Bắt đầu Fact Check", use_container_width=True, type="primary")
        
    if btn_check:
        if not gemini_key:
            st.error("⚠️ Vui lòng nhập Gemini API Key ở thanh bên trái!")
        elif not input_text.strip():
            st.warning("⚠️ Vui lòng nhập nội dung cần kiểm tra!")
        else:
            with st.spinner("🕵️ Agent đang trích xuất tuyên bố & tìm kiếm xác thực từ Google..."):
                try:
                    results = fact_check_content(input_text, max_claims, gemini_key)
                    st.session_state["factcheck_results"] = results
                except Exception as e:
                    st.error(f"Lỗi khi kiểm tra fact-check: {e}")
                    
    # Hiển thị kết quả
    results = st.session_state.get("factcheck_results")
    if results:
        st.subheader("📊 Báo cáo kiểm định chi tiết")
        
        # Thống kê nhanh
        total = len(results)
        confirmed = sum(1 for r in results if r["status"] == "confirmed")
        needs_review = sum(1 for r in results if r["status"] == "needs_review")
        incorrect = sum(1 for r in results if r["status"] == "incorrect")
        unverifiable = sum(1 for r in results if r["status"] == "unverifiable")
        
        col_t, col_c, col_nr, col_i, col_u = st.columns(5)
        col_t.metric("Tổng số tuyên bố", total)
        col_c.metric("✅ Chính xác", confirmed)
        col_nr.metric("⚠️ Cần xem lại", needs_review)
        col_i.metric("❌ Sai lệch", incorrect)
        col_u.metric("🔍 Chưa rõ", unverifiable)
        
        st.write("")
        
        # Render từng tuyên bố
        for i, res in enumerate(results, start=1):
            claim = res.get("claim", "")
            status = res.get("status", "unverifiable")
            verdict = res.get("verdict", "")
            explanation = res.get("explanation", "")
            sources = res.get("sources", [])
            corrected = res.get("corrected")
            
            status_pill_html = _get_status_pill(status)
            
            with st.expander(f"Tuyên bố #{i}: {claim[:60]}...", expanded=True):
                st.markdown(f"**Trạng thái:** {status_pill_html}", unsafe_allow_html=True)
                st.markdown(f'<div class="claim-quote">"{claim}"</div>', unsafe_allow_html=True)
                st.markdown(f"**Phán quyết:** {verdict}")
                st.markdown(f"**Giải thích:** {explanation}")
                
                # Hiển thị nguồn
                if sources:
                    st.markdown("**Nguồn tham chiếu:**")
                    for src in sources:
                        if src.startswith("http"):
                            st.markdown(f"- [{src}]({src})")
                        else:
                            st.markdown(f"- {src}")
                            
                # Hiển thị sửa đổi gợi ý
                if status in ["incorrect", "needs_review"] and corrected:
                    st.warning(f"💡 **Gợi ý sửa đổi:**\n{corrected}")
                    
        # Action buttons
        st.divider()
        c_btn1, c_btn2 = st.columns(2)
        
        with c_btn1:
            # Nút tự động sửa đổi bài viết
            if st.button("🔧 Tự động cập nhật sửa đổi vào bài viết", use_container_width=True, type="secondary"):
                new_text = apply_corrected_claims(input_text, results)
                st.session_state["factcheck_input_text"] = new_text
                st.success("✅ Đã tự động cập nhật các phần sửa đổi vào bài viết phía trên!")
                st.rerun()
                
        with c_btn2:
            # Tạo báo cáo Markdown để tải xuống
            report_md = "# Báo cáo Fact-checking\n\n"
            for i, r in enumerate(results, start=1):
                report_md += f"### Tuyên bố #{i}: {r.get('claim')}\n"
                report_md += f"- **Trạng thái**: {r.get('status').upper()}\n"
                report_md += f"- **Phán quyết**: {r.get('verdict')}\n"
                report_md += f"- **Giải thích**: {r.get('explanation')}\n"
                if r.get('corrected'):
                    report_md += f"- **Gợi ý sửa đổi**: {r.get('corrected')}\n"
                if r.get('sources'):
                    report_md += "- **Nguồn**:\n"
                    for s in r.get('sources'):
                        report_md += f"  - {s}\n"
                report_md += "\n"
                
            st.download_button(
                "📥 Tải báo cáo kiểm định (.md)",
                data=report_md,
                file_name="Fact_Checking_Report.md",
                mime="text/markdown",
                use_container_width=True
            )
            
    elif not btn_check:
        st.markdown("""
        <div style='text-align:center;padding:3rem 1rem;color:#94a3b8;'>
            <div style='font-size:3.5rem;margin-bottom:1rem;'>🕵️</div>
            <div style='font-size:1.1rem;font-weight:600;color:#64748b;margin-bottom:0.5rem;'>
                Chưa thực hiện kiểm tra
            </div>
            <div style='font-size:0.9rem;'>
                Dán nội dung cần kiểm định vào ô văn bản phía trên và nhấn <b>"Bắt đầu Fact Check"</b>.
            </div>
        </div>
        """, unsafe_allow_html=True)
