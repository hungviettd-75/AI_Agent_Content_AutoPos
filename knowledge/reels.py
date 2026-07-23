from config.config import DEFAULT_STYLE_RULES

def generate_knowledge_reels_script(topic, audience="Người mới", ai_tool="AI", duration_seconds=45):
    safe_duration = max(30, min(int(duration_seconds or 45), 60))
    topic_text = str(topic).strip() or "một kỹ năng AI thực chiến"
    audience_text = str(audience).strip() or "Người mới"
    tool_text = str(ai_tool).strip() or "AI"

    return f"""# Knowledge Reels Script: {topic_text}

**Thời lượng:** {safe_duration} giây  
**Đối tượng:** {audience_text}  
**Công cụ/chủ đề:** {tool_text}

## Hook
Bạn đang dùng {tool_text} nhưng kết quả vẫn chung chung? Có thể bạn thiếu đúng 1 bước: nói rõ bối cảnh trước khi yêu cầu AI trả lời.

## Scene
| Thời gian | Cảnh quay | Mục tiêu giữ chân |
| --- | --- | --- |
| 0-3s | Cận mặt người nói, mở bằng câu hỏi trực diện trên màn hình. | Gây đồng cảm với lỗi phổ biến. |
| 4-12s | Hiển thị ví dụ prompt sai: "Viết giúp tôi nội dung về {topic_text}". | Cho người xem thấy vấn đề quen thuộc. |
| 13-28s | Chuyển sang prompt tốt hơn có ROLE, CONTEXT, TASK, OUTPUT. | Tạo cảm giác có công thức áp dụng ngay. |
| 29-42s | So sánh kết quả trước/sau bằng 2 khung text ngắn. | Chứng minh khác biệt cụ thể. |
| 43-{safe_duration}s | Người nói tóm tắt 3 ý chính, hiện checklist. | Chốt bài học và tăng lưu nhớ. |

## Voice over
"If you ask AI too broadly, the answer will usually be broad as well.  
For example: 'Help me write content about {topic_text}' sounds okay, but AI doesn't know who you are writing for, what your goal is, or what output format you want.  
A better way is to add 4 parts: role, context, task, and output format.  
For example: 'You are an AI trainer for {audience_text}. Explain {topic_text} using simple examples and include a checklist at the end.'  
By just adding context like this, the response will be much more targeted."

## Subtitle
- Đừng hỏi AI quá chung
- Prompt thiếu bối cảnh = kết quả mơ hồ
- Công thức nhanh: ROLE + CONTEXT + TASK + OUTPUT
- Ví dụ tốt hơn: nói rõ người đọc, mục tiêu, định dạng
- Muốn AI trả lời tốt, hãy giao việc rõ như giao cho một nhân sự thật

## CTA
Bạn thử lấy một prompt đang dùng hằng ngày và thêm 4 phần: ROLE, CONTEXT, TASK, OUTPUT. Sau đó so sánh kết quả trước và sau.
""".strip()

def generate_reels_prompt(topic, audience="Người mới", ai_tool="AI", duration_seconds=45):
    safe_duration = max(30, min(int(duration_seconds or 45), 60))
    return f"""Tạo kịch bản video short {safe_duration} giây cho Facebook Reels/TikTok.

Chủ đề: {topic}
Đối tượng: {audience}
Công cụ/chủ đề AI: {ai_tool}

Yêu cầu phong cách:
- Dễ hiểu.
- Giáo dục.
- Không quảng cáo.
- Không bán hàng.
- Retention cao.
- Nhiều ví dụ thực tế.

Output đúng 5 phần:
1. Hook
2. Scene
3. Voice over
4. Subtitle
5. CTA
""".strip()
