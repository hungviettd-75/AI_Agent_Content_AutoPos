import re

def parse_viral_score_and_reason(full_content):
    """
    Trích xuất điểm số Viral Score (1-10) và Lý do chấm điểm từ nội dung bài viết marketing sinh ra bởi AI.
    """
    viral_score = None
    reason = ""
    
    # Tìm kiếm phần Viral Score
    score_match = re.search(r"### 14\.\s*Viral Score\s*\(1-10\)\s*\n+(.*)", full_content, re.IGNORECASE)
    if score_match:
        score_text = score_match.group(1).strip()
        # Tìm số từ 1 đến 10 trong dòng đầu tiên của phần này
        num_match = re.search(r"\b([1-9]|10)\b", score_text)
        if num_match:
            try:
                viral_score = int(num_match.group(1))
            except ValueError:
                pass
                
    # Tìm kiếm phần Lý do chấm điểm
    reason_match = re.search(r"### 15\.\s*Lý do chấm điểm\s*\n+([\s\S]*)", full_content, re.IGNORECASE)
    if reason_match:
        reason = reason_match.group(1).strip()
        # Loại bỏ các thông tin thừa ở cuối nếu có
        reason = reason.split("🌐 Website")[0].strip()
        
    return viral_score, reason
