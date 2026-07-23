# --- AI TOOLS & META ---
AI_TOOLS = [
    "ChatGPT",
    "Claude",
    "Gemini",
    "Cursor",
    "Codex",
    "Windsurf",
    "n8n",
    "Make",
    "MCP",
    "Lovable",
    "Bolt",
]

CONTENT_TYPES = [
    "Marketing Viral",
    "AI Knowledge Sharing"
]

AI_AUDIENCES = ["Người mới", "Nhân viên", "CEO", "Developer", "AI Specialist"]
AI_DIFFICULTIES = ["Beginner", "Intermediate", "Advanced"]
AI_KNOWLEDGE_TYPES = [
    "Tutorial", "Tips", "Case Study", "Comparison", "Mistakes",
    "Best Practice", "Deep Dive"
]

# --- CONTENT PLANNER CONSTANTS ---
CONTENT_MIX = [
    ("AI Basics", 6),
    ("Prompt Engineering", 6),
    ("AI Tools", 6),
    ("Case Study", 5),
    ("Automation", 4),
    ("Future Trends", 3),
]

TARGETS = ["Người mới", "Nhân viên", "CEO", "Developer", "AI Specialist"]
DIFFICULTIES = ["Beginner", "Intermediate", "Advanced"]
FORMATS = ["Tutorial", "Tips", "Case Study", "Comparison", "Mistakes", "Best Practice", "Deep Dive", "Reels"]

TOPIC_BANK = {
    "AI Basics": [
        "AI là gì và dùng vào việc gì trong công việc hằng ngày?",
        "Phân biệt chatbot, AI agent và automation",
        "Cách đặt kỳ vọng đúng khi dùng AI",
        "Những việc nên và không nên giao cho AI",
        "Cách kiểm tra câu trả lời của AI trước khi dùng",
        "Quy trình dùng AI an toàn cho người mới",
    ],
    "Prompt Engineering": [
        "Công thức ROLE - TASK - CONTEXT - DATA - OUTPUT - CONSTRAINTS",
        "Cách viết prompt có bối cảnh để AI trả lời sát việc",
        "Prompt sửa lỗi nội dung và cải thiện chất lượng đầu ra",
        "Cách yêu cầu AI đưa ví dụ thực tế thay vì trả lời chung chung",
        "Prompt checklist để kiểm tra công việc trước khi gửi",
        "Các lỗi prompt phổ biến khiến kết quả AI kém chất lượng",
    ],
    "AI Tools": [
        "Khi nào nên dùng ChatGPT, Claude hay Gemini?",
        "Cursor và Codex khác gì khi hỗ trợ lập trình?",
        "Cách chọn AI tool theo mục tiêu công việc",
        "So sánh công cụ AI cho viết nội dung, phân tích và coding",
        "Ứng dụng MCP trong kết nối dữ liệu và công cụ",
        "Lovable, Bolt và cách tạo prototype nhanh",
    ],
    "Case Study": [
        "Case study dùng AI giảm thời gian xử lý báo cáo nội bộ",
        "Case study dùng AI hỗ trợ chăm sóc khách hàng",
        "Case study dùng AI để chuẩn hóa quy trình viết nội dung",
        "Case study dùng AI trong đào tạo nhân viên mới",
        "Case study triển khai AI nhỏ trước khi mở rộng toàn công ty",
    ],
    "Automation": [
        "Tự động hóa quy trình nhận form và tạo bản nháp nội dung",
        "Dùng n8n để nối Google Sheet, AI và email phê duyệt",
        "Dùng Make để tự động phân loại yêu cầu khách hàng",
        "Checklist trước khi tự động hóa một quy trình bằng AI",
    ],
    "Future Trends": [
        "AI agent sẽ thay đổi cách làm việc nhóm như thế nào?",
        "Xu hướng kết hợp AI với automation trong doanh nghiệp nhỏ",
        "Kỹ năng AI quan trọng nhất trong 12 tháng tới",
    ],
}

GOALS = {
    "AI Basics": "Giúp người đọc hiểu nền tảng AI và biết cách áp dụng an toàn.",
    "Prompt Engineering": "Giúp người đọc viết prompt rõ hơn và nhận đầu ra thực tế hơn.",
    "AI Tools": "Giúp người đọc chọn đúng công cụ AI theo nhu cầu công việc.",
    "Case Study": "Giúp người đọc học từ tình huống triển khai AI thực tế.",
    "Automation": "Giúp người đọc hiểu cách tự động hóa quy trình có kiểm soát.",
    "Future Trends": "Giúp người đọc chuẩn bị cho xu hướng AI sắp tới.",
}

# --- REELS CONSTANTS ---
DEFAULT_STYLE_RULES = [
    "Dễ hiểu, nói như hướng dẫn cho người mới.",
    "Tập trung giáo dục và kinh nghiệm thực chiến.",
    "Không quảng cáo, không bán hàng, không PR dịch vụ.",
    "Giữ retention cao bằng hook rõ, nhịp cảnh nhanh, ví dụ cụ thể.",
    "Phù hợp Facebook Reels/TikTok, thời lượng 30-60 giây.",
]

# --- CASE STUDY PROFILES ---
COMPANY_SIZE_PROFILES = {
    "small": {
        "label": "doanh nghiệp nhỏ",
        "employees": "10-50 nhân sự",
        "monthly_volume": "300-1.500 tác vụ/tháng",
        "implementation_weeks": "3-6 tuần",
        "roi_range": "120-220% sau 6 tháng",
    },
    "medium": {
        "label": "doanh nghiệp vừa",
        "employees": "50-250 nhân sự",
        "monthly_volume": "1.500-8.000 tác vụ/tháng",
        "implementation_weeks": "6-10 tuần",
        "roi_range": "150-280% sau 6-9 tháng",
    },
    "large": {
        "label": "doanh nghiệp lớn",
        "employees": "trên 250 nhân sự",
        "monthly_volume": "8.000-30.000 tác vụ/tháng",
        "implementation_weeks": "10-16 tuần",
        "roi_range": "180-320% sau 9-12 tháng",
    },
}

INDUSTRY_CONTEXT = {
    "retail": {
        "label": "bán lẻ",
        "workflow": "chăm sóc khách hàng, quản lý đơn, phản hồi inbox, tổng hợp phản hồi sản phẩm",
        "kpi": ["thời gian phản hồi", "tỷ lệ xử lý đúng yêu cầu", "chi phí chăm sóc mỗi đơn", "tỷ lệ khách quay lại"],
    },
    "education": {
        "label": "giáo dục",
        "workflow": "tư vấn tuyển sinh, nhắc lịch học, cá nhân hóa tài liệu, tổng hợp phản hồi học viên",
        "kpi": ["thời gian tư vấn", "tỷ lệ chuyển đổi lead", "tỷ lệ học viên hoàn thành", "mức hài lòng học viên"],
    },
    "finance": {
        "label": "tài chính",
        "workflow": "phân loại yêu cầu, tóm tắt hồ sơ, hỗ trợ kiểm tra thông tin, báo cáo vận hành",
        "kpi": ["thời gian xử lý hồ sơ", "tỷ lệ lỗi nhập liệu", "tỷ lệ SLA", "chi phí xử lý mỗi hồ sơ"],
    },
    "manufacturing": {
        "label": "sản xuất",
        "workflow": "báo cáo ca, kiểm tra checklist, tổng hợp lỗi sản xuất, dự báo nhu cầu vật tư",
        "kpi": ["thời gian tổng hợp báo cáo", "tỷ lệ lỗi lặp lại", "thời gian phản hồi sự cố", "mức tuân thủ checklist"],
    },
    "service": {
        "label": "dịch vụ",
        "workflow": "tiếp nhận yêu cầu, phân loại ticket, soạn phản hồi, tổng hợp báo cáo chất lượng dịch vụ",
        "kpi": ["thời gian phản hồi đầu tiên", "tỷ lệ ticket xử lý trong ngày", "CSAT", "chi phí vận hành"],
    },
}

# --- COMPARISON DATA ---
CRITERIA = [
    "chất lượng",
    "tốc độ",
    "giá",
    "coding",
    "reasoning",
    "automation",
    "image",
    "video",
    "business",
]

COMPARISON_DATA = {
    "ChatGPT": {
        "chất lượng": "Rất cao, đa dụng",
        "tốc độ": "Nhanh",
        "giá": "Trung bình",
        "coding": "Tốt",
        "reasoning": "Rất tốt",
        "automation": "Tốt khi kết hợp API/GPTs",
        "image": "Mạnh",
        "video": "Hạn chế/tùy gói",
        "business": "Rất mạnh cho nội dung, phân tích, vận hành",
    },
    "Claude": {
        "chất lượng": "Rất cao, văn phong tự nhiên",
        "tốc độ": "Nhanh",
        "giá": "Trung bình",
        "coding": "Tốt",
        "reasoning": "Rất mạnh với tài liệu dài",
        "automation": "Khá, cần tích hợp ngoài",
        "image": "Hạn chế",
        "video": "Hạn chế",
        "business": "Mạnh cho phân tích, viết, policy, tài liệu",
    },
    "Gemini": {
        "chất lượng": "Cao, mạnh hệ sinh thái Google",
        "tốc độ": "Nhanh",
        "giá": "Cạnh tranh",
        "coding": "Khá tốt",
        "reasoning": "Tốt",
        "automation": "Tốt với Google Workspace/API",
        "image": "Tốt",
        "video": "Tốt hơn nhiều công cụ chat",
        "business": "Mạnh nếu doanh nghiệp dùng Google",
    },
    "Cursor": {
        "chất lượng": "Rất cao cho lập trình",
        "tốc độ": "Nhanh trong IDE",
        "giá": "Trung bình",
        "coding": "Rất mạnh",
        "reasoning": "Tốt theo ngữ cảnh codebase",
        "automation": "Hạn chế, chủ yếu trong dev workflow",
        "image": "Không phù hợp",
        "video": "Không phù hợp",
        "business": "Mạnh cho đội kỹ thuật",
    },
    "Codex": {
        "chất lượng": "Rất cao cho tác vụ coding có ngữ cảnh",
        "tốc độ": "Tốt, tùy độ lớn repo",
        "giá": "Tùy nền tảng sử dụng",
        "coding": "Rất mạnh",
        "reasoning": "Rất tốt cho chỉnh sửa, kiểm tra, giải thích code",
        "automation": "Tốt cho workflow kỹ thuật trong workspace",
        "image": "Không phải trọng tâm",
        "video": "Không phù hợp",
        "business": "Mạnh cho sản phẩm, internal tools, bảo trì hệ thống",
    },
    "Windsurf": {
        "chất lượng": "Cao cho lập trình AI-assisted",
        "tốc độ": "Nhanh",
        "giá": "Trung bình",
        "coding": "Rất mạnh",
        "reasoning": "Tốt theo project context",
        "automation": "Khá trong dev workflow",
        "image": "Không phù hợp",
        "video": "Không phù hợp",
        "business": "Mạnh cho đội dev cần tăng tốc build",
    },
    "Lovable": {
        "chất lượng": "Tốt cho prototype app",
        "tốc độ": "Rất nhanh",
        "giá": "Trung bình",
        "coding": "Khá, thiên về no-code/low-code",
        "reasoning": "Khá",
        "automation": "Khá khi nối với backend/API",
        "image": "Hạn chế",
        "video": "Không phù hợp",
        "business": "Mạnh cho MVP, landing app, demo ý tưởng",
    },
    "Bolt": {
        "chất lượng": "Tốt cho web app nhanh",
        "tốc độ": "Rất nhanh",
        "giá": "Trung bình",
        "coding": "Tốt cho frontend/full-stack prototype",
        "reasoning": "Khá",
        "automation": "Hạn chế ngoài phạm vi app",
        "image": "Hạn chế",
        "video": "Không phù hợp",
        "business": "Mạnh cho thử nghiệm sản phẩm nhanh",
    },
    "n8n": {
        "chất lượng": "Rất cao cho automation linh hoạt",
        "tốc độ": "Nhanh sau khi setup",
        "giá": "Tốt nếu self-host",
        "coding": "Khá, hỗ trợ code node",
        "reasoning": "Phụ thuộc AI node tích hợp",
        "automation": "Rất mạnh",
        "image": "Qua tích hợp API",
        "video": "Qua tích hợp API",
        "business": "Rất mạnh cho vận hành, CRM, content workflow",
    },
    "Make": {
        "chất lượng": "Cao cho automation trực quan",
        "tốc độ": "Nhanh khi dùng template",
        "giá": "Cạnh tranh, tăng theo operations",
        "coding": "Hạn chế hơn n8n",
        "reasoning": "Phụ thuộc AI module/API",
        "automation": "Rất mạnh",
        "image": "Qua tích hợp API",
        "video": "Qua tích hợp API",
        "business": "Rất mạnh cho phòng ban không chuyên kỹ thuật",
    },
}
