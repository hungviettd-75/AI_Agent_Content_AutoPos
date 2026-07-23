# 🎨 CREATIVE CONCEPT ENGINE
## Tài Liệu Đặc Tả — Hệ Thống Sinh Creative Concept Thumbnail Tự Động

> **Version**: 1.0  
> **Ngày tạo**: 2026-07-12  
> **Thuộc dự án**: AI_Agent_Content_AutoPos  
> **Tác giả**: Antigravity AI — Creative Director · AI Marketing Strategist · Brand Designer · Senior Prompt Engineer  
> **Tích hợp tại**: `ui/tab_content_studio_workspace.py`  
> **Prompt engine tại**: `agents/prompt_templates.py` → `get_creative_concept_prompt()`

---

## 1. 🎯 MỤC TIÊU

Sau khi AI hoàn thành bài viết trong **Content Studio Workspace**, hệ thống **KHÔNG được kết thúc quy trình**.

AI phải tiếp tục phân tích bài viết để tạo ra **03 Creative Concept hoàn toàn khác nhau** phục vụ thiết kế Thumbnail.

---

## 2. 🔍 QUY TẮC PHÂN TÍCH BÀI VIẾT

### AI phải đọc TOÀN BỘ bài viết

❌ Không được chỉ đọc:
- Tiêu đề
- Từ khóa
- Đoạn mở đầu

✅ AI phải hiểu và trích xuất:

| Yếu tố | Ý nghĩa |
|--------|---------|
| **Chủ đề** | Bài viết viết về điều gì? |
| **Thông điệp cốt lõi** | Tóm tắt thông điệp chính trong 1 câu duy nhất |
| **Giá trị cốt lõi** | Giá trị thực sự mang lại cho người đọc |
| **Đối tượng mục tiêu** | Ai sẽ đọc bài này? (CEO / Marketer / Freelancer...) |
| **Mục tiêu marketing** | Awareness / Engagement / Conversion / Education |
| **Cảm xúc muốn truyền tải** | Tò mò / Tin tưởng / Cảm hứng / Lo lắng / Hứng khởi |
| **CTA của bài viết** | Người đọc cần làm gì sau khi đọc xong? |

---

## 3. 📐 CẤU TRÚC 03 CREATIVE CONCEPT

Mỗi Concept phải **khác biệt hoàn toàn** về:
- Mục tiêu truyền thông
- Visual Story (câu chuyện hình ảnh)
- Cảm xúc truyền tải
- Bố cục và composition

> ❌ KHÔNG được chỉ thay đổi màu sắc hoặc góc chụp giữa 3 Concept.

---

### 🏢 CONCEPT 1 — BUSINESS PROFESSIONAL

```
Mục tiêu truyền thông : Xây dựng uy tín
Đối tượng chính       : CEO · Chủ doanh nghiệp · LinkedIn · Facebook Business
```

**15 trường bắt buộc:**

| Trường | Nội dung |
|--------|----------|
| `CONCEPT NAME` | Tên concept mô tả phong cách visual ngắn gọn |
| `MARKETING GOAL` | Mục tiêu truyền thông cụ thể — xây dựng uy tín thương hiệu |
| `TARGET AUDIENCE` | CEO · Giám đốc · Chủ doanh nghiệp · LinkedIn Professional |
| `MAIN MESSAGE` | Thông điệp chính dưới góc nhìn lãnh đạo, ngắn gọn, mạnh mẽ |
| `VISUAL STORY` | Câu chuyện hình ảnh: ai đang làm gì, trong bối cảnh nào |
| `HERO SUBJECT` | Nhân vật chính hoặc vật thể trọng tâm trong ảnh |
| `SUPPORTING OBJECTS` | Các yếu tố phụ trợ làm nền hoặc tạo context |
| `ENVIRONMENT` | Bối cảnh: văn phòng cao cấp / phòng họp / cityscape |
| `MOOD` | Professional · Authoritative · Confident · Trustworthy |
| `EMOTION` | Cảm xúc người xem phải cảm nhận khi nhìn ảnh |
| `COLOR DIRECTION` | Navy Blue · Charcoal · Gold · Clean White |
| `COMPOSITION IDEA` | Rule of Thirds / Central / Split-Screen / Hero Shot |
| `HEADLINE SUGGESTION` | Tiêu đề ≤ 7 từ, VIẾT HOA, phong cách lãnh đạo |
| `CTA POSITION` | Vị trí đặt CTA hoặc URL thương hiệu trên ảnh |
| `BUSINESS VALUE` | Lý do concept này hiệu quả với CEO và LinkedIn |

---

### 🎬 CONCEPT 2 — CINEMATIC STORYTELLING

```
Mục tiêu truyền thông : Thu hút người xem · Tăng CTR · Tạo cảm xúc
Đối tượng chính       : Facebook · Instagram · YouTube · Đại chúng
```

**15 trường bắt buộc:**

| Trường | Nội dung |
|--------|----------|
| `CONCEPT NAME` | Tên concept mô tả phong cách điện ảnh |
| `MARKETING GOAL` | Tăng CTR · Thu hút ánh nhìn · Kích hoạt cảm xúc mạnh |
| `TARGET AUDIENCE` | Người dùng mạng xã hội · Facebook · Instagram · YouTube |
| `MAIN MESSAGE` | Thông điệp cảm xúc truyền tải qua hình ảnh |
| `VISUAL STORY` | Kịch bản điện ảnh: khoảnh khắc cao trào / xung đột / chuyển hóa |
| `HERO SUBJECT` | Nhân vật chính hoặc yếu tố kịch tính nhất |
| `SUPPORTING OBJECTS` | Các yếu tố tạo không khí và chiều sâu |
| `ENVIRONMENT` | Đô thị về đêm / studio tối / ánh sáng kịch tính |
| `MOOD` | Cinematic · Dramatic · Emotional · Story-driven |
| `EMOTION` | Tò mò / Hy vọng / Lo lắng / Kỳ vọng / Bùng cháy |
| `COLOR DIRECTION` | Deep Teal · Orange Glow · Midnight Blue · Amber |
| `COMPOSITION IDEA` | Dutch Angle / Low Angle Hero Shot / Leading Lines |
| `HEADLINE SUGGESTION` | Tiêu đề hook tò mò ≤ 7 từ, dạng câu hỏi hoặc shock |
| `CTA POSITION` | Góc dưới / overlay giữa / ẩn trong bố cục |
| `BUSINESS VALUE` | Lý do concept này tăng CTR và viral trên mạng xã hội |

---

### 📊 CONCEPT 3 — INFOGRAPHIC / DATA DRIVEN

```
Mục tiêu truyền thông : Giáo dục · Case Study · Chia sẻ số liệu
Đối tượng chính       : LinkedIn · Facebook · Pinterest · SlideShare
```

**15 trường bắt buộc:**

| Trường | Nội dung |
|--------|----------|
| `CONCEPT NAME` | Tên concept mô tả phong cách infographic |
| `MARKETING GOAL` | Giáo dục · Chia sẻ dữ liệu · Tăng Save & Share · Case Study |
| `TARGET AUDIENCE` | Professional · Người học · Marketer · Data-driven thinker |
| `MAIN MESSAGE` | Thông điệp qua số liệu, biểu đồ hoặc framework |
| `VISUAL STORY` | Cấu trúc: trước-sau / bước-bước / so sánh / thống kê |
| `HERO SUBJECT` | Yếu tố data nổi bật: con số / biểu đồ / framework / checklist |
| `SUPPORTING OBJECTS` | Icons · Arrows · Charts · Percentage indicators |
| `ENVIRONMENT` | Clean White / Light Gray / Minimalist Tech Background |
| `MOOD` | Educational · Clear · Trustworthy · Data-Driven |
| `EMOTION` | Aha-moment · Tin tưởng · Muốn lưu · Muốn chia sẻ |
| `COLOR DIRECTION` | Bright Blue · Clean White · Accent Orange · Gray Scale |
| `COMPOSITION IDEA` | Grid Layout / Flow Diagram / Split Comparison |
| `HEADLINE SUGGESTION` | Dạng số liệu: "3 BƯỚC..." · "87% CEO..." · "TRƯỚC & SAU" |
| `CTA POSITION` | Footer infographic / nút Download / URL thương hiệu |
| `BUSINESS VALUE` | Lý do concept này được chia sẻ nhiều và tăng authority |

---

## 4. ⚙️ KIẾN TRÚC TÍCH HỢP

### Luồng xử lý trong Content Studio Workspace

```
┌──────────────────────────────────────────────────┐
│      Người dùng bấm "🚀 Sinh bài viết bằng AI"  │
└──────────────────────────┬───────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────┐
│   generate_marketing_or_knowledge_content()      │
│   → Tạo bài viết hoàn chỉnh qua Gemini API      │
│   → Điền vào Editor                             │
└──────────────────────────┬───────────────────────┘
                           │  HỆ THỐNG KHÔNG KẾT THÚC
                           ▼
┌──────────────────────────────────────────────────┐
│   AUTO TRIGGER: Creative Concept Engine          │
│                                                  │
│   studio_creative_concepts_loading = True        │
│   studio_creative_concepts = ""  (reset)         │
│   → Thông báo: "Chuyển sang tab Creative Concepts"│
└──────────────────────────┬───────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────┐
│   Tab "🎨 Creative Concepts" (preview_tabs[1])   │
│                                                  │
│   if loading == True and concepts == "":         │
│       → Gọi get_creative_concept_prompt(         │
│             full_article_content = editor_content│
│         )                                        │
│       → generate_with_gemini(prompt)             │
│       → Lưu kết quả vào session_state            │
└──────────────────────────┬───────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────┐
│   Tách kết quả thành 3 phần riêng biệt           │
│                                                  │
│   📋 Bước 1: Phân tích bài viết (expander)       │
│   🏢 Concept 1: Business Professional            │
│   🎬 Concept 2: Cinematic Storytelling           │
│   📊 Concept 3: Infographic / Data Driven        │
│                                                  │
│   Mỗi Concept:                                   │
│   ├── Badge màu riêng (Blue / Purple / Green)    │
│   ├── Dải màu top-border đặc trưng               │
│   ├── Nội dung 15 trường đầy đủ                  │
│   └── Nút "📋 Copy Concept X"                    │
└──────────────────────────────────────────────────┘
```

### State Management

| State Key | Kiểu | Mô tả |
|-----------|------|-------|
| `studio_creative_concepts_{workspace_id}` | `str` | Nội dung 3 Concept do AI sinh ra |
| `studio_creative_concepts_loading_{workspace_id}` | `bool` | Cờ trigger sinh Concept |

---

## 5. 🗂️ FILE THAY ĐỔI

### `agents/prompt_templates.py`

**Hàm mới thêm:**

```python
def get_creative_concept_prompt(full_article_content: str) -> str:
    """
    Sinh prompt phân tích TOÀN BỘ bài viết và tạo 03 Creative Concept
    khác nhau phục vụ thiết kế Thumbnail.

    Args:
        full_article_content: Toàn bộ nội dung bài viết (không rút gọn)

    Returns:
        Chuỗi prompt hoàn chỉnh gửi đến Gemini
    """
```

**Logic prompt:**
1. Nhúng toàn bộ nội dung bài viết vào prompt (`{full_article_content}`)
2. Yêu cầu AI phân tích 7 yếu tố (Bước 1)
3. Sinh 03 Creative Concept đủ 15 trường mỗi Concept (Bước 2)

---

### `ui/tab_content_studio_workspace.py`

**Thay đổi:**

| Vị trí | Thay đổi |
|--------|---------|
| **Import** | Thêm `from agents.prompt_templates import get_creative_concept_prompt` |
| **CSS** | Thêm styles: `.concept-card`, `.concept-badge-1/2/3`, `.concept-stripe-1/2/3`, `.concept-engine-banner` |
| **State Init** | Thêm `creative_concepts_key` và `creative_concepts_loading_key` |
| **AI Create trigger** | Sau khi sinh bài, set `loading = True` thay vì kết thúc |
| **Copy Framework trigger** | Tương tự — tự động kích hoạt Concept Engine |
| **Preview Tabs** | Thêm tab `🎨 Creative Concepts` (index 1) — tổng 5 tabs |
| **Tab mới** | Hiển thị banner, nút sinh manual, auto-generate logic, 3 Concept cards |

---

## 6. 📊 PHÂN TÍCH SO SÁNH 3 CONCEPT

| Tiêu chí | 🏢 Business Professional | 🎬 Cinematic Storytelling | 📊 Infographic / Data |
|----------|--------------------------|---------------------------|------------------------|
| **Mục tiêu** | Uy tín & Trust | CTR & Cảm xúc | Giáo dục & Share |
| **Platform** | LinkedIn · FB Business | FB · IG · YouTube | LinkedIn · FB · Pinterest |
| **Visual chủ đạo** | Con người · Văn phòng | Kịch tính · Ánh sáng | Số liệu · Framework |
| **Màu sắc** | Navy · Gold · White | Teal · Amber · Deep Blue | Blue · White · Orange |
| **Tỷ lệ CTR** | ★★★☆☆ | ★★★★★ | ★★★★☆ |
| **Tỷ lệ Save** | ★★☆☆☆ | ★★☆☆☆ | ★★★★★ |
| **Tỷ lệ Share** | ★★★☆☆ | ★★★★☆ | ★★★★★ |
| **Tỷ lệ Trust** | ★★★★★ | ★★★☆☆ | ★★★★☆ |

---

## 7. 🚫 QUY TẮC BẮT BUỘC

### Nghiêm cấm

- ❌ Không sinh Prompt tạo ảnh
- ❌ Không sinh ảnh
- ❌ Không chỉ thay đổi màu sắc giữa 3 Concept
- ❌ Không chỉ thay đổi góc chụp giữa 3 Concept
- ❌ Không chỉ đọc tiêu đề, từ khóa hoặc đoạn mở đầu

### Bắt buộc

- ✅ AI đọc TOÀN BỘ bài viết trước khi sinh Concept
- ✅ Mỗi Concept có mục tiêu truyền thông riêng biệt
- ✅ Mỗi Concept kể câu chuyện hình ảnh khác hoàn toàn
- ✅ Mỗi Concept nhắm tâm lý cảm xúc khác nhau
- ✅ Mỗi Concept xuất đủ 15 trường thông tin
- ✅ Kết quả bằng Tiếng Việt

---

## 8. 🎨 DESIGN TOKENS UI

### Color Palette theo Concept

```css
/* Concept 1 — Business Professional */
--concept1-gradient: linear-gradient(135deg, #004ac6, #2563eb);
--concept1-stripe:   linear-gradient(90deg, #004ac6, #2563eb);

/* Concept 2 — Cinematic Storytelling */
--concept2-gradient: linear-gradient(135deg, #7c3aed, #a855f7);
--concept2-stripe:   linear-gradient(90deg, #7c3aed, #a855f7);

/* Concept 3 — Infographic / Data Driven */
--concept3-gradient: linear-gradient(135deg, #059669, #10b981);
--concept3-stripe:   linear-gradient(90deg, #059669, #10b981);

/* Engine Banner */
--banner-bg:         linear-gradient(135deg, #0f172a, #1e293b);
--banner-accent:     #f59e0b;
```

---

## 9. 📁 VỊ TRÍ FILE

```
AI_Agent_Content_AutoPos/
│
├── CREATIVE_CONCEPT_ENGINE.md                  ← Tài liệu này
│
├── agents/
│   └── prompt_templates.py                     ← get_creative_concept_prompt() [MỚI]
│
└── ui/
    └── tab_content_studio_workspace.py         ← Đã nâng cấp [MODIFIED]
        ├── STUDIO_CSS → thêm concept styles
        ├── State → creative_concepts_key
        ├── AI Create → auto trigger engine
        ├── Copy Framework → auto trigger engine
        └── Preview Tab[1] → 🎨 Creative Concepts [MỚI]
```

---

## 10. 🔄 WORKFLOW NGƯỜI DÙNG

```
1. Mở Content Studio Workspace
       │
       ▼
2. Nhập chủ đề → Bấm "🚀 Sinh bài viết bằng AI"
       │
       ▼
3. AI tạo bài viết hoàn chỉnh → Điền vào Editor
       │
       ▼  [HỆ THỐNG KHÔNG KẾT THÚC]
       │
       ▼
4. Thông báo: "🎨 Creative Concept Engine đang phân tích..."
       │
       ▼
5. Người dùng bấm sang tab "🎨 Creative Concepts"
       │
       ▼
6. AI tự động phân tích TOÀN BỘ bài viết
       │
       ▼
7. Hiển thị 3 Creative Concept:
   ├── 🏢 Concept 1: Business Professional
   ├── 🎬 Concept 2: Cinematic Storytelling
   └── 📊 Concept 3: Infographic / Data Driven
       │
       ▼
8. Người dùng Copy Concept yêu thích
       │
       ▼
9. Chuyển sang Thumbnail Studio để thiết kế
```

---

*Tài liệu thiết kế bởi Antigravity AI*  
*Creative Director · AI Marketing Strategist · Brand Designer · Senior Prompt Engineer*  
*Cập nhật lần cuối: 2026-07-12*
