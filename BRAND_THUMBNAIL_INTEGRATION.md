# 🎨 Brand Integration with AI Thumbnail Generator Specification

Tài liệu này đặc tả cơ chế tích hợp các yếu tố nhận diện thương hiệu (**Brand Identity**) vào module **AI Thumbnail Generator** mà không sửa đổi module `Brand` hoặc schema cơ sở dữ liệu hiện tại của hệ thống.

---

## 🛠️ 1. Nguyên Tắc Hoạt Động (Operational Principles)

Hệ thống hoạt động dựa trên cơ chế kiểm tra sự tồn tại của cấu hình **Brand** trong cơ sở dữ liệu ứng với Workspace hiện tại thông qua [BrandModel.get_by_workspace](file:///e:/Save%20APP/AI_Agent_Content_AutoPos/database/models/brand.py#L47):

```
                       ┌─────────────────────────────────────┐
                       │     Yêu cầu sinh Thumbnail mới       │
                       └──────────────────┬──────────────────┘
                                          │
                                          ▼
                      ┌──────────────────────────────────────┐
                      │ Gọi BrandModel.get_by_workspace()    │
                      └──────────────────┬──────────────────┘
                                          │
                                          ▼
                                🌟 Brand tồn tại?
                                /              \
                             (Có)             (Không)
                             /                    \
                            ▼                      ▼
             ┌────────────────────────┐      ┌────────────────────────┐
             │ BẮT BUỘC SỬ DỤNG BRAND │      │ AI TỰ ĐỀ XUẤT BRAND    │
             │   - Brand Voice        │      │   - Brand Voice đề xuất│
             │   - Brand Colors       │      │   - Colors hài hòa     │
             │   - Typography         │      │   - Typography mặc định│
             │   - Logo/Watermark     │      │   - Style đề xuất      │
             │   - Guideline áp dụng  │      │   - Sinh Guideline mới │
             └──────────┬─────────────┘      └──────────┬─────────────┘
                        │                               │
                        └───────────────┬───────────────┘
                                        │
                                        ▼
                       ┌─────────────────────────────────────┐
                       │   Tạo Prompts & Render Preview      │
                       └─────────────────────────────────────┘
```

---

## 📦 2. Cơ Chế Tích Hợp Chi Tiết Từng Thành Phần Brand

### 2.1. Brand Voice (Giọng điệu thương hiệu)
*   **Nếu đã có**: 
    - Lấy giá trị `tone_of_voice` từ Database (ví dụ: *casual, professional, bold*).
    - AI Engine sử dụng tone này để viết **Text Overlay** (Tiêu đề, Nhãn phụ) và thiết kế **Emotion** của nhân vật trong `Image Prompt`.
*   **Nếu chưa có**:
    - AI tự động phân tích chủ đề bài viết (`Article`) và đối tượng mục tiêu (`Audience`) để đề xuất một `tone_of_voice` phù hợp nhất và giải thích ngắn gọn lý do đề xuất.

### 2.2. Brand Color (Màu sắc thương hiệu)
*   **Nếu đã có**:
    - Lấy cấu trúc JSON `brand_colors` (ví dụ: `{"primary": "#2563eb", "secondary": "#10b981", "accent": "#facc15"}`).
    - AI sử dụng chính xác các mã màu này để thiết kế đề xuất phối màu cho chữ (`text_color`) và các khối nền (`background_theme`).
    - Nhúng các từ khóa màu này vào `Image Prompt` tiếng Anh (ví dụ: *"...with blue and teal neon accents matching the brand colors..."*).
*   **Nếu chưa có**:
    - AI phân tích màu sắc tâm lý học ứng với lĩnh vực của bài viết và đề xuất một bảng màu gồm 3 mã màu HEX (Primary, Secondary, Accent) kèm độ tương phản tốt nhất cho thiết kế.

### 2.3. Typography (Kiểu chữ)
*   **Nếu đã có**:
    - Trích xuất thông tin phông chữ từ trường `brand_guidelines` (nếu doanh nghiệp có ghi rõ phông chữ như *Inter, Montserrat, Playfair Display*).
    - Đưa phông chữ này vào thuộc tính `Typography` của cấu hình render Thumbnail.
*   **Nếu chưa có**:
    - AI dựa trên phân loại bài viết để đề xuất phông chữ:
      - Bài viết chuyên sâu/doanh nghiệp: Đề xuất phông chữ sans-serif hiện đại như `Inter` hoặc `Outfit`.
      - Bài viết tin tức/giật gân: Đề xuất phông chữ dày như `Archivo Black` hoặc `Impact`.

### 2.4. Logo & Watermark
*   **Nếu đã có**:
    - Đọc đường dẫn ảnh `logo_url` trong cơ sở dữ liệu.
    - Trong `Thumbnail Prompt` và `Image Prompt`, hướng dẫn AI thiết kế chừa một góc (mặc định là góc dưới bên trái hoặc góc dưới bên phải) để hệ thống tự động chèn lớp phủ logo (Logo overlay).
*   **Nếu chưa có**:
    - Sử dụng watermark dạng chữ màu trắng thanh lịch hiển thị tên miền thương hiệu hoặc website mặc định (`hungvietai.com`) ở góc dưới bên phải ảnh nền.

### 2.5. Brand Style (Phong cách thương hiệu)
*   **Nếu đã có**:
    - Đọc phong cách thương hiệu trong `brand_guidelines` (ví dụ: *Futuristic SaaS, Minimalist Editorial, Retro Cyberpunk*).
    - Cố định trường `Style` trong output của Thumbnail Prompt Engine theo phong cách này.
*   **Nếu chưa có**:
    - AI đề xuất phong cách mỹ thuật phù hợp dựa trên kênh phân phối (`Platform`). Ví dụ: LinkedIn ưu tiên phong cách *Corporate Premium Editorial Photography*, TikTok/Reels ưu tiên *Vibrant Modern 3D Render*.

### 2.6. Brand Guideline (Quy chuẩn thương hiệu)
*   **Nếu đã có**:
    - Đọc toàn bộ văn bản mô tả trong `brand_guidelines` và danh sách từ cấm `blacklist_words`.
    - Gửi thông tin này làm điều kiện ràng buộc trong System Prompt của AI Thumbnail Engine để loại trừ từ cấm ra khỏi tiêu đề viết lên ảnh, đồng thời tuân thủ các quy tắc cấm/nên làm.
*   **Nếu chưa có**:
    - AI tự động phác thảo một Guideline ngắn gồm 3 quy tắc thiết kế cốt lõi dành riêng cho chủ đề bài viết đó để người dùng có thể tham khảo áp dụng lâu dài.

---

## 🦾 3. Đặc Tả Tích Hợp Trong System Prompt của AI Engine

Khi gọi API của Google Gemini để sinh thông số Thumbnail, logic code sẽ tự động lấy dữ liệu từ `BrandModel` và đưa vào prompt:

### Kịch bản A: Workspace ĐÃ CÓ Brand Profile
```markdown
Hệ thống phát hiện tài khoản đã thiết lập Brand Profile. Bạn BẮT BUỘC phải áp dụng chính xác các cấu hình thương hiệu sau vào Thumbnail:
- Tone giọng (Brand Voice): {brand_profile['tone_of_voice']}
- Bảng màu (Brand Colors): {brand_profile['brand_colors']}
- Hướng dẫn thiết kế (Brand Guidelines): {brand_profile['brand_guidelines']}
- Danh sách từ cấm (Blacklist): {brand_profile['blacklist_words']} (Tuyệt đối không dùng các từ này trên chữ viết của Thumbnail)
- Logo thương hiệu: {brand_profile['logo_url']} (Chừa khoảng trống ở góc dưới bên trái cho logo)

Đầu ra của bạn phải tối ưu hóa để hiển thị các màu sắc và phong cách này.
```

### Kịch bản B: Workspace CHƯA CÓ Brand Profile (Mới khởi tạo)
```markdown
Hệ thống chưa thiết lập Brand Profile cho Workspace này. 
Nhiệm vụ của bạn là:
1. Phân tích nội dung bài viết và đối tượng mục tiêu để ĐỀ XUẤT một bộ nhận diện thương hiệu tối ưu cho Thumbnail bao gồm:
   - 1 Brand Voice (Giọng điệu khuyên dùng)
   - 3 Brand Colors (Mã màu HEX: Primary, Secondary, Accent hài hòa)
   - 1 Typography (Phông chữ thiết kế đề xuất)
   - 1 Brand Style (Phong cách mỹ thuật cho ảnh nền)
   - 1 Tóm tắt ngắn gọn Brand Guideline thiết kế (3 quy tắc nên làm)
2. Điền các đề xuất này trực tiếp vào các trường tương ứng trong JSON đầu ra và giải thích lý do đề xuất trong trường "brand_proposal_rationale".
```

---

## 🗃️ 4. Cấu Trúc JSON Phản Hồi Tích Hợp (Unified JSON Output Schema)

Engine sẽ trả về cấu trúc JSON mở rộng dưới đây để bao quát cả hai kịch bản:

```json
{
  "brand_status": "applied" or "proposed",
  "brand_proposal": {
    "proposed_tone": "Giọng điệu đề xuất (nếu chưa có brand, ngược lại để trống)",
    "proposed_colors": {
      "primary": "#HEX",
      "secondary": "#HEX",
      "accent": "#HEX"
    },
    "proposed_typography": "Phông chữ đề xuất",
    "proposed_style": "Phong cách thiết kế đề xuất",
    "proposed_guideline_rules": [
      "Quy tắc thiết kế đề xuất 1",
      "Quy tắc thiết kế đề xuất 2"
    ],
    "brand_proposal_rationale": "Lý do đề xuất bộ nhận diện thương hiệu này dựa trên nội dung bài viết và đối tượng khách hàng."
  },
  "thumbnail_prompt": "Mô tả tổng quan thiết kế thumbnail bằng Tiếng Việt...",
  "image_prompt": "A detailed English prompt for image generation AI...",
  "text_overlay": {
    "title": "TIÊU ĐỀ VIẾT HOA",
    "subtitle": "Tiêu đề phụ",
    "badge": "Nhãn nổi bật",
    "cta": "Nút bấm"
  },
  "color_suggestion": {
    "background_theme": "Tông màu chủ đạo",
    "text_color": "Màu của chữ tiêu đề chính",
    "accent_color": "Màu của chữ tiêu đề phụ"
  },
  "composition": "Mô tả cấu trúc bố cục",
  "emotion": "Cảm xúc",
  "camera": "Góc chụp",
  "lighting": "Ánh sáng",
  "style": "Phong cách nghệ thuật",
  "negative_prompt": "ugly, deformed, text overlay...",
  "aspect_ratio": "Tỷ lệ khung hình"
}
```

---

## 🗺️ 5. Bảng Ánh Xạ Brand → Design Parameters (Brand → Design Mapping Table)

Bảng dưới đây quy định mỗi trường dữ liệu Brand trong Database ánh xạ sang thông số thiết kế Thumbnail nào:

| Trường Brand trong DB | Kiểu Dữ Liệu | Ánh xạ sang Output Thumbnail | Bắt buộc |
| :--- | :--- | :--- | :---: |
| `tone_of_voice` | `string` | → `emotion`, nội dung `text_overlay.title` & `subtitle` | ✅ |
| `brand_colors.primary` | `string (HEX)` | → `color_suggestion.text_color`, màu nổi bật trong `image_prompt` | ✅ |
| `brand_colors.secondary` | `string (HEX)` | → `color_suggestion.background_theme` | ✅ |
| `brand_colors.accent` | `string (HEX)` | → `color_suggestion.accent_color`, màu nút `text_overlay.cta` | ✅ |
| `logo_url` | `string (URL)` | → Hướng dẫn chừa vùng góc trong `image_prompt` để đặt logo | ✅ |
| `tagline` | `string` | → `text_overlay.subtitle` hoặc `text_overlay.badge` | ⬜ |
| `brand_guidelines` | `string (text dài)` | → `style`, `negative_prompt`, `typography` | ✅ |
| `blacklist_words` | `list[string]` | → Nhúng vào `negative_prompt`, cấm dùng trong `text_overlay` | ✅ |
| `keywords` | `list[string]` | → Ưu tiên nhắc trong `thumbnail_prompt` & `image_prompt` | ⬜ |
| `vision` | `string` | → Định hướng cảm xúc tổng thể của `emotion` | ⬜ |
| `mission` | `string` | → Điều chỉnh thông điệp trong `thumbnail_prompt` | ⬜ |
| `cta` | `string` | → Ưu tiên dùng làm `text_overlay.cta` nếu phù hợp với nền tảng | ⬜ |

> **Ghi chú**: ✅ = Bắt buộc áp dụng khi có dữ liệu. ⬜ = Tùy chọn, tham khảo khi có.

---

## 💡 6. Bảng Tra Cứu Đề Xuất AI Khi Chưa Có Brand (AI Proposal Lookup Table)

Khi `BrandModel.get_by_workspace()` trả về `{}`, Engine căn cứ vào `Platform` và `Audience` để tự động đề xuất:

### 6.1. Đề Xuất Brand Voice theo Audience

| Audience | Brand Voice đề xuất |
| :--- | :--- |
| CEO / Quản lý cấp cao | `Chuyên nghiệp & Tin cậy (Professional & Trustworthy)` |
| Chuyên gia AI / Developer | `Đột phá & Sáng tạo (Bold & Creative)` |
| Freelancer / Content Creator | `Thân thiện & Gần gũi (Casual & Friendly)` |
| Chủ shop online | `Đồng cảm & Chia sẻ (Empathetic & Supportive)` |
| Sales / Nhân viên kinh doanh | `Hài hước & Dí dỏm (Humorous & Witty)` |
| Giáo viên / Educator | `Trang trọng & Lịch sự (Formal & Polite)` |

### 6.2. Đề Xuất Brand Color theo Platform

| Platform | Primary | Secondary | Accent | Ghi chú |
| :--- | :--- | :--- | :--- | :--- |
| **LinkedIn** | `#0a66c2` | `#0f172a` | `#fbbf24` | Corporate, trust |
| **Facebook** | `#1877f2` | `#f0f2f5` | `#fa383e` | Viral, attention |
| **Facebook Ads** | `#1c1c1e` | `#f97316` | `#facc15` | High conversion |
| **YouTube** | `#ff0000` | `#0f0f0f` | `#ffffff` | Entertainment |
| **Zalo OA** | `#006af5` | `#e8f4fd` | `#34d399` | Friendly, local |
| **Instagram** | `#833ab4` | `#fd1d1d` | `#fcaf45` | Aesthetic, style |
| **TikTok / Reels** | `#010101` | `#fe2c55` | `#25f4ee` | Trendy, dynamic |

### 6.3. Đề Xuất Typography theo Phong Cách Bài Viết

| Phong cách bài viết | Typography đề xuất | Lý do |
| :--- | :--- | :--- |
| Doanh nghiệp / Corporate | `Outfit` + `Inter` | Hiện đại, tin cậy, dễ đọc |
| Lãnh đạo / CEO Personal Brand | `Playfair Display` + `Montserrat` | Sang trọng, cổ điển, tầm nhìn |
| Tin tức / Breaking News | `Archivo Black` hoặc `Impact` | Dày, mạnh, tạo cảm giác cấp bách |
| Giáo dục / Education | `Merriweather` + `Open Sans` | Học thuật, dễ tiêu hóa |
| AI & Công nghệ | `Orbitron` + `Space Grotesk` | Tương lai, kỹ thuật số |
| Marketing / Sales | `Plus Jakarta Sans` | Năng động, trẻ trung, tỉ lệ nhấp tốt |

### 6.4. Đề Xuất Brand Style theo Platform + Audience

| Platform | Audience chính | Brand Style đề xuất |
| :--- | :--- | :--- |
| LinkedIn | CEO / Quản lý cấp cao | `Premium Corporate Editorial Photography` |
| Facebook | Chủ shop / Freelancer | `Vibrant Lifestyle Commercial Photography` |
| Facebook Ads | Mọi đối tượng | `Clean Ad-Safe Product Mockup with High Contrast` |
| YouTube | Mọi đối tượng | `Bold Thumbnail Style with Strong Typography` |
| TikTok / Reels | Giới trẻ | `Vibrant Modern 3D Render or Animated Style` |
| Zalo OA | Khách hàng local | `Friendly Vietnamese Context Photography` |

---

## 📝 7. Ví Dụ Đầy Đủ Cho 2 Kịch Bản (Full Use-Case Examples)

### 7.1. Kịch Bản A — Workspace ĐÃ CÓ Brand Profile

**Giả định Brand Profile trong DB (workspace_id = 5):**
```json
{
  "tone_of_voice": "Chuyên nghiệp & Tin cậy (Professional & Trustworthy)",
  "brand_colors": { "primary": "#0f172a", "secondary": "#2563eb", "accent": "#fbbf24" },
  "logo_url": "https://cdn.hungvietai.com/logo/logo-white.png",
  "tagline": "AI đơn giản hóa mọi thứ",
  "brand_guidelines": "Phong cách: Corporate Premium. Typography: Outfit + Inter. Không dùng hình ảnh cartoon, anime. Chừa logo góc dưới bên trái.",
  "blacklist_words": ["rẻ tiền", "chắc chắn 100%", "miễn phí hoàn toàn"],
  "keywords": ["AI Agent", "tự động hóa", "hiệu suất"],
  "vision": "Trở thành nền tảng marketing AI tin cậy nhất Đông Nam Á.",
  "mission": "Giải phóng thời gian sáng tạo nội dung cho doanh nghiệp Việt."
}
```

**Input Engine:** Article = *"5 cách AI Agent đang thay thế nhân viên marketing và tiết kiệm 40% chi phí vận hành"* | Audience = *CEO* | Platform = *LinkedIn*

**Output JSON:**
```json
{
  "brand_status": "applied",
  "brand_proposal": {},
  "thumbnail_prompt": "Thumbnail LinkedIn 4:5 phong cách Corporate Premium. Split-screen: bên phải CEO đứng trước dashboard AI, bên trái nền navy #0f172a + chữ trắng/gold. Góc dưới bên trái chừa 80×80px cho logo.",
  "image_prompt": "A confident Vietnamese male executive in a dark tailored suit, standing in a modern high-tech office with holographic blue AI dashboards. Clear empty space on the left 40% for text overlay. Eye-level 85mm lens, warm cinematic lighting, premium editorial photography. --ar 4:5",
  "text_overlay": {
    "title": "AI THAY THẾ MARKETING?",
    "subtitle": "Tiết kiệm 40% OpEx",
    "badge": "EXECUTIVE INSIGHT",
    "cta": "ĐỌC NGAY"
  },
  "color_suggestion": {
    "background_theme": "Dark Navy #0f172a with cool blue glow",
    "text_color": "Pure White #FFFFFF (title) + Warm Gold #FBBF24 (emphasis)",
    "accent_color": "Royal Blue #2563eb (badge)"
  },
  "composition": "Split-screen 40/60. Text left, subject right with natural edge fade.",
  "emotion": "Focused, analytical, authoritative",
  "camera": "Eye-level medium shot, 85mm f/2.0, bokeh background",
  "lighting": "Warm cinematic office key light + cool blue fill from hologram screens",
  "style": "Premium Corporate Editorial Photography — Outfit typography, navy & gold palette",
  "negative_prompt": "rẻ tiền, chắc chắn 100%, miễn phí hoàn toàn, cartoon, anime, distorted face, bad hands, blurry",
  "aspect_ratio": "4:5"
}
```

---

### 7.2. Kịch Bản B — Workspace CHƯA CÓ Brand Profile

**Input Engine:** Article = *"Cách chốt đơn Zalo hiệu quả không cần chạy ads — tăng tỷ lệ chuyển đổi lên 300%"* | Audience = *Chủ shop online* | Platform = *Zalo OA*

**Output JSON:**
```json
{
  "brand_status": "proposed",
  "brand_proposal": {
    "proposed_tone": "Đồng cảm & Chia sẻ (Empathetic & Supportive)",
    "proposed_colors": {
      "primary": "#006af5",
      "secondary": "#e8f4fd",
      "accent": "#f97316"
    },
    "proposed_typography": "Plus Jakarta Sans + Inter",
    "proposed_style": "Friendly Vietnamese Context Lifestyle Photography",
    "proposed_guideline_rules": [
      "1. Luôn dùng ảnh thật người Việt — không dùng hình ảnh nước ngoài hoặc 3D robot.",
      "2. Tiêu đề tối đa 7 từ, font dày, dễ đọc trên điện thoại nhỏ.",
      "3. Bảng màu nền sáng + chữ tối để dễ đọc trong mọi điều kiện ánh sáng."
    ],
    "brand_proposal_rationale": "Chủ shop Zalo cần sự tin tưởng và gần gũi. Màu Zalo Blue (#006af5) tạo đồng nhất với nền tảng quen thuộc. Phong cách lifestyle photography thực tế giúp người đọc đồng cảm hơn với nội dung."
  },
  "thumbnail_prompt": "Thumbnail 1:1 thân thiện cho Zalo OA. Nền sáng, chủ shop nữ Việt trẻ cầm điện thoại hiển thị chat Zalo nhiều đơn hàng. Chữ xanh Zalo nổi bật bên trái, cảm giác gần gũi đời thường.",
  "image_prompt": "A cheerful young Vietnamese female shop owner at a bright minimal home office desk, holding a smartphone showing a busy Zalo chat conversation. Natural window light, warm airy atmosphere, happy confident expression. Clear bright empty space on the left side. Eye-level 50mm lens, bright lifestyle commercial photography. --ar 1:1",
  "text_overlay": {
    "title": "CHỐT ĐƠN ZALO +300%",
    "subtitle": "Không cần chạy Ads",
    "badge": "BÍ QUYẾT",
    "cta": "XEM NGAY"
  },
  "color_suggestion": {
    "background_theme": "Bright white and sky blue with warm orange pops",
    "text_color": "Zalo Blue #006AF5 (title), Deep Charcoal #1C1C1E (subtitle)",
    "accent_color": "Warm Orange #F97316 (badge and CTA)"
  },
  "composition": "Central focus, subject on right two-thirds. Left third bright and empty for text.",
  "emotion": "Happy, confident, relatable, trustworthy",
  "camera": "Eye-level medium close-up, 50mm natural lens, bright high-key look",
  "lighting": "Natural window daylight from the right, bright lifestyle lighting",
  "style": "Friendly Vietnamese Lifestyle Commercial Photography",
  "negative_prompt": "ugly, distorted hands, stock foreigner photos, dark moody lighting, cluttered background, low quality, anime, blurry",
  "aspect_ratio": "1:1"
}
```

---

## 🔗 8. Thiết Kế Tích Hợp Code (Code Integration Blueprint)

Module mới `thumbnail/thumbnail_prompt_engine.py` gọi vào `BrandModel` theo **chế độ READ-ONLY** — không sửa bất kỳ file hiện tại nào:

```python
# thumbnail/thumbnail_prompt_engine.py
# ====================================
# Module MỚI — Không sửa đổi bất kỳ file hiện tại nào.
# Chỉ đọc (READ-ONLY) từ BrandModel qua interface có sẵn.

from database.models.brand import BrandModel       # Chỉ gọi get_by_workspace()
from services.gemini_client import generate_with_gemini
import json

PLATFORM_DEFAULTS = {
    "LinkedIn":       {"aspect_ratio": "4:5",  "style": "Premium Corporate Editorial Photography"},
    "Facebook":       {"aspect_ratio": "16:9", "style": "Vibrant Lifestyle Photography"},
    "Facebook Ads":   {"aspect_ratio": "16:9", "style": "Clean High-Contrast Ad-Safe Commercial"},
    "YouTube":        {"aspect_ratio": "16:9", "style": "Bold YouTube Thumbnail Style"},
    "Zalo OA":        {"aspect_ratio": "1:1",  "style": "Friendly Vietnamese Context Photography"},
    "Instagram":      {"aspect_ratio": "1:1",  "style": "Aesthetic Minimal Lifestyle"},
    "TikTok / Reels": {"aspect_ratio": "9:16", "style": "Vibrant 3D Motion Graphics"},
}

def build_brand_context(workspace_id: int) -> dict:
    """
    Đọc Brand Profile từ DB và trả về context dict cho Engine.
    READ-ONLY: Không ghi hay sửa dữ liệu Brand.
    """
    brand = BrandModel.get_by_workspace(workspace_id)  # Gọi interface có sẵn
    if brand:
        return {
            "status":     "applied",
            "tone":       brand.get("tone_of_voice", ""),
            "colors":     brand.get("brand_colors", {}),
            "logo_url":   brand.get("logo_url", ""),
            "tagline":    brand.get("tagline", ""),
            "guidelines": brand.get("brand_guidelines", ""),
            "blacklist":  brand.get("blacklist_words", []),
            "keywords":   brand.get("keywords", []),
            "vision":     brand.get("vision", ""),
            "mission":    brand.get("mission", ""),
            "cta":        brand.get("cta", ""),
        }
    return {"status": "proposed"}


def build_system_prompt(article: str, audience: str, platform: str, brand_ctx: dict) -> str:
    """Xây dựng System Prompt hoàn chỉnh theo kịch bản A hoặc B."""
    platform_cfg = PLATFORM_DEFAULTS.get(
        platform, {"aspect_ratio": "16:9", "style": "Commercial Photography"}
    )

    if brand_ctx["status"] == "applied":
        # Kịch bản A — Brand đã tồn tại: BẮT BUỘC áp dụng
        blacklist_str = ", ".join(brand_ctx["blacklist"]) if brand_ctx["blacklist"] else "Không có"
        keywords_str  = ", ".join(brand_ctx["keywords"])  if brand_ctx["keywords"]  else "Không có"
        colors_str    = json.dumps(brand_ctx["colors"], ensure_ascii=False)
        brand_block   = f"""
## 🎨 BRAND PROFILE — BẮT BUỘC ÁP DỤNG CHÍNH XÁC:
- Brand Voice  : {brand_ctx['tone']}
- Brand Colors : {colors_str}
- Tagline      : {brand_ctx['tagline']}
- Keywords     : {keywords_str}
- Guidelines   : {brand_ctx['guidelines']}
- Logo URL     : {brand_ctx['logo_url']} → Chừa góc dưới bên trái 80×80px cho logo.
- Blacklist    : {blacklist_str} → TUYỆT ĐỐI không dùng các từ này trên Text Overlay.
- Vision       : {brand_ctx['vision']}
- Mission      : {brand_ctx['mission']}
- CTA mặc định: {brand_ctx['cta']}
"""
    else:
        # Kịch bản B — Chưa có Brand: AI tự đề xuất
        brand_block = """
## 🤖 BRAND PROPOSAL — CHƯA CÓ BRAND PROFILE:
Workspace chưa thiết lập Brand Profile. Phân tích Article và Audience để:
1. Đề xuất: Brand Voice, Brand Colors (3 HEX), Typography, Brand Style, 2–3 Guideline Rules.
2. Điền vào trường `brand_proposal` trong JSON đầu ra.
3. Giải thích lý do đề xuất trong `brand_proposal.brand_proposal_rationale`.
"""

    return f"""Bạn là Art Director chuyên Marketing SaaS. Phân tích dữ liệu đầu vào và sinh JSON.

## INPUT:
- Article       : {article}
- Audience      : {audience}
- Platform      : {platform}
- Aspect Ratio  : {platform_cfg['aspect_ratio']}
- Default Style : {platform_cfg['style']}

{brand_block}

## OUTPUT: Trả về đúng JSON schema theo THUMBNAIL_PROMPT_ENGINE.md.
Trường `brand_status` = "{brand_ctx['status']}". Chỉ trả về JSON thuần túy.
"""


def generate_thumbnail_prompt(
    workspace_id: int,
    article: str,
    audience: str,
    platform: str,
    api_key: str
) -> dict:
    """Hàm điều phối chính — gọi từ UI Thumbnail Studio."""
    brand_ctx     = build_brand_context(workspace_id)
    system_prompt = build_system_prompt(article, audience, platform, brand_ctx)
    raw_output    = generate_with_gemini(system_prompt, api_key=api_key)
    try:
        clean = raw_output.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        return json.loads(clean)
    except Exception:
        return {"error": "Không thể phân tích JSON từ Gemini.", "raw": raw_output}
```

---

## ✅ 9. Checklist Kiểm Tra Tích Hợp (Integration Validation Checklist)

### Kịch bản A — Brand đã có
- [ ] `brand_status` = `"applied"` trong JSON trả về.
- [ ] `color_suggestion.text_color` chứa màu Primary từ `brand_colors`.
- [ ] `text_overlay` không chứa bất kỳ từ nào trong `blacklist_words`.
- [ ] `image_prompt` đề cập khoảng trống logo góc dưới bên trái.
- [ ] `style` đồng bộ với phong cách ghi trong `brand_guidelines`.
- [ ] `emotion` phù hợp với `tone_of_voice` của Brand.
- [ ] `text_overlay.cta` ưu tiên dùng giá trị từ trường `cta` của Brand nếu có.

### Kịch bản B — Brand chưa có
- [ ] `brand_status` = `"proposed"` trong JSON trả về.
- [ ] `brand_proposal.proposed_colors` chứa đủ 3 mã HEX hợp lệ.
- [ ] `brand_proposal.proposed_typography` trả về tên font cụ thể.
- [ ] `brand_proposal.proposed_guideline_rules` có ít nhất 2 quy tắc.
- [ ] `brand_proposal.brand_proposal_rationale` không rỗng.
- [ ] Màu sắc đề xuất phù hợp với `Platform` theo Bảng 6.2.
- [ ] Brand Voice đề xuất phù hợp với `Audience` theo Bảng 6.1.

### Chung — Mọi kịch bản
- [ ] `aspect_ratio` đúng tỷ lệ của `Platform` đã chọn.
- [ ] `negative_prompt` bao gồm ít nhất: `ugly, distorted hands, blurry, low quality`.
- [ ] `image_prompt` viết hoàn toàn bằng Tiếng Anh.
- [ ] `text_overlay.title` viết HOA toàn bộ, dưới 7 từ.
- [ ] **Không sửa đổi bất kỳ dòng nào trong các file hiện tại:**
  - [`database/models/brand.py`](file:///e:/Save%20APP/AI_Agent_Content_AutoPos/database/models/brand.py)
  - [`ui/tab_brand.py`](file:///e:/Save%20APP/AI_Agent_Content_AutoPos/ui/tab_brand.py)
  - [`services/brand_voice_engine.py`](file:///e:/Save%20APP/AI_Agent_Content_AutoPos/services/brand_voice_engine.py)

---

*Tài liệu này bổ sung cho [THUMBNAIL_PROMPT_ENGINE.md](file:///e:/Save%20APP/AI_Agent_Content_AutoPos/THUMBNAIL_PROMPT_ENGINE.md) và không thay thế tài liệu đó. Cập nhật lần cuối: 2026-07-12.*
