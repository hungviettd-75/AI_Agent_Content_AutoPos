"""
services/fact_check_service.py
===============================
Fact Checking Agent – Tác nhân kiểm tra dữ liệu và tuyên bố trong bài viết.
Sử dụng Gemini API + Google Search Grounding để tra cứu thông tin trực tiếp.
"""
import json
import re
from config.config import logger
from services.gemini_client import generate_with_gemini


def extract_claims(text: str, max_claims: int = 5, api_key: str = None) -> list[str]:
    """
    Trích xuất các tuyên bố, số liệu, sự kiện chính cần kiểm chứng từ nội dung.
    """
    logger.info(f"[FactCheck] Trích xuất tuyên bố từ nội dung (Tối đa: {max_claims})")
    
    prompt = f"""Bạn là một chuyên gia phân tích và Fact Checker.
Nhiệm vụ: Hãy trích xuất từ nội dung dưới đây tối đa {max_claims} tuyên bố, số liệu, sự kiện hoặc luận điểm chính cần được kiểm chứng tính xác thực (Fact-check).
Chỉ trích xuất những tuyên bố có thể kiểm chứng được (ví dụ: số liệu thống kê, tên người/sự kiện, tuyên bố về công nghệ, sản phẩm, dữ liệu lịch sử...).

Nội dung:
---
{text}
---

Yêu cầu đầu ra: Trả về ĐÚNG định dạng JSON sau, không giải thích thêm:
{{
  "claims": [
    "Tuyên bố 1",
    "Tuyên bố 2"
  ]
}}
"""
    try:
        raw_response = generate_with_gemini(prompt, api_key=api_key)
        
        # Parse JSON
        try:
            data = json.loads(raw_response.strip())
            return data.get("claims", [])[:max_claims]
        except json.JSONDecodeError:
            pass

        # Match markdown block
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_response, re.DOTALL)
        if match:
            data = json.loads(match.group(1))
            return data.get("claims", [])[:max_claims]

        # Match generic braces
        match = re.search(r"\{.*\}", raw_response, re.DOTALL)
        if match:
            data = json.loads(match.group(0))
            return data.get("claims", [])[:max_claims]

        # Fallback split
        lines = [line.strip().lstrip("-*1234567890. ") for line in raw_response.split("\n") if line.strip()]
        return [l for l in lines if len(l) > 10][:max_claims]
        
    except Exception as e:
        logger.error(f"[FactCheck] Lỗi trích xuất tuyên bố: {e}", exc_info=True)
        return []


def verify_claim(claim: str, api_key: str = None) -> dict:
    """
    Xác minh một tuyên bố cụ thể bằng cách sử dụng Google Search Grounding qua Gemini.
    """
    logger.info(f"[FactCheck] Xác minh tuyên bố: '{claim[:50]}...'")
    
    prompt = f"""Bạn là một Fact Checker độc lập chuyên nghiệp.
Nhiệm vụ: Hãy kiểm chứng tuyên bố dưới đây. Sử dụng Google Search để tìm kiếm các bằng chứng, bài báo, tài liệu uy tín nhất liên quan đến tuyên bố này.

Tuyên bố cần kiểm chứng:
"{claim}"

Yêu cầu trả về kết quả dưới dạng JSON ĐÚNG cấu trúc sau, không giải thích thêm:
{{
  "claim": "Tuyên bố gốc được kiểm chứng",
  "status": "confirmed | needs_review | incorrect | unverifiable",
  "verdict": "Phán quyết ngắn gọn (1 câu, tối đa 15 từ)",
  "explanation": "Giải thích chi tiết các bằng chứng tìm thấy và lý do đưa ra phán quyết (3-4 câu)",
  "sources": [
    "URL nguồn uy tín 1 hoặc tên nguồn chính thức",
    "URL nguồn uy tín 2 hoặc tên nguồn chính thức"
  ],
  "corrected": "Phiên bản sửa đổi chính xác của tuyên bố nếu status là 'incorrect' hoặc 'needs_review'. Nếu đúng hoặc không thể xác minh, để null."
}}

Quy tắc phân loại trạng thái (status):
- "confirmed": Nếu tuyên bố hoàn toàn chính xác và có nguồn uy tín xác thực.
- "needs_review": Nếu tuyên bố chỉ đúng một phần, thiếu ngữ cảnh quan trọng hoặc số liệu có sai lệch nhẹ.
- "incorrect": Nếu tuyên bố là sai sự thật, số liệu sai lệch nghiêm trọng hoặc có bằng chứng mâu thuẫn rõ ràng.
- "unverifiable": Nếu không tìm thấy đủ nguồn thông tin uy tín để đưa ra kết luận.
"""
    try:
        # Gọi Gemini với Google Search Grounding (enable_research=True)
        raw_response = generate_with_gemini(prompt, api_key=api_key, enable_research=True)
        
        # Parse JSON
        try:
            result = json.loads(raw_response.strip())
        except json.JSONDecodeError:
            match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_response, re.DOTALL)
            if match:
                result = json.loads(match.group(1))
            else:
                match = re.search(r"\{.*\}", raw_response, re.DOTALL)
                if match:
                    result = json.loads(match.group(0))
                else:
                    raise ValueError("Không thể trích xuất JSON")
                    
        # Đảm bảo các field tồn tại
        result["claim"] = result.get("claim", claim)
        status = result.get("status", "unverifiable").strip().lower()
        if status not in ["confirmed", "needs_review", "incorrect", "unverifiable"]:
            status = "unverifiable"
        result["status"] = status
        result["verdict"] = result.get("verdict", "Không thể xác định")
        result["explanation"] = result.get("explanation", "Không thể lấy thông tin chi tiết.")
        result["sources"] = result.get("sources", [])
        if not isinstance(result["sources"], list):
            result["sources"] = [str(result["sources"])]
        result["corrected"] = result.get("corrected", None)
        
        return result
        
    except Exception as e:
        logger.error(f"[FactCheck] Lỗi xác minh tuyên bố '{claim[:30]}': {e}", exc_info=True)
        return {
            "claim": claim,
            "status": "unverifiable",
            "verdict": "Lỗi hệ thống khi xác minh",
            "explanation": f"Gặp lỗi khi xác minh tuyên bố: {str(e)}",
            "sources": [],
            "corrected": None
        }


def fact_check_content(text: str, max_claims: int = 5, api_key: str = None) -> list[dict]:
    """
    Hàm chính: Trích xuất các claims và thực hiện xác minh từng claim một.
    """
    claims = extract_claims(text, max_claims, api_key)
    results = []
    
    if not claims:
        logger.warning("[FactCheck] Không trích xuất được tuyên bố nào từ nội dung.")
        return []
        
    for c in claims:
        res = verify_claim(c, api_key)
        results.append(res)
        
    return results


def apply_corrected_claims(original_text: str, fact_check_results: list[dict]) -> str:
    """
    Thay thế các tuyên bố sai (incorrect/needs_review) trong văn bản gốc bằng phiên bản đã sửa đổi (corrected).
    """
    modified_text = original_text
    for res in fact_check_results:
        original_claim = res.get("claim")
        corrected_claim = res.get("corrected")
        status = res.get("status")
        
        if status in ["incorrect", "needs_review"] and corrected_claim and original_claim:
            # Thay thế đơn giản (case-insensitive)
            # Thử tìm khớp chính xác trước
            if original_claim in modified_text:
                modified_text = modified_text.replace(original_claim, corrected_claim)
            else:
                # Nếu không tìm thấy khớp chính xác, thử thay thế với regex cơ bản hoặc skip
                # Do Gemini viết lại claim có thể lệch một chút so với câu gốc, nên cố gắng tìm kiếm tương đồng
                pass
                
    return modified_text
