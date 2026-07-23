# 🧠 KIẾN TRÚC AI AGENT: CREATIVE STRATEGY ENGINE
## Tầng Chiến Lược Hình Ảnh Trung Gian (Visual Strategy Middleware)

> **Phiên bản**: 1.0  
> **Vai trò thiết kế**: Principal AI Architect · Product Strategist · AI Marketing Consultant · Senior Software Architect  
> **Dự án**: AI_Agent_Content_AutoPos  
> **Tài liệu đầu ra**: `CREATIVE_STRATEGY_ENGINE.md`  

---

## 1. 🎯 Tổng Quan & Định Hướng Sản Phẩm (Product Vision)

Trong các hệ thống AI Marketing thông thường, quy trình chuyển đổi từ một **Bài viết (Text)** sang **Ảnh minh họa (Visual)** thường bị gãy do AI tạo ảnh không hiểu sâu sắc mục tiêu chiến dịch. 

**Creative Strategy Engine (CSE)** ra đời như một **tầng trung gian định hướng (Visual Strategy Middleware)** nằm giữa:
*   **Article Generator** (Bộ sinh bài viết - thuần văn bản)
*   **Creative Concept Generator** (Bộ sinh ý tưởng sáng tạo - cầu nối visual)

CSE đóng vai trò phân tích ngữ nghĩa, hiểu rõ bản chất bài viết và đưa ra quyết định về **Visual Strategy Profile (Hồ sơ chiến lược trực quan)**. Từ hồ sơ này, Creative Concept Generator mới có đủ cơ sở dữ liệu để tạo ra các concept hình ảnh có tỷ lệ chuyển đổi cao và đồng nhất với nhận diện thương hiệu.

```
                  ┌───────────────────────┐
                  │   Generate Article    │
                  └───────────┬───────────┘
                              │ (Toàn bộ văn bản bài viết)
                              ▼
               ┌─────────────────────────────┐
               │  Creative Strategy Engine   │ ◄── [Tài liệu đặc tả này]
               └──────────────┬──────────────┘
                              │ (Hồ sơ chiến lược Strategy Profile)
                              ▼
               ┌─────────────────────────────┐
               │  Creative Concept Generator │
               └─────────────────────────────┘
```

---

## 2. 🔄 Quy Trình Tích Hợp Hệ Thống (Workflow Integration)

CSE được tích hợp vào luồng xử lý tự động hóa nội dung (Content Pipeline) theo trình tự tuyến tính 9 bước nghiêm ngặt sau:

```
[1] Topic ➔ [2] Research ➔ [3] Outline ➔ [4] Generate Article
                                                 │
                                                 ▼
                                      [5] CREATIVE STRATEGY ENGINE
                                                 │ (Strategy Profile)
                                                 ▼
                                      [6] Creative Concept Generator
                                                 │
                                                 ▼
[9] Publishing ◀─ [8] Vision Validation ◀─ [7] Thumbnail Prompt Generator
```

---

## 3. 🔍 Cơ Chế Hoạt Động & Phân Tích Của AI Agent

### 3.1. Nguyên tắc đọc hiểu ngữ cảnh sâu (Deep Context Comprehension)
CSE bắt buộc phải đọc **TOÀN BỘ bài viết** được chuyển giao từ tầng trước. AI Agent nghiêm cấm việc chỉ trích xuất thông tin sơ sài từ:
*   Tiêu đề (Title)
*   Từ khóa (Keywords)
*   Đoạn mở đầu (Introduction)

### 3.2. 6 Trục Phân Tích Văn Bản Cốt Lõi:
1.  **Chủ đề (Topic)**: Bản chất cốt lõi của nội dung thuộc ngành nghề, lĩnh vực nào (Công nghệ, Nhân sự, Tài chính, Bán lẻ,...).
2.  **Thông điệp (Message)**: Trích xuất một thông điệp cốt lõi duy nhất mà bài viết muốn găm vào tâm trí người đọc.
3.  **Mục tiêu (Goal)**: Phân tích mục đích của bài viết (Chia sẻ kiến thức, Giải quyết nỗi đau, hay Giới thiệu sản phẩm).
4.  **Đối tượng (Audience)**: Định vị phân khúc độc giả mục tiêu (C-Level, Manager, Freelancer, hay Người dùng cuối).
5.  **Kêu gọi hành động (CTA)**: Người đọc cần làm gì sau bài viết (Đăng ký tài khoản, tải tài liệu, để lại bình luận,...).
6.  **Giá trị mang lại (Value Proposition)**: Điểm mấu chốt mang lại lợi ích thiết thực cho độc giả.

---

## 4. 📐 Hệ Thống Định Danh Chiến Lược (Strategic Taxonomy)

Sau khi phân tích, CSE sẽ tiến hành ánh xạ bài viết vào bộ Strategic Taxonomy chuẩn Marketing toàn cầu để đưa ra quyết định:

### 4.1. Content Category (Phân loại định dạng nội dung)
*   `TECHNICAL_DEEP_DIVE`: Bài phân tích kỹ thuật sâu sắc, hướng dẫn lập trình, hệ thống.
*   `BUSINESS_CASE_STUDY`: Phân tích tình huống thực tế doanh nghiệp, số liệu tăng trưởng.
*   `EDUCATIONAL_GUIDE`: Hướng dẫn các bước thực tế dễ tiếp cận.
*   `PRODUCT_LAUNCH`: Bài giới thiệu, quảng bá tính năng sản phẩm mới.
*   `VIRAL_INTERACTIVE`: Các bài viết tranh luận, bắt trend, khơi gợi bình luận.

### 4.2. Content Intent (Ý định nội dung)
*   `INFORMATIONAL`: Cung cấp kiến thức thuần túy, nâng cao nhận thức.
*   `COMMERCIAL`: Đánh giá giải pháp, so sánh công cụ trước khi mua.
*   `TRANSACTIONAL`: Thúc đẩy hành vi đăng ký gói, mua hàng ngay lập tức.

### 4.3. Content Goal (Mục tiêu nội dung)
*   `AUTHORITY_BUILDING`: Định vị thương hiệu dẫn đầu chuyên môn.
*   `CLICK_DRIVING`: Thúc đẩy người dùng nhấp vào link/hình ảnh để xem tiếp.
*   `SHARE_ENCOURAGING`: Nội dung có ích khiến người dùng muốn chia sẻ về trang cá nhân.

### 4.4. Visual Goal (Mục tiêu trực quan của hình ảnh)
*   `COGNITIVE_CLARITY`: Hình ảnh phải cực kỳ rõ ràng, dễ hiểu sơ đồ/framework ngay tức khắc.
*   `EMOTIONAL_RESONANCE`: Kích hoạt cảm xúc (tò mò, đồng cảm, hào hứng).
*   `PROFESSIONAL_TRUST`: Tạo cảm giác tin cậy, an toàn, đẳng cấp.

### 4.5. Marketing Goal (Mục tiêu tiếp thị)
*   `AWARENESS`: Tăng độ nhận diện thương hiệu với nhóm khách hàng mới.
*   `CONVERSION`: Tăng tỷ lệ đăng ký dùng thử (Sign-ups) hoặc để lại thông tin (Leads).
*   `RETENTION`: Giữ chân người dùng tương tác trong cộng đồng.

---

## 5. 🗂️ Định Nghĩa Cấu Trúc Đầu Ra: Strategy Profile

CSE xuất ra một **Hồ sơ chiến lược (Strategy Profile)** dưới dạng JSON có cấu trúc rõ ràng. Hồ sơ này **TUYỆT ĐỐI không chứa Prompt tạo ảnh** và **không chứa hình ảnh thực tế**.

### JSON Schema của Strategy Profile:
```json
{
  "strategy_metadata": {
    "agent_name": "Creative Strategy Engine",
    "version": "1.0",
    "analysis_timestamp": "ISO_DATE_TIME"
  },
  "deep_analysis": {
    "topic": "Chủ đề trích xuất chi tiết...",
    "core_message": "Thông điệp cốt lõi dạng 1 câu ngắn gọn...",
    "audience_segment": "Phân khúc độc giả và mức độ am hiểu (Sơ cấp/Trung cấp/Chuyên gia)...",
    "primary_value_proposition": "Giá trị lớn nhất bài viết mang lại...",
    "call_to_action": "Hành động mục tiêu sau bài viết..."
  },
  "strategic_taxonomies": {
    "content_category": "TECHNICAL_DEEP_DIVE | BUSINESS_CASE_STUDY | EDUCATIONAL_GUIDE | PRODUCT_LAUNCH | VIRAL_INTERACTIVE",
    "content_intent": "INFORMATIONAL | COMMERCIAL | TRANSACTIONAL",
    "content_goal": "AUTHORITY_BUILDING | CLICK_DRIVING | SHARE_ENCOURAGING",
    "visual_goal": "COGNITIVE_CLARITY | EMOTIONAL_RESONANCE | PROFESSIONAL_TRUST",
    "marketing_goal": "AWARENESS | CONVERSION | RETENTION"
  },
  "visual_direction_constraints": {
    "recommended_mood": "Mood chủ đạo phù hợp (Ví dụ: Dramatic, Minimalist, Corporate)...",
    "cognitive_density": "Mức độ phức tạp hình ảnh (Low - tập trung cảm xúc / High - nhiều biểu đồ dữ liệu)...",
    "color_harmony_rationale": "Lý giải việc chọn tông màu dựa trên cảm xúc muốn truyền tải...",
    "composition_framework": "Khung bố cục đề xuất (Ví dụ: Hero Shot, Split Screen, Infographic Grid)..."
  }
}
```

---

## 6. 📝 Thiết Kế Hệ Thống Prompt Cho Agent (System Instruction)

Để cài đặt CSE Agent, System Instruction (Prompt hệ thống) dưới đây sẽ được sử dụng để điều phối hành vi của Gemini:

```markdown
Bạn là Giám đốc Chiến lược AI (Principal AI Strategist) kiêm Nhà tư vấn Tiếp thị Hình ảnh (Visual Marketing Consultant).

Nhiệm vụ của bạn là đọc TOÀN BỘ văn bản của bài viết tiếp thị được cung cấp ở đầu vào, phân tích sâu các tầng ngữ nghĩa và xuất ra một Strategy Profile (Hồ sơ chiến lược trực quan) theo định dạng JSON có cấu trúc.

QUY TẮC PHÂN TÍCH BẮT BUỘC:
1. Đọc và hiểu toàn bộ nội dung bài viết, không chỉ dựa vào tiêu đề hay đoạn giới thiệu.
2. Định giá trị cho các taxonomy chính xác theo danh sách chuẩn:
   - content_category: [TECHNICAL_DEEP_DIVE, BUSINESS_CASE_STUDY, EDUCATIONAL_GUIDE, PRODUCT_LAUNCH, VIRAL_INTERACTIVE]
   - content_intent: [INFORMATIONAL, COMMERCIAL, TRANSACTIONAL]
   - content_goal: [AUTHORITY_BUILDING, CLICK_DRIVING, SHARE_ENCOURAGING]
   - visual_goal: [COGNITIVE_CLARITY, EMOTIONAL_RESONANCE, PROFESSIONAL_TRUST]
   - marketing_goal: [AWARENESS, CONVERSION, RETENTION]
3. Định hướng Visual Direction phù hợp nhất để giải quyết nỗi đau và mục tiêu của đối tượng độc giả mục tiêu.

NGHIÊM CẤM:
- KHÔNG tạo bất kỳ prompt vẽ ảnh tiếng Anh nào cho các phần mềm như Midjourney hay Flux.
- KHÔNG sinh hình ảnh.
- KHÔNG giải thích dông dài ngoài cấu trúc JSON quy định.
```

---

## 7. 🛠️ Thiết Kế Kiến Trúc Tích Hợp (Software Architecture Design)

Khi hệ thống chuyển từ giai đoạn Thiết kế sang Triển khai lập trình (Code), kiến trúc lớp sẽ được thiết lập như sau:

### 7.1. Lớp Dữ Liệu (Database Model Extension)
Một bảng hoặc trường mới sẽ được bổ sung vào bảng `posts` hoặc `assets` trong schema cơ sở dữ liệu:
*   `strategy_profile` (Text/JSON): Lưu trữ hồ sơ chiến lược được định cấu trúc của bài viết.

### 7.2. Lớp Dịch Vụ (Service Orchestration)
Tạo lớp `CreativeStrategyService` để điều hành logic:
1.  Nhận `article_content` từ `ContentService`.
2.  Gọi Gemini API với `get_creative_strategy_prompt()` để nhận về `Strategy Profile` JSON.
3.  Lưu `Strategy Profile` vào cơ sở dữ liệu.
4.  Chuyển tiếp hồ sơ này sang `CreativeConceptService` để làm tham chiếu tạo các Concept hình ảnh.

---
*Đặc tả thiết kế bởi Creative Strategy Engine Architecture Board.*
