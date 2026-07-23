# 🎨 AI Image Prompt Generator Specification

Tài liệu này đặc tả thiết kế kiến trúc và hệ thống Prompt cho **AI Image Prompt Generator** (Bộ sinh prompt vẽ ảnh tự động).

Nhiệm vụ của module này là tiếp nhận dữ liệu kịch bản trực quan dạng JSON từ *Visual Story AI* kết hợp với quy chuẩn thương hiệu (*Brand Guideline*), nền tảng xuất bản (*Platform*), thông điệp chiến dịch (*Campaign*), độc giả mục tiêu (*Audience*) để tổng hợp thành các câu lệnh prompt tiếng Anh chuyên sâu, tương thích hoàn toàn với các mô hình sinh ảnh hàng đầu hiện nay.

---

## 📐 1. Cấu Trúc Đầu Ra Của Prompt (Prompt Blueprint Structure)

VIE Prompt Generator sẽ định cấu trúc đầu ra cho mỗi prompt vẽ ảnh bao gồm 15 thành phần cốt lõi:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        AI IMAGE PROMPT MATRIX                          │
├──────────────────────────┬──────────────────────────┬──────────────────┤
│  1. THẨM MỸ CƠ BẢN       │  2. THÔNG SỐ ĐỒ HỌA      │  3. THAM SỐ ENGINE│
│  (Core Aesthetics)       │  (Graphic Composition)   │  (Model Settings)│
│                          │                          │                  │
│  • Subject               │  • Perspective           │  • Negative      │
│  • Background            │  • Camera Type           │  • Aspect Ratio  │
│  • Mood / Emotion        │  • Lighting              │  • Quality       │
│  • Business Style        │  • Typography Area       │  • Image Model   │
│  • Color Palette         │  • Safe Area             │    Parameters    │
└──────────────────────────┴──────────────────────────┴──────────────────┘
```

---

## 🤖 2. System Prompt Cho Prompt Generator Agent

Dưới đây là System Prompt chuẩn được thiết kế cho Google Gemini để dịch và cấu trúc prompt vẽ ảnh tối ưu:

```markdown
Bạn là chuyên gia Senior Prompt Engineer chuyên nghiệp thế giới, có hiểu biết sâu sắc về các mô hình sinh ảnh AI (DALL-E 3, Midjourney v6, Imagen 3, Stable Diffusion XL/3, Flux.1). Nhiệm vụ của bạn là tiếp nhận dữ liệu đầu vào và sinh ra các prompt vẽ ảnh tiếng Anh tối ưu nhất.

### THÔNG TIN ĐẦU VÀO (INPUT):
- **Visual Story JSON**: {input_visual_story_json}
- **Brand Guideline**: {input_brand_guidelines}
- **Platform**: {input_platform}
- **Campaign**: {input_campaign}
- **Audience**: {input_audience}

### NGUYÊN TẮC THIẾT KẾ PROMPT (PROMPT STRUCTURING RULES):
1. **Phần mô tả chính (English Main Prompt)**: Phải là một câu văn liền mạch mô tả chân thực bối cảnh, kết hợp hài hòa: `[Subject] in [Background], showing [Mood] emotion, [Business Style] style, [Perspective] view, shot with [Camera Type] using [Lighting], featuring [Color Palette] color scheme`.
2. **Khoảng trống thiết kế (Typography & Safe Area)**: Bạn BẮT BUỘC phải đưa các chỉ dẫn tạo khoảng trống vào prompt để chừa chỗ cho chữ chồng (ví dụ: "...with a clean, out-of-focus background on the left 40% of the frame to serve as copy space for text overlay...").
3. **Tuyệt đối KHÔNG tự vẽ chữ**: Nhắc nhở mô hình sinh ảnh tránh tự sinh các chữ cái vô nghĩa (gibberish text) trên hình ảnh chính.

### ĐỊNH DẠNG ĐẦU RA BẮT BUỘC (JSON SCHEMA):
Bạn phải trả về một JSON object duy nhất trong thẻ markdown ```json...``` với cấu trúc như sau:

{
  "midjourney_v6": "Prompt tối ưu cho Midjourney v6 kèm tham số (ví dụ: --ar 16:9 --style raw --v 6.0 --q 2)",
  "dalle_3": "Prompt tối ưu cho DALL-E 3 mô tả chi tiết, rõ ràng và mạch lạc",
  "imagen_3": "Prompt tối ưu cho Google Imagen 3 tập trung vào tính chân thực",
  "flux_1": "Prompt tối ưu cho FLUX.1 (Dev/Schnell) giàu chi tiết và bố cục chuẩn",
  "stable_diffusion_xl": "Prompt tích hợp định dạng thẻ từ khóa ngăn cách bằng dấu phẩy cho SDXL",
  "negative_prompt": "ugly, deformed, bad anatomy, text overlay on main image, low quality, watermark, logo, blurry, extra fingers",
  "design_parameters": {
    "aspect_ratio": "Tỷ lệ khung hình (ví dụ: 16:9 | 4:5 | 1:1)",
    "safe_area_description": "Mô tả vùng an toàn để đặt logo và text",
    "main_colors": ["Mã HEX 1", "Mã HEX 2", "Mã HEX 3"]
  }
}
```

---

## 📐 3. Khả Năng Tương Thích Mô Hình (Model Compatibility Specifications)

VIE Prompt Generator tự động tối ưu cấu trúc từ ngữ phù hợp với cơ chế hiểu ngôn ngữ của từng model:

### 3.1 DALL-E 3 (GPT-based Image Model)
- **Đặc trưng**: Ưu tiên mô tả dạng văn cảnh tự nhiên (Natural language descriptions), dài, mạch lạc và giàu chi tiết.
- **Tối ưu**: Tránh dùng từ khóa rời rạc ngăn bằng dấu phẩy; tập trung mô tả câu truyện đầy đủ.

### 3.2 Midjourney v6
- **Đặc trưng**: Ưu tiên phong cách điện ảnh (cinematic), chi tiết kỹ thuật camera và các tham số điều khiển.
- **Tối ưu**: Thêm các thông số camera cụ thể (ví dụ: `shot on 85mm lens, f/1.8`) và tham số hệ thống ở cuối (`--ar 4:5 --v 6.0 --style raw`).

### 3.3 Stable Diffusion (SDXL / SD 3)
- **Đặc trưng**: Hoạt động tốt nhất với cấu trúc từ khóa (tag-based) ngăn cách bởi dấu phẩy và phân bổ trọng số (prompt weighting).
- **Tối ưu**: Dùng cấu trúc: `subject description, background, camera lens, lighting, highly detailed, 8k resolution`.

### 3.4 Flux.1
- **Đặc trưng**: Khả năng render chi tiết bàn tay và văn bản rất mạnh, hiểu ngữ nghĩa cực tốt.
- **Tối ưu**: Mô tả chân thực, chi tiết giải phẫu học rõ ràng để mô hình tận dụng tối đa sức mạnh tái tạo.

---

## 📝 4. Ví Dụ Cấu Hình Output Thực Tế

```json
{
  "midjourney_v6": "A professional portrait of a Vietnamese female store owner in her late 20s, holding a smartphone with a happy and relieved expression. Clean modern home office background with bokeh lights, warm cinematic window daylight, shot on 85mm lens, f/1.8. Asymmetric composition, copy space on the left 40% of the frame. --ar 16:9 --style raw --v 6.0",
  "dalle_3": "A realistic photo of a young Vietnamese female entrepreneur at her clean workspace, smiling as she looks at her smartphone. Beside her is an open laptop showing customer dashboard graphics. The shot is at eye-level, with warm natural light coming from the side window. The background on the left is softly blurred and empty, specifically designed to leave space for text overlay.",
  "imagen_3": "A high-quality commercial photo of a happy young Vietnamese woman entrepreneur checking her phone at a bright minimalist desk. Warm organic lighting, shallow depth of field, clear empty space in the left third of the image, professional marketing aesthetic.",
  "flux_1": "A detailed commercial photograph of a Vietnamese woman shop owner looking at her smartphone with a satisfied smile. On her wooden table sits a laptop displaying business analytics charts. Warm office morning lighting, realistic skin texture and hands. Left-side empty space for copy text overlay.",
  "stable_diffusion_xl": "Vietnamese business woman, looking at smartphone, smiling, happy emotion, warm window light, modern workspace, laptop, highly detailed, 8k resolution, photorealistic, copy space on the left",
  "negative_prompt": "ugly, deformed, bad anatomy, blurry, text overlay on main image, low quality, watermark, logo, extra fingers",
  "design_parameters": {
    "aspect_ratio": "16:9",
    "safe_area_description": "Vùng trống 40% bên trái để chèn chữ tiêu đề chính; chừa góc dưới bên phải cho watermark logo.",
    "main_colors": ["#006af5", "#e8f4fd", "#f97316"]
  }
}
```

---

*Tài liệu đặc tả bộ sinh prompt vẽ ảnh. Cập nhật lần cuối: 2026-07-12.*
