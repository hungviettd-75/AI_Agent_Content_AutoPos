# 🧠 THUMBNAIL PROMPT ENGINE
## Hệ Thống Tạo Prompt Ảnh Thumbnail Theo Bộ Nhận Diện Thương Hiệu Đa Nền Tảng

> **Version**: 2.0  
> **Tác giả**: Principal Prompt Engineer & AI Image Specialist  
> **Cầu nối**: `agents/prompt_templates.py` -> `get_creative_concept_prompt()` & `get_thumbnail_image_prompt()`  
> **Mục tiêu**: Tự động chuyển dịch từ **Creative Concept**, **Brand Guideline** (màu sắc, typography, logo, style), **Platform** (tỷ lệ an toàn), **Audience**, và **Campaign** thành câu Prompt tiếng Anh siêu chi tiết tương thích đa dạng AI tạo ảnh (DALL-E 3, Midjourney v6, Stable Diffusion XL, Flux, Imagen).

---

## 1. ⚙️ CẤU TRÚC PROMPT 19 THÀNH PHẦN (PROMPT STRUCTURE SPECIFICATION)

Để đảm bảo prompt được sinh ra đồng nhất, chi tiết và có độ kiểm soát thẩm mỹ tối đa, mỗi Prompt được tạo ra bởi engine phải chứa đầy đủ 19 trường thông tin sau:

| STT | Thành phần | Mô tả kỹ thuật |
|-----|------------|----------------|
| 1 | **Main Subject** | Chủ thể chính của ảnh thumbnail (con người, robot, thiết bị, biểu đồ...) |
| 2 | **Visual Story** | Hoạt động hay mối quan hệ trực quan đang diễn ra trong khung hình |
| 3 | **Scene** | Hành động cụ thể hoặc khoảnh khắc ngưng đọng tạo sự kịch tính |
| 4 | **Environment** | Bối cảnh không gian bao quanh chủ thể (văn phòng, thành phố đêm, studio...) |
| 5 | **Composition** | Bố cục sắp xếp đối tượng (Rule of thirds, Split-screen, Central focus) chừa khoảng trống cho chữ |
| 6 | **Camera Angle** | Góc đặt camera (Eye-level, Low-angle, High-angle, Dutch angle) |
| 7 | **Perspective** | Điểm tụ, chiều sâu hoặc tiêu cự giả định (Close-up, Wide-angle, Macro, Deep focus) |
| 8 | **Lighting** | Hướng sáng, tính chất ánh sáng (Cinematic lighting, Warm glow, Neon rim light, Soft studio light) |
| 9 | **Color Palette** | Hệ màu cụ thể được quy định theo bộ nhận diện thương hiệu (Brand Colors) |
| 10 | **Mood** | Không khí nghệ thuật, tông màu xúc cảm (Professional, Cyberpunk, Cinematic, Minimalist) |
| 11 | **Emotion** | Cảm xúc thể hiện trên gương mặt nhân vật hoặc biểu cảm visual (Focused, Excited, Proud) |
| 12 | **Typography Safe Area** | Vùng trống được tính toán để đảm bảo không bị chủ thể hay các chi tiết nhiễu đè lên chữ |
| 13 | **Headline Area** | Phân vùng cụ thể đặt tiêu đề chính (Vị trí: góc trên trái, bên phải, hoặc overlay...) |
| 14 | **CTA Area** | Vị trí dự phòng để ghép nút bấm CTA hoặc lời kêu gọi hành động |
| 15 | **Logo Safe Area** | Quy chuẩn góc hiển thị logo (Mặc định: góc trên bên phải hoặc dưới bên phải) |
| 16 | **Aspect Ratio** | Tỷ lệ khung hình tối ưu theo nền tảng: `--ar 16:9` (FB Post/YT), `--ar 4:5` (LinkedIn), `--ar 1:1` (Zalo) |
| 17 | **Quality** | Từ khóa định hình chất lượng cao: `photorealistic, ultra detailed, 8k resolution, cinematic look` |
| 18 | **Style** | Phong cách mỹ thuật (Commercial Editorial Photography, 3D claymation, Vector illustration) |
| 19 | **Negative Prompt** | Các từ khóa cấm để ngăn chặn lỗi giải phẫu hình thể, méo tay, chữ rác tự phát, mờ nhòe |

---

## 2. 🎛️ KHẢ NĂNG TƯƠNG THÍCH ĐA ENGINE TẠO ẢNH (CROSS-MODEL COMPATIBILITY)

Engine sinh ra prompt tiếng Anh chất lượng cao, tối giản và được chuẩn hóa cấu trúc để hoạt động mượt mà trên tất cả các nền tảng sinh ảnh lớn hiện nay:

- **Midjourney v6**: Hỗ trợ đầy đủ tham số tỷ lệ khung hình (`--ar 16:9` hoặc `--ar 4:5`), phong cách (`--style raw`), chất lượng thẩm mỹ và cấu trúc mô tả từ trái qua phải.
- **Flux.1 (Schnell/Dev/Pro)**: Hiểu cực tốt các chi tiết mô tả bố cục vật thể phức tạp và độ chân thực của con người cùng các mô tả vị trí chữ.
- **DALL-E 3 (GPT Image)**: Hiểu ý định chừa khoảng trống thiết kế và vẽ chữ trong vùng trống rất tốt thông qua mô tả tự nhiên tiếng Anh.
- **Stable Diffusion (SDXL/SD3)**: Phù hợp để kết hợp với Negative Prompt truyền thống giúp loại bỏ rác hình ảnh và giữ đúng phong cách nhiếp ảnh/render.
- **Imagen 3**: Đọc hiểu bối cảnh tốt, tối ưu hóa màu sắc thương hiệu và độ chân thực của bối cảnh văn phòng.

---

## 3. 🌐 TÍCH HỢP BRAND GUIDELINES & PLATFORM SPECIFICATIONS

Hệ thống tự động biên dịch và liên kết các thông tin thương hiệu động để sinh prompt:
- **Brand Colors & Accent Colors**: Chuyển đổi mã màu Hex (ví dụ `#004ac6` thành `navy blue`, `#ec4899` thành `neon pink`) để đưa trực tiếp vào mô tả màu nền, màu ánh sáng rim light.
- **Logo Position**: Định vị vùng chừa trống cho Logo tương ứng với cấu hình thương hiệu.
- **Platform Ratio (Tỷ lệ khung hình an toàn)**:
  - **Facebook Post / Ad**: `16:9 aspect ratio` hoặc `1:1 square ratio` (Chừa 20% Text Safe Area để tránh vi phạm chính sách hiển thị quảng cáo).
  - **LinkedIn Post**: `4:5 portrait ratio` (Thiết kế sang trọng, chuyên nghiệp, tone lạnh navy/charcoal).
  - **Zalo OA**: `1:1 aspect ratio` hoặc `16:9 ratio` (Đơn giản, độ tương phản cao, dễ đọc trên di động).

---

## 4. 🤖 PHƯƠNG THỨC HOẠT ĐỘNG TRONG PROMPT TEMPLATES

Chúng tôi đã bổ sung hàm tạo prompt hình ảnh chi tiết dưới mỗi concept. Dưới đây là cấu trúc prompt hệ thống được thiết kế để Gemini sinh ra các trường prompt Thumbnail chuyên sâu:

```
Bạn là Principal Prompt Engineer và AI Image Specialist hàng đầu.

Nhiệm vụ của bạn là nhận:
1. Thông tin Creative Concept (Business Professional / Cinematic Storytelling / Infographic)
2. Bài viết hoàn chỉnh (Article)
3. Hướng dẫn nhận diện thương hiệu (Brand Guideline bao gồm màu sắc, logo, phong cách chụp ảnh/vẽ hình)
4. Nền tảng hiển thị (Platform) và Đối tượng mục tiêu (Audience)

Hãy sinh ra Prompt tạo ảnh bằng TIẾNG ANH chi tiết nhất để người dùng copy trực tiếp vào Midjourney, Flux, DALL-E 3, Stable Diffusion.

Mỗi prompt phải thể hiện rõ 19 trường thông tin bắt buộc theo định dạng sau:
1. Main Subject: [Mô tả chi tiết bằng tiếng Anh]
2. Visual Story: [Mô tả hành động/câu chuyện]
3. Scene: [Mô tả bối cảnh khoảnh khắc]
4. Environment: [Không gian xung quanh]
5. Composition: [Bố cục sắp xếp tạo khoảng trống chèn chữ]
6. Camera Angle: [Góc máy]
7. Perspective: [Cận cảnh, viễn cảnh...]
8. Lighting: [Phong cách ánh sáng và hướng sáng]
9. Color Palette: [Dựa theo màu chủ đạo thương hiệu]
10. Mood: [Không khí và tâm trạng visual]
11. Emotion: [Biểu cảm gương mặt nhân vật]
12. Typography Safe Area: [Mô tả khoảng không trống để chèn chữ]
13. Headline Area: [Vị trí đặt tiêu đề chính trên ảnh]
14. CTA Area: [Vị trí đặt nút bấm CTA]
15. Logo Safe Area: [Góc an toàn để đặt Logo thương hiệu]
16. Aspect Ratio: [Tỷ lệ ảnh phù hợp nền tảng]
17. Quality: [Các từ khóa chất lượng cao]
18. Style: [Mỹ thuật: Photography / 3D Render / Flat Vector]
19. Negative Prompt: [Các từ cấm và yếu tố cần tránh]

YÊU CẦU:
- Không tạo ảnh, chỉ tạo prompt văn bản.
- Trả về cấu trúc 19 phần rõ ràng dưới dạng Markdown.
```

---

## 5. 📂 VỊ TRÍ HẠ TẦNG FILE

```
AI_Agent_Content_AutoPos/
│
├── THUMBNAIL_PROMPT_ENGINE.md                  ← Tài liệu này [NEW]
│
├── agents/
│   └── prompt_templates.py                     ← get_creative_concept_prompt() [MODIFIED]
│
└── ui/
    └── tab_content_studio_workspace.py         ← Đã tích hợp hiển thị 19 thành phần prompt hình ảnh của từng Concept.
```

---

*Tài liệu được thiết kế bởi Principal Prompt Engineer & AI Image Specialist*  
*Cập nhật lần cuối: 2026-07-12*
