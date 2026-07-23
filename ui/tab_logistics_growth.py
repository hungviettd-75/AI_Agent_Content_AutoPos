"""Logistics Sales & Marketing Growth Center.

This tab adds lightweight sales pipeline, lead scoring, campaign funnel, and
sales enablement workflows for logistics businesses without changing database
schema. Leads live in the Streamlit session and can be imported/exported as CSV.
"""

from __future__ import annotations

from datetime import date, timedelta
from io import StringIO

import pandas as pd
import streamlit as st

from config.logistics_vertical import (
    LOGISTICS_ANGLES,
    LOGISTICS_DEFAULT_CTA,
    LOGISTICS_PILLAR_BANK,
    LOGISTICS_TARGETS,
)
from database.models.posts import PostModel

PIPELINE_STAGES = [
    "New Lead",
    "Qualified",
    "Needs Analysis",
    "Proposal Sent",
    "Negotiation",
    "Won",
    "Lost",
]

LOGISTICS_SEGMENTS = [
    "E-commerce / Chủ shop online",
    "B2B Manufacturing",
    "Retail Chain",
    "Importer / Exporter",
    "Marketplace Seller",
    "F&B / Cold Chain",
    "SME cần vận chuyển nội địa",
]

PAIN_POINTS = [
    "Chi phí vận chuyển cao",
    "Tỷ lệ giao thất bại cao",
    "Không theo dõi SLA realtime",
    "Kho xử lý đơn chậm",
    "Khó kiểm soát hoàn hàng",
    "Mùa cao điểm quá tải",
    "Thiếu báo cáo cho khách B2B",
]

CAMPAIGN_TYPES = [
    "Lead Magnet",
    "LinkedIn B2B Thought Leadership",
    "Facebook Case Study",
    "Zalo Follow-up / CSKH",
    "Retargeting Content",
    "Proposal Nurture",
]


def _growth_key(workspace_id: int | None, name: str) -> str:
    return f"logistics_growth_{workspace_id or 'none'}_{name}"


def _sample_leads() -> pd.DataFrame:
    today = date.today()
    return pd.DataFrame([
        {
            "company": "Shop thời trang tăng trưởng nhanh",
            "segment": "E-commerce / Chủ shop online",
            "contact_role": "Founder",
            "need": "Giảm hoàn hàng và giao thất bại",
            "monthly_shipments": 4500,
            "pain_point": "Tỷ lệ giao thất bại cao",
            "source_channel": "Facebook Case Study",
            "stage": "Qualified",
            "next_follow_up": (today + timedelta(days=1)).isoformat(),
            "notes": "Quan tâm fulfillment mùa sale.",
        },
        {
            "company": "Nhà máy linh kiện B2B",
            "segment": "B2B Manufacturing",
            "contact_role": "Supply Chain Manager",
            "need": "Báo cáo SLA giao hàng cho khách B2B",
            "monthly_shipments": 1200,
            "pain_point": "Thiếu báo cáo cho khách B2B",
            "source_channel": "LinkedIn B2B Thought Leadership",
            "stage": "Needs Analysis",
            "next_follow_up": (today + timedelta(days=2)).isoformat(),
            "notes": "Cần demo dashboard vận hành.",
        },
        {
            "company": "Chuỗi F&B giao lạnh",
            "segment": "F&B / Cold Chain",
            "contact_role": "Operations Manager",
            "need": "Kiểm soát SLA và nhiệt độ giao nhận",
            "monthly_shipments": 800,
            "pain_point": "Không theo dõi SLA realtime",
            "source_channel": "Zalo Follow-up / CSKH",
            "stage": "Proposal Sent",
            "next_follow_up": (today + timedelta(days=3)).isoformat(),
            "notes": "Đang so sánh với nhà cung cấp hiện tại.",
        },
    ])


def _score_lead(row: pd.Series) -> int:
    score = 20
    shipments = int(row.get("monthly_shipments") or 0)
    if shipments >= 5000:
        score += 30
    elif shipments >= 1000:
        score += 22
    elif shipments >= 300:
        score += 12
    role = str(row.get("contact_role", "")).lower()
    if any(token in role for token in ["ceo", "founder", "owner", "procurement", "supply chain", "operations"]):
        score += 18
    pain = str(row.get("pain_point", ""))
    if pain in {"Chi phí vận chuyển cao", "Tỷ lệ giao thất bại cao", "Không theo dõi SLA realtime"}:
        score += 18
    stage = str(row.get("stage", ""))
    score += {
        "New Lead": 0,
        "Qualified": 8,
        "Needs Analysis": 12,
        "Proposal Sent": 16,
        "Negotiation": 20,
        "Won": 25,
        "Lost": -20,
    }.get(stage, 0)
    return max(0, min(100, score))


def _next_action(row: pd.Series) -> str:
    stage = str(row.get("stage", "New Lead"))
    pain = str(row.get("pain_point", "điểm nghẽn logistics"))
    actions = {
        "New Lead": f"Gửi checklist audit {pain.lower()} và hỏi khối lượng đơn/tháng.",
        "Qualified": "Hẹn 20 phút discovery call để bóc tách chi phí, SLA, hoàn hàng và quy trình hiện tại.",
        "Needs Analysis": "Chuẩn bị mini proposal: pain point, baseline KPI, giải pháp, timeline 30 ngày.",
        "Proposal Sent": "Follow-up bằng case study tương tự và bảng so sánh tổng chi phí sở hữu.",
        "Negotiation": "Chốt pilot 30 ngày với KPI rõ: SLA, tỷ lệ giao thành công, chi phí/đơn.",
        "Won": "Chuyển sang onboarding, thu thập dữ liệu, lên lịch case study sau 45 ngày.",
        "Lost": "Đưa vào nurture 60 ngày với nội dung ROI và checklist vận hành.",
    }
    return actions.get(stage, actions["New Lead"])


def _sales_script(row: pd.Series, channel: str) -> str:
    company = row.get("company", "doanh nghiệp của anh/chị")
    pain = row.get("pain_point", "chi phí logistics")
    need = row.get("need", "tối ưu vận hành logistics")
    role = row.get("contact_role", "anh/chị")
    if channel == "LinkedIn":
        return (
            f"Chào anh/chị {role}, tôi thấy nhiều doanh nghiệp giống {company} đang gặp bài toán {pain.lower()}.\n\n"
            f"Điểm đáng chú ý là vấn đề này thường không chỉ nằm ở giá vận chuyển, mà nằm ở SLA, hoàn hàng, dữ liệu tuyến và thời gian xử lý đơn.\n\n"
            f"Bên tôi có một checklist giúp rà soát nhanh {need.lower()} trong 15 phút. Anh/chị muốn tôi gửi bản checklist không?"
        )
    if channel == "Zalo":
        return (
            f"Chào anh/chị, em gửi nhanh 1 checklist kiểm tra {pain.lower()} cho {company}.\n\n"
            "Checklist này giúp nhìn ra đơn đang thất thoát ở khâu giao, kho hay chăm sóc khách.\n\n"
            "Anh/chị muốn em gửi bản mẫu để đội vận hành tự rà trong tuần này không?"
        )
    return (
        f"Nếu {company} đang muốn {need.lower()}, điểm đầu tiên nên đo không phải là giá/đơn.\n\n"
        f"Hãy nhìn vào {pain.lower()}, SLA, tỷ lệ giao thành công và chi phí hoàn hàng.\n\n"
        "Một bảng audit đơn giản có thể cho thấy doanh nghiệp đang mất tiền ở đâu.\n\n"
        f"{LOGISTICS_DEFAULT_CTA}"
    )


def _campaign_plan(segment: str, campaign_type: str, pain_point: str, days: int) -> pd.DataFrame:
    pillars = list(LOGISTICS_PILLAR_BANK.keys())
    rows = []
    for idx in range(days):
        pillar = pillars[idx % len(pillars)]
        topic = LOGISTICS_PILLAR_BANK[pillar][idx % len(LOGISTICS_PILLAR_BANK[pillar])]
        angle = LOGISTICS_ANGLES[idx % len(LOGISTICS_ANGLES)]
        platform = ["LinkedIn", "Facebook", "Zalo"][idx % 3]
        funnel = ["Awareness", "Consideration", "Conversion", "Nurture"][idx % 4]
        rows.append({
            "Ngày": (date.today() + timedelta(days=idx)).isoformat(),
            "Kênh": platform,
            "Funnel": funnel,
            "Campaign": campaign_type,
            "Segment": segment,
            "Pain point": pain_point,
            "Chủ đề": f"{topic}: {angle}",
            "CTA": "Tải checklist" if funnel == "Awareness" else "Đặt lịch audit 20 phút" if funnel == "Conversion" else "Nhắn Zalo để nhận tư vấn",
        })
    return pd.DataFrame(rows)


def render_tab_logistics_growth(gemini_key: str = "", workspace_id: int = 1, role: str = "editor", user_id: int | None = None):
    del gemini_key
    can_edit = (role or "viewer").lower() != "viewer"
    leads_key = _growth_key(workspace_id, "leads")
    campaign_key = _growth_key(workspace_id, "campaign")

    if leads_key not in st.session_state:
        st.session_state[leads_key] = _sample_leads()

    st.markdown("### AI Sales & Marketing Growth Platform for Logistics")
    st.caption("Quản lý lead, chấm điểm cơ hội, tạo campaign funnel và kịch bản follow-up cho dịch vụ vận chuyển, fulfillment, kho bãi và tối ưu logistics.")

    tabs = st.tabs(["Lead Pipeline", "Lead Scoring", "Campaign Funnel", "Sales Scripts", "Growth Dashboard"])

    with tabs[0]:
        st.markdown("##### Logistics Lead Pipeline")
        upload = st.file_uploader("Import lead CSV", type=["csv"], key=f"{leads_key}_upload", disabled=not can_edit)
        if upload is not None and can_edit:
            imported = pd.read_csv(upload)
            required = ["company", "segment", "contact_role", "need", "monthly_shipments", "pain_point", "source_channel", "stage", "next_follow_up", "notes"]
            for col in required:
                if col not in imported.columns:
                    imported[col] = "" if col != "monthly_shipments" else 0
            st.session_state[leads_key] = imported[required]
            st.success(f"Đã import {len(imported)} leads.")

        df = st.session_state[leads_key].copy()
        edited = st.data_editor(
            df,
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic" if can_edit else "fixed",
            disabled=not can_edit,
            column_config={
                "segment": st.column_config.SelectboxColumn("segment", options=LOGISTICS_SEGMENTS),
                "pain_point": st.column_config.SelectboxColumn("pain_point", options=PAIN_POINTS),
                "stage": st.column_config.SelectboxColumn("stage", options=PIPELINE_STAGES),
                "source_channel": st.column_config.SelectboxColumn("source_channel", options=CAMPAIGN_TYPES),
                "monthly_shipments": st.column_config.NumberColumn("monthly_shipments", min_value=0, step=100),
            },
            key=f"{leads_key}_editor",
        )
        if can_edit:
            st.session_state[leads_key] = edited

        csv = edited.to_csv(index=False).encode("utf-8-sig")
        st.download_button("Export lead pipeline CSV", csv, "logistics_lead_pipeline.csv", "text/csv", use_container_width=True, key=f"{leads_key}_download")

    with tabs[1]:
        st.markdown("##### Lead Scoring & Next Best Action")
        df = st.session_state[leads_key].copy()
        if df.empty:
            st.info("Chưa có lead để chấm điểm.")
        else:
            df["score"] = df.apply(_score_lead, axis=1)
            df["priority"] = pd.cut(df["score"], bins=[-1, 49, 74, 100], labels=["Low", "Medium", "High"])
            df["next_best_action"] = df.apply(_next_action, axis=1)
            st.dataframe(df[["company", "segment", "contact_role", "stage", "pain_point", "monthly_shipments", "score", "priority", "next_best_action"]].sort_values("score", ascending=False), use_container_width=True, hide_index=True)

    with tabs[2]:
        st.markdown("##### Campaign Funnel Builder")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            segment = st.selectbox("Segment", LOGISTICS_SEGMENTS, key=f"{campaign_key}_segment")
        with c2:
            campaign_type = st.selectbox("Campaign type", CAMPAIGN_TYPES, key=f"{campaign_key}_type")
        with c3:
            pain_point = st.selectbox("Pain point", PAIN_POINTS, key=f"{campaign_key}_pain")
        with c4:
            campaign_days = st.number_input("Số ngày", min_value=7, max_value=60, value=14, key=f"{campaign_key}_days")
        if st.button("Tạo campaign funnel", type="primary", use_container_width=True, key=f"{campaign_key}_generate"):
            st.session_state[campaign_key] = _campaign_plan(segment, campaign_type, pain_point, int(campaign_days))
            st.success("Đã tạo campaign funnel.")
        plan = st.session_state.get(campaign_key)
        if isinstance(plan, pd.DataFrame) and not plan.empty:
            st.dataframe(plan, use_container_width=True, hide_index=True)
            st.download_button("Export campaign CSV", plan.to_csv(index=False).encode("utf-8-sig"), "logistics_campaign_funnel.csv", "text/csv", use_container_width=True, key=f"{campaign_key}_download")
            if st.button("Lưu 5 chủ đề đầu vào Draft Posts", disabled=not can_edit, use_container_width=True, key=f"{campaign_key}_save_posts"):
                created = 0
                for _, row in plan.head(5).iterrows():
                    content = f"Campaign: {row['Campaign']}\nSegment: {row['Segment']}\nPain point: {row['Pain point']}\nFunnel: {row['Funnel']}\nCTA: {row['CTA']}"
                    platform = str(row["Kênh"]).lower()
                    PostModel.create(
                        content=content,
                        platform="linkedin" if platform == "linkedin" else "facebook" if platform == "facebook" else "zalo",
                        content_type="marketing_viral",
                        topic=row["Chủ đề"],
                        title=str(row["Chủ đề"])[:80],
                        status="draft",
                        workspace_id=workspace_id,
                        created_by=user_id,
                        ai_metadata={"source": "logistics_growth_campaign", "funnel": row["Funnel"], "campaign": row["Campaign"]},
                    )
                    created += 1
                st.success(f"Đã lưu {created} campaign drafts.")

    with tabs[3]:
        st.markdown("##### Sales Scripts Generator")
        df = st.session_state[leads_key].copy()
        if df.empty:
            st.info("Thêm lead ở tab Lead Pipeline để tạo script theo từng khách.")
        else:
            lead_idx = st.selectbox("Chọn lead", options=list(range(len(df))), format_func=lambda i: f"{df.iloc[i]['company']} - {df.iloc[i]['stage']}", key=f"{leads_key}_script_lead")
            channel = st.selectbox("Kênh", ["LinkedIn", "Zalo", "Facebook"], key=f"{leads_key}_script_channel")
            script = _sales_script(df.iloc[lead_idx], channel)
            st.text_area("Script đề xuất", value=script, height=220, key=f"{leads_key}_script_text")
            if st.button("Lưu script vào Draft Posts", disabled=not can_edit, use_container_width=True, key=f"{leads_key}_save_script"):
                row = df.iloc[lead_idx]
                PostModel.create(
                    content=script,
                    platform=channel.lower() if channel != "Zalo" else "zalo",
                    content_type="marketing_viral",
                    topic=f"Sales follow-up - {row['company']}",
                    title=f"Sales follow-up - {row['company']}"[:80],
                    status="draft",
                    workspace_id=workspace_id,
                    created_by=user_id,
                    ai_metadata={"source": "logistics_growth_sales_script", "lead_company": row["company"], "stage": row["stage"]},
                )
                st.success("Đã lưu sales script vào draft posts.")

    with tabs[4]:
        st.markdown("##### Growth Dashboard")
        df = st.session_state[leads_key].copy()
        if df.empty:
            st.info("Chưa có dữ liệu lead.")
        else:
            df["score"] = df.apply(_score_lead, axis=1)
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total leads", len(df))
            m2.metric("High-score leads", int((df["score"] >= 75).sum()))
            m3.metric("Open pipeline", int(df[~df["stage"].isin(["Won", "Lost"])].shape[0]))
            m4.metric("Avg score", round(float(df["score"].mean()), 1))
            stage_counts = df["stage"].value_counts().reindex(PIPELINE_STAGES, fill_value=0).reset_index()
            stage_counts.columns = ["Stage", "Leads"]
            st.bar_chart(stage_counts, x="Stage", y="Leads", use_container_width=True)
            st.markdown("##### Growth Operating Rhythm")
            st.markdown("- Mỗi tuần tạo 1 campaign funnel theo segment ưu tiên.\n- Mỗi ngày xử lý lead High-score trước.\n- Mỗi proposal phải gắn KPI: SLA, giao thành công, chi phí/đơn, hoàn hàng.\n- Mỗi khách Won cần tạo case study sau 45-60 ngày để quay lại Marketing.")
