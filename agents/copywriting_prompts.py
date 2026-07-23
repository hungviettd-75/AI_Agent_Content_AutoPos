"""
agents/copywriting_prompts.py
==============================
Prompt templates chuyên sâu cho Copywriting Agent.
Hỗ trợ 9 framework copywriting kinh điển × 9 loại copy.
"""

# ── Danh sách hằng số ─────────────────────────────────────────────────────────

COPY_FRAMEWORKS = [
    "AIDA (Attention – Interest – Desire – Action)",
    "PAS (Problem – Agitate – Solution)",
    "FAB (Features – Advantages – Benefits)",
    "BAB (Before – After – Bridge)",
    "STAR (Situation – Task – Action – Result)",
    "4P (Promise – Picture – Proof – Push)",
    "PPPP (Picture – Promise – Prove – Push)",
    "Hook – Story – Offer",
    "AI tự chọn framework tối ưu nhất",
]

COPY_TYPES = [
    "Facebook / Zalo Ad Copy",
    "Google Search Ad (Headline + Description)",
    "Email Marketing (Subject + Body)",
    "Landing Page (Toàn trang)",
    "Sales Letter (Dài)",
    "Mô tả sản phẩm (Product Description)",
    "Video Sales Letter – VSL Script",
    "Push Notification (Cực ngắn)",
    "Tin nhắn Zalo / WhatsApp",
]

COPY_TONES = [
    "Chuyên nghiệp & Tin cậy",
    "Thân thiện & Gần gũi",
    "Khẩn cấp & Kêu gọi hành động",
    "Truyền cảm hứng & Động lực",
    "Mạnh mẽ & Thuyết phục",
    "Hài hước & Sáng tạo",
]

# ── Giải thích framework hiển thị cho người dùng ──────────────────────────────

FRAMEWORK_EXPLAINERS = {
    "AIDA (Attention – Interest – Desire – Action)": (
        "**AIDA** là framework kinh điển nhất trong copywriting.\n"
        "- 🎯 **Attention**: Thu hút sự chú ý ngay từ dòng đầu\n"
        "- 💡 **Interest**: Kích thích sự quan tâm bằng thông tin giá trị\n"
        "- ❤️ **Desire**: Tạo khao khát sở hữu/trải nghiệm\n"
        "- 🚀 **Action**: Kêu gọi hành động rõ ràng, cụ thể"
    ),
    "PAS (Problem – Agitate – Solution)": (
        "**PAS** là framework mạnh nhất cho quảng cáo và email.\n"
        "- ⚠️ **Problem**: Xác định nỗi đau cụ thể của khách hàng\n"
        "- 🔥 **Agitate**: Khuếch đại nỗi đau, làm nó trở nên cấp bách\n"
        "- ✅ **Solution**: Giới thiệu giải pháp như lối thoát duy nhất"
    ),
    "FAB (Features – Advantages – Benefits)": (
        "**FAB** tập trung vào giá trị thực sự của sản phẩm.\n"
        "- 📦 **Features**: Đặc điểm/tính năng của sản phẩm\n"
        "- ⚡ **Advantages**: Ưu điểm vượt trội so với đối thủ\n"
        "- 🏆 **Benefits**: Lợi ích thực tế khách hàng nhận được"
    ),
    "BAB (Before – After – Bridge)": (
        "**BAB** dùng kỹ thuật chuyển đổi trạng thái để thuyết phục.\n"
        "- 😟 **Before**: Mô tả tình trạng hiện tại (có vấn đề)\n"
        "- 😊 **After**: Vẽ ra bức tranh tương lai lý tưởng\n"
        "- 🌉 **Bridge**: Sản phẩm/dịch vụ là cây cầu nối hai thế giới"
    ),
    "STAR (Situation – Task – Action – Result)": (
        "**STAR** dùng cấu trúc câu chuyện để tạo niềm tin.\n"
        "- 📍 **Situation**: Bối cảnh ban đầu\n"
        "- 🎯 **Task**: Nhiệm vụ/mục tiêu cần đạt được\n"
        "- 🔧 **Action**: Hành động đã thực hiện với sản phẩm\n"
        "- 📊 **Result**: Kết quả cụ thể, đo lường được"
    ),
    "4P (Promise – Picture – Proof – Push)": (
        "**4P** là framework mạnh cho sales letter và landing page.\n"
        "- 🤝 **Promise**: Lời hứa táo bạo ngay từ đầu\n"
        "- 🖼️ **Picture**: Vẽ bức tranh sống động về kết quả\n"
        "- 📋 **Proof**: Bằng chứng, số liệu, testimonial\n"
        "- 👉 **Push**: Thúc đẩy hành động với urgency/scarcity"
    ),
    "PPPP (Picture – Promise – Prove – Push)": (
        "**PPPP** là biến thể nâng cao của 4P, mở đầu bằng hình ảnh mạnh.\n"
        "- 🎨 **Picture**: Hình ảnh/kịch bản kết quả lý tưởng\n"
        "- 🤝 **Promise**: Cam kết sản phẩm sẽ đưa đến đó\n"
        "- ✅ **Prove**: Chứng minh bằng case study/data\n"
        "- 🚀 **Push**: CTA mạnh với lý do hành động ngay"
    ),
    "Hook – Story – Offer": (
        "**Hook-Story-Offer** là framework của Russell Brunson, tối ưu cho VSL và email.\n"
        "- 🎣 **Hook**: Câu mở đầu kéo người đọc vào không thể rời\n"
        "- 📖 **Story**: Câu chuyện cá nhân tạo kết nối cảm xúc\n"
        "- 🎁 **Offer**: Trình bày offer không thể từ chối"
    ),
    "AI tự chọn framework tối ưu nhất": (
        "**AI tự chọn** – Gemini sẽ phân tích sản phẩm, đối tượng và mục tiêu\n"
        "để tự động chọn và kết hợp framework copywriting phù hợp nhất."
    ),
}


# ── Builder prompt chính ───────────────────────────────────────────────────────

def get_copywriting_prompt(
    product: str,
    benefit: str,
    target: str,
    framework: str,
    copy_type: str,
    tone: str,
    brand_instructions: str = "",
    enable_ab: bool = False,
) -> str:
    """
    Tạo prompt chuyên sâu cho Copywriting Agent.

    Args:
        product: Tên sản phẩm / dịch vụ
        benefit: Lợi ích nổi bật / Unique Value Proposition
        target: Đối tượng khách hàng mục tiêu
        framework: Framework copywriting đã chọn
        copy_type: Loại copy cần tạo
        tone: Giọng điệu / Tone of voice
        brand_instructions: Hướng dẫn Brand & Company Memory (nếu có)
        enable_ab: True → tạo 3 biến thể A/B thay vì 1 bản

    Returns:
        Chuỗi prompt hoàn chỉnh gửi đến Gemini
    """

    ab_instruction = ""
    if enable_ab:
        ab_instruction = """
## YÊU CẦU ĐẶC BIỆT: A/B TESTING
Thay vì 1 bản copy, hãy tạo ĐÚNG 3 BIẾN THỂ khác nhau (Phiên bản A, B, C).
Mỗi biến thể phải sử dụng cách tiếp cận, góc độ hoặc cảm xúc khác nhau
để phục vụ mục đích A/B testing thực chiến.
Đánh dấu rõ: **--- PHIÊN BẢN A ---**, **--- PHIÊN BẢN B ---**, **--- PHIÊN BẢN C ---**
"""

    framework_detail = _get_framework_instruction(framework, copy_type)

    prompt = f"""Bạn là một Copywriter chuyên nghiệp hàng đầu, có 15 năm kinh nghiệm viết copy bán hàng
thuyết phục cao cho thị trường Việt Nam. Bạn thành thạo mọi framework copywriting kinh điển
và biết cách biến mỗi từ ngữ thành đòn bẩy tạo ra chuyển đổi.

## THÔNG TIN ĐẦU VÀO

- **Sản phẩm / Dịch vụ**: {product}
- **Lợi ích nổi bật / USP**: {benefit}
- **Đối tượng mục tiêu**: {target}
- **Framework copywriting**: {framework}
- **Loại copy cần tạo**: {copy_type}
- **Giọng điệu (Tone)**: {tone}

## FRAMEWORK & CẤU TRÚC BẮT BUỘC

{framework_detail}

## QUY TẮC CHẤT LƯỢNG BẮT BUỘC

1. **Mở đầu bằng Hook cực mạnh** – 3 giây đầu quyết định tất cả
2. **Tập trung vào LỢI ÍCH, không phải tính năng** – Khách hàng mua kết quả, không mua sản phẩm
3. **Dùng ngôn ngữ của khách hàng** – Nói đúng từ ngữ của "{target}"
4. **Tạo sự khẩn cấp/khan hiếm** nếu phù hợp với loại copy
5. **CTA cụ thể và rõ ràng** – Không mơ hồ, không chung chung
6. **Bằng chứng xã hội / Social Proof** – Thêm số liệu, kết quả cụ thể khi có thể
7. **Ngôn ngữ Tiếng Việt tự nhiên, đúng văn hóa Việt** – Không dịch máy
8. **Đúng giọng điệu**: {tone}

## QUY TẮC ĐỊNH DẠNG

- Sử dụng xuống dòng và khoảng trắng để tạo nhịp đọc tốt
- Các điểm quan trọng dùng **in đậm** hoặc emoji phù hợp
- Độ dài phải phù hợp với loại copy: {copy_type}
{ab_instruction}
{brand_instructions}

## YÊU CẦU ĐẦU RA

Hãy viết copy HOÀN CHỈNH, SẴN SÀNG SỬ DỤNG NGAY, không cần chỉnh sửa thêm.
Không giải thích, không ghi chú, không tiêu đề thừa – CHỈ TRẢ VỀ BẢN COPY.
"""
    return prompt


def _get_framework_instruction(framework: str, copy_type: str) -> str:
    """Trả về hướng dẫn cấu trúc cụ thể cho từng framework + copy_type."""

    base = framework.split(" (")[0].strip().upper()

    if "AIDA" in base:
        return f"""Áp dụng framework **AIDA** cho {copy_type}:
**A – ATTENTION (Thu hút)**: Dòng mở đầu phải gây sốc, tạo tò mò hoặc đánh trúng nỗi đau trong <5 từ đầu
**I – INTEREST (Quan tâm)**: Cung cấp thông tin thú vị, thống kê, hoặc sự thật bất ngờ để giữ người đọc
**D – DESIRE (Khao khát)**: Vẽ bức tranh kết quả lý tưởng, làm người đọc thèm muốn sở hữu
**A – ACTION (Hành động)**: CTA mạnh, rõ ràng, tạo urgency nếu phù hợp"""

    elif "PAS" in base:
        return f"""Áp dụng framework **PAS** cho {copy_type}:
**P – PROBLEM (Vấn đề)**: Xác định CHÍNH XÁC nỗi đau mà "{copy_type}" nhắm đến, dùng ngôn ngữ của họ
**A – AGITATE (Khuếch đại)**: Làm nỗi đau trở nên đau hơn, cấp bách hơn – mô tả hậu quả nếu không giải quyết
**S – SOLUTION (Giải pháp)**: Giới thiệu sản phẩm/dịch vụ như lối thoát duy nhất, nhấn mạnh USP"""

    elif "FAB" in base:
        return f"""Áp dụng framework **FAB** cho {copy_type}:
**F – FEATURES (Tính năng)**: Liệt kê các tính năng/đặc điểm nổi bật của sản phẩm
**A – ADVANTAGES (Ưu điểm)**: Giải thích tại sao mỗi tính năng vượt trội hơn giải pháp thông thường
**B – BENEFITS (Lợi ích)**: Chuyển hóa mỗi ưu điểm thành kết quả THỰC TẾ mà khách hàng nhận được"""

    elif "BAB" in base:
        return f"""Áp dụng framework **BAB** cho {copy_type}:
**B – BEFORE (Trước)**: Mô tả sống động tình trạng hiện tại đau khổ, bế tắc của khách hàng
**A – AFTER (Sau)**: Vẽ bức tranh tương lai lý tưởng khi đã có giải pháp – đầy cảm xúc và cụ thể
**B – BRIDGE (Cầu nối)**: Sản phẩm/dịch vụ là cây cầu duy nhất đưa họ từ Before sang After"""

    elif "STAR" in base:
        return f"""Áp dụng framework **STAR** cho {copy_type}:
**S – SITUATION (Tình huống)**: Mô tả bối cảnh ban đầu của khách hàng hoặc case study thực tế
**T – TASK (Nhiệm vụ)**: Nêu rõ mục tiêu/thách thức cần giải quyết
**A – ACTION (Hành động)**: Mô tả cách sản phẩm/dịch vụ được triển khai để giải quyết
**R – RESULT (Kết quả)**: Số liệu, kết quả cụ thể, đo lường được – tạo niềm tin mạnh mẽ"""

    elif "4P" in base:
        return f"""Áp dụng framework **4P** cho {copy_type}:
**P – PROMISE (Lời hứa)**: Tuyên bố táo bạo, lợi ích lớn nhất ngay từ dòng đầu tiên
**P – PICTURE (Hình ảnh)**: Vẽ bức tranh sống động về cuộc sống sau khi có sản phẩm
**P – PROOF (Bằng chứng)**: Cung cấp bằng chứng: số liệu, testimonial, giải thưởng, chứng nhận
**P – PUSH (Thúc đẩy)**: CTA mạnh kết hợp với urgency, scarcity hoặc bonus đặc biệt"""

    elif "PPPP" in base:
        return f"""Áp dụng framework **PPPP** cho {copy_type}:
**P – PICTURE (Hình ảnh)**: Mở đầu bằng kịch bản/hình ảnh kết quả lý tưởng, sống động và cảm xúc
**P – PROMISE (Lời hứa)**: Cam kết sản phẩm sẽ đưa họ đến bức tranh đó
**P – PROVE (Chứng minh)**: Case study, số liệu, bằng chứng thực tế không thể phủ nhận
**P – PUSH (Thúc đẩy)**: CTA mạnh với lý do hành động ngay bây giờ, không chần chờ"""

    elif "HOOK" in base or "STORY" in base:
        return f"""Áp dụng framework **Hook – Story – Offer** của Russell Brunson cho {copy_type}:
**HOOK (Câu móc)**: Câu mở đầu cực mạnh tạo sự tò mò không thể cưỡng lại, kéo người đọc vào
**STORY (Câu chuyện)**: Kể câu chuyện cá nhân/khách hàng có arc cảm xúc: xung đột → khám phá → chuyển hóa
**OFFER (Đề nghị)**: Trình bày offer với giá trị stack rõ ràng, bonus, guarantee và CTA không thể từ chối"""

    else:  # AI tự chọn
        return f"""Phân tích sản phẩm, đối tượng và mục tiêu để **tự chọn và kết hợp** các framework
copywriting phù hợp nhất cho {copy_type}. Ghi rõ framework bạn đã chọn ở đầu bản copy
dưới dạng: [Framework đã chọn: ...]"""
