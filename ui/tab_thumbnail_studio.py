"""
ui/tab_thumbnail_studio.py
==========================
Giao diện Thumbnail Studio của Apex AI Portal.
Chứa:
1. Template Library
2. AI Generation Form (Prompt, Versioning, History)
3. Visual Intelligence Engine (VIE) — Visual Story + Image Prompt + Vision Score
4. Preview, Version Restore & Export
"""

import streamlit as st
import io
import json
from datetime import datetime
from PIL import Image
from database.models.assets import AssetModel
from database.models.thumbnail_analytics import ThumbnailAnalyticsModel
from database.models.brand import BrandModel
from services.thumbnail_generator_service import ThumbnailGeneratorService, PLATFORM_DEFAULTS
from services.thumbnail_publishing_service import ThumbnailProcessor, get_spec

# Custom CSS cho giao diện chuyên nghiệp
THUMBNAIL_STUDIO_CSS = """
<style>
.studio-header {
    background: linear-gradient(135deg, #712ae2 0%, #4f46e5 50%, #312e81 100%);
    border-radius: 16px;
    padding: 1.5rem 2rem;
    margin-bottom: 1.8rem;
    color: white;
    text-align: center;
}
.studio-header h2 { color: white !important; margin: 0 0 0.3rem 0; font-size: 1.6rem; }
.studio-header p { color: rgba(255,255,255,0.85); margin: 0; font-size: 0.95rem; }

.template-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 10px;
    margin-bottom: 8px;
    cursor: pointer;
    transition: all 0.2s ease-in-out;
}
.template-card:hover {
    transform: scale(1.02);
    border-color: #712ae2;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
}

.live-preview-box {
    border: 2px dashed #cbd5e1;
    border-radius: 12px;
    padding: 16px;
    background: #f8fafc;
    text-align: center;
    min-height: 250px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
}

.badge-layer {
    background-color: #ef4444;
    color: white;
    padding: 4px 8px;
    font-size: 0.75rem;
    font-weight: 700;
    border-radius: 4px;
    margin-bottom: 8px;
    display: inline-block;
}
.title-layer {
    font-size: 1.5rem;
    font-weight: 800;
    color: #0f172a;
    line-height: 1.2;
    margin-bottom: 4px;
}
.subtitle-layer {
    font-size: 0.95rem;
    color: #475569;
    margin-bottom: 12px;
}
.cta-layer {
    background-color: #2563eb;
    color: white;
    padding: 6px 12px;
    font-size: 0.85rem;
    font-weight: 600;
    border-radius: 6px;
    display: inline-block;
}

/* VIE Cards */
.vie-card {
    background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%);
    border-radius: 12px;
    padding: 14px 18px;
    margin-bottom: 12px;
    color: white;
}
.vie-card h4 { color: #a5b4fc; margin: 0 0 6px 0; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em; }
.vie-card p  { color: #e0e7ff; margin: 0; font-size: 0.9rem; line-height: 1.5; }

.score-pill {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 9999px;
    font-weight: 700;
    font-size: 0.85rem;
    margin-right: 6px;
}
.score-pass { background: #bbf7d0; color: #166534; }
.score-fail { background: #fecaca; color: #991b1b; }
.score-warn { background: #fef08a; color: #854d0e; }

.vie-status-running {
    background: linear-gradient(90deg, #312e81, #4f46e5, #312e81);
    background-size: 200% auto;
    animation: shimmer 2s linear infinite;
    border-radius: 8px;
    padding: 10px 16px;
    color: #e0e7ff;
    font-size: 0.9rem;
}
@keyframes shimmer { 0% { background-position: 0% } 100% { background-position: 200% } }
</style>
"""

# 16 Nhóm Templates
TEMPLATES_LIBRARY = {
    "split_corporate": {"name": "Business / Corporate", "desc": "Cột đôi 40/60, Navy & Gold, Outfit font.", "cat": "corporate", "icon": "🏢"},
    "ceo_leadership": {"name": "CEO Personal Brand", "desc": "Diagonal Gradient, Ruby Red, Playfair font.", "cat": "ceo", "icon": "👑"},
    "marketing_viral": {"name": "Marketing High-Conversion", "desc": "Purple-Pink Gradient, Jakarta font.", "cat": "marketing", "icon": "📣"},
    "cyber_tech": {"name": "AI / Cyber Tech", "desc": "Futuristic Slate, Cyan Glow, Orbitron font.", "cat": "ai", "icon": "🤖"},
    "growth_sales": {"name": "Sales Growth", "desc": "Urgent Red-Orange, Archivo Black font.", "cat": "sales", "icon": "💰"},
    "edu_editorial": {"name": "Education / Tutorial", "desc": "Green Mint, Merriweather serif font.", "cat": "education", "icon": "📚"},
    "case_study": {"name": "Case Study Data", "desc": "Blue & Green, Sora font, Stats focus.", "cat": "case_study", "icon": "📊"},
    "comparison": {"name": "Comparison / Versus", "desc": "Coral vs Sky 50/50 Split layout.", "cat": "comparison", "icon": "⚔️"},
    "checklist": {"name": "Checklist / Listicle", "desc": "Teal & Yellow, DM Sans minimalist.", "cat": "checklist", "icon": "☑️"},
    "infographic": {"name": "Infographic Card", "desc": "Pastel palette, flat illustrations.", "cat": "infographic", "icon": "🗺️"},
    "statistics": {"name": "Big Number Statistics", "desc": "Black & Lime, Anton font focus.", "cat": "statistics", "icon": "💯"},
    "webinar": {"name": "Webinar Event", "desc": "Live event layout, photo placeholder.", "cat": "webinar", "icon": "🎙️"},
    "breaking_news": {"name": "Breaking News Cover", "desc": "Yellow/Red background banner.", "cat": "breaking_news", "icon": "🚨"},
    "social_proof": {"name": "Social Proof Speech", "desc": "Speech bubble quote style, Lora serif.", "cat": "social_proof", "icon": "💬"},
    "product_launch": {"name": "Product Premium Launch", "desc": "Black Matte, Gold gradient Aura.", "cat": "product", "icon": "✨"},
}


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: Render Vision Score
# ─────────────────────────────────────────────────────────────────────────────

def _render_vision_score(score: float, label: str = "") -> str:
    if score >= 8.0:
        cls = "score-pass"
        icon = "✅"
    elif score >= 7.0:
        cls = "score-warn"
        icon = "⚠️"
    else:
        cls = "score-fail"
        icon = "❌"
    txt = f"{label}: {score:.1f}" if label else f"{score:.1f}"
    return f'<span class="score-pill {cls}">{icon} {txt}</span>'


def _render_vie_panel(vie_result: dict) -> None:
    """Render panel Visual Intelligence Engine Results."""
    st.markdown("---")
    st.markdown("#### 🧠 Visual Intelligence Engine Results")

    vs = vie_result.get("visual_story", {})
    vval = vie_result.get("vision_validation", {})
    ip = vie_result.get("image_prompt", {})
    ch = vie_result.get("correction_history", [])

    # Visual Story card
    if vs:
        st.markdown(f"""
<div class="vie-card">
  <h4>🎬 Visual Story</h4>
  <p><b>Theme:</b> {vs.get('main_theme', '')}</p>
  <p><b>Emotion:</b> {vs.get('target_emotion', '')} &nbsp;|&nbsp; <b>Mood:</b> {vs.get('mood', '')}</p>
  <p><b>Key Message:</b> {vs.get('key_message', '')}</p>
  <p><b>Metaphor:</b> {vs.get('visual_metaphor', '') or '—'}</p>
</div>
""", unsafe_allow_html=True)

    # Vision Score card
    if vval:
        overall = vval.get("overall_score", 0)
        passed = vval.get("passed", False)
        pills = (
            _render_vision_score(vval.get("vision_score", 0), "Visual") +
            _render_vision_score(vval.get("ai_score", 0), "AI") +
            _render_vision_score(vval.get("brand_score", 0), "Brand") +
            _render_vision_score(vval.get("emotion_score", 0), "Emotion")
        )
        status_str = "✅ ĐẠT ngưỡng" if passed else "⚠️ CHƯA ĐẠT ngưỡng"
        st.markdown(f"""
<div class="vie-card">
  <h4>👁️ Vision Validation — Overall: {overall:.1f}/10 — {status_str}</h4>
  <div style="margin-bottom:8px">{pills}</div>
  <p style="font-size:0.85rem;color:#c7d2fe">{vval.get('vlm_feedback','')[:200]}</p>
</div>
""", unsafe_allow_html=True)

    # Correction history
    if ch and len(ch) > 1:
        with st.expander(f"🔄 Self-Correction History ({len(ch)} vòng)"):
            for step in ch:
                icon = "✅" if step.get("passed") else "🔄"
                st.caption(f"{icon} Vòng {step['iteration']} — Score: {step.get('overall_score', 0):.1f} — {step.get('prompt_snippet', '')[:80]}...")

    # Image Prompt copy box
    if ip and ip.get("primary_prompt"):
        with st.expander("📋 Image Prompt (copy để dùng với Midjourney / DALL-E / FLUX)"):
            st.text_area("Primary Prompt:", value=ip.get("primary_prompt", ""), height=120, key="vie_primary_prompt_view")
            st.text_area("Secondary Prompt:", value=ip.get("secondary_prompt", ""), height=80, key="vie_secondary_prompt_view")
            st.text_area("Negative Prompt:", value=ip.get("negative_prompt", ""), height=60, key="vie_negative_prompt_view")
            style_kw = ip.get("style_keywords", [])
            if style_kw:
                st.caption("Style Keywords: " + " | ".join(style_kw))


# ─────────────────────────────────────────────────────────────────────────────
# MAIN RENDER FUNCTION
# ─────────────────────────────────────────────────────────────────────────────

def render_tab_thumbnail_studio(workspace_id: int, user_id: int, user_email: str, role: str, api_key: str):
    st.markdown(THUMBNAIL_STUDIO_CSS, unsafe_allow_html=True)

    st.markdown("""
    <div class="studio-header">
        <h2>🎨 Thumbnail Studio — Apex AI</h2>
        <p>Thiết kế, tạo, chỉnh sửa và quản lý Thumbnail chuẩn thương hiệu cho mọi nền tảng</p>
    </div>
    """, unsafe_allow_html=True)

    # ── SIDEBAR TRÁI: TEMPLATE GALLERY & HISTORY ──
    col_left, col_mid, col_right = st.columns([1, 2, 1.5], gap="medium")

    with col_left:
        st.markdown("### 📁 Template Library")
        for tid, tinfo in TEMPLATES_LIBRARY.items():
            if st.button(f"{tinfo['icon']} {tinfo['name']}", key=f"tpl_{tid}", use_container_width=True):
                st.session_state["selected_template"] = tid
                st.session_state["selected_template_info"] = tinfo
                st.success(f"Đã chọn: {tinfo['name']}")

        st.divider()
        st.markdown("### ⏱️ History & Versions")
        history_assets = AssetModel.list_by_workspace(workspace_id, file_type="image")
        thumbnail_history = []
        for asset in history_assets:
            tags = asset.get("tags", {})
            if isinstance(tags, dict) and tags.get("thumbnail", {}).get("is_thumbnail"):
                thumbnail_history.append(asset)

        if not thumbnail_history:
            st.caption("Chưa có lịch sử thiết kế.")
        else:
            for idx, th in enumerate(thumbnail_history[:5]):
                ver = th.get("tags", {}).get("lifecycle", {}).get("version", 1)
                st.markdown(f"**v{ver}** — {th['name']}")
                st.caption(f"Kênh: {th['tags'].get('thumbnail', {}).get('platform', 'N/A')}")

                # Hiển thị Vision Score trong history nếu có
                mi = th.get("tags", {}).get("media_intelligence", {})
                vs_score = mi.get("vision_score", None)
                if vs_score is not None:
                    st.caption(f"Vision Score: {vs_score:.1f}")

                if st.button("🔄 Khôi phục", key=f"restore_{th['id']}", use_container_width=True):
                    st.session_state["active_thumbnail_config"] = th["tags"].get("thumbnail_config", {})
                    st.session_state["active_thumbnail_url"] = th["url"]
                    st.session_state["active_thumbnail_version"] = ver
                    # Khôi phục cả VIE result nếu có
                    if "media_intelligence" in th.get("tags", {}):
                        st.session_state["vie_result"] = th["tags"]["media_intelligence"]
                    st.success("Đã khôi phục phiên bản!")
                    st.rerun()

    # ── CỘT GIỮA: EDITOR CANVAS & AI SETUP ──
    with col_mid:
        st.markdown("### 📝 Studio Editor")

        # ── Tabs: Classic vs VIE ──
        tab_vie, tab_classic = st.tabs(["🧠 Visual Intelligence (AI từ bài viết)", "⚙️ Cấu hình thủ công"])

        # ── TAB: VISUAL INTELLIGENCE ENGINE ──
        with tab_vie:
            st.info("🤖 VIE sẽ đọc toàn bộ bài viết, phân tích Visual Story, sinh Image Prompt chất lượng cao và tự kiểm tra Vision Score. Ảnh KHÔNG được sinh từ tiêu đề.")

            vie_article = st.text_area(
                "📄 Toàn bộ nội dung bài viết (VIE sẽ đọc và phân tích):",
                value=st.session_state.get("vie_article_cache", ""),
                height=180,
                key="vie_article_input",
                placeholder="Dán toàn bộ nội dung bài viết vào đây. AI sẽ hiểu sâu nội dung để tạo Visual Story và Image Prompt phù hợp nhất..."
            )

            vie_platform = st.selectbox(
                "Nền tảng xuất bản:",
                list(PLATFORM_DEFAULTS.keys()),
                key="vie_platform_sel"
            )

            # Cấu hình nâng cao
            with st.expander("⚙️ Cấu hình Vision Score (nâng cao)"):
                vie_threshold = st.slider(
                    "Ngưỡng Vision Score tối thiểu (0–10):",
                    min_value=5.0, max_value=9.5, value=7.5, step=0.5,
                    key="vie_threshold_slider"
                )
                vie_max_loops = st.slider(
                    "Số vòng tự sửa tối đa:",
                    min_value=1, max_value=5, value=3, step=1,
                    key="vie_max_loops_slider"
                )

            c1, c2 = st.columns(2)
            btn_vie_gen   = c1.button("🧠 Phân tích & Generate", type="primary", use_container_width=True, key="btn_vie_gen")
            btn_vie_regen = c2.button("🔄 Regenerate VIE", type="secondary", use_container_width=True, key="btn_vie_regen")

            if (btn_vie_gen or btn_vie_regen):
                if not api_key:
                    st.error("⚠️ Vui lòng cấu hình Gemini API Key!")
                elif not vie_article.strip():
                    st.error("⚠️ Vui lòng nhập nội dung bài viết!")
                else:
                    # Lưu cache bài viết
                    st.session_state["vie_article_cache"] = vie_article

                    with st.spinner("🧠 Visual Intelligence Engine đang hoạt động..."):
                        try:
                            from services.visual_intelligence_engine import VisualIntelligenceEngine

                            vie_result = VisualIntelligenceEngine.run(
                                article      = vie_article,
                                platform     = vie_platform,
                                workspace_id = workspace_id,
                                api_key      = api_key,
                                threshold    = vie_threshold,
                                max_loops    = vie_max_loops,
                            )

                            if vie_result.success:
                                # Tạo asset tags
                                asset_tags = vie_result.to_asset_tags(
                                    platform     = vie_platform,
                                    workspace_id = workspace_id,
                                )

                                # Lưu vào session state
                                st.session_state["active_thumbnail_config"] = asset_tags.get("thumbnail_config", {})
                                st.session_state["vie_result_full"] = asset_tags
                                st.session_state["vie_result"] = {
                                    "visual_story":      asset_tags.get("media_intelligence", {}).get("visual_story", {}),
                                    "vision_validation": asset_tags.get("media_intelligence", {}).get("vision_detail", {}),
                                    "image_prompt":      asset_tags.get("media_intelligence", {}).get("prompt_detail", {}),
                                    "correction_history":asset_tags.get("correction_history", []),
                                }
                                st.session_state["vie_platform"] = vie_platform

                                # Giả lập ảnh preview (sẽ được thay bằng ảnh thực từ API sau)
                                import random
                                seed = random.randint(1, 9999)
                                st.session_state["active_thumbnail_url"] = f"https://picsum.photos/seed/{seed}/1200/630"

                                # Tăng analytics
                                sel_tpl = st.session_state.get("selected_template", "split_corporate")
                                tpl_info = TEMPLATES_LIBRARY.get(sel_tpl, TEMPLATES_LIBRARY["split_corporate"])
                                ThumbnailAnalyticsModel.increment_template_usage(
                                    workspace_id   = workspace_id,
                                    template_id    = sel_tpl,
                                    platform       = vie_platform,
                                    template_name  = tpl_info["name"],
                                    template_category = tpl_info["cat"]
                                )

                                score = vie_result.vision_validation.overall_score if vie_result.vision_validation else 0
                                passed = vie_result.vision_validation.passed if vie_result.vision_validation else False
                                if passed:
                                    st.success(f"✅ VIE hoàn tất! Vision Score: {score:.1f}/10 — ĐẠT ngưỡng ({vie_result.total_iterations} vòng)")
                                else:
                                    st.warning(f"⚠️ VIE hoàn tất nhưng chưa đạt ngưỡng. Best Score: {score:.1f}/10 ({vie_result.total_iterations} vòng)")

                                st.rerun()
                            else:
                                st.error(f"❌ VIE lỗi: {vie_result.error_message}")

                        except Exception as e:
                            st.error(f"Lỗi VIE: {e}")

            # Render VIE result panel
            if "vie_result" in st.session_state:
                _render_vie_panel(st.session_state["vie_result"])

        # ── TAB: CLASSIC GENERATOR ──
        with tab_classic:
            article_content = st.text_area(
                "Nội dung bài viết / Chủ đề bài viết:",
                value="Cách chốt đơn Zalo hiệu quả không cần chạy ads — tăng tỷ lệ chuyển đổi lên 300%",
                height=100,
                key="classic_article_input"
            )

            audience_sel = st.selectbox(
                "Đối tượng mục tiêu:",
                ["Chủ shop online", "CEO / Quản lý cấp cao", "Freelancer", "Chuyên gia AI"],
                key="classic_audience"
            )

            platform_sel = st.selectbox(
                "Nền tảng xuất bản:",
                list(PLATFORM_DEFAULTS.keys()),
                key="classic_platform"
            )

            st.subheader("🤖 AI Cấu Hình Prompt")
            custom_prompt = st.text_area(
                "Yêu cầu bổ sung cho AI (Prompt tùy chỉnh):",
                value="Tạo thiết kế rực rỡ, thu hút và hiện đại.",
                height=80,
                key="classic_custom_prompt"
            )

            c1, c2 = st.columns(2)
            btn_gen   = c1.button("🤖 Generate với AI", type="primary",   use_container_width=True, key="btn_classic_gen")
            btn_regen = c2.button("🔄 Regenerate",      type="secondary", use_container_width=True, key="btn_classic_regen")

            if btn_gen or btn_regen:
                if not api_key:
                    st.error("⚠️ Vui lòng cấu hình Gemini API Key ở thanh bên trái!")
                else:
                    with st.spinner("AI đang thiết kế và sinh cấu hình..."):
                        res = ThumbnailGeneratorService.generate(
                            workspace_id = workspace_id,
                            article      = article_content + "\n" + custom_prompt,
                            audience     = audience_sel,
                            platform     = platform_sel,
                            api_key      = api_key
                        )

                        if "error" in res:
                            st.error(res["error"])
                        else:
                            st.session_state["active_thumbnail_config"] = res
                            import random
                            seed = random.randint(1, 1000)
                            st.session_state["active_thumbnail_url"] = f"https://picsum.photos/seed/{seed}/1200/630"
                            st.success("Đã sinh cấu hình Thumbnail thành công!")

                            sel_tpl = st.session_state.get("selected_template", "split_corporate")
                            tpl_info = TEMPLATES_LIBRARY.get(sel_tpl, TEMPLATES_LIBRARY["split_corporate"])
                            ThumbnailAnalyticsModel.increment_template_usage(
                                workspace_id      = workspace_id,
                                template_id       = sel_tpl,
                                platform          = platform_sel,
                                template_name     = tpl_info["name"],
                                template_category = tpl_info["cat"]
                            )
                            st.rerun()

        # ── Text Overlay Editor (chung cho cả 2 tab) ──
        if "active_thumbnail_config" in st.session_state:
            cfg = st.session_state["active_thumbnail_config"]
            st.subheader("🎨 Điều chỉnh các lớp văn bản & thiết kế")

            overlay = cfg.setdefault("text_overlay", {})
            title_text    = st.text_input("Tiêu đề trên ảnh:", value=overlay.get("title", "TIÊU ĐỀ THUMBNAIL"), key="overlay_title")
            subtitle_text = st.text_input("Tiêu đề phụ:",      value=overlay.get("subtitle", ""),             key="overlay_subtitle")
            badge_text    = st.text_input("Badge nổi bật:",     value=overlay.get("badge", ""),               key="overlay_badge")
            cta_text      = st.text_input("CTA Button:",        value=overlay.get("cta", ""),                 key="overlay_cta")

            overlay["title"]    = title_text
            overlay["subtitle"] = subtitle_text
            overlay["badge"]    = badge_text
            overlay["cta"]      = cta_text

    # ── CỘT PHẢI: LIVE PREVIEW & EXPORT ──
    with col_right:
        st.markdown("### 👁️ Live Preview")

        if "active_thumbnail_config" not in st.session_state:
            st.markdown(
                '<div class="live-preview-box">Chọn mẫu và nhấp nút "Generate" để xem trước thiết kế</div>',
                unsafe_allow_html=True
            )
        else:
            cfg     = st.session_state["active_thumbnail_config"]
            img_url = st.session_state.get("active_thumbnail_url", "")

            st.markdown("##### 🖥️ Thiết kế trực quan:")

            overlay = cfg.get("text_overlay", {})
            badge_html    = f'<div class="badge-layer">{overlay.get("badge", "")}</div>'   if overlay.get("badge")    else ""
            subtitle_html = f'<div class="subtitle-layer">{overlay.get("subtitle", "")}</div>' if overlay.get("subtitle") else ""
            cta_html      = f'<div class="cta-layer">{overlay.get("cta", "XEM NGAY")}</div>' if overlay.get("cta")     else ""

            st.markdown(
                f"""
                <div style="background-image: url('{img_url}'); background-size: cover; background-position: center; border-radius: 12px; padding: 24px; min-height: 280px; display: flex; flex-direction: column; justify-content: flex-end; align-items: flex-start; color: white; box-shadow: 0 4px 10px rgba(0,0,0,0.15);">
                    <div style="background: rgba(255,255,255,0.92); border-radius: 8px; padding: 12px 16px; width: 100%; box-sizing: border-box;">
                        {badge_html}
                        <div class="title-layer">{overlay.get("title", "")}</div>
                        {subtitle_html}
                        {cta_html}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Hiển thị Vision Score tóm tắt ở preview nếu có
            vie_res = st.session_state.get("vie_result", {})
            vval = vie_res.get("vision_validation", {})
            if vval and vval.get("overall_score"):
                score  = vval["overall_score"]
                passed = vval.get("passed", False)
                pill   = _render_vision_score(score, "Vision Score Overall")
                st.markdown(f"<div style='margin-top:8px'>{pill}</div>", unsafe_allow_html=True)

            # Form export / lưu trữ
            st.divider()
            st.subheader("📥 Export & Save")
            platform_for_save = st.session_state.get("vie_platform", list(PLATFORM_DEFAULTS.keys())[0])
            export_name = st.text_input(
                "Tên Thumbnail:",
                value=f"Thumbnail_{platform_for_save}_{datetime.now().strftime('%d%m_%H%M')}",
                key="export_name_input"
            )

            c_save, c_dl = st.columns(2)
            if c_save.button("💾 Lưu vào Media Library", type="primary", use_container_width=True, key="btn_save_asset"):
                current_ver  = st.session_state.get("active_thumbnail_version", 0) + 1

                # Ưu tiên dùng VIE result tags nếu có
                if "vie_result_full" in st.session_state:
                    asset_tags = st.session_state["vie_result_full"]
                    asset_tags["lifecycle"]["version"] = current_ver
                    asset_tags["thumbnail_config"]["text_overlay"] = cfg.get("text_overlay", {})
                else:
                    asset_tags = {
                        "thumbnail": {
                            "is_thumbnail": True,
                            "platform":     platform_for_save,
                        },
                        "lifecycle": {
                            "status":  "draft",
                            "version": current_ver,
                        },
                        "thumbnail_config": cfg
                    }

                new_asset_id = AssetModel.create(
                    workspace_id = workspace_id,
                    name         = export_name,
                    url          = img_url,
                    file_type    = "image",
                    tags         = asset_tags,
                    uploaded_by  = user_id
                )

                st.session_state["active_thumbnail_version"] = current_ver
                st.success(f"✅ Đã lưu Asset #{new_asset_id} (v{current_ver}) vào Media Library!")
                st.rerun()

            c_dl.markdown(
                f'<a href="{img_url}" target="_blank"><button style="width:100%; background-color:#16a34a; color:white; border:none; padding:8px; border-radius:8px; font-weight:bold; cursor:pointer;">📥 Tải Ảnh Gốc</button></a>',
                unsafe_allow_html=True
            )
