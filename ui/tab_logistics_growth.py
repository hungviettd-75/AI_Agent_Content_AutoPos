"""Logistics Sales & Marketing Growth Center.

This tab adds lightweight sales pipeline, lead scoring, campaign funnel, and
sales enablement workflows for logistics businesses without changing database
schema. Leads live in the Streamlit session and can be imported/exported as CSV.
"""

from __future__ import annotations

from datetime import date, timedelta
from io import StringIO
import re
from urllib.parse import quote_plus
import unicodedata

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

FREIGHT_MODES = ["Air Freight", "Sea Freight LCL", "Sea Freight FCL 20ft", "Sea Freight FCL 40ft", "Road / Cross-border"]

SERVICE_LEVELS = ["Economy", "Standard", "Express", "Priority"]

COUNTRY_ZONES = {
    "Việt Nam": "ASEAN",
    "Thái Lan": "ASEAN",
    "Singapore": "ASEAN",
    "Malaysia": "ASEAN",
    "Indonesia": "ASEAN",
    "Trung Quốc": "East Asia",
    "Hàn Quốc": "East Asia",
    "Nhật Bản": "East Asia",
    "Ấn Độ": "South Asia",
    "Hoa Kỳ": "North America",
    "Canada": "North America",
    "Đức": "Europe",
    "Pháp": "Europe",
    "Anh": "Europe",
    "Úc": "Oceania",
}

TRACKING_CARRIERS = {
    "DHL": "https://www.dhl.com/global-en/home/tracking/tracking-express.html?submit=1&tracking-id={tracking}",
    "FedEx": "https://www.fedex.com/fedextrack/?trknbr={tracking}",
    "UPS": "https://www.ups.com/track?tracknum={tracking}",
    "USPS": "https://tools.usps.com/go/TrackConfirmAction?tLabels={tracking}",
    "Vietnam Post": "https://www.vnpost.vn/vi-vn/dinh-vi/buu-pham?key={tracking}",
    "17TRACK": "https://t.17track.net/en#nums={tracking}",
}

CARGO_TYPES = {
    "Hàng thường": {"risk": 1.0, "duty": 0.05, "handling": 1.0},
    "Hàng điện tử": {"risk": 1.12, "duty": 0.08, "handling": 1.08},
    "Thời trang / may mặc": {"risk": 0.98, "duty": 0.12, "handling": 1.0},
    "Mỹ phẩm": {"risk": 1.18, "duty": 0.18, "handling": 1.12},
    "Thực phẩm khô": {"risk": 1.2, "duty": 0.1, "handling": 1.15},
    "Hàng lạnh / cold chain": {"risk": 1.45, "duty": 0.08, "handling": 1.35},
    "Máy móc / phụ tùng": {"risk": 1.08, "duty": 0.06, "handling": 1.1},
    "Hàng dễ vỡ": {"risk": 1.22, "duty": 0.07, "handling": 1.2},
}

INCOTERMS = ["EXW", "FOB", "FCA", "CFR", "CIF", "DAP", "DDP"]

DELIVERY_WINDOWS = ["Tiết kiệm", "Cân bằng", "Nhanh", "Gấp"]

FREIGHT_CARRIERS = [
    {"carrier": "DHL Express", "mode": "Air", "base_rate": 4.9, "speed": 1.85, "reliability": 96, "best_for": "Hàng nhỏ, cần giao nhanh, tracking mạnh"},
    {"carrier": "FedEx International", "mode": "Air", "base_rate": 4.65, "speed": 1.72, "reliability": 94, "best_for": "B2B quốc tế, hàng giá trị cao"},
    {"carrier": "UPS Worldwide", "mode": "Air", "base_rate": 4.45, "speed": 1.62, "reliability": 93, "best_for": "Tuyến US/EU ổn định"},
    {"carrier": "Maersk LCL", "mode": "Sea LCL", "base_rate": 88, "speed": 0.72, "reliability": 90, "best_for": "CBM lớn, tối ưu chi phí"},
    {"carrier": "CMA CGM LCL", "mode": "Sea LCL", "base_rate": 82, "speed": 0.68, "reliability": 88, "best_for": "Hàng không gấp, tuyến biển"},
    {"carrier": "Kuehne+Nagel Road/Air", "mode": "Hybrid", "base_rate": 2.95, "speed": 1.12, "reliability": 91, "best_for": "Cân bằng chi phí và thời gian"},
]


HS_CODE_LIBRARY = [
    {
        "keywords": ["ca phe rang", "roasted coffee", "coffee roasted"],
        "hs_code": "0901.21",
        "description": "Roasted coffee, not decaffeinated",
        "duty": "VN export duty: usually 0%. Import duty depends on destination tariff.",
        "vat": "Vietnam VAT: usually 8-10% depending invoice context; destination VAT/GST applies on import.",
        "fta": "Check AJCEP/VJEPA/CPTPP/EVFTA/RCEP by destination and C/O form.",
        "documents": "Commercial Invoice, Packing List, Sales Contract, Customs Declaration, C/O if claiming FTA, food safety/phytosanitary docs when required.",
        "restrictions": "Food labeling, phytosanitary/food safety checks, origin and ingredient traceability may be required.",
    },
    {
        "keywords": ["xoai", "mango", "fresh mango"],
        "hs_code": "0804.50",
        "description": "Guavas, mangoes and mangosteens, fresh or dried",
        "duty": "VN export duty: usually 0%. Destination import duty depends on market and FTA.",
        "vat": "VAT/GST is assessed by destination market on import basis.",
        "fta": "Japan route: check VJEPA/AJCEP/CPTPP eligibility and C/O form.",
        "documents": "Commercial Invoice, Packing List, Phytosanitary Certificate, C/O, export customs declaration, treatment certificate if required.",
        "restrictions": "Fresh fruit may need approved orchards/packing houses, pest treatment, quarantine inspection and cold-chain control.",
    },
    {
        "keywords": ["may mac", "ao thun", "garment", "t shirt", "clothing"],
        "hs_code": "6109.10",
        "description": "T-shirts, singlets and other vests, knitted or crocheted, of cotton",
        "duty": "Duty varies by destination; FTA can materially reduce tariff if origin rules are met.",
        "vat": "Destination VAT/GST normally applies on import.",
        "fta": "Check CPTPP/EVFTA/RCEP and rules of origin for fabric/yarn-forward requirements.",
        "documents": "Invoice, Packing List, C/O, Bill of Lading/Air Waybill, customs declaration, product labels.",
        "restrictions": "Labeling, fiber composition, brand/IP checks and restricted chemical rules may apply.",
    },
]

CUSTOMS_DOCUMENTS = {
    "Invoice": "Shows seller, buyer, product, quantity, unit price, total value, currency and Incoterms.",
    "Packing List": "Shows cartons, dimensions, weights, marks and packing details.",
    "CO": "Certificate of Origin used to support preferential tariff claims.",
    "COO": "Country of Origin evidence; often part of the same origin package as C/O depending market wording.",
    "Bill of Lading": "Ocean transport document for sea shipments.",
    "Air Waybill": "Air transport document for air shipments.",
}

EXPORT_MARKET_RULES = {
    "japan": {
        "allowed": "Generally possible if the product meets Japan import, quarantine and food safety rules.",
        "documents": "Invoice, Packing List, Phytosanitary Certificate, C/O, customs declaration, treatment certificate and cold-chain records when applicable.",
        "tax": "Import duty depends on HS code and FTA claim; consumption tax is usually assessed at import.",
        "quarantine": "Fresh fruit normally requires plant quarantine inspection and may require approved treatment/packing protocol.",
        "timeline": "Air: 2-5 days door/airport. Sea cold chain: about 10-18 days depending port pair.",
        "ports": "Vietnam: Cat Lai, Cai Mep, Noi Bai, Tan Son Nhat. Japan: Tokyo/Yokohama, Osaka/Kobe, Narita, Haneda, Kansai.",
        "carriers": "Air for fresh mango: ANA Cargo, JAL Cargo, DHL/FedEx for samples. Sea reefer: ONE, Maersk, CMA CGM.",
        "freight": "Indicative: air USD 3.5-6.5/kg; reefer/LCL varies by season, CBM, temperature and surcharge.",
    }
}


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


def _sample_shipments() -> pd.DataFrame:
    today = date.today()
    rows = []
    samples = [
        ("SHP-2607-001", "Minh An Coffee", "Viet Nam", "Japan", "DHL Express", "Air Freight", 860, 3, 3, "Delivered"),
        ("SHP-2607-002", "Lotus Fashion", "Viet Nam", "United States", "FedEx International", "Air Freight", 1420, 5, 6, "In Transit"),
        ("SHP-2607-003", "Saigon Parts", "Viet Nam", "Germany", "UPS Worldwide", "Air Freight", 1980, 5, 5, "Delivered"),
        ("SHP-2607-004", "Mekong Foods", "Viet Nam", "Singapore", "DHL Express", "Air Freight", 520, 2, 2, "Delivered"),
        ("SHP-2607-005", "Nova Retail", "Viet Nam", "Canada", "Kuehne+Nagel Road/Air", "Hybrid", 1240, 8, 10, "Delayed"),
        ("SHP-2607-006", "Blue Ocean Import", "Viet Nam", "Australia", "CMA CGM LCL", "Sea LCL", 3120, 22, 24, "In Transit"),
        ("SHP-2607-007", "An Phu Electronics", "Viet Nam", "South Korea", "FedEx International", "Air Freight", 930, 4, 4, "Delivered"),
        ("SHP-2607-008", "Green Farm Export", "Viet Nam", "Japan", "Maersk LCL", "Sea LCL", 2680, 18, 21, "Delayed"),
        ("SHP-2607-009", "Urban Home", "Viet Nam", "France", "UPS Worldwide", "Air Freight", 1760, 6, 7, "In Transit"),
        ("SHP-2607-010", "Binh Minh Trading", "Viet Nam", "Singapore", "DHL Express", "Air Freight", 610, 2, 2, "Delivered"),
        ("SHP-2607-011", "Vina Textile", "Viet Nam", "Germany", "Maersk LCL", "Sea LCL", 3450, 24, 27, "Delayed"),
        ("SHP-2607-012", "Asia Marketplace", "Viet Nam", "United States", "FedEx International", "Air Freight", 1510, 5, 5, "Delivered"),
    ]
    for idx, item in enumerate(samples):
        shipment_id, customer, origin, destination, carrier, mode, cost, planned_eta, actual_eta, status = item
        ship_date = today - timedelta(days=58 - idx * 5)
        rows.append({
            "shipment_id": shipment_id,
            "customer": customer,
            "origin_country": origin,
            "destination_country": destination,
            "carrier": carrier,
            "mode": mode,
            "ship_date": ship_date.isoformat(),
            "month": ship_date.strftime("%Y-%m"),
            "shipping_cost_usd": cost,
            "planned_eta_days": planned_eta,
            "actual_eta_days": actual_eta,
            "status": status,
        })
    return pd.DataFrame(rows)


def _prepare_shipping_dashboard(df: pd.DataFrame) -> pd.DataFrame:
    prepared = df.copy()
    required_defaults = {
        "shipment_id": "",
        "customer": "",
        "origin_country": "",
        "destination_country": "",
        "carrier": "",
        "mode": "",
        "ship_date": date.today().isoformat(),
        "status": "In Transit",
    }
    for col, default in required_defaults.items():
        if col not in prepared.columns:
            prepared[col] = default
    for col in ["shipping_cost_usd", "planned_eta_days", "actual_eta_days"]:
        prepared[col] = pd.to_numeric(prepared.get(col, 0), errors="coerce").fillna(0)
    ship_dates = pd.to_datetime(prepared["ship_date"], errors="coerce")
    if "month" not in prepared.columns:
        prepared["month"] = "Unknown"
    prepared["month"] = ship_dates.dt.strftime("%Y-%m").fillna(prepared["month"])
    prepared["is_late"] = prepared["actual_eta_days"] > prepared["planned_eta_days"]
    prepared["delay_days"] = (prepared["actual_eta_days"] - prepared["planned_eta_days"]).clip(lower=0)
    return prepared


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



def _zone_distance_factor(origin: str, destination: str) -> float:
    if origin == destination:
        return 0.65
    origin_zone = COUNTRY_ZONES.get(origin, "Other")
    destination_zone = COUNTRY_ZONES.get(destination, "Other")
    if origin_zone == destination_zone:
        return 1.0
    pair = {origin_zone, destination_zone}
    if pair & {"North America", "Europe", "Oceania"}:
        return 2.35
    if pair & {"East Asia", "South Asia"}:
        return 1.45
    return 1.75


def _service_multiplier(service_level: str) -> float:
    return {
        "Economy": 0.86,
        "Standard": 1.0,
        "Express": 1.28,
        "Priority": 1.55,
    }.get(service_level, 1.0)


def _freight_quote(
    origin: str,
    destination: str,
    mode: str,
    service_level: str,
    gross_weight_kg: float,
    volume_cbm: float,
    cargo_value_usd: float,
    include_insurance: bool,
    include_customs: bool,
) -> dict[str, float | str]:
    gross_weight_kg = max(float(gross_weight_kg or 0), 0.0)
    volume_cbm = max(float(volume_cbm or 0), 0.0)
    cargo_value_usd = max(float(cargo_value_usd or 0), 0.0)
    distance_factor = _zone_distance_factor(origin, destination)
    service_factor = _service_multiplier(service_level)

    if mode == "Air Freight":
        chargeable_weight = max(gross_weight_kg, volume_cbm * 167)
        freight = 2.8 * chargeable_weight * distance_factor * service_factor
        eta = "2-5 ngày"
    elif mode == "Sea Freight LCL":
        chargeable_weight = max(gross_weight_kg / 1000, volume_cbm)
        freight = 62 * chargeable_weight * distance_factor * service_factor + 45
        eta = "14-32 ngày"
    elif mode == "Sea Freight FCL 20ft":
        chargeable_weight = 1
        freight = 1150 * distance_factor * service_factor
        eta = "18-35 ngày"
    elif mode == "Sea Freight FCL 40ft":
        chargeable_weight = 1
        freight = 1850 * distance_factor * service_factor
        eta = "18-35 ngày"
    else:
        chargeable_weight = max(gross_weight_kg / 250, volume_cbm)
        freight = 95 * chargeable_weight * distance_factor * service_factor + 35
        eta = "3-12 ngày"

    origin_fee = 38 if mode == "Air Freight" else 65
    destination_fee = 42 if mode == "Air Freight" else 70
    customs_fee = 55 if include_customs else 0
    insurance_fee = cargo_value_usd * 0.006 if include_insurance else 0
    total = freight + origin_fee + destination_fee + customs_fee + insurance_fee

    return {
        "origin": origin,
        "destination": destination,
        "mode": mode,
        "service_level": service_level,
        "chargeable_weight": round(chargeable_weight, 2),
        "freight_usd": round(freight, 2),
        "origin_fee_usd": round(origin_fee, 2),
        "destination_fee_usd": round(destination_fee, 2),
        "customs_fee_usd": round(customs_fee, 2),
        "insurance_fee_usd": round(insurance_fee, 2),
        "total_usd": round(total, 2),
        "eta": eta,
    }



def _delivery_window_multiplier(delivery_window: str) -> float:
    return {
        "Tiết kiệm": 0.88,
        "Cân bằng": 1.0,
        "Nhanh": 1.22,
        "Gấp": 1.5,
    }.get(delivery_window, 1.0)


def _incoterm_fee_factor(incoterm: str) -> float:
    return {
        "EXW": 1.18,
        "FOB": 0.96,
        "FCA": 0.98,
        "CFR": 1.02,
        "CIF": 1.08,
        "DAP": 1.14,
        "DDP": 1.24,
    }.get(incoterm, 1.0)


def _estimate_transit_days(mode: str, origin: str, destination: str, delivery_window: str, speed: float) -> tuple[int, int]:
    distance_factor = _zone_distance_factor(origin, destination)
    if mode == "Air":
        base_min, base_max = 2, 6
    elif mode == "Sea LCL":
        base_min, base_max = 16, 38
    else:
        base_min, base_max = 6, 18

    urgency_factor = {"Tiết kiệm": 1.18, "Cân bằng": 1.0, "Nhanh": 0.82, "Gấp": 0.68}.get(delivery_window, 1.0)
    min_days = max(1, round(base_min * distance_factor * urgency_factor / speed))
    max_days = max(min_days + 1, round(base_max * distance_factor * urgency_factor / speed))
    return min_days, max_days


def _freight_quote_comparison(
    origin: str,
    destination: str,
    cargo_type: str,
    weight_kg: float,
    length_cm: float,
    width_cm: float,
    height_cm: float,
    quantity: int,
    incoterm: str,
    delivery_window: str,
    cargo_value_usd: float,
) -> pd.DataFrame:
    quantity = max(int(quantity or 1), 1)
    weight_kg = max(float(weight_kg or 0), 0.0)
    volume_cbm = (max(length_cm, 0.0) * max(width_cm, 0.0) * max(height_cm, 0.0) / 1_000_000) * quantity
    gross_weight = weight_kg * quantity
    air_chargeable = max(gross_weight, volume_cbm * 167)
    sea_chargeable = max(gross_weight / 1000, volume_cbm)
    cargo = CARGO_TYPES.get(cargo_type, CARGO_TYPES["Hàng thường"])
    distance_factor = _zone_distance_factor(origin, destination)
    urgency_multiplier = _delivery_window_multiplier(delivery_window)
    incoterm_factor = _incoterm_fee_factor(incoterm)
    rows = []

    for option in FREIGHT_CARRIERS:
        mode = option["mode"]
        if mode == "Air":
            chargeable = air_chargeable
            freight = option["base_rate"] * chargeable * distance_factor * urgency_multiplier * cargo["handling"]
        elif mode == "Sea LCL":
            chargeable = sea_chargeable
            freight = option["base_rate"] * chargeable * distance_factor * urgency_multiplier * cargo["handling"] + 65
        else:
            chargeable = max(gross_weight / 300, volume_cbm)
            freight = option["base_rate"] * max(gross_weight, 1) * distance_factor * urgency_multiplier * cargo["handling"] + 45

        origin_fee = 38 * incoterm_factor if incoterm in {"EXW", "FCA"} else 24
        destination_fee = 42 * incoterm_factor if incoterm in {"DAP", "DDP"} else 28
        fuel_surcharge = freight * (0.11 if mode == "Sea LCL" else 0.18 if mode == "Air" else 0.14)
        security_fee = max(9, chargeable * 0.06) if mode == "Air" else 12
        customs_fee = 0 if incoterm in {"FOB", "CFR"} else 55 * incoterm_factor
        estimated_duty_tax = max(float(cargo_value_usd or 0), 0.0) * float(cargo["duty"]) if incoterm == "DDP" else max(float(cargo_value_usd or 0), 0.0) * float(cargo["duty"]) * 0.35
        risk_buffer = freight * (float(cargo["risk"]) - 1) * 0.35
        total = freight + origin_fee + destination_fee + fuel_surcharge + security_fee + customs_fee + estimated_duty_tax + risk_buffer
        min_days, max_days = _estimate_transit_days(mode, origin, destination, delivery_window, float(option["speed"]))
        cost_score = 100 / (1 + total / 500)
        time_score = 100 / (1 + max_days / 10)
        route_score = (float(option["reliability"]) * 0.45) + (cost_score * 0.35) + (time_score * 0.2)
        rows.append({
            "Hãng vận chuyển": option["carrier"],
            "Tuyến / Mode": f"{origin} -> {destination} | {mode}",
            "Phù hợp nhất": option["best_for"],
            "Chargeable": round(chargeable, 2),
            "Freight USD": round(freight, 2),
            "Thuế ước tính USD": round(estimated_duty_tax, 2),
            "Phụ phí USD": round(origin_fee + destination_fee + fuel_surcharge + security_fee + customs_fee + risk_buffer, 2),
            "Tổng ước tính USD": round(total, 2),
            "Transit time": f"{min_days}-{max_days} ngày",
            "Độ tin cậy": f"{option['reliability']}%",
            "Điểm tối ưu": round(route_score, 2),
        })

    df = pd.DataFrame(rows).sort_values(["Tổng ước tính USD", "Điểm tối ưu"], ascending=[True, False]).reset_index(drop=True)
    df.insert(0, "Xếp hạng", range(1, len(df) + 1))
    return df


def _freight_ai_recommendation(quotes: pd.DataFrame, delivery_window: str) -> str:
    if quotes.empty:
        return "Chưa đủ dữ liệu để đề xuất phương án."
    cheapest = quotes.iloc[0]
    fastest_candidates = quotes[quotes["Tuyến / Mode"].str.contains("Air", na=False)]
    fastest = fastest_candidates.iloc[0] if not fastest_candidates.empty else cheapest
    optimal = quotes.sort_values("Điểm tối ưu", ascending=False).iloc[0]
    if delivery_window in {"Nhanh", "Gấp"}:
        primary = fastest
        reason = "ưu tiên thời gian giao và độ ổn định tracking"
    elif delivery_window == "Tiết kiệm":
        primary = cheapest
        reason = "ưu tiên tổng chi phí thấp nhất"
    else:
        primary = optimal
        reason = "cân bằng giữa chi phí, thời gian và độ tin cậy"
    return (
        f"Đề xuất: chọn {primary['Hãng vận chuyển']} ({primary['Transit time']}) vì {reason}. "
        f"Phương án tiết kiệm nhất hiện là {cheapest['Hãng vận chuyển']} với tổng ước tính ${cheapest['Tổng ước tính USD']:,.2f}. "
        f"Tuyến tối ưu theo điểm AI là {optimal['Hãng vận chuyển']} với điểm {optimal['Điểm tối ưu']}."
    )
def _shipping_calculation(
    origin: str,
    destination: str,
    service_level: str,
    cargo_type: str,
    product_cost_usd: float,
    declared_value_usd: float,
    weight_kg: float,
    length_cm: float,
    width_cm: float,
    height_cm: float,
    quantity: int,
    customs_rate_pct: float,
    vat_rate_pct: float,
    insurance_rate_pct: float,
    handling_fee_usd: float,
    documentation_fee_usd: float,
    last_mile_fee_usd: float,
    target_margin_pct: float,
) -> dict[str, float | str]:
    quantity = max(int(quantity or 1), 1)
    actual_weight = max(float(weight_kg or 0), 0.0) * quantity
    dimensional_weight = (max(length_cm, 0.0) * max(width_cm, 0.0) * max(height_cm, 0.0) / 5000) * quantity
    billable_weight = max(actual_weight, dimensional_weight)
    cargo = CARGO_TYPES.get(cargo_type, CARGO_TYPES["Hàng thường"])
    distance_factor = _zone_distance_factor(origin, destination)
    service_factor = _service_multiplier(service_level)

    product_cost = max(float(product_cost_usd or 0), 0.0) * quantity
    declared_value = max(float(declared_value_usd or 0), 0.0)
    freight = 5.2 * billable_weight * distance_factor * service_factor * float(cargo["handling"]) + 11.5
    fuel_surcharge = freight * 0.14
    customs = declared_value * max(float(customs_rate_pct or 0), 0.0) / 100
    vat_base = declared_value + freight + fuel_surcharge + customs
    vat = vat_base * max(float(vat_rate_pct or 0), 0.0) / 100
    insurance = declared_value * max(float(insurance_rate_pct or 0), 0.0) / 100
    handling = max(float(handling_fee_usd or 0), 0.0)
    documentation = max(float(documentation_fee_usd or 0), 0.0)
    last_mile = max(float(last_mile_fee_usd or 0), 0.0)
    logistics_total = freight + fuel_surcharge + customs + vat + insurance + handling + documentation + last_mile
    total_landed_cost = product_cost + logistics_total
    landed_cost_per_unit = total_landed_cost / quantity
    target_margin = min(max(float(target_margin_pct or 0), 0.0), 95.0) / 100
    minimum_selling_price = landed_cost_per_unit / (1 - target_margin) if target_margin < 1 else landed_cost_per_unit
    gross_profit_per_unit = minimum_selling_price - landed_cost_per_unit

    return {
        "origin": origin,
        "destination": destination,
        "service_level": service_level,
        "cargo_type": cargo_type,
        "quantity": quantity,
        "actual_weight_kg": round(actual_weight, 2),
        "dimensional_weight_kg": round(dimensional_weight, 2),
        "billable_weight_kg": round(billable_weight, 2),
        "product_cost_usd": round(product_cost, 2),
        "freight_usd": round(freight, 2),
        "fuel_surcharge_usd": round(fuel_surcharge, 2),
        "customs_usd": round(customs, 2),
        "vat_usd": round(vat, 2),
        "insurance_usd": round(insurance, 2),
        "handling_usd": round(handling, 2),
        "documentation_usd": round(documentation, 2),
        "last_mile_usd": round(last_mile, 2),
        "logistics_total_usd": round(logistics_total, 2),
        "total_landed_cost_usd": round(total_landed_cost, 2),
        "landed_cost_per_unit_usd": round(landed_cost_per_unit, 2),
        "minimum_selling_price_usd": round(minimum_selling_price, 2),
        "gross_profit_per_unit_usd": round(gross_profit_per_unit, 2),
        "target_margin_pct": round(target_margin * 100, 2),
        "eta": {"Economy": "6-12 ngày", "Standard": "4-8 ngày", "Express": "2-5 ngày", "Priority": "1-3 ngày"}.get(service_level, "4-8 ngày"),
    }


def _shipping_ai_pricing_note(costs: dict[str, float | str]) -> str:
    return (
        f"Total Landed Cost là ${costs['total_landed_cost_usd']:,.2f}, tương đương "
        f"${costs['landed_cost_per_unit_usd']:,.2f}/đơn vị. Để đạt margin mục tiêu "
        f"{costs['target_margin_pct']}%, giá bán tối thiểu nên là "
        f"${costs['minimum_selling_price_usd']:,.2f}/đơn vị. Nếu thị trường không chấp nhận mức giá này, "
        "nên tối ưu lại freight, last mile hoặc điều kiện mua hàng trước khi scale."
    )


def _shipping_cost_breakdown(costs: dict[str, float | str]) -> pd.DataFrame:
    rows = [
        ("Product cost", costs["product_cost_usd"]),
        ("Freight", costs["freight_usd"]),
        ("Fuel surcharge", costs["fuel_surcharge_usd"]),
        ("Customs", costs["customs_usd"]),
        ("VAT", costs["vat_usd"]),
        ("Insurance", costs["insurance_usd"]),
        ("Handling", costs["handling_usd"]),
        ("Documentation", costs["documentation_usd"]),
        ("Last Mile", costs["last_mile_usd"]),
    ]
    return pd.DataFrame([{"Cost item": name, "USD": value} for name, value in rows])


def _ascii_fold(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", str(value or ""))
    return "".join(ch for ch in normalized if not unicodedata.combining(ch)).lower().strip()


def _country_index(countries: list[str], search_name: str, fallback: int = 0) -> int:
    target = _ascii_fold(search_name)
    for idx, country in enumerate(countries):
        if _ascii_fold(country) == target:
            return idx
    return fallback


def _lookup_hs_code(product_query: str, destination: str) -> pd.DataFrame:
    query = _ascii_fold(product_query)
    rows = []
    for item in HS_CODE_LIBRARY:
        keywords = item.get("keywords", [])
        if not query or any(keyword in query or query in keyword for keyword in keywords):
            rows.append({
                "Step": "HS Code",
                "Result": item["hs_code"],
                "Details": item["description"],
            })
            rows.extend([
                {"Step": "Duty", "Result": item["duty"], "Details": f"Destination: {destination}"},
                {"Step": "VAT", "Result": item["vat"], "Details": "Confirm with customs broker before filing."},
                {"Step": "FTA", "Result": item["fta"], "Details": "FTA benefit requires valid origin documents."},
                {"Step": "Required Documents", "Result": item["documents"], "Details": "Use this as the first filing checklist."},
                {"Step": "Restrictions", "Result": item["restrictions"], "Details": "Check product-specific rules in destination market."},
            ])
            break
    if not rows:
        rows = [
            {"Step": "HS Code", "Result": "Needs broker review", "Details": "No close match in the built-in sample library."},
            {"Step": "Next action", "Result": "Collect product composition, use, catalog and photos", "Details": "Then classify with customs broker or official tariff portal."},
        ]
    return pd.DataFrame(rows)


def _customs_document_audit(selected_docs: list[str], shipment_mode: str, claim_fta: bool) -> pd.DataFrame:
    required = ["Invoice", "Packing List"]
    if shipment_mode == "Sea":
        required.append("Bill of Lading")
    elif shipment_mode == "Air":
        required.append("Air Waybill")
    else:
        required.extend(["Bill of Lading", "Air Waybill"])
    if claim_fta:
        required.extend(["CO", "COO"])

    rows = []
    for doc_name, purpose in CUSTOMS_DOCUMENTS.items():
        is_required = doc_name in required
        is_ready = doc_name in selected_docs
        rows.append({
            "Document": doc_name,
            "Required": "Yes" if is_required else "Optional/conditional",
            "Status": "Ready" if is_ready else "Missing" if is_required else "Not provided",
            "Purpose": purpose,
        })
    return pd.DataFrame(rows)


def _export_consultation(product: str, destination: str, mode: str, cargo_value_usd: float, weight_kg: float) -> dict[str, str]:
    destination_key = _ascii_fold(destination)
    product_key = _ascii_fold(product)
    market = EXPORT_MARKET_RULES.get(destination_key, {})
    hs_table = _lookup_hs_code(product, destination)
    hs_code = hs_table.iloc[0]["Result"] if not hs_table.empty else "Needs review"
    mango_japan = "xoai" in product_key and destination_key == "japan"
    if not market:
        market = {
            "allowed": "Likely possible, subject to destination import rules and product-specific restrictions.",
            "documents": "Invoice, Packing List, transport document, C/O if claiming FTA, customs declaration and permits depending product.",
            "tax": "Duty/VAT depend on HS code and destination tariff schedule.",
            "quarantine": "Check whether food, plant, animal, chemical or regulated goods controls apply.",
            "timeline": "Air: 2-7 days. Sea: 14-35 days depending route.",
            "ports": "Select port/airport based on buyer location and carrier service.",
            "carriers": "Compare express, air cargo, LCL/FCL and forwarder options by urgency and cargo profile.",
            "freight": "Use quote tool for an indicative estimate; confirm final rate with carrier/forwarder.",
        }
    if mango_japan:
        allowed = "Yes, but only when orchard/packing/treatment/quarantine requirements are satisfied."
    else:
        allowed = market["allowed"]
    freight_estimate = max(weight_kg, 1) * (4.8 if mode == "Air" else 0.65) + max(cargo_value_usd, 0) * 0.006
    return {
        "Allowed": allowed,
        "HS Code": str(hs_code),
        "Required documents": market["documents"],
        "Duty and tax": market["tax"],
        "Quarantine": market["quarantine"],
        "Timeline": market["timeline"],
        "Ports": market["ports"],
        "Suitable carriers": market["carriers"],
        "Estimated freight": f"{market['freight']} Quick estimate for this shipment: USD {freight_estimate:,.2f}.",
    }



FREIGHT_KB_TOPICS = {
    "Incoterms": "Incoterms defines risk transfer, cost responsibility, and document obligations between seller and buyer.",
    "Logistics": "Logistics covers freight, warehousing, fulfillment, customs, insurance, tracking, last mile, and SLA management.",
    "Customs": "Customs review needs invoice, packing list, transport document, HS code, declared value, origin, and permits for controlled goods.",
    "Tax": "Import duty, VAT/GST, and surcharges depend on HS code, customs value, Incoterms, and destination-country rules.",
    "HS Code": "HS Code classifies goods for tariff, import controls, documents, and compliance requirements.",
    "FTA": "FTA can reduce duty when rules of origin are met and valid C/O or origin documents are available.",
    "Country Rules": "Each market has its own labeling, safety, quarantine, technical standards, import restrictions, and recordkeeping rules.",
}


def _extract_destination(message: str) -> str:
    folded = _ascii_fold(message)
    for country in COUNTRY_ZONES:
        country_folded = _ascii_fold(country)
        if country_folded in folded:
            return country
    if "canada" in folded:
        return "Canada"
    return "Canada"


def _extract_weight_kg(message: str, fallback: float = 300.0) -> float:
    match = re.search(r"(\d+(?:[.,]\d+)?)\s*(kg|kilogram|kgs)", message, re.IGNORECASE)
    if not match:
        return fallback
    return float(match.group(1).replace(",", "."))


def _ai_sales_agent_workflow(message: str, origin: str, product: str, service_level: str) -> tuple[pd.DataFrame, dict[str, str | float], str, str]:
    destination = _extract_destination(message)
    weight_kg = _extract_weight_kg(message)
    volume_cbm = max(weight_kg / 250, 0.1)
    cargo_value = max(weight_kg * 8, 500)
    quote = _freight_quote(origin, destination, "Air Freight", service_level, weight_kg, volume_cbm, cargo_value, True, True)
    steps = [
        ("Chat", "Receive request", message),
        ("Collect info", "Ask follow-up", "Cargo type, dimensions, pickup/delivery address, Incoterms, cargo value, deadline, and available documents."),
        ("Create Quote", "Fast estimate", f"{origin} -> {destination}, {weight_kg:,.0f} kg, estimated total USD {float(quote['total_usd']):,.2f}, ETA {quote['eta']}."),
        ("Send Email", "Draft reply", "Send quote, pricing terms, document checklist, and booking confirmation link."),
        ("Follow-up", "Automated reminder", "If no reply after 24 hours, send Economy/Standard/Express comparison and ask for delivery deadline."),
        ("Move to CRM", "Create deal", "Stage: Qualified, owner: Sales logistics, next action: discovery call + customs requirement check."),
    ]
    workflow = pd.DataFrame(steps, columns=["AI Step", "Action", "Output"])
    email = (
        f"Chao anh/chi,\n\n"
        f"Em da nhan nhu cau gui {weight_kg:,.0f} kg {product} tu {origin} sang {destination}. "
        f"Uoc tinh nhanh: Air Freight {service_level}, ETA {quote['eta']}, tong phi du kien USD {float(quote['total_usd']):,.2f}.\n\n"
        "De chot gia chinh xac, anh/chi vui long gui them: kich thuoc kien, dia chi pickup/delivery, gia tri hang, Incoterms va deadline giao.\n\n"
        "Em se cap nhat quote chinh thuc ngay khi co du thong tin."
    )
    crm_note = (
        f"Lead from chat: {message}\n"
        f"Route: {origin} -> {destination}\n"
        f"Weight: {weight_kg:,.0f} kg\n"
        f"Estimated quote: USD {float(quote['total_usd']):,.2f}\n"
        "Stage: Qualified\nNext follow-up: 24h"
    )
    return workflow, quote, email, crm_note


def _freight_rag_answer(question: str, topic: str, product: str, destination: str) -> tuple[pd.DataFrame, str]:
    rows = [{"Knowledge source": name, "Relevant context": body} for name, body in FREIGHT_KB_TOPICS.items()]
    context = FREIGHT_KB_TOPICS.get(topic, FREIGHT_KB_TOPICS["Logistics"])
    hs_result = _lookup_hs_code(product, destination)
    hs_code = hs_result.iloc[0]["Result"] if not hs_result.empty else "Needs review"
    answer = (
        f"RAG context for {topic}: {context}\n\n"
        f"For the question: \"{question}\", AI should answer by classifying HS Code first, checking duty/VAT, "
        f"confirming FTA eligibility and required documents, then matching the result against {destination} country rules. "
        f"Sample product '{product}' currently maps to HS Code: {hs_code}. Final filing should be confirmed by broker or official customs source."
    )
    return pd.DataFrame(rows), answer


def _freight_context_hub(
    question: str,
    topic: str,
    origin: str,
    destination: str,
    product: str,
    quote_mode: str,
    service_level: str,
    weight_kg: float,
    volume_cbm: float,
    cargo_value_usd: float,
    shipment_mode: str,
    selected_docs: list[str],
    claim_fta: bool,
    tracking_number: str,
    carrier: str,
    promised_days: int,
    product_cost_usd: float,
    target_margin_pct: float,
) -> dict[str, object]:
    weight_kg = max(float(weight_kg or 0), 1.0)
    volume_cbm = max(float(volume_cbm or 0), 0.1)
    cargo_value_usd = max(float(cargo_value_usd or 0), 0.0)
    product_cost_usd = max(float(product_cost_usd or 0), 0.0)
    export_mode = "Sea" if "Sea" in quote_mode else "Air"
    cargo_type = next(iter(CARGO_TYPES.keys()))

    kb_sources, kb_answer = _freight_rag_answer(question, topic, product, destination)
    hs_table = _lookup_hs_code(product, destination)
    customs_audit = _customs_document_audit(selected_docs, shipment_mode, claim_fta)
    export_advice = _export_consultation(product, destination, export_mode, cargo_value_usd, weight_kg)
    quote = _freight_quote(origin, destination, quote_mode, service_level, weight_kg, volume_cbm, cargo_value_usd, True, True)
    shipping = _shipping_calculation(
        origin=origin,
        destination=destination,
        service_level=service_level,
        cargo_type=cargo_type,
        product_cost_usd=product_cost_usd,
        declared_value_usd=cargo_value_usd,
        weight_kg=weight_kg,
        length_cm=100.0,
        width_cm=100.0,
        height_cm=max(volume_cbm * 100.0, 1.0),
        quantity=1,
        customs_rate_pct=8.0,
        vat_rate_pct=10.0,
        insurance_rate_pct=0.6,
        handling_fee_usd=35.0,
        documentation_fee_usd=25.0,
        last_mile_fee_usd=60.0,
        target_margin_pct=target_margin_pct,
    )
    tracking = _tracking_snapshot(tracking_number, carrier, promised_days) if tracking_number.strip() else {}
    timeline = _tracking_timeline(tracking) if tracking else pd.DataFrame()
    sales_message = f"I need to ship {weight_kg:,.0f} kg of {product} to {destination}"
    sales_workflow, sales_quote, email_draft, crm_note = _ai_sales_agent_workflow(sales_message, origin, product, service_level)
    route_options = _route_planner_options(weight_kg, cargo_value_usd, "Balanced")

    missing_docs = customs_audit[customs_audit["Status"] == "Missing"]["Document"].tolist()
    hs_code = hs_table.iloc[0]["Result"] if not hs_table.empty else "Needs review"
    tracking_status = tracking.get("status", "No tracking") if tracking else "No tracking"
    tracking_risk = tracking.get("risk_level", "N/A") if tracking else "N/A"
    best_route = route_options.iloc[0]

    summary = pd.DataFrame([
        {"Connected module": "HS Code Agent", "Status": "Linked", "Context output": f"HS Code: {hs_code}"},
        {"Connected module": "AI Customs", "Status": "Linked", "Context output": "Missing docs: " + (", ".join(missing_docs) if missing_docs else "None")},
        {"Connected module": "AI Export Consultant", "Status": "Linked", "Context output": str(export_advice.get("Allowed", "Review required"))},
        {"Connected module": "AI Freight Quote", "Status": "Linked", "Context output": f"Total quote USD {float(quote['total_usd']):,.2f}, ETA {quote['eta']}"},
        {"Connected module": "Shipping Cost", "Status": "Linked", "Context output": f"Landed cost/unit USD {float(shipping['landed_cost_per_unit_usd']):,.2f}"},
        {"Connected module": "Tracking Agent", "Status": "Linked", "Context output": f"{tracking_status}, risk {tracking_risk}"},
        {"Connected module": "AI Sales Agent", "Status": "Linked", "Context output": f"CRM handoff ready, sales quote USD {float(sales_quote['total_usd']):,.2f}"},
        {"Connected module": "AI Route Planner", "Status": "Linked", "Context output": f"Best route: {best_route['Option']}"},
    ])

    hub_answer = (
        f"{kb_answer}\n\n"
        f"Context Hub decision: use HS Code {hs_code}, quote {quote_mode} {service_level} at USD {float(quote['total_usd']):,.2f}, "
        f"landed cost/unit USD {float(shipping['landed_cost_per_unit_usd']):,.2f}, customs missing docs: "
        f"{', '.join(missing_docs) if missing_docs else 'none'}, tracking status: {tracking_status}. "
        "Sales can use the email draft and CRM handoff below without re-entering shipment data."
    )

    return {
        "summary": summary,
        "kb_sources": kb_sources,
        "answer": hub_answer,
        "hs_table": hs_table,
        "customs_audit": customs_audit,
        "export_advice": pd.DataFrame([{"Topic": key, "AI answer": value} for key, value in export_advice.items()]),
        "quote": pd.DataFrame([quote]),
        "shipping": pd.DataFrame([shipping]),
        "tracking": pd.DataFrame([tracking]) if tracking else pd.DataFrame(),
        "timeline": timeline,
        "route_options": route_options,
        "sales_workflow": sales_workflow,
        "email_draft": email_draft,
        "crm_note": crm_note,
    }


def _route_planner_options(weight_kg: float, cargo_value_usd: float, priority: str) -> pd.DataFrame:
    route = "Vietnam -> Singapore -> Germany -> Netherlands -> Last Mile"
    options = [
        ("Balanced multimodal", "Air + EU road", 8, 4.2, 1.55),
        ("Cost saver", "Sea/Air hybrid", 18, 2.7, 0.92),
        ("Fast lane", "Air priority", 5, 5.8, 2.15),
    ]
    priority_weight = {
        "Balanced": (0.34, 0.33, 0.33),
        "Fastest": (0.55, 0.25, 0.20),
        "Lowest cost": (0.25, 0.55, 0.20),
        "Lowest CO2": (0.25, 0.25, 0.50),
    }.get(priority, (0.34, 0.33, 0.33))
    rows = []
    for name, mode, days, usd_per_kg, co2_per_kg in options:
        cost = weight_kg * usd_per_kg + cargo_value_usd * 0.006 + 85
        co2 = weight_kg * co2_per_kg
        time_score = 100 / days
        cost_score = 1000 / max(cost, 1)
        co2_score = 500 / max(co2, 1)
        score = time_score * priority_weight[0] + cost_score * priority_weight[1] + co2_score * priority_weight[2]
        rows.append({
            "Option": name,
            "Route": route,
            "Mode": mode,
            "Transit time": f"{days} days",
            "Cost USD": round(cost, 2),
            "CO2 kg": round(co2, 2),
            "AI score": round(score, 2),
        })
    return pd.DataFrame(rows).sort_values("AI score", ascending=False).reset_index(drop=True)


def _margin_scenario(product_price: float, shipping: float, duty: float, vat: float, commission: float, new_shipping: float) -> tuple[pd.DataFrame, str]:
    base_cost = shipping + duty + vat + commission
    new_cost = new_shipping + duty + vat + commission
    base_margin = ((product_price - base_cost) / product_price * 100) if product_price else 0
    new_margin = ((product_price - new_cost) / product_price * 100) if product_price else 0
    rows = pd.DataFrame([
        {"Scenario": "Current", "Product price USD": product_price, "Shipping USD": shipping, "Duty USD": duty, "VAT USD": vat, "Commission USD": commission, "Margin %": round(base_margin, 2)},
        {"Scenario": "Change carrier", "Product price USD": product_price, "Shipping USD": new_shipping, "Duty USD": duty, "VAT USD": vat, "Commission USD": commission, "Margin %": round(new_margin, 2)},
    ])
    recommendation = (
        f"Changing carrier from USD {shipping:,.2f} shipping to USD {new_shipping:,.2f} "
        f"moves margin from {base_margin:.1f}% to {new_margin:.1f}%. "
        "AI recommends the new option if SLA, tracking quality, and customs risk remain acceptable."
    )
    return rows, recommendation


def _quote_pdf_bytes(quote: dict[str, str | float], customer: str, product: str, payment_terms: str, notes: str) -> bytes | None:
    try:
        from fpdf import FPDF

        def safe(value: object) -> str:
            text_value = str(value or "")
            normalized = unicodedata.normalize("NFKD", text_value)
            return "".join(ch for ch in normalized if not unicodedata.combining(ch) and ord(ch) < 128)

        pdf = FPDF(orientation="P", unit="mm", format="A4")
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "LOGISTICS QUOTATION", ln=True, align="C")
        pdf.ln(4)
        pdf.set_font("Arial", size=10)
        lines = [
            ("Customer", customer),
            ("Product", product),
            ("Origin", quote.get("origin")),
            ("Destination", quote.get("destination")),
            ("Mode", quote.get("mode")),
            ("Service level", quote.get("service_level")),
            ("Freight", f"USD {float(quote.get('freight_usd', 0)):,.2f}"),
            ("Insurance", f"USD {float(quote.get('insurance_fee_usd', 0)):,.2f}"),
            ("ETA", quote.get("eta")),
            ("Terms", "Subject to space, customs clearance, fuel surcharge and final cargo details."),
            ("Payment terms", payment_terms),
            ("Total", f"USD {float(quote.get('total_usd', 0)):,.2f}"),
        ]
        for label, value in lines:
            pdf.set_font("Arial", "B", 10)
            pdf.cell(42, 8, safe(label), border=1)
            pdf.set_font("Arial", size=10)
            pdf.multi_cell(138, 8, safe(value), border=1)
        if notes.strip():
            pdf.ln(4)
            pdf.set_font("Arial", "B", 11)
            pdf.cell(0, 8, "Notes", ln=True)
            pdf.set_font("Arial", size=10)
            pdf.multi_cell(0, 7, safe(notes))
        return bytes(pdf.output())
    except Exception as exc:
        print(f"Quote PDF error: {exc}")
        return None


def _tracking_snapshot(tracking_number: str, carrier: str, promised_days: int = 7) -> dict[str, str | int | bool]:
    clean_tracking = tracking_number.strip().upper()
    checksum = sum(ord(ch) for ch in clean_tracking)
    statuses = [
        ("Label Created", "Đơn đã được tạo nhãn và chờ bàn giao carrier."),
        ("Picked Up", "Carrier đã nhận kiện hàng từ kho gửi."),
        ("In Transit", "Kiện hàng đang di chuyển qua hub quốc tế."),
        ("Customs Clearance", "Đang xử lý khai báo và thông quan tại nước đến."),
        ("Out For Delivery", "Kiện hàng đang được giao chặng cuối."),
        ("Delivered", "Carrier ghi nhận đã giao thành công."),
    ]
    status_idx = checksum % len(statuses)
    status, description = statuses[status_idx]
    elapsed_days = max(1, (checksum % 11) + status_idx)
    promised_days = max(int(promised_days or 1), 1)
    delay_days = max(0, elapsed_days - promised_days) if status != "Delivered" else 0
    is_delayed = delay_days > 0
    risk_level = "High" if delay_days >= 3 or status == "Customs Clearance" else "Medium" if delay_days > 0 or status == "In Transit" else "Low"
    likely_reason = _tracking_likely_reason(status, delay_days, carrier)
    tracking_url = TRACKING_CARRIERS.get(carrier, TRACKING_CARRIERS["17TRACK"]).format(tracking=quote_plus(clean_tracking))
    return {
        "tracking_number": clean_tracking,
        "carrier": carrier,
        "status": status,
        "description": description,
        "last_event": (date.today() - timedelta(days=checksum % 4)).isoformat(),
        "elapsed_days": elapsed_days,
        "promised_days": promised_days,
        "delay_days": delay_days,
        "is_delayed": is_delayed,
        "risk_level": risk_level,
        "likely_reason": likely_reason,
        "tracking_url": tracking_url,
    }


def _tracking_likely_reason(status: str, delay_days: int, carrier: str) -> str:
    if delay_days <= 0:
        return "Shipment đang nằm trong SLA dự kiến; tiếp tục theo dõi event mới từ carrier."
    if status == "Customs Clearance":
        return "Lý do có khả năng do kiểm tra hải quan, thiếu chứng từ, sai HS code hoặc cần xác minh declared value."
    if status == "In Transit":
        return "Lý do có khả năng do backlog tại hub trung chuyển, thiếu chuyến bay/tàu nối tuyến hoặc tắc nghẽn line-haul."
    if status == "Picked Up":
        return "Lý do có khả năng do kiện hàng chưa được scan vào hub xuất khẩu hoặc carrier gom chuyến chậm hơn lịch thường lệ."
    if status == "Out For Delivery":
        return "Lý do có khả năng do địa chỉ khó giao, người nhận chưa sẵn sàng hoặc last-mile quá tải."
    return f"{carrier} chưa ghi nhận event mới; khả năng cao là chậm scan, giữ hàng tại hub hoặc pending xử lý vận hành."


def _tracking_timeline(tracking: dict[str, str | int | bool]) -> pd.DataFrame:
    stages = ["Label Created", "Picked Up", "In Transit", "Customs Clearance", "Out For Delivery", "Delivered"]
    current_idx = stages.index(str(tracking["status"])) if str(tracking["status"]) in stages else 0
    start_date = date.today() - timedelta(days=int(tracking["elapsed_days"]))
    rows = []
    for idx, stage in enumerate(stages):
        if idx < current_idx:
            state = "Completed"
            event_date = start_date + timedelta(days=idx + 1)
        elif idx == current_idx:
            state = "Current"
            event_date = date.fromisoformat(str(tracking["last_event"]))
        else:
            state = "Pending"
            event_date = None
        rows.append({"Stage": stage, "State": state, "Event date": event_date.isoformat() if event_date else "-"})
    return pd.DataFrame(rows)


def _tracking_ai_summary(tracking: dict[str, str | int | bool]) -> str:
    if bool(tracking["is_delayed"]):
        delay_text = f"Shipment delayed {tracking['delay_days']} days."
    else:
        delay_text = "Shipment is currently within the promised delivery window."
    return (
        f"{delay_text} Trạng thái hiện tại là {tracking['status']} sau {tracking['elapsed_days']} ngày theo dõi. "
        f"Risk level: {tracking['risk_level']}. {tracking['likely_reason']}"
    )
def render_tab_logistics_growth(gemini_key: str = "", workspace_id: int = 1, role: str = "editor", user_id: int | None = None):
    del gemini_key
    can_edit = (role or "viewer").lower() != "viewer"
    leads_key = _growth_key(workspace_id, "leads")
    campaign_key = _growth_key(workspace_id, "campaign")

    if leads_key not in st.session_state:
        st.session_state[leads_key] = _sample_leads()

    st.markdown("### AI Sales & Marketing Growth Platform for Logistics")
    st.caption("Quản lý lead, chấm điểm cơ hội, tạo campaign funnel và kịch bản follow-up cho dịch vụ vận chuyển, fulfillment, kho bãi và tối ưu logistics.")

    tab_labels = [
        "Lead Pipeline",
        "Lead Scoring",
        "Campaign Funnel",
        "Sales Scripts",
        "Freight Quote",
        "Shipping Calculator",
        "International Tracking",
        "HS Code",
        "Customs Assistant",
        "Export Consultant",
        "Quote Generator",
        "AI Sales Agent",
        "AI Knowledge Base",
        "AI Route Planner",
        "AI Margin Simulator",
        "AI Shipping Dashboard",
    ]
    selected_tab = st.pills(
        "Logistics Growth menu",
        tab_labels,
        default=tab_labels[0],
        key=_growth_key(workspace_id, "active_tab"),
        label_visibility="collapsed",
        width="stretch",
    ) or tab_labels[0]


    if selected_tab == tab_labels[0]: 
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

    elif selected_tab == tab_labels[1]: 
        st.markdown("##### Lead Scoring & Next Best Action")
        df = st.session_state[leads_key].copy()
        if df.empty:
            st.info("Chưa có lead để chấm điểm.")
        else:
            df["score"] = df.apply(_score_lead, axis=1)
            df["priority"] = pd.cut(df["score"], bins=[-1, 49, 74, 100], labels=["Low", "Medium", "High"])
            df["next_best_action"] = df.apply(_next_action, axis=1)
            st.dataframe(df[["company", "segment", "contact_role", "stage", "pain_point", "monthly_shipments", "score", "priority", "next_best_action"]].sort_values("score", ascending=False), use_container_width=True, hide_index=True)

    elif selected_tab == tab_labels[2]: 
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

    elif selected_tab == tab_labels[3]: 
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

    elif selected_tab == tab_labels[4]: 
        st.markdown("##### Freight Quote Assistant")
        st.caption("Nhập thông tin shipment một lần để AI so sánh nhiều hãng vận chuyển, gợi ý tuyến tối ưu, dự đoán transit time, ước tính thuế/phụ phí và chọn phương án tiết kiệm nhất.")

        countries = list(COUNTRY_ZONES.keys())
        input_cols = st.columns(4)
        with input_cols[0]:
            freight_origin = st.selectbox("Điểm đi", countries, index=countries.index("Việt Nam"), key=f"{campaign_key}_freight_origin")
        with input_cols[1]:
            freight_destination = st.selectbox("Điểm đến", countries, index=countries.index("Hoa Kỳ"), key=f"{campaign_key}_freight_destination")
        with input_cols[2]:
            cargo_type = st.selectbox("Loại hàng", list(CARGO_TYPES.keys()), key=f"{campaign_key}_cargo_type")
        with input_cols[3]:
            delivery_window = st.selectbox("Thời gian giao", DELIVERY_WINDOWS, index=1, key=f"{campaign_key}_delivery_window")

        size_cols = st.columns(5)
        with size_cols[0]:
            quantity = st.number_input("Số kiện", min_value=1, value=1, step=1, key=f"{campaign_key}_freight_qty")
        with size_cols[1]:
            gross_weight = st.number_input("Trọng lượng/kiện (kg)", min_value=0.0, value=250.0, step=10.0, key=f"{campaign_key}_freight_weight")
        with size_cols[2]:
            length_cm = st.number_input("Dài (cm)", min_value=0.0, value=120.0, step=5.0, key=f"{campaign_key}_freight_l")
        with size_cols[3]:
            width_cm = st.number_input("Rộng (cm)", min_value=0.0, value=80.0, step=5.0, key=f"{campaign_key}_freight_w")
        with size_cols[4]:
            height_cm = st.number_input("Cao (cm)", min_value=0.0, value=90.0, step=5.0, key=f"{campaign_key}_freight_h")

        term_cols = st.columns([1, 1, 2])
        with term_cols[0]:
            incoterm = st.selectbox("Incoterms", INCOTERMS, index=INCOTERMS.index("DAP"), key=f"{campaign_key}_incoterm")
        with term_cols[1]:
            cargo_value = st.number_input("Giá trị hàng (USD)", min_value=0.0, value=5000.0, step=100.0, key=f"{campaign_key}_freight_value")
        with term_cols[2]:
            st.info("AI đang dùng rate card nội bộ mô phỏng nhiều carrier. Khi có API DHL/FedEx/UPS/forwarder, có thể thay phần rate source để lấy giá realtime.")

        quote_options = _freight_quote_comparison(
            freight_origin,
            freight_destination,
            cargo_type,
            gross_weight,
            length_cm,
            width_cm,
            height_cm,
            int(quantity),
            incoterm,
            delivery_window,
            cargo_value,
        )
        best_price = quote_options.iloc[0]
        best_ai = quote_options.sort_values("Điểm tối ưu", ascending=False).iloc[0]
        fastest = quote_options[quote_options["Tuyến / Mode"].str.contains("Air", na=False)].iloc[0]

        metric_cols = st.columns(4)
        metric_cols[0].metric("Tiết kiệm nhất", best_price["Hãng vận chuyển"], f"${best_price['Tổng ước tính USD']:,.2f}")
        metric_cols[1].metric("Tuyến tối ưu", best_ai["Hãng vận chuyển"], f"Điểm {best_ai['Điểm tối ưu']}")
        metric_cols[2].metric("Nhanh nhất", fastest["Hãng vận chuyển"], fastest["Transit time"])
        metric_cols[3].metric("Thuế + phụ phí", f"${best_price['Thuế ước tính USD'] + best_price['Phụ phí USD']:,.2f}")

        st.markdown("##### AI Recommendation")
        st.success(_freight_ai_recommendation(quote_options, delivery_window))
        st.dataframe(quote_options, use_container_width=True, hide_index=True)
        st.download_button(
            "Export freight comparison CSV",
            quote_options.to_csv(index=False).encode("utf-8-sig"),
            "freight_quote_comparison.csv",
            "text/csv",
            use_container_width=True,
            key=f"{campaign_key}_freight_download",
        )
    elif selected_tab == tab_labels[5]: 
        st.markdown("##### Shipping Landed Cost Calculator")
        st.caption("Tính toàn bộ chi phí từ Freight, Fuel surcharge, Customs, VAT, Insurance, Handling, Documentation, Last Mile đến Total Landed Cost và giá bán tối thiểu.")

        countries = list(COUNTRY_ZONES.keys())
        route_cols = st.columns(4)
        with route_cols[0]:
            ship_origin = st.selectbox("Ship from", countries, index=countries.index("Việt Nam"), key=f"{campaign_key}_ship_origin")
        with route_cols[1]:
            ship_destination = st.selectbox("Ship to", countries, index=countries.index("Singapore"), key=f"{campaign_key}_ship_destination")
        with route_cols[2]:
            ship_service = st.selectbox("Service level", SERVICE_LEVELS, index=1, key=f"{campaign_key}_ship_service")
        with route_cols[3]:
            ship_cargo_type = st.selectbox("Loại hàng", list(CARGO_TYPES.keys()), key=f"{campaign_key}_ship_cargo_type")

        product_cols = st.columns(4)
        with product_cols[0]:
            quantity = st.number_input("Số lượng", min_value=1, value=100, step=1, key=f"{campaign_key}_ship_qty")
        with product_cols[1]:
            product_cost = st.number_input("Giá vốn/đơn vị (USD)", min_value=0.0, value=12.0, step=0.5, key=f"{campaign_key}_product_cost")
        with product_cols[2]:
            declared_value = st.number_input("Declared value (USD)", min_value=0.0, value=1200.0, step=50.0, key=f"{campaign_key}_declared_value")
        with product_cols[3]:
            target_margin = st.number_input("Margin mục tiêu (%)", min_value=0.0, max_value=95.0, value=30.0, step=1.0, key=f"{campaign_key}_target_margin")

        dimension_cols = st.columns(4)
        with dimension_cols[0]:
            weight = st.number_input("Weight/pc (kg)", min_value=0.0, value=0.6, step=0.1, key=f"{campaign_key}_ship_weight")
        with dimension_cols[1]:
            length = st.number_input("Dài (cm)", min_value=0.0, value=30.0, step=1.0, key=f"{campaign_key}_ship_l")
        with dimension_cols[2]:
            width = st.number_input("Rộng (cm)", min_value=0.0, value=20.0, step=1.0, key=f"{campaign_key}_ship_w")
        with dimension_cols[3]:
            height = st.number_input("Cao (cm)", min_value=0.0, value=10.0, step=1.0, key=f"{campaign_key}_ship_h")

        fee_cols = st.columns(4)
        with fee_cols[0]:
            customs_rate = st.number_input("Customs (%)", min_value=0.0, max_value=100.0, value=8.0, step=0.5, key=f"{campaign_key}_customs_rate")
        with fee_cols[1]:
            vat_rate = st.number_input("VAT (%)", min_value=0.0, max_value=100.0, value=10.0, step=0.5, key=f"{campaign_key}_vat_rate")
        with fee_cols[2]:
            insurance_rate = st.number_input("Insurance (%)", min_value=0.0, max_value=20.0, value=0.6, step=0.1, key=f"{campaign_key}_insurance_rate")
        with fee_cols[3]:
            handling_fee = st.number_input("Handling (USD)", min_value=0.0, value=35.0, step=5.0, key=f"{campaign_key}_handling_fee")

        local_cols = st.columns(3)
        with local_cols[0]:
            documentation_fee = st.number_input("Documentation (USD)", min_value=0.0, value=25.0, step=5.0, key=f"{campaign_key}_documentation_fee")
        with local_cols[1]:
            last_mile_fee = st.number_input("Last Mile (USD)", min_value=0.0, value=60.0, step=5.0, key=f"{campaign_key}_last_mile_fee")
        with local_cols[2]:
            st.info("Total Landed Cost = Giá vốn + Freight + Fuel + Customs + VAT + Insurance + Handling + Documentation + Last Mile.")

        shipping = _shipping_calculation(
            ship_origin,
            ship_destination,
            ship_service,
            ship_cargo_type,
            product_cost,
            declared_value,
            weight,
            length,
            width,
            height,
            int(quantity),
            customs_rate,
            vat_rate,
            insurance_rate,
            handling_fee,
            documentation_fee,
            last_mile_fee,
            target_margin,
        )

        summary_cols = st.columns(4)
        summary_cols[0].metric("Total Landed Cost", f"${shipping['total_landed_cost_usd']:,.2f}")
        summary_cols[1].metric("Landed cost/unit", f"${shipping['landed_cost_per_unit_usd']:,.2f}")
        summary_cols[2].metric("Giá bán tối thiểu", f"${shipping['minimum_selling_price_usd']:,.2f}")
        summary_cols[3].metric("ETA", str(shipping["eta"]))

        st.success(_shipping_ai_pricing_note(shipping))
        breakdown = _shipping_cost_breakdown(shipping)
        b1, b2 = st.columns([2, 1])
        with b1:
            st.dataframe(breakdown, use_container_width=True, hide_index=True)
        with b2:
            st.bar_chart(breakdown, x="Cost item", y="USD", use_container_width=True)

        st.markdown("##### Full Calculation")
        st.dataframe(pd.DataFrame([shipping]), use_container_width=True, hide_index=True)
        st.download_button(
            "Export landed cost CSV",
            pd.DataFrame([shipping]).to_csv(index=False).encode("utf-8-sig"),
            "shipping_landed_cost.csv",
            "text/csv",
            use_container_width=True,
            key=f"{campaign_key}_ship_landed_download",
        )
    elif selected_tab == tab_labels[6]: 
        st.markdown("##### International Tracking")
        st.caption("Nhập Tracking Number để AI theo dõi trạng thái, tóm tắt tiến trình, phát hiện chậm và cảnh báo rủi ro vận chuyển quốc tế.")
        t1, t2, t3 = st.columns([2, 1, 1])
        with t1:
            tracking_number = st.text_input("Tracking number", value="JD014600006789012345", key=f"{campaign_key}_tracking_number")
        with t2:
            carrier = st.selectbox("Carrier", list(TRACKING_CARRIERS.keys()), key=f"{campaign_key}_tracking_carrier")
        with t3:
            promised_days = st.number_input("SLA promised days", min_value=1, value=7, step=1, key=f"{campaign_key}_tracking_promised_days")

        if tracking_number.strip():
            tracking = _tracking_snapshot(tracking_number, carrier, int(promised_days))
            timeline = _tracking_timeline(tracking)
            risk_icon = {"Low": "Ổn định", "Medium": "Cần theo dõi", "High": "Cảnh báo"}.get(str(tracking["risk_level"]), "Cần theo dõi")

            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Status", tracking["status"])
            k2.metric("Delay", f"{tracking['delay_days']} ngày")
            k3.metric("Risk", risk_icon)
            k4.metric("Last event", tracking["last_event"])

            summary = _tracking_ai_summary(tracking)
            if bool(tracking["is_delayed"]):
                st.warning(summary)
            else:
                st.success(summary)

            st.markdown("##### Progress Timeline")
            st.dataframe(timeline, use_container_width=True, hide_index=True)

            st.markdown("##### Risk Explanation")
            st.write(tracking["likely_reason"])
            st.markdown(f"[Mở trang tracking chính thức]({tracking['tracking_url']})")

            followup = (
                f"Cập nhật đơn {tracking['tracking_number']}: {summary} "
                "Team CSKH sẽ tiếp tục theo dõi event mới và chủ động báo khi trạng thái thay đổi."
            )
            st.text_area("CSKH follow-up message", value=followup, height=140, key=f"{campaign_key}_tracking_message")
        else:
            st.info("Nhập tracking number để AI phân tích tiến trình và cảnh báo rủi ro.")
    elif selected_tab == tab_labels[7]: 
        st.markdown("##### HS Code Lookup")
        st.caption("Enter a product name and get a structured compliance path: HS Code -> Duty -> VAT -> FTA -> Required Documents -> Restrictions.")
        countries = list(COUNTRY_ZONES.keys())
        hs_cols = st.columns([2, 1])
        with hs_cols[0]:
            hs_product = st.text_input("Product", value="Ca phe rang", key=f"{campaign_key}_hs_product")
        with hs_cols[1]:
            hs_destination = st.selectbox("Destination market", countries, index=_country_index(countries, "nhat ban"), key=f"{campaign_key}_hs_destination")
        hs_result = _lookup_hs_code(hs_product, hs_destination)
        st.dataframe(hs_result, use_container_width=True, hide_index=True)
        st.download_button(
            "Export HS code checklist CSV",
            hs_result.to_csv(index=False).encode("utf-8-sig"),
            "hs_code_checklist.csv",
            "text/csv",
            use_container_width=True,
            key=f"{campaign_key}_hs_download",
        )

    elif selected_tab == tab_labels[8]: 
        st.markdown("##### Customs Assistant")
        st.caption("Check whether the customs file has enough core documents for declaration support.")
        ca_cols = st.columns([1, 2, 1])
        with ca_cols[0]:
            shipment_mode = st.selectbox("Shipment mode", ["Air", "Sea", "Multi-modal"], key=f"{campaign_key}_customs_mode")
        with ca_cols[1]:
            selected_docs = st.multiselect("Documents available", list(CUSTOMS_DOCUMENTS.keys()), default=["Invoice", "Packing List"], key=f"{campaign_key}_customs_docs")
        with ca_cols[2]:
            claim_fta = st.checkbox("Claim FTA", value=True, key=f"{campaign_key}_customs_fta")
        audit = _customs_document_audit(selected_docs, shipment_mode, claim_fta)
        missing = audit[audit["Status"] == "Missing"]
        if missing.empty:
            st.success("Document set is ready for first customs review.")
        else:
            st.warning("Missing required documents: " + ", ".join(missing["Document"].tolist()))
        st.dataframe(audit, use_container_width=True, hide_index=True)
        st.text_area(
            "Declaration assistant note",
            value="Prepare customs declaration with invoice value, HS code, origin, Incoterms, gross/net weight, package count and transport document number. Confirm final HS/duty with broker before filing.",
            height=120,
            key=f"{campaign_key}_customs_note",
        )

    elif selected_tab == tab_labels[9]: 
        st.markdown("##### Export Consultant")
        st.caption("Ask an export question and get a practical answer covering permission, documents, tax, quarantine, timing, ports, carriers and estimated freight.")
        ec_cols = st.columns([2, 1, 1, 1])
        with ec_cols[0]:
            export_product = st.text_input("Product", value="Xoai", key=f"{campaign_key}_export_product")
        with ec_cols[1]:
            export_destination = st.selectbox("Destination", ["Japan", "Singapore", "United States", "Germany", "Australia"], key=f"{campaign_key}_export_destination")
        with ec_cols[2]:
            export_mode = st.selectbox("Mode", ["Air", "Sea"], key=f"{campaign_key}_export_mode")
        with ec_cols[3]:
            export_weight = st.number_input("Weight kg", min_value=1.0, value=500.0, step=25.0, key=f"{campaign_key}_export_weight")
        export_value = st.number_input("Cargo value USD", min_value=0.0, value=3000.0, step=100.0, key=f"{campaign_key}_export_value")
        consultation = _export_consultation(export_product, export_destination, export_mode, export_value, export_weight)
        st.dataframe(pd.DataFrame([{"Topic": key, "AI answer": value} for key, value in consultation.items()]), use_container_width=True, hide_index=True)
        st.text_area(
            "Consultant response draft",
            value="\n".join(f"{key}: {value}" for key, value in consultation.items()),
            height=260,
            key=f"{campaign_key}_export_response",
        )

    elif selected_tab == tab_labels[10]: 
        st.markdown("##### Quote Generator")
        st.caption("Generate a customer-ready PDF quote with Freight, Insurance, ETA, Terms and payment terms.")
        countries = list(COUNTRY_ZONES.keys())
        q_cols = st.columns(4)
        with q_cols[0]:
            quote_customer = st.text_input("Customer", value="ABC Trading", key=f"{campaign_key}_quote_customer")
        with q_cols[1]:
            quote_product = st.text_input("Product", value="Roasted coffee", key=f"{campaign_key}_quote_product")
        with q_cols[2]:
            quote_origin = st.selectbox("Origin", countries, index=_country_index(countries, "viet nam"), key=f"{campaign_key}_quote_origin")
        with q_cols[3]:
            quote_destination = st.selectbox("Destination", countries, index=_country_index(countries, "nhat ban"), key=f"{campaign_key}_quote_destination")

        q2_cols = st.columns(5)
        with q2_cols[0]:
            quote_mode = st.selectbox("Mode", FREIGHT_MODES, key=f"{campaign_key}_quote_mode")
        with q2_cols[1]:
            quote_service = st.selectbox("Service", SERVICE_LEVELS, index=1, key=f"{campaign_key}_quote_service")
        with q2_cols[2]:
            quote_weight = st.number_input("Gross kg", min_value=0.0, value=120.0, step=10.0, key=f"{campaign_key}_quote_weight")
        with q2_cols[3]:
            quote_volume = st.number_input("CBM", min_value=0.0, value=1.2, step=0.1, key=f"{campaign_key}_quote_cbm")
        with q2_cols[4]:
            quote_value = st.number_input("Cargo value", min_value=0.0, value=2500.0, step=100.0, key=f"{campaign_key}_quote_value")

        q3_cols = st.columns([1, 1, 2])
        with q3_cols[0]:
            quote_insurance = st.checkbox("Insurance", value=True, key=f"{campaign_key}_quote_insurance")
        with q3_cols[1]:
            quote_customs = st.checkbox("Customs service", value=True, key=f"{campaign_key}_quote_customs")
        with q3_cols[2]:
            payment_terms = st.selectbox("Payment terms", ["100% before pickup", "50% deposit, 50% before release", "Net 7 after invoice", "Net 15 approved account"], key=f"{campaign_key}_payment_terms")
        quote_notes = st.text_area("Terms / notes", value="Rate valid for 7 days. Excludes duties, taxes, storage, inspection and destination special handling unless stated.", height=90, key=f"{campaign_key}_quote_notes")

        quote = _freight_quote(quote_origin, quote_destination, quote_mode, quote_service, quote_weight, quote_volume, quote_value, quote_insurance, quote_customs)
        quote_metrics = st.columns(4)
        quote_metrics[0].metric("Freight", f"${quote['freight_usd']:,.2f}")
        quote_metrics[1].metric("Insurance", f"${quote['insurance_fee_usd']:,.2f}")
        quote_metrics[2].metric("ETA", str(quote["eta"]))
        quote_metrics[3].metric("Total", f"${quote['total_usd']:,.2f}")
        st.dataframe(pd.DataFrame([quote]), use_container_width=True, hide_index=True)
        quote_pdf = _quote_pdf_bytes(quote, quote_customer, quote_product, payment_terms, quote_notes)
        if quote_pdf:
            st.download_button(
                "Download quote PDF",
                data=quote_pdf,
                file_name="logistics_quote.pdf",
                mime="application/pdf",
                use_container_width=True,
                key=f"{campaign_key}_quote_pdf_download",
            )

    elif selected_tab == tab_labels[11]: 
        st.markdown("##### AI Sales Agent")
        st.caption("Customer leaves a request, AI chats, collects shipment info, creates quote, drafts email, follows up, and hands off to CRM.")
        countries = list(COUNTRY_ZONES.keys())
        sa_cols = st.columns([2, 1, 1])
        with sa_cols[0]:
            sales_message = st.text_area("Customer message", value="Toi can gui 300 kg sang Canada", height=90, key=f"{campaign_key}_sales_agent_message")
        with sa_cols[1]:
            sales_origin = st.selectbox("Origin", countries, index=_country_index(countries, "viet nam"), key=f"{campaign_key}_sales_agent_origin")
            sales_product = st.text_input("Product", value="General cargo", key=f"{campaign_key}_sales_agent_product")
        with sa_cols[2]:
            sales_service = st.selectbox("Service", SERVICE_LEVELS, index=1, key=f"{campaign_key}_sales_agent_service")
        workflow, sales_quote, email_draft, crm_note = _ai_sales_agent_workflow(sales_message, sales_origin, sales_product, sales_service)
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Destination", str(sales_quote["destination"]))
        k2.metric("Weight", f"{float(sales_quote['chargeable_weight']):,.0f} kg")
        k3.metric("ETA", str(sales_quote["eta"]))
        k4.metric("Quote", f"${float(sales_quote['total_usd']):,.2f}")
        st.dataframe(workflow, use_container_width=True, hide_index=True)
        e1, e2 = st.columns(2)
        with e1:
            st.text_area("Email draft", value=email_draft, height=220, key=f"{campaign_key}_sales_email")
        with e2:
            st.text_area("CRM handoff", value=crm_note, height=220, key=f"{campaign_key}_sales_crm")

    elif selected_tab == tab_labels[12]: 
        st.markdown("##### AI Freight Knowledge Base")
        st.caption("Freight Context Hub: one shipment context powers RAG, Quote, Customs, Export Consultant, Shipping Cost, HS Code, Tracking, and Sales Agent.")
        countries = list(COUNTRY_ZONES.keys())
        kb_cols = st.columns([1, 1, 1, 1])
        with kb_cols[0]:
            kb_topic = st.selectbox("Knowledge area", list(FREIGHT_KB_TOPICS.keys()), key=f"{campaign_key}_kb_topic")
            kb_origin = st.selectbox("Origin", countries, index=_country_index(countries, "viet nam"), key=f"{campaign_key}_hub_origin")
        with kb_cols[1]:
            kb_destination = st.selectbox("Destination", countries, index=_country_index(countries, "canada"), key=f"{campaign_key}_kb_destination")
            kb_product = st.text_input("Product / HS context", value="Roasted coffee", key=f"{campaign_key}_kb_product")
        with kb_cols[2]:
            kb_mode = st.selectbox("Quote mode", FREIGHT_MODES, key=f"{campaign_key}_hub_mode")
            kb_service = st.selectbox("Service", SERVICE_LEVELS, index=1, key=f"{campaign_key}_hub_service")
        with kb_cols[3]:
            kb_weight = st.number_input("Weight kg", min_value=1.0, value=300.0, step=25.0, key=f"{campaign_key}_hub_weight")
            kb_value = st.number_input("Cargo value USD", min_value=0.0, value=2400.0, step=100.0, key=f"{campaign_key}_hub_value")

        hub_cols = st.columns([1, 1, 1, 1])
        with hub_cols[0]:
            kb_volume = st.number_input("Volume CBM", min_value=0.1, value=1.2, step=0.1, key=f"{campaign_key}_hub_cbm")
        with hub_cols[1]:
            hub_shipment_mode = st.selectbox("Customs mode", ["Air", "Sea", "Multi-modal"], key=f"{campaign_key}_hub_customs_mode")
        with hub_cols[2]:
            hub_tracking = st.text_input("Tracking number", value="JD014600006789012345", key=f"{campaign_key}_hub_tracking")
        with hub_cols[3]:
            hub_carrier = st.selectbox("Carrier", list(TRACKING_CARRIERS.keys()), key=f"{campaign_key}_hub_carrier")

        hub_docs = st.multiselect(
            "Documents available",
            list(CUSTOMS_DOCUMENTS.keys()),
            default=["Invoice", "Packing List"],
            key=f"{campaign_key}_hub_docs",
        )
        hub_claim_fta = st.checkbox("Claim FTA / preferential tariff", value=True, key=f"{campaign_key}_hub_fta")
        kb_question = st.text_area(
            "Question",
            value="What should I check for Incoterms, HS Code, tax, documents, quote, shipping cost, tracking, and sales follow-up when shipping to Canada?",
            height=90,
            key=f"{campaign_key}_kb_question",
        )

        hub = _freight_context_hub(
            question=kb_question,
            topic=kb_topic,
            origin=kb_origin,
            destination=kb_destination,
            product=kb_product,
            quote_mode=kb_mode,
            service_level=kb_service,
            weight_kg=kb_weight,
            volume_cbm=kb_volume,
            cargo_value_usd=kb_value,
            shipment_mode=hub_shipment_mode,
            selected_docs=hub_docs,
            claim_fta=hub_claim_fta,
            tracking_number=hub_tracking,
            carrier=hub_carrier,
            promised_days=7,
            product_cost_usd=40.0,
            target_margin_pct=30.0,
        )

        st.success(str(hub["answer"]))
        st.markdown("##### Connected Modules")
        st.dataframe(hub["summary"], use_container_width=True, hide_index=True)

        hub_tab_labels = ["RAG", "Quote", "Shipping Cost", "HS Code", "Customs", "Export", "Tracking", "Sales"]
        selected_hub_tab = st.pills(
            "Knowledge Base section",
            hub_tab_labels,
            default=hub_tab_labels[0],
            key=f"{campaign_key}_hub_active_section",
            label_visibility="collapsed",
            width="stretch",
        ) or hub_tab_labels[0]
        if selected_hub_tab == hub_tab_labels[0]: 
            st.dataframe(hub["kb_sources"], use_container_width=True, hide_index=True)
            st.dataframe(hub["route_options"], use_container_width=True, hide_index=True)
        elif selected_hub_tab == hub_tab_labels[1]: 
            st.dataframe(hub["quote"], use_container_width=True, hide_index=True)
        elif selected_hub_tab == hub_tab_labels[2]: 
            st.dataframe(hub["shipping"], use_container_width=True, hide_index=True)
        elif selected_hub_tab == hub_tab_labels[3]: 
            st.dataframe(hub["hs_table"], use_container_width=True, hide_index=True)
        elif selected_hub_tab == hub_tab_labels[4]: 
            st.dataframe(hub["customs_audit"], use_container_width=True, hide_index=True)
        elif selected_hub_tab == hub_tab_labels[5]: 
            st.dataframe(hub["export_advice"], use_container_width=True, hide_index=True)
        elif selected_hub_tab == hub_tab_labels[6]: 
            st.dataframe(hub["tracking"], use_container_width=True, hide_index=True)
            if not hub["timeline"].empty:
                st.dataframe(hub["timeline"], use_container_width=True, hide_index=True)
        elif selected_hub_tab == hub_tab_labels[7]: 
            st.dataframe(hub["sales_workflow"], use_container_width=True, hide_index=True)
            s1, s2 = st.columns(2)
            with s1:
                st.text_area("Sales email from hub", value=str(hub["email_draft"]), height=200, key=f"{campaign_key}_hub_email")
            with s2:
                st.text_area("CRM note from hub", value=str(hub["crm_note"]), height=200, key=f"{campaign_key}_hub_crm")

    elif selected_tab == tab_labels[13]: 
        st.markdown("##### AI Route Planner")
        st.caption("Optimize Vietnam -> Singapore -> Germany -> Netherlands -> Last Mile and compare transit time, cost, and CO2.")
        rp_cols = st.columns(3)
        with rp_cols[0]:
            route_weight = st.number_input("Weight kg", min_value=1.0, value=300.0, step=25.0, key=f"{campaign_key}_route_weight")
        with rp_cols[1]:
            route_value = st.number_input("Cargo value USD", min_value=0.0, value=2400.0, step=100.0, key=f"{campaign_key}_route_value")
        with rp_cols[2]:
            route_priority = st.selectbox("Priority", ["Balanced", "Fastest", "Lowest cost", "Lowest CO2"], key=f"{campaign_key}_route_priority")
        route_options = _route_planner_options(route_weight, route_value, route_priority)
        best_route = route_options.iloc[0]
        r1, r2, r3 = st.columns(3)
        r1.metric("Best option", best_route["Option"])
        r2.metric("Cost", f"${best_route['Cost USD']:,.2f}")
        r3.metric("CO2", f"{best_route['CO2 kg']:,.0f} kg")
        st.dataframe(route_options, use_container_width=True, hide_index=True)
        st.info(f"AI recommends {best_route['Option']} because it matches priority '{route_priority}' with score {best_route['AI score']}.")

    elif selected_tab == tab_labels[14]: 
        st.markdown("##### AI Margin Simulator")
        st.caption("Simulate margin when shipping, duty, VAT, commission, or carrier cost changes.")
        margin_cols = st.columns(6)
        with margin_cols[0]:
            product_price = st.number_input("Product price", min_value=0.0, value=40.0, step=1.0, key=f"{campaign_key}_margin_price")
        with margin_cols[1]:
            margin_shipping = st.number_input("Shipping", min_value=0.0, value=8.0, step=0.5, key=f"{campaign_key}_margin_shipping")
        with margin_cols[2]:
            margin_duty = st.number_input("Duty", min_value=0.0, value=6.0, step=0.5, key=f"{campaign_key}_margin_duty")
        with margin_cols[3]:
            margin_vat = st.number_input("VAT", min_value=0.0, value=4.0, step=0.5, key=f"{campaign_key}_margin_vat")
        with margin_cols[4]:
            margin_commission = st.number_input("Commission", min_value=0.0, value=5.0, step=0.5, key=f"{campaign_key}_margin_commission")
        with margin_cols[5]:
            new_shipping = st.number_input("New shipping", min_value=0.0, value=6.0, step=0.5, key=f"{campaign_key}_margin_new_shipping")
        margin_table, margin_recommendation = _margin_scenario(product_price, margin_shipping, margin_duty, margin_vat, margin_commission, new_shipping)
        m1, m2 = st.columns(2)
        m1.metric("Current margin", f"{float(margin_table.iloc[0]['Margin %']):.1f}%")
        m2.metric("Optimized margin", f"{float(margin_table.iloc[1]['Margin %']):.1f}%")
        st.dataframe(margin_table, use_container_width=True, hide_index=True)
        st.success(margin_recommendation)

    elif selected_tab == tab_labels[15]: 
        st.markdown("##### AI Shipping Dashboard")
        st.caption("Tong hop hieu suat van chuyen: shipment volume, monthly cost, ETA, on-time rate, cost by country, carrier, customer, and delayed shipment alerts.")

        shipments_key = _growth_key(workspace_id, "shipments")
        if shipments_key not in st.session_state:
            st.session_state[shipments_key] = _sample_shipments()

        upload = st.file_uploader("Import shipment CSV", type=["csv"], key=f"{shipments_key}_upload", disabled=not can_edit)
        if upload is not None and can_edit:
            imported = pd.read_csv(upload)
            st.session_state[shipments_key] = imported
            st.success(f"Imported {len(imported)} shipments.")

        raw_shipments = st.session_state[shipments_key].copy()
        if raw_shipments.empty:
            st.info("Chua co du lieu lo hang. Hay import CSV hoac them dong moi trong bang ben duoi.")
        else:
            display_cols = [
                "shipment_id",
                "customer",
                "origin_country",
                "destination_country",
                "carrier",
                "mode",
                "ship_date",
                "shipping_cost_usd",
                "planned_eta_days",
                "actual_eta_days",
                "status",
            ]
            for col in display_cols:
                if col not in raw_shipments.columns:
                    raw_shipments[col] = "" if col not in {"shipping_cost_usd", "planned_eta_days", "actual_eta_days"} else 0

            edited_shipments = st.data_editor(
                raw_shipments[display_cols],
                use_container_width=True,
                hide_index=True,
                num_rows="dynamic" if can_edit else "fixed",
                disabled=not can_edit,
                column_config={
                    "shipping_cost_usd": st.column_config.NumberColumn("shipping_cost_usd", min_value=0.0, step=50.0),
                    "planned_eta_days": st.column_config.NumberColumn("planned_eta_days", min_value=0, step=1),
                    "actual_eta_days": st.column_config.NumberColumn("actual_eta_days", min_value=0, step=1),
                    "status": st.column_config.SelectboxColumn("status", options=["Delivered", "In Transit", "Delayed", "Exception", "Cancelled"]),
                },
                key=f"{shipments_key}_editor",
            )
            if can_edit:
                st.session_state[shipments_key] = edited_shipments

            shipments = _prepare_shipping_dashboard(edited_shipments)
            total_shipments = len(shipments)
            total_cost = float(shipments["shipping_cost_usd"].sum())
            avg_eta = float(shipments["actual_eta_days"].mean()) if total_shipments else 0.0
            on_time_rate = float((~shipments["is_late"]).mean() * 100) if total_shipments else 0.0
            delayed_count = int(shipments["is_late"].sum())

            k1, k2, k3, k4, k5 = st.columns(5)
            k1.metric("Tong so lo hang", f"{total_shipments:,}")
            k2.metric("Tong chi phi", f"${total_cost:,.0f}")
            k3.metric("ETA trung binh", f"{avg_eta:.1f} ngay")
            k4.metric("Ty le dung han", f"{on_time_rate:.1f}%")
            k5.metric("Lo hang cham", delayed_count)

            cost_by_month = shipments.groupby("month", as_index=False)["shipping_cost_usd"].sum().sort_values("month")
            country_cost = shipments.groupby("destination_country", as_index=False)["shipping_cost_usd"].sum().sort_values("shipping_cost_usd", ascending=False)
            carrier_cost = shipments.groupby("carrier", as_index=False)["shipping_cost_usd"].sum().sort_values("shipping_cost_usd", ascending=False)
            customer_cost = shipments.groupby("customer", as_index=False)["shipping_cost_usd"].sum().sort_values("shipping_cost_usd", ascending=False)

            chart_a, chart_b = st.columns(2)
            with chart_a:
                st.markdown("##### Chi phi van chuyen theo thang")
                st.line_chart(cost_by_month, x="month", y="shipping_cost_usd", use_container_width=True)
            with chart_b:
                st.markdown("##### Chi phi theo quoc gia")
                st.bar_chart(country_cost, x="destination_country", y="shipping_cost_usd", use_container_width=True)

            chart_c, chart_d = st.columns(2)
            with chart_c:
                st.markdown("##### Chi phi theo hang")
                st.bar_chart(carrier_cost, x="carrier", y="shipping_cost_usd", use_container_width=True)
            with chart_d:
                st.markdown("##### Chi phi theo khach hang")
                st.bar_chart(customer_cost.head(10), x="customer", y="shipping_cost_usd", use_container_width=True)

            delayed_shipments = shipments[shipments["is_late"]].sort_values(["delay_days", "shipping_cost_usd"], ascending=[False, False])
            st.markdown("##### Canh bao lo hang cham")
            if delayed_shipments.empty:
                st.success("Khong co lo hang cham so voi ETA ke hoach.")
            else:
                st.warning(f"Co {len(delayed_shipments)} lo hang cham. Uu tien lien he carrier va cap nhat khach hang trong ngay.")
                st.dataframe(
                    delayed_shipments[[
                        "shipment_id",
                        "customer",
                        "destination_country",
                        "carrier",
                        "planned_eta_days",
                        "actual_eta_days",
                        "delay_days",
                        "shipping_cost_usd",
                        "status",
                    ]],
                    use_container_width=True,
                    hide_index=True,
                )

            st.download_button(
                "Export shipping dashboard CSV",
                shipments.to_csv(index=False).encode("utf-8-sig"),
                "ai_shipping_dashboard.csv",
                "text/csv",
                use_container_width=True,
                key=f"{shipments_key}_download",
            )
