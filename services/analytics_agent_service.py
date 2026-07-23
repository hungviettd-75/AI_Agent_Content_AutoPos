"""Service wrapper for Analytics Agent model calls."""

import json

from services.gemini_client import generate_with_gemini


def analyze_analytics_question(summary: dict, days_range: str, user_query: str, api_key: str) -> str:
    """Return an Analytics Agent answer from a compact analytics summary.

    The API key is accepted as an argument and is never logged or persisted here.
    """
    prompt = f"""
Ban la Analytics Agent chuyen nghiep trong he thong AI-Agent Marketing Portal.
Nhiem vu: Phan tich du lieu va dua ra loi khuyen chien luoc cu the, co the hanh dong ngay.

KPI & Du lieu ({days_range}):
{json.dumps(summary, ensure_ascii=False, indent=2)}

Cau hoi: "{user_query}"

Trinh bay theo cau truc Markdown:
1. **Phan tich so lieu** - nhan xet truc tiep voi so lieu cu the
2. **Insight noi bat** - 3 diem thu vi nhat tu du lieu
3. **De xuat hanh dong** - 3-5 buoc cu the de cai thien ROI, CTR, Lead
4. **Canh bao rui ro** - diem nao dang yeu can chu y?

Chi neu tuong quan khi du lieu chi cho thay tuong quan; khong khang dinh quan he nhan qua neu khong co thiet ke thi nghiem.
Luon tra loi bang Tieng Viet chuyen nghiep, than thien.
"""
    return generate_with_gemini(prompt, api_key=api_key)
