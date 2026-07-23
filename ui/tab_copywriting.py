import streamlit as st
from agents.copywriting_prompts import (
    COPY_FRAMEWORKS, COPY_TYPES, COPY_TONES, FRAMEWORK_EXPLAINERS
)
from services.copywriting_service import generate_copy

# ── CSS ───────────────────────────────────────────────────────────────────────
_CSS = """
<style>
.copy-header {
    background: linear-gradient(135deg, #7c3aed 0%, #4f46e5 50%, #2563eb 100%);
    border-radius: 16px;
    padding: 1.5rem 2rem;
    margin-bottom: 1.8rem;
    color: white;
    text-align: center;
}
.copy-header h2 { color: white !important; margin: 0 0 0.3rem 0; font-size: 1.6rem; }
.copy-header p  { color: rgba(255,255,255,0.85); margin: 0; font-size: 0.95rem; }

.framework-pill {
    display: inline-block;
    background: linear-gradient(90deg, #7c3aed, #4f46e5);
    color: white;
    border-radius: 99px;
    padding: 4px 16px;
    font-size: 0.82rem;
    font-weight: 700;
    margin-bottom: 0.8rem;
}
.explainer-box {
    background: #f5f3ff;
    border: 1px solid #ddd6fe;
    border-left: 4px solid #7c3aed;
    border-radius: 12px;
    padding: 1rem 1.25rem;
    margin-bottom: 1.2rem;
    font-size: 0.88rem;
    color: #3730a3;
    line-height: 1.6;
}
.copy-result-box {
    background: #ffffff;
    border: 1.5px solid #e2e8f0;
    border-radius: 14px;
    padding: 1.5rem;
    margin-bottom: 1.2rem;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}
.ab-tab-header {
    font-weight: 700;
    color: #4f46e5;
    font-size: 0.95rem;
    margin-bottom: 0.5rem;
}
.result-label {
    font-size: 0.82rem;
    font-weight: 700;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.3rem;
}
</style>
"""


def _framework_short(fw: str) -> str:
    """Lấy tên ngắn của framework."""
    return fw.split(" (")[0].strip()


def _copy_type_short(ct: str) -> str:
    """Lấy tên ngắn của copy type."""
    return ct.split(" (")[0].strip()


def render_tab_copywriting(
    gemini_key: str = "",
    workspace_id: int = 1,
    role: str = "editor",
):
    """Render toàn bộ tab Copywriting Agent."""
    st.markdown(_CSS, unsafe_allow_html=True)

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="copy-header">
        <h2>✍️ Copywriting Agent – Viết Copy Bán Hàng Chuyên Nghiệp</h2>
        <p>Áp dụng 9 framework copywriting kinh điển để tạo copy thuyết phục và chuyển đổi cao</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Layout 2 cột ──────────────────────────────────────────────────────────
    left_col, right_col = st.columns([1, 1], gap="large")

    # ════════════════════════════════════════════════════════════
    # CỘT TRÁI: Form nhập liệu
    # ════════════════════════════════════════════════════════════
    with left_col:
        st.markdown("### 📋 Thông tin Copy")

        with st.form("copywriting_form"):
            product = st.text_input(
                "🛍️ Tên sản phẩm / Dịch vụ *",
                placeholder="VD: Khóa học AI Agent thực chiến 30 ngày",
            )
            benefit = st.text_area(
                "💎 Lợi ích nổi bật / USP *",
                placeholder=(
                    "VD: Học viên tạo được AI Agent đầu tiên trong 7 ngày, "
                    "không cần biết code, có mentor 1-1 hỗ trợ"
                ),
                height=100,
            )
            target = st.text_input(
                "🎯 Đối tượng khách hàng mục tiêu *",
                placeholder="VD: Chủ doanh nghiệp vừa và nhỏ, 30-50 tuổi, muốn tăng doanh thu bằng AI",
            )

            st.markdown("---")

            framework = st.selectbox(
                "🧠 Framework Copywriting",
                COPY_FRAMEWORKS,
                help="Framework quyết định cấu trúc và logic thuyết phục của copy"
            )
            copy_type = st.selectbox(
                "📄 Loại Copy cần tạo",
                COPY_TYPES,
            )
            tone = st.selectbox(
                "🎭 Giọng điệu (Tone)",
                COPY_TONES,
            )

            st.markdown("---")
            enable_research = st.checkbox(
                "🌐 Bật Research Agent (Tìm kiếm dữ liệu thực tế)",
                value=False,
                help="AI sẽ tìm kiếm Google để lấy số liệu, xu hướng và social proof thực tế"
            )

            submitted = st.form_submit_button(
                "✍️ Tạo Copy ngay",
                use_container_width=True,
            )

        # ── Nút A/B Testing (ngoài form) ──────────────────────────────────────
        st.markdown("---")
        st.markdown("### 🔀 A/B Testing")
        st.caption("Tạo 3 biến thể copy khác nhau để thử nghiệm hiệu quả")
        ab_submitted = st.button(
            "🔀 Tạo 3 biến thể A/B Testing",
            use_container_width=True,
            disabled=not (product and benefit and target and gemini_key),
        )

    # ════════════════════════════════════════════════════════════
    # CỘT PHẢI: Kết quả
    # ════════════════════════════════════════════════════════════
    with right_col:
        st.markdown("### 📝 Kết quả Copy")

        # ── Xử lý submit tạo copy đơn ─────────────────────────────────────────
        if submitted:
            if not gemini_key:
                st.error("⚠️ Vui lòng nhập Gemini API Key ở thanh bên trái!")
            elif not product or not benefit or not target:
                st.error("⚠️ Vui lòng điền đầy đủ: Tên sản phẩm, Lợi ích và Đối tượng!")
            else:
                with st.spinner(f"✍️ Đang viết {_copy_type_short(copy_type)} theo framework {_framework_short(framework)}..."):
                    try:
                        result = generate_copy(
                            product=product,
                            benefit=benefit,
                            target=target,
                            framework=framework,
                            copy_type=copy_type,
                            tone=tone,
                            api_key=gemini_key,
                            workspace_id=workspace_id,
                            enable_research=enable_research,
                            enable_ab=False,
                        )
                        st.session_state["copy_result"] = result
                        st.session_state["copy_product"] = product
                        st.session_state["copy_benefit"] = benefit
                        st.session_state["copy_target"] = target
                        st.session_state["copy_framework"] = framework
                        st.session_state["copy_type"] = copy_type
                        st.session_state["copy_tone"] = tone
                        st.session_state["copy_chat_history"] = [
                            {"role": "user", "content": f"Tạo copy cho: {product}"},
                            {"role": "model", "content": result["copy"]},
                        ]
                    except Exception as e:
                        if "429" in str(e):
                            st.error("🚫 Hết hạn mức API. Vui lòng thử lại sau vài phút.")
                        else:
                            st.error(f"❌ Lỗi: {e}")

        # ── Xử lý A/B Testing ─────────────────────────────────────────────────
        if ab_submitted:
            if not gemini_key:
                st.error("⚠️ Vui lòng nhập Gemini API Key!")
            else:
                _product = st.session_state.get("copy_product", product)
                _benefit = st.session_state.get("copy_benefit", benefit)
                _target  = st.session_state.get("copy_target", target)
                _fw      = st.session_state.get("copy_framework", framework)
                _ct      = st.session_state.get("copy_type", copy_type)
                _tone    = st.session_state.get("copy_tone", tone)

                with st.spinner("🔀 Đang tạo 3 biến thể A/B Testing..."):
                    try:
                        result = generate_copy(
                            product=_product,
                            benefit=_benefit,
                            target=_target,
                            framework=_fw,
                            copy_type=_ct,
                            tone=_tone,
                            api_key=gemini_key,
                            workspace_id=workspace_id,
                            enable_research=enable_research,
                            enable_ab=True,
                        )
                        st.session_state["copy_result"] = result
                    except Exception as e:
                        st.error(f"❌ Lỗi A/B Testing: {e}")

        # ── Hiển thị kết quả ──────────────────────────────────────────────────
        result = st.session_state.get("copy_result")

        if result:
            _fw_used = result.get("framework_used", "")
            _ab      = result.get("ab_variants")

            # Framework explainer
            explainer = FRAMEWORK_EXPLAINERS.get(_fw_used, "")
            if explainer:
                st.markdown(
                    f'<div class="explainer-box">{explainer}</div>',
                    unsafe_allow_html=True,
                )

            if _ab and len(_ab) >= 2:
                # Hiển thị A/B variants dưới dạng tabs
                st.success(f"✅ Đã tạo {len(_ab)} biến thể A/B Testing!")
                tab_labels = [f"Phiên bản {chr(65+i)}" for i in range(len(_ab))]
                ab_tabs = st.tabs(tab_labels)
                for i, (tab, variant) in enumerate(zip(ab_tabs, _ab)):
                    with tab:
                        st.text_area(
                            f"Copy – Phiên bản {chr(65+i)}",
                            value=variant,
                            height=350,
                            key=f"ab_copy_{i}",
                        )
            else:
                # Hiển thị 1 bản copy
                st.success("✅ Copy đã tạo xong! Sao chép và dùng ngay.")
                st.text_area(
                    "📋 Bản Copy hoàn chỉnh",
                    value=result["copy"],
                    height=450,
                    key="single_copy_output",
                )

        elif not submitted and not ab_submitted:
            # Placeholder
            st.markdown("""
            <div style='text-align:center;padding:3rem 1rem;color:#94a3b8;'>
                <div style='font-size:3.5rem;margin-bottom:1rem;'>✍️</div>
                <div style='font-size:1.1rem;font-weight:600;color:#64748b;margin-bottom:0.5rem;'>
                    Chưa có copy nào được tạo
                </div>
                <div style='font-size:0.9rem;'>
                    Điền thông tin bên trái và nhấn <b>"Tạo Copy ngay"</b> để bắt đầu.
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════
    # CONVERSATION MEMORY CHAT – Tinh chỉnh Copy
    # ════════════════════════════════════════════════════════════
    if st.session_state.get("copy_result"):
        st.divider()
        st.subheader("💬 Tinh chỉnh Copy (Conversation Memory)")
        st.caption(
            "Nhập yêu cầu để AI chỉnh sửa bản copy – ví dụ: 'viết ngắn hơn', "
            "'thêm urgency', 'đổi tone mạnh hơn', 'thêm testimonial giả định'..."
        )

        # Hiển thị lịch sử
        for msg in st.session_state.get("copy_chat_history", []):
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        user_input = st.chat_input(
            "Nhập yêu cầu tinh chỉnh copy tại đây...",
            key="copywriting_chat_input",
        )
        if user_input:
            st.session_state["copy_chat_history"].append(
                {"role": "user", "content": user_input}
            )
            with st.spinner("Đang tinh chỉnh copy theo yêu cầu..."):
                try:
                    from services.chat_service import refine_content_with_history
                    from database.models.brand import BrandModel
                    from database.models.companies import CompanyModel

                    brand_profile   = BrandModel.get_by_workspace(workspace_id)
                    company_profile = CompanyModel.get_by_workspace(workspace_id)

                    refined = refine_content_with_history(
                        chat_history=st.session_state["copy_chat_history"][:-1],
                        user_instruction=user_input,
                        brand_profile=brand_profile,
                        api_key=gemini_key,
                        company_profile=company_profile,
                    )
                    if refined:
                        st.session_state["copy_result"]["copy"] = refined
                        st.session_state["copy_chat_history"].append(
                            {"role": "model", "content": refined}
                        )
                        st.rerun()
                except Exception as e:
                    st.error(f"Lỗi khi tinh chỉnh: {e}")
