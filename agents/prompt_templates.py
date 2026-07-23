def get_weekly_plan_prompt(topic=None, target=None, goal=None, days=7, style=None):
    safe_days = int(days or 7)
    if not topic or not str(topic).strip():
        return f"""
        Hãy đóng vai một Content Strategist. Lập kế hoạch nội dung {safe_days} ngày để quảng bá dịch vụ "Xây dựng AI-Agent thương hiệu cá nhân".
        Yêu cầu:
        - Mỗi ngày có 1 chủ đề chính.
        - Phân bổ: 2 bài chuyên sâu kỹ thuật, 2 bài về lợi ích kinh tế (kiếm tiền), 2 bài Case Study, 1 bài kêu gọi dịch vụ.
        - Trả về kết quả dưới dạng JSON thuần túy (Array of Objects).
        - Mỗi Object bắt buộc có đúng các field: "day", "topic", "target", "goal", "format", "angle", "hook", "cta".
        - "day": Thứ/ngày trong kế hoạch.
        - "topic": Chủ đề nội dung của ngày đó.
        - "target": Đối tượng mục tiêu phù hợp nhất.
        - "goal": Mục tiêu của bài viết.
        - "format": Định dạng nội dung, ví dụ: Facebook post, LinkedIn post, Reels, Case Study, Tutorial.
        - "angle": Góc nhìn tiếp cận.
        - "hook": Câu mở đầu thu hút.
        - "cta": Câu hỏi/kêu gọi tương tác tự nhiên.
        - Ngôn ngữ: Tiếng Việt.
        - Chỉ trả về JSON Array hợp lệ để Python json.loads đọc được, không giải thích thêm.
        - Không dùng dấu ngoặc kép " bên trong giá trị text; nếu cần nhấn mạnh, dùng dấu nháy đơn hoặc bỏ ngoặc.
        - Không xuống dòng bên trong value, không thêm dấu phẩy thừa.
        """
    else:
        return f"""
        Hãy đóng vai một Content Strategist. Lập kế hoạch nội dung {safe_days} ngày theo chủ đề người dùng nhập.

        Thông tin đầu vào:
        - Chủ đề chính: {topic}
        - Đối tượng mục tiêu: {target or 'Tự chọn đối tượng phù hợp nhất'}
        - Mục tiêu nội dung: {goal or 'Giáo dục, chia sẻ kinh nghiệm thực chiến và tạo tương tác tự nhiên'}
        - Phong cách: {style or 'Dễ hiểu, thực chiến, có giá trị ứng dụng'}

        Yêu cầu:
        - Mỗi ngày có 1 ý tưởng nội dung khác nhau, không trùng lặp.
        - Nội dung phải bám sát chủ đề chính.
        - Trả về kết quả dưới dạng JSON thuần túy (Array of Objects).
        - Mỗi Object bắt buộc có đúng các field: "day", "topic", "target", "goal", "format", "angle", "hook", "cta".
        - "day": Thứ/ngày trong kế hoạch.
        - "topic": Chủ đề nội dung của ngày đó.
        - "target": Đối tượng mục tiêu của bài viết.
        - "goal": Mục tiêu cụ thể của bài viết.
        - "format": Định dạng nội dung, ví dụ: Facebook post, LinkedIn post, Reels, Case Study, Tutorial.
        - "angle": Góc nhìn tiếp cận.
        - "hook": Câu mở đầu thu hút.
        - "cta": Câu hỏi/kêu gọi tương tác tự nhiên.
        - Ngôn ngữ: Tiếng Việt.
        - Chỉ trả về JSON Array hợp lệ để Python json.loads đọc được, không giải thích thêm.
        - Không dùng dấu ngoặc kép " bên trong giá trị text; nếu cần nhấn mạnh, dùng dấu nháy đơn hoặc bỏ ngoặc.
        - Không xuống dòng bên trong value, không thêm dấu phẩy thừa.
        """

def get_ai_knowledge_sharing_prompt(tool_name, topic, audience, difficulty, knowledge_type):
    return f"""
Ban la chuyen gia chia se kien thuc AI thuc chien.

Hay tao mot noi dung AI Knowledge Sharing bang tieng Viet.

Thong tin dau vao:
- AI Tool: {tool_name}
- Topic: {topic}
- Audience: {audience}
- Difficulty: {difficulty}
- Knowledge Type: {knowledge_type}

Nguyen tac bat buoc:
- Khong quang cao.
- Khong ban hang.
- Khong PR dich vu, khoa hoc, cong ty hoac ca nhan.
- Tap trung chia se kinh nghiem thuc chien.
- Viet de hieu, ro rang, co tinh ung dung cao.
- Dua nhieu vi du cu the, gan voi cong viec thuc te.
- Dieu chinh ngon ngu va do sau theo Audience va Difficulty.
- Neu noi ve prompt, workflow hoac automation, hay dua mau co the ap dung ngay.
- Moi y chinh hoac dong quan trong nen bat dau bang 1 emoji phu hop voi y nghia cua cau, vi du: 💡 y tuong, ✅ viec nen lam, ⚠️ canh bao, 🎯 muc tieu, 📌 ghi nho, 🔍 phan tich, 🚀 hanh dong, 📊 so lieu, 🧩 framework, 💬 cau hoi.
- Emoji phai giup nguoi doc quet noi dung nhanh hon, khong dung qua day, khong chen emoji vo nghia vao giua cau.
- Voi CEO hoac AI Specialist, dung emoji tiet che va chuyen nghiep; uu tien 📊 🎯 🔍 ⚠️ ✅ 📌 thay vi emoji cam xuc qua manh.
- Khong them phan nao ngoai 15 phan ben duoi.

Output gom dung 15 phan, dung thu tu va dung tieu de sau:

### 1. Overview
Giai thich tong quan ve chu de, boi canh su dung {tool_name}, va nguoi doc se hoc duoc gi.

### 2. Why people fail
Chi ra nhung ly do pho bien khien moi nguoi ap dung sai hoac khong hieu dung chu de nay.

### 3. Best practices
Liet ke cac nguyen tac thuc chien nen lam, co vi du minh hoa cho tung y quan trong.

### 4. Workflow
Dua ra workflow tung buoc de ap dung vao cong viec thuc te.

### 5. Prompt framework
Dua ra khung prompt/cong thuc thao tac co the tai su dung, kem 2-3 mau prompt cu the.

### 6. Real example
Dua mot vi du thuc te, co dau vao, cach lam, va ket qua mong doi.

### 7. Case study
Viet mot case study ngan, trung tinh, co van de ban dau, cach ap dung, ket qua va bai hoc.

### 8. Comparison
So sanh cach lam dung va cach lam sai, hoac so sanh {tool_name} voi cach lam thu cong/cong cu lien quan.

### 9. Mistakes
Liet ke cac sai lam thuong gap va cach sua tung sai lam.

### 10. Checklist
Tao checklist ngan gon de nguoi doc tu kiem tra truoc khi ap dung.

### 11. Facebook post
Viet mot bai Facebook chia se kien thuc, khong ban hang, ngan gon, de doc, co vi du.

### 12. LinkedIn post
Viet mot bai LinkedIn chuyen nghiep, thuc chien, co insight va bai hoc ro rang.

### 13. Zalo post
Viet mot bai Zalo ngan, gan gui, de hieu, phu hop de gui/dua len Zalo.

### 14. Reels
Dua kich ban Reels ngan gom hook, canh quay, voice-over, text overlay va ket bai.

### 15. CTA
Dua cac cau hoi goi mo thao luan/hoc tap, khong keu goi mua hang, khong ban hang.
"""

def get_illustration_image_prompt(topic, target, content_type, platform, ai_tool=""):
    tool_context = f" using {ai_tool}" if ai_tool else ""
    return f"""### 3 prompt ảnh minh họa cho bài viết

#### Prompt 1 - Ảnh chính / Editorial Hero
A professional editorial hero image for a social media post about "{topic}"{tool_context}, designed for {platform}. The audience is {target}. Show a realistic Vietnamese business or work context, people using AI thoughtfully, modern workspace, subtle technology elements, clear focal point, warm cinematic lighting, natural colors, professional but approachable mood, educational tone, high trust, premium social media visual, 4:5 aspect ratio, sharp focus, no sales banner, no clickbait, no clutter, no distorted hands, no unreadable text, no logos.

#### Prompt 2 - Ảnh giải thích / Infographic Concept
A clean educational infographic-style illustration about "{topic}"{tool_context}, designed for {platform} and suitable for {target}. Visualize the main idea as a simple workflow, before-after comparison, or step-by-step framework. Use modern flat-realistic design, clear hierarchy, minimal Vietnamese business aesthetic, soft background, icons and abstract UI elements, professional blue-green accent colors, easy to understand at a glance, 4:5 aspect ratio, no tiny unreadable text, no fake brand logos, no exaggerated marketing claims.

#### Prompt 3 - Ảnh tương tác / Social Thumbnail
A scroll-stopping but professional social media thumbnail image about "{topic}"{tool_context}, designed for {platform}. Create a strong visual metaphor that highlights the key pain point or benefit for {target}: focused human expression, AI assistant interface, practical business setting, balanced composition with empty space for optional headline text, high contrast, crisp lighting, realistic details, trustworthy educational mood, 16:9 or 4:5 aspect ratio, no clickbait, no messy background, no distorted hands, no unreadable text, no logos.
""".strip()

def get_viral_marketing_prompt(platform, topic, target, angle_selection):
    return f"""
Bạn là chuyên gia Viral Content Marketing cho Facebook, LinkedIn và Zalo (CONTENT ENGINE), bậc thầy tạo hook thu hút (HOOK GENERATOR), chuyên gia phân tích cấu trúc bài viết lan truyền (VIRAL STRUCTURE ENGINE), chuyên gia giữ chân người đọc (RETENTION ENGINE), bậc thầy đa dạng hóa góc nhìn (MULTI ANGLE GENERATOR), chuyên gia thiết kế hình ảnh thu hút (REELS & THUMBNAIL ENGINE) kiêm chuyên gia định vị đối tượng mục tiêu sâu sắc (AUDIENCE PERSONALIZATION).

Nhiệm vụ: Hãy tạo ra bộ nội dung tiếp thị viral toàn diện cho nền tảng {platform} dựa trên chủ đề và đối tượng mục tiêu dưới đây.

Chủ đề: {topic}
Đối tượng mục tiêu được chọn: {target}
Góc nhìn yêu cầu: {angle_selection}

---
BẮT BUỘC TRẢ VỀ ĐÚNG 16 PHẦN THEO ĐỨNG THỨ TỰ VÀ ĐỊNH DẠNG DƯỚI ĐÂY (SỬ DỤNG TIÊU ĐỀ MARKDOWN CÓ SỐ THỨ TỰ RÕ RÀNG):

### 1. Audience Insight
Phân tích sâu sắc hành vi, tâm lý, nỗi sợ thầm kín, rào cản và khao khát lớn nhất của nhóm đối tượng "{target}" liên quan đến chủ đề "{topic}".

### 2. Pain Point
Chỉ ra nỗi đau cụ thể, những nhức nhối thực tế mà đối tượng đang gặp phải hàng ngày khi chưa có giải pháp.

### 3. Desire
Kết quả lý tưởng, mong muốn tột cùng mà đối tượng khát khao đạt được để giải quyết nỗi đau đó.

### 4. 7 góc triển khai
Mô tả tóm tắt ngắn gọn cách tiếp cận chủ đề dưới 7 góc nhìn hoàn toàn khác biệt:
1. Góc sai lầm phổ biến: Chỉ ra sai lầm của hầu hết mọi người và vạch trần hậu quả.
2. Góc câu chuyện thực tế: Kể một câu chuyện có thật xảy ra ngoài đời để chứng minh.
3. Góc trải nghiệm cá nhân: Dùng góc nhìn thứ nhất "Tôi" chia sẻ bài học xương máu của bản thân.
4. Góc tranh luận: Đưa ra góc nhìn trái chiều cực đoan, thách thức niềm tin cũ để khơi mào tranh luận.
5. Góc xu hướng: Liên kết chủ đề với một làn sóng, trào lưu hay công nghệ đang bùng nổ hiện nay.
6. Góc hướng dẫn: Đưa ra các bước thực hiện vô cùng rõ ràng, cụ thể dạng "Làm thế nào để...".
7. Góc case study: Mô tả một trường hợp thành công cụ thể với số liệu trước và sau rõ ràng. ĐẶC BIỆT: Nếu đối tượng mục tiêu là CEO, bắt buộc bổ sung ngay sau phần này một lớp phân tích chuyên sâu mang tên "Executive Insight" để làm rõ bài học cốt lõi dưới lăng kính quản trị vĩ mô, đòn bẩy công nghệ và quản trị sự thay đổi.

### 5. 10 tiêu đề viral
Danh sách 10 tiêu đề giật tít siêu cuốn hút, kích thích tò mò cực độ khiến người dùng dừng lướt và click đọc ngay lập tức. (Lưu ý: Đối với CEO, tiêu đề phải giữ tính chuyên nghiệp, tránh từ ngữ giật gân rẻ tiền).

### 6. Bài Facebook
Viết một bài đăng Facebook hoàn chỉnh, tối ưu hóa hiển thị và tương tác.

**QUY TẮC BỐ CỤC TRÌNH BÀY BẮT MẮT (BẮT BUỘC):**
- Dòng đầu tiên: Ghi "[Cấu trúc tối ưu: AIDA/PAS/Storytelling/Listicle/Before-After]". Cấu trúc phải phù hợp với góc nhìn được yêu cầu.
- HOOK 3 DÒNG ĐẦU: Viết in đậm bằng chữ HOA hoặc dùng emoji ⚡🔥❌ mở đầu để gây chú ý tức thì. Xoáy vào Nỗi đau, Sai lầm, Góc nhìn trái chiều, Kết quả bất ngờ, hoặc Câu hỏi tò mò.
- PHÂN TÁCH CÁC PHẦN bằng dấu ━━━━━━━━━━ hoặc emoji 👇🔽▶️ để tạo nhịp đọc rõ ràng, không nhìn thành một khối chữ dày đặc.
- MỖI Ý CHÍNH bắt đầu bằng một emoji phù hợp với ý nghĩa của câu (💡 ý tưởng, ✅ việc nên làm, ⚠️ cảnh báo, 🎯 mục tiêu, 📌 ghi nhớ, 🔍 phân tích, 🚀 hành động, 📊 số liệu, 🧩 framework, 💬 câu hỏi) rồi viết ngắn 1 câu, xuống dòng ngay.
- Emoji phải làm nổi bật ý chính và giúp người đọc quét nhanh nội dung; không lạm dụng, không nhồi emoji liên tục, không dùng emoji sai ngữ cảnh.
- Với CEO, Chuyên gia AI hoặc Nhà đầu tư, dùng emoji tiết chế và chuyên nghiệp; ưu tiên 📊 🎯 🔍 ⚠️ ✅ 📌 thay vi emoji cảm xúc quá mạnh.
- GIỮA CÁC ĐOẠN để 1 dòng trống tạo khoảng thở cho mắt.
- PHẦN CTA cuối bài: Tách hẳn bằng dấu ━━━ hoặc ──── rồi đặt câu hỏi mở kèm emoji 💬🤔.
- HASHTAG: Tách riêng 1 khối ở cuối cùng, mỗi hashtag cách nhau 1 khoảng trắng.

**QUY TẮC NỘI DUNG:**
  * Nếu Góc nhìn yêu cầu là "Sinh trọn bộ 7 bài (Multi-Angle)": Hãy viết chi tiết 7 bài viết Facebook hoàn toàn khác biệt tương ứng với 7 góc triển khai ở mục 4, đánh số rõ ràng "Bài 1 (Góc sai lầm phổ biến)..." đến "Bài 7 (Góc case study)...". Mỗi bài vẫn tuân thủ đầy đủ các quy tắc bên dưới.
  * Ngược lại, viết 1 bài viết chi tiết tập trung sâu vào đúng Góc nhìn yêu cầu ({angle_selection}).
- Áp dụng các kỹ thuật giữ chân (RETENTION ENGINE): Open Loop (mở ra câu hỏi chưa có lời giải ngay), Curiosity Gap (khoảng cách tò mò), và Delayed Reveal (trì hoãn việc tiết lộ giải pháp/thực tế quan trọng nhất đến cuối bài).
- Khéo léo chèn một trong các câu dẫn dắt kịch tính sau: "Nhưng đó chưa phải điều quan trọng nhất...", "Điều bất ngờ hơn là...", "Và đây mới là lý do thật sự...", "Phần lớn mọi người đều bỏ qua điều này...".
- ĐẶC BIỆT: Nếu đối tượng mục tiêu là CEO, bài viết Facebook PHẢI bổ sung một lớp phân tích ngắn mang tên "Executive Insight" ở cuối bài viết (ngay trước phần Hashtag) để đúc rút bài học quản trị cốt lõi dưới lăng kính quản trị hệ thống, đòn bẩy công nghệ và quản trị sự thay đổi, nâng tầm uy tín của tác giả như một nhà tư vấn chiến lược hay chuyên gia AI đầu ngành.
- VIẾT CỰC KỲ NGẮN GỌN, XÚC TÍCH: Tối đa KHÔNG QUÁ 800 KÝ TỰ (bao gồm cả khoảng trắng) cho mỗi bài viết. Mỗi đoạn CHỈ VIẾT 1 CÂU DUY NHẤT rồi xuống dòng. Không viết lan man, không giải thích dài dòng. Ưu tiên câu ngắn dưới 15 từ. Bỏ mọi phần thừa, chỉ giữ lại ý cốt lõi nhất.
- Ngôn ngữ đơn giản, gần gũi, đời thường, giàu cảm xúc (tò mò, đồng cảm, ngạc nhiên, hy vọng, truyền cảm hứng). Nhúng Emoji đa dạng theo ngữ cảnh. ĐẶC BIỆT: Khi viết cho đối tượng CEO hay Chuyên gia AI, cần tuyệt đối tránh các từ ngữ cảm xúc phóng đại rẻ tiền.
- KÊU GỌI TƯƠNG TÁC TỰ NHIÊN (CTA): Hỏi ý kiến người đọc bằng các câu hỏi mở kích thích thảo luận sâu (Không dùng "Comment YES" hay "Bình luận tôi muốn").
- Hashtag: Thêm 5-8 hashtag tối ưu SEO và viral ở cuối mỗi bài viết (#Marketing #AI #...).

### 7. Bài LinkedIn
Viết một bài đăng LinkedIn hoàn chỉnh, chuyên nghiệp, có insight điều hành và bài học thực chiến rõ ràng. Tối ưu cho đối tượng chuyên môn, quản lý, CEO hoặc chủ doanh nghiệp.

**QUY TẮC BỐ CỤC LINKEDIN (BẮT BUỘC):**
- Dòng đầu tiên là hook chuyên nghiệp, ngắn, sắc, không giật gân rẻ tiền.
- Mở bài bằng một quan sát, nghịch lý, số liệu, hoặc vấn đề quản trị liên quan trực tiếp đến "{topic}".
- Thân bài chia thành các đoạn ngắn, mỗi đoạn 1-2 câu, dễ đọc trên LinkedIn.
- Bắt buộc có một phần "Executive Insight" nếu đối tượng mục tiêu là CEO / Chuyên gia AI / Nhà đầu tư.
- Có một bài học quản trị hoặc bài học triển khai rõ ràng, tránh văn phong quảng cáo.
- Kết bài bằng câu hỏi mở để kích hoạt thảo luận chuyên môn.
- Hashtag: Thêm 3-5 hashtag chuyên nghiệp, liên quan đến AI, quản trị, vận hành hoặc chủ đề chính.
- Nếu Góc nhìn yêu cầu là "Sinh trọn bộ 7 bài (Multi-Angle)", hãy viết 7 bài LinkedIn ngắn tương ứng với 7 góc triển khai ở mục 4.

### 8. Bài Zalo
Viết một bài đăng Zalo hoàn chỉnh. TỐI ĐA KHÔNG QUÁ 500 KÝ TỰ (bao gồm cả khoảng trắng).

**QUY TẮC BỐ CỤC TRÌNH BÀY BẮT MẮT CHO ZALO (BẮT BUỘC):**
- DÒNG ĐẦU TIÊN: Hook mạnh kèm emoji ⚡🔥 viết ngắn gọn gây tò mò tức thì.
- MỖI Ý bắt đầu bằng emoji (✅ 👉 💡 📌 🎯) rồi viết 1 câu cực ngắn, xuống dòng ngay.
- GIỮA CÁC Ý: Để 1 dòng trống tạo khoảng thở, tránh viết chữ dính liền nhau.
- PHẦN KẾT: Dùng emoji 💬 hoặc 🤔 mở đầu câu hỏi CTA, tách riêng khỏi nội dung chính bằng dấu ────.
- Văn phong gần gũi như nhắn tin trực tiếp 1-1, mỗi ý chỉ 1 câu ngắn rồi xuống dòng.
(Lưu ý: Nếu Góc nhìn yêu cầu là "Sinh trọn bộ 7 bài (Multi-Angle)", hãy viết tóm tắt nhanh/bài viết ngắn gọn tương ứng cho cả 7 bài để dễ gửi Zalo).
- ĐẶC BIỆT: Đối với CEO, bài Zalo vẫn phải giữ chiều sâu chiến lược và bổ sung lớp "Executive Insight" tóm tắt cực kỳ gọn gàng, súc tích, tránh hoàn toàn các từ ngữ sáo rỗng.

### 9. Kịch bản Reels
Một kịch bản video ngắn (Reels/TikTok) kịch tính, hấp dẫn và giữ chân người xem cao nhất:
- Hook video (3 giây đầu tiên cực mạnh để giữ chân người xem)
- Voice-over (Lời thuyết minh chi tiết từng câu)
- Cảnh quay (Mô tả chi tiết hình ảnh, hành động của nhân vật hoặc bối cảnh diễn ra trên màn hình)
- Text Overlay (Chữ lớn nổi bật hiển thị trên video tương ứng từng phân cảnh)
- CTA (Lời kêu gọi hành động cuốn hút ở cuối)

### 10. Caption Reels
Viết caption đăng kèm video Reels (2-3 dòng, tối đa 150 ký tự). Yêu cầu bắt buộc:
- Mở đầu bằng một "Open Loop" mạnh mẽ, gợi mở câu hỏi chưa có câu trả lời rõ ràng để kích thích sự tò mò (Ví dụ: "90% doanh nghiệp đang phải trả giá đắt cho một sai lầm vô hình...", "Tôi đã mất hàng nghìn USD chi phí vận hành trước khi nhận ra điều này...").
- TUYỆT ĐỐI KHÔNG dùng ngôn ngữ quảng cáo, giật gân, kêu gọi mua hàng hay PR sáo rỗng.
- ĐỐI VỚI CEO / Chuyên gia AI / Nhà đầu tư: Caption phải là một lát cắt tư duy quản trị hoặc insight điều hành sâu sắc (Ví dụ: "Công nghệ không giải quyết được lỗ hổng cấu trúc. Hệ thống vận hành mới là đòn bẩy thực tế."). Nội dung phải giống như một dòng trạng thái đúc rút kinh nghiệm của một chuyên gia chiến lược trên LinkedIn.

### 11. CTA
Danh sách các câu hỏi gợi mở thảo luận sâu sắc dành riêng cho đối tượng "{target}" liên quan đến chủ đề này.

### 12. Thumbnail Titles
Đưa ra đúng 3 tiêu đề ảnh Thumbnail (ngắn gọn, dưới 7 từ, viết HOA toàn bộ) tương ứng với 3 bối cảnh ảnh bên dưới.
- Đối với CEO/Chuyên gia AI/Nhà đầu tư: Tiêu đề phải mang chiều sâu chiến lược và quản trị, tránh cảm giác câu view rẻ tiền (Ví dụ: "TỰ ĐỘNG HÓA VẬN HÀNH").
- Đối với các nhóm khác: Tiêu đề dạng clickbait kích thích tò mò (Ví dụ: "AI SẮP THAY ĐỔI MỌI THỨ").

### 13. AI Thumbnail Prompts
Tạo đúng 3 prompt vẽ ảnh AI bằng tiếng Anh (Dành cho Midjourney, DALL-E 3) tương ứng cho 3 bối cảnh:
1. Bối cảnh Công nghệ (Technology)
2. Bối cảnh Doanh nhân (Entrepreneur)
3. Bối cảnh An toàn cho Quảng cáo Facebook (Facebook Ads Safe)
* Mỗi prompt BẮT BUỘC phải tích hợp chính xác hai yếu tố sau lồng trực tiếp vào thiết kế ảnh:
- Tiêu đề Thumbnail tương ứng từ Mục 12 dưới dạng chữ Typography nổi bật, tinh tế trên ảnh (clean typography overlay text).
- Website "hungvietai.com" ở góc dưới bên phải ảnh dưới dạng watermark nhỏ gọn, tinh xảo (small elegant white text "hungvietai.com" watermark in the bottom-right corner).
* Định dạng bắt buộc: [Subject] + [Emotion] + [Cinematic Lighting] + [Professional Composition] + [Ultra Detailed] + [Social Media Thumbnail Style] + [clean typography overlay text "THUMBNAIL_TITLE_HERE"] + [small elegant white text "hungvietai.com" watermark in the bottom-right corner]
Ví dụ: "A futuristic AI robot working on multiple screens, focused emotion, warm cinematic lighting, close-up professional composition, ultra detailed, social media thumbnail style, clean typography overlay text 'AUTOMATE PROCESSES', small elegant white text 'hungvietai.com' watermark in the bottom-right corner"

### 14. Hashtags
Danh sách 5-8 hashtag tối ưu SEO và có độ lan truyền cao nhất cho chủ đề này.

### 15. Viral Score (1-10)
Đánh giá khách quan điểm số tiềm năng lan truyền của bộ nội dung này từ 1 đến 10 dựa trên tính giật gân, chất lượng bài viết và mức độ thu hút đối tượng mục tiêu.

### 16. Lý do chấm điểm
Phân tích ngắn gọn lý do vì sao bộ nội dung này đạt được điểm số đó, chỉ ra điểm sáng giá nhất giúp tăng Reach, Engagement hoặc Comment.

---
LƯU Ý QUAN TRỌNG VỀ ĐỊNH HƯỚNG VĂN PHONG VÀ NGÔN NGỮ (BẮT BUỘC PHẢI TUÂN THỦ):

1. ĐỐI VỚI ĐỐI TƯỢNG "CEO (Chiến lược, Tăng trưởng, Lợi nhuận)" HOẶC "Chuyên gia AI (AI Agent, Automation, Công nghệ)" HOẶC "Nhà đầu tư (Xu hướng, ROI, Cơ hội)":
- BÀI VIẾT PHẢI CÓ PHONG THÁI CỦA MỘT CEO ĐIỀU HÀNH HOẶC CHUYÊN GIA TƯ VẤN CHIẾN LƯỢC CẤP CAO (NHƯ MCKINSEY, BCG), TUYỆT ĐỐI KHÔNG PHẢI BÀI MARKETING CỦA COPYWRITER QUẢNG CÁO.
- NGHIÊM CẤM TUYỆT ĐỐI (BLACKLIST) SỬ DỤNG CÁC TỪ NGỮ QUẢNG CÁO SÁO RỖNG, CẢM TÍNH, PHÓNG ĐẠI, GIẬT GÂN SAU ĐÂY: "phép màu", "minh chứng hùng hồn", "âm thầm tạo ra", "đáng kinh ngạc", "ngoạn mục", "thần kỳ", "bí mật", "thần tốc", "vi diệu", "kỳ tích", "đột phá ngoạn mục", "vũ khí tối tân". Nếu sử dụng bất kỳ từ nào trong số này, bài viết sẽ bị coi là thất bại nghiêm trọng.
- THAY VÀO ĐÓ, BẮT BUỘC sử dụng tư duy điều hành quản trị doanh nghiệp (Executive Mindset), tư duy hệ thống và văn phong thực chứng, điềm đạm, đẳng cấp, chuyên nghiệp.
- PHẢI tăng cường tối đa dữ liệu thực chứng (Data-driven), chỉ số đo lường thực tế (KPI, ROI, OpEx - chi phí vận hành, CapEx - chi phí đầu tư, LTV - giá trị trọn đời khách hàng, CAC - chi phí sở hữu khách hàng, tỷ lệ chuyển đổi, tỷ suất lợi nhuận ròng).
- PHẢI sử dụng các thuật ngữ quản trị và công nghệ chuẩn xác: "chuỗi giá trị (value chain)", "đòn bẩy quy mô", "mô hình vận hành tích hợp (operating model)", "tối ưu hóa tài nguyên", "quản trị rủi ro hệ thống", "quản trị sự thay đổi (change management)", "tự động hóa quy trình nghiệp vụ (BPA)", "mô hình ngôn ngữ lớn (LLM)", "hạ tầng dữ liệu (data infrastructure)", "hiệu suất nhân sự", "năng lực cốt lõi (core competency)".
- Phân tích sâu sắc các rào cản thực tế về văn hóa doanh nghiệp, bài toán chuyển đổi số từ góc nhìn của ban điều hành cấp cao chứ không chỉ ca ngợi công nghệ đơn thuần.
- ĐẶC BIỆT: Bổ sung lớp "Executive Insight" ngay sau phần Case Study (mục 4.7) và ở phần cuối của Bài Facebook (mục 6), Bài LinkedIn (mục 7), Bài Zalo (mục 8) khi đối tượng mục tiêu là CEO / Chuyên gia AI / Nhà đầu tư.

2. ĐỐI VỚI CÁC ĐỐI TƯỢNG KHÁC:
- Sales: Chốt sale thần tốc, Khách hàng tiềm năng, Bùng nổ doanh số. Văn phong thực chiến, năng động.
- Chủ Shop: Quản lý đơn hàng, Marketing hiệu quả, Quảng cáo ra đơn rẻ. Văn phong gần gũi, thực tế.
- Freelancer: Thương hiệu cá nhân, Gia tăng thu nhập, Khách hàng chất lượng. Văn phong tự do, truyền cảm hứng.

Xuất ra toàn bộ 16 phần theo đúng số thứ tự rõ ràng từ 1 đến 16. Không giải thích gì thêm ngoài cấu trúc được yêu cầu.
"""


def get_creative_concept_prompt(full_article_content: str) -> str:
    """
    Sinh prompt phân tích TOÀN BỘ bài viết và tạo 03 Creative Concept
    khác nhau phục vụ thiết kế Thumbnail kèm Prompt tạo ảnh cho mỗi Concept.

    Args:
        full_article_content: Toàn bộ nội dung bài viết (không rút gọn)

    Returns:
        Chuỗi prompt hoàn chỉnh gửi đến Gemini
    """
    return f"""Bạn là Creative Director, AI Marketing Strategist, Brand Designer và Senior Prompt Engineer hàng đầu.

Bạn vừa hoàn thành bài viết dưới đây.
Nhiệm vụ tiếp theo: Phân tích TOÀN BỘ bài viết — không bỏ qua bất kỳ đoạn nào — để sinh 03 Creative Concept thiết kế Thumbnail kèm Prompt tạo ảnh bằng Tiếng Anh cho mỗi Concept.

=== TOÀN BỘ BÀI VIẾT ===
{full_article_content}
========================

---

## BƯỚC 1 — PHÂN TÍCH BÀI VIẾT

Đọc toàn bộ nội dung trên và trích xuất chính xác:

**Phân tích bài viết:**
- **Chủ đề chính**: [Bài viết viết về điều gì?]
- **Thông điệp cốt lõi**: [Tóm tắt thông điệp chính trong 1 câu]
- **Giá trị cốt lõi**: [Giá trị thực sự mang lại cho người đọc]
- **Đối tượng mục tiêu**: [Ai sẽ đọc bài này? CEO / Marketer / Freelancer / ...]
- **Mục tiêu marketing**: [Awareness / Engagement / Conversion / Education]
- **Cảm xúc muốn truyền tải**: [Tò mò / Tin tưởng / Cảm hứng / Lo lắng / Hứng khởi]
- **CTA của bài viết**: [Người đọc cần làm gì sau khi đọc xong?]

---

## BƯỚC 2 — SINH 03 CREATIVE CONCEPT KÈM IMAGE PROMPT

Dựa trên phân tích ở Bước 1, sinh 03 Creative Concept hoàn toàn khác nhau.

**QUY TẮC BẮT BUỘC:**
- Mỗi Concept phải khác biệt hoàn toàn về: Mục tiêu truyền thông · Visual Story · Cảm xúc · Bố cục
- KHÔNG được chỉ thay đổi màu sắc hoặc góc chụp
- BẮT BUỘC phải viết Prompt tạo ảnh chi tiết bằng Tiếng Anh dưới trường PREVIEW PROMPT của mỗi Concept. Prompt phải dựa trên Visual Story và chứa chi tiết: Subject, Environment, Composition, Camera Angle, Lighting, Mood, Aspect ratio (ví dụ: --ar 16:9), và PHẢI tích hợp typography text overlay trực tiếp lên ảnh theo trường TEXT_OVERLAY.
- KHÔNG tự động sinh ảnh thực tế, chỉ sinh văn bản mô tả và prompt.

---

### 🏢 CONCEPT 1 — BUSINESS PROFESSIONAL
*Mục tiêu: Xây dựng uy tín — Đối tượng: CEO, Chủ doanh nghiệp, LinkedIn, Facebook Business*

Xuất đầy đủ 16 trường sau:

**CONCEPT NAME**: [Tên concept mô tả phong cách visual ngắn gọn]
**MARKETING GOAL**: [Mục tiêu truyền thông cụ thể của concept này]
**TARGET AUDIENCE**: [Đối tượng chính: CEO, Giám đốc, Chủ doanh nghiệp, LinkedIn Professional]
**MAIN MESSAGE**: [Thông điệp chính dưới góc nhìn lãnh đạo, ngắn gọn, mạnh mẽ]
**VISUAL STORY**: [Mô tả câu chuyện hình ảnh: ai đang làm gì, trong bối cảnh nào, tạo cảm giác gì]
**HERO SUBJECT**: [Nhân vật chính hoặc vật thể trọng tâm trong ảnh]
**SUPPORTING OBJECTS**: [Các yếu tố phụ trợ làm nền hoặc context]
**ENVIRONMENT**: [Bối cảnh: văn phòng cao cấp / phòng họp / cityscape / studio]
**MOOD**: [Professional · Authoritative · Confident · Trustworthy — chọn phù hợp với bài]
**EMOTION**: [Cảm xúc người xem phải cảm nhận được khi nhìn ảnh]
**COLOR DIRECTION**: [Bảng màu: Navy Blue · Charcoal · Gold · Clean White — hoặc màu phù hợp brand]
**COMPOSITION IDEA**: [Cách bố cục: Rule of Thirds / Central / Split-Screen / Hero Shot]
**HEADLINE SUGGESTION**: [Gợi ý tiêu đề ngắn gọn, dưới 7 từ, VIẾT HOA, phong cách lãnh đạo]
**CTA POSITION**: [Vị trí đặt CTA hoặc URL thương hiệu trên ảnh]
**BUSINESS VALUE**: [Lý do tại sao concept này hiệu quả với CEO và LinkedIn]
**TEXT_OVERLAY**: [Xác định 1–2 dòng text nổi bật NHẤT cần in lên ảnh. Dòng 1: Tiêu đề chính VIẾT HOA ngắn gọn (tối đa 6 từ) phản ánh thông điệp cốt lõi. Dòng 2 (tuỳ chọn): Sub-text hoặc con số nổi bật như "Tăng 3x doanh số" hoặc URL thương hiệu nhỏ góc dưới. Chỉ định font style: Bold Sans-Serif / Elegant Serif / Condensed Impact. Chỉ định vị trí: góc trái / trung tâm / dải ngang phía dưới / vùng tối bên phải.]
**PREVIEW PROMPT**: [Detailed English image prompt for Midjourney/Flux with clean typography text overlay integrated into composition. Include: Subject, Environment, Composition, Camera Angle, Lighting, Mood, Aspect ratio. MUST include text overlay instruction at end, e.g.: '...with bold white sans-serif headline text "HEADLINE HERE" overlaid on the lower-left dark area, small elegant watermark "hungvietai.com" bottom-right corner --ar 16:9']

---

### 🎬 CONCEPT 2 — CINEMATIC STORYTELLING
*Mục tiêu: Thu hút người xem · Tăng CTR · Tạo cảm xúc — Đối tượng: Facebook, Instagram, YouTube*

Xuất đầy đủ 16 trường sau:

**CONCEPT NAME**: [Tên concept mô tả phong cách điện ảnh]
**MARKETING GOAL**: [Mục tiêu: Tăng CTR · Thu hút ánh nhìn · Kích hoạt cảm xúc mạnh]
**TARGET AUDIENCE**: [Người dùng mạng xã hội · Facebook · Instagram · YouTube]
**MAIN MESSAGE**: [Thông điệp cảm xúc được truyền tải qua hình ảnh]
**VISUAL STORY**: [Kịch bản hình ảnh điện ảnh: khoảnh khắc cao trào, xung đột, chuyển hóa]
**HERO SUBJECT**: [Nhân vật chính hoặc yếu tố kịch tính nhất]
**SUPPORTING OBJECTS**: [Các yếu tố tạo không khí và chiều sâu]
**ENVIRONMENT**: [Bối cảnh cinematic: đô thị về đêm / studio tối / ánh sáng kịch tính]
**MOOD**: [Cinematic · Dramatic · Emotional · Story-driven — chọn phù hợp]
**EMOTION**: [Cảm xúc người xem: tò mò / hy vọng / lo lắng / kỳ vọng / bùng cháy]
**COLOR DIRECTION**: [Bảng màu cinematic: Deep Teal · Orange Glow · Midnight Blue · Amber]
**COMPOSITION IDEA**: [Bố cục điện ảnh: Dutch Angle / Low Angle Hero Shot / Leading Lines]
**HEADLINE SUGGESTION**: [Tiêu đề gây hook tò mò, dưới 7 từ, dạng câu hỏi hoặc shock]
**CTA POSITION**: [Vị trí CTA: góc dưới / overlay giữa / ẩn trong bố cục]
**BUSINESS VALUE**: [Lý do tại sao concept này tăng CTR và viral trên mạng xã hội]
**TEXT_OVERLAY**: [Xác định 1–2 dòng text nổi bật NHẤT cần in lên ảnh. Dòng 1: Câu hook ngắn VIẾT HOA (tối đa 6 từ) kích thích tò mò mạnh. Dòng 2 (tuỳ chọn): Sub-text tạo cảm xúc như số liệu bất ngờ hoặc câu hỏi ngắn. Font style: Condensed Impact / Heavy Bold / Italic Dramatic. Vị trí: dải ngang trung tâm / vùng tối phía trên / góc trái có nền mờ semi-transparent.]
**PREVIEW PROMPT**: [Detailed English image prompt for Midjourney/Flux with cinematic typography text overlay. Include: Subject, Environment, Composition, Camera Angle, Lighting, Mood, Aspect ratio. MUST include text overlay instruction, e.g.: '...with large bold condensed white text "HOOK TEXT HERE" dramatically overlaid center-frame, small elegant watermark "hungvietai.com" bottom-right --ar 16:9']

---

### 📊 CONCEPT 3 — INFOGRAPHIC / DATA DRIVEN
*Mục tiêu: Giáo dục · Case Study · Chia sẻ số liệu — Đối tượng: LinkedIn, Facebook, Pinterest*

Xuất đầy đủ 16 trường sau:

**CONCEPT NAME**: [Tên concept mô tả phong cách infographic]
**MARKETING GOAL**: [Giáo dục · Chia sẻ dữ liệu · Tăng Save & Share · Case Study]
**TARGET AUDIENCE**: [Professional · Người học · Marketer · Data-driven thinker]
**MAIN MESSAGE**: [Thông điệp được truyền tải qua số liệu, biểu đồ hoặc framework]
**VISUAL STORY**: [Cấu trúc infographic: trước-sau / bước-bước / so sánh / thống kê]
**HERO SUBJECT**: [Yếu tố data nổi bật nhất: con số / biểu đồ / framework / checklist]
**SUPPORTING OBJECTS**: [Icons · Arrows · Charts · Percentage indicators]
**ENVIRONMENT**: [Nền sạch: Clean White / Light Gray / Minimalist Tech Background]
**MOOD**: [Educational · Clear · Trustworthy · Data-Driven]
**EMOTION**: [Aha-moment · Tin tưởng · Muốn lưu lại · Muốn chia sẻ]
**COLOR DIRECTION**: [Bright Blue · Clean White · Accent Orange · Gray Scale]
**COMPOSITION IDEA**: [Bố cục thông tin: Grid Layout / Flow Diagram / Split Comparison]
**HEADLINE SUGGESTION**: [Tiêu đề dạng số liệu: "3 BƯỚC...", "87% CEO...", "TRƯỚC & SAU"]
**CTA POSITION**: [Vị trí CTA: footer infographic / nút Download / URL thương hiệu]
**BUSINESS VALUE**: [Lý do tại sao concept này được chia sẻ nhiều và tăng authority]
**TEXT_OVERLAY**: [Xác định 1–2 dòng text nội dung cần in lên ảnh infographic. Dòng 1: Tiêu đề số liệu nổi bật VIẾT HOA (ví dụ: "GIẢM 45% CHI PHÍ", "3 BƯỚC TỰ ĐỘNG HÓA") tối đa 6 từ. Dòng 2 (tuỳ chọn): Sub-label mô tả ngắn hoặc URL thương hiệu ở footer. Font style: Clean Bold Sans-Serif / Data Display / Modern Geometric. Vị trí: tiêu đề phía trên cùng trên nền trắng / dải màu ngang footer / vùng trống bên trái.]
**PREVIEW PROMPT**: [Detailed English image prompt for Midjourney/Flux with clean data typography overlay. Include: Subject, Environment, Composition, Camera Angle, Lighting, Mood, Aspect ratio. MUST include text overlay instruction, e.g.: '...with clean bold sans-serif text "KEY STAT HERE" prominently displayed in the upper section on white background, small elegant watermark "hungvietai.com" footer --ar 16:9']

---

Trả lời bằng Tiếng Việt.
Không giải thích thêm ngoài cấu trúc được yêu cầu.
"""

def get_single_concept_prompt(full_article_content: str, concept_name: str) -> str:
    """
    Sinh prompt để tái tạo (regenerate) duy nhất một Concept cụ thể kèm Prompt tạo ảnh của nó.
    """
    return f"""Bạn là Creative Director, AI Marketing Strategist và Senior Prompt Engineer hàng đầu.

Dựa trên bài viết dưới đây, hãy sinh lại duy nhất một Creative Concept có tên: "{concept_name}".

=== TOÀN BỘ BÀI VIẾT ===
{full_article_content}
========================

Yêu cầu xuất đầy đủ các trường thông tin của concept đó (giống như cấu trúc trong đặc tả gốc), bao gồm cả trường "PREVIEW PROMPT" chứa prompt tiếng Anh chi tiết để vẽ ảnh cho concept này.

Trả lời bằng Tiếng Việt.
Không giải thích thêm ngoài cấu trúc được yêu cầu.
"""



def get_thumbnail_image_prompt(concept_name: str, target_audience: str, platform: str, main_message: str, brand_guideline_str: str = "", campaign_context_str: str = "", headline_text: str = "", sub_text: str = "") -> str:
    """
    Sinh prompt tiếng Anh chi tiết gồm 22 trường để vẽ ảnh thumbnail bằng AI (Flux, Midjourney, DALL-E 3, SDXL, Imagen).
    Hỗ trợ text overlay (headline + sub-text) tích hợp trực tiếp lên ảnh để làm nổi bật nội dung bài viết.
    """
    sub_text_display = sub_text if sub_text else "Không có"
    if headline_text:
        overlay_instruction = (
            "\n- **Headline Text để overlay**: \"" + headline_text + "\""
            "\n- **Sub-text để overlay**: \"" + sub_text_display + "\""
        )
    else:
        overlay_instruction = (
            "\n- **Headline Text để overlay**: AI tự quyết định câu ngắn gọn nhất phản ánh Main Message (tối đa 6 từ VIẾT HOA)"
            "\n- **Sub-text để overlay**: AI tự quyết định sub-label phù hợp (số liệu nổi bật / URL thương hiệu / câu sub-hook)"
        )

    return f"""Bạn là Principal Prompt Engineer và AI Image Specialist hàng đầu thế giới.

Nhiệm vụ: Nhận thông tin đầu vào và sinh ra một Image Prompt tiếng Anh cực kỳ chi tiết, tối ưu cho DALL-E 3, Midjourney v6, Stable Diffusion XL, Flux, Imagen — với TEXT OVERLAY tích hợp trực tiếp lên ảnh để làm nổi bật nội dung bài viết.

## THÔNG TIN ĐẦU VÀO
- **Creative Concept**: {concept_name}
- **Target Audience**: {target_audience}
- **Platform**: {platform}
- **Main Message**: {main_message}
- **Brand Guideline**: {brand_guideline_str or 'Không có cấu hình'}
- **Campaign Context**: {campaign_context_str or 'Không có chiến dịch cụ thể'}{overlay_instruction}

## NGUYÊN TẮC TEXT OVERLAY (BẮT BUỘC ÁP DỤNG)
- Text phải ngắn gọn, sắc bén — tối đa 2 dòng, mỗi dòng không quá 6 từ.
- Màu chữ phải tương phản cực cao với nền ảnh (chữ trắng trên nền tối, chữ đen đậm trên nền sáng).
- Vị trí đặt text phải nằm trong vùng an toàn (safe zone) không che khuất nhân vật chính hoặc yếu tố trực quan cốt lõi.
- Font style phải phù hợp với Concept: Bold Sans-Serif cho Business/Cinematic, Clean Geometric cho Infographic, Condensed Impact cho Viral/CTR cao.
- Có thể dùng semi-transparent dark/light overlay strip phía sau chữ để tăng độ đọc được (legibility).

## YÊU CẦU ĐẦU RA — 22 TRƯỜNG KỸ THUẬT (OUTPUT FORMAT)
Xuất ra đúng 22 trường sau bằng Tiếng Việt. Nội dung kỹ thuật và prompt viết bằng TIẾNG ANH chuyên nghiệp để người dùng copy trực tiếp. Không giải thích thêm.

1. **Main Subject**: [Chi tiết về chủ thể chính]
2. **Visual Story**: [Hoạt động/câu chuyện hình ảnh đang diễn ra]
3. **Scene**: [Mô tả cảnh hành động]
4. **Environment**: [Bối cảnh không gian]
5. **Composition**: [Bố cục — PHẢI chừa vùng an toàn cho text overlay]
6. **Camera Angle**: [Góc camera]
7. **Perspective**: [Tiêu cự/điểm nhìn]
8. **Lighting**: [Hướng sáng/loại sáng]
9. **Color Palette**: [Hệ màu — bám sát Brand Colors nếu có]
10. **Mood**: [Tông không khí]
11. **Emotion**: [Cảm xúc nhân vật/người xem]
12. **Typography Safe Area**: [Vùng trống an toàn cho text overlay — mô tả rõ góc/dải nào của ảnh]
13. **Headline Text**: [Nội dung dòng text chính VIẾT HOA sẽ in lên ảnh]
14. **Headline Style**: [Font weight · Màu chữ · Kích cỡ tương đối · Có nền mờ không]
15. **Headline Position**: [Vị trí chính xác của headline trên ảnh: góc trái trên / dải ngang dưới / trung tâm / ...]
16. **Sub-text Content**: [Nội dung dòng text phụ — số liệu nổi bật / URL / sub-hook / để trống nếu không cần]
17. **Sub-text Style**: [Font style nhỏ hơn · Màu sắc · Vị trí so với Headline]
18. **CTA Area**: [Vị trí kêu gọi hành động / logo URL]
19. **Aspect Ratio**: [Tỷ lệ ảnh, ví dụ: --ar 16:9 hoặc --ar 4:5]
20. **Quality**: [Các từ khóa chất lượng cao]
21. **Style**: [Phong cách mỹ thuật: photography / 3d render / illustration...]
22. **Negative Prompt**: [Các yếu tố cần loại bỏ: distorted text, blurry, watermark gốc AI, messy layout, bad hands...]

---

### **PROMPT TẠO ẢNH HOÀN CHỈNH (COMPLETE IMAGE PROMPT)**
[Gộp tất cả 22 trường trên thành một prompt tiếng Anh hoàn chỉnh, mạch lạc, sẵn sàng paste vào Midjourney / Flux / DALL-E 3. PHẢI bao gồm chỉ dẫn typography text overlay tích hợp tự nhiên vào thiết kế ảnh. Trình bày trong thẻ codeblock.]
"""



