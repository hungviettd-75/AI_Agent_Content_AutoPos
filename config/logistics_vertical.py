"""Reusable Logistics vertical presets for marketing/content workflows."""

LOGISTICS_TARGETS = [
    "CEO doanh nghiệp Logistics",
    "Supply Chain Manager",
    "Procurement Manager",
    "Operations Manager",
    "E-commerce Owner",
    "Chủ shop online",
    "Import-Export Manager",
    "Warehouse Manager",
]

LOGISTICS_ANGLES = [
    "Tối ưu chi phí vận chuyển",
    "Cam kết SLA giao hàng",
    "Giảm tỷ lệ giao thất bại",
    "Tối ưu tồn kho và kho bãi",
    "Case study tiết kiệm chi phí logistics",
    "So sánh tự vận hành và thuê 3PL",
    "Quy trình fulfillment cho thương mại điện tử",
    "Tự động hóa chăm sóc khách sau giao hàng",
    "Dashboard vận hành realtime",
    "Rủi ro mùa cao điểm",
]

LOGISTICS_CONTENT_MIX = [
    {"group": "Nỗi đau vận hành", "ratio": 25, "pillars": ["Chi phí vận chuyển", "SLA giao hàng", "Giao thất bại"]},
    {"group": "Kiến thức logistics thực chiến", "ratio": 25, "pillars": ["Fulfillment", "Kho bãi", "Tối ưu tuyến"]},
    {"group": "Case Study doanh nghiệp", "ratio": 20, "pillars": ["Case Study Logistics", "ROI Logistics"]},
    {"group": "Giải pháp và công nghệ", "ratio": 15, "pillars": ["Automation Logistics", "Dashboard vận hành"]},
    {"group": "Xu hướng thị trường", "ratio": 10, "pillars": ["E-commerce Logistics", "Cross-border"]},
    {"group": "Niềm tin thương hiệu", "ratio": 5, "pillars": ["Hậu trường vận hành", "Cam kết dịch vụ"]},
]

LOGISTICS_PILLAR_BANK = {
    "Chi phí vận chuyển": [
        "Vì sao chi phí giao hàng tăng nhưng doanh thu không tăng",
        "3 điểm rò rỉ chi phí trong vận chuyển nội địa",
        "Cách đọc lại bảng phí vận chuyển để tìm khoản lãng phí",
        "Khi nào nên gom đơn, khi nào nên tách tuyến",
        "Chi phí ẩn khi tự vận hành đội giao hàng",
    ],
    "SLA giao hàng": [
        "SLA giao hàng ảnh hưởng thế nào đến tỷ lệ mua lại",
        "Cam kết giao đúng hẹn cần dữ liệu gì",
        "Vì sao giao nhanh chưa chắc tạo lợi nhuận tốt",
        "Cách thiết kế SLA theo từng nhóm khách hàng",
        "Báo cáo SLA nào CEO nên xem mỗi tuần",
    ],
    "Giao thất bại": [
        "Tỷ lệ giao thất bại đang ăn mòn lợi nhuận ra sao",
        "5 nguyên nhân khiến đơn hàng giao không thành công",
        "Cách giảm hoàn hàng bằng xác nhận đơn thông minh",
        "Kịch bản chăm sóc khách trước khi giao hàng",
        "Dữ liệu nào dự báo nguy cơ giao thất bại",
    ],
    "Fulfillment": [
        "Fulfillment khác gì kho hàng truyền thống",
        "Khi nào shop online nên thuê fulfillment",
        "Quy trình fulfillment chuẩn cho đơn thương mại điện tử",
        "Sai lầm khi chọn đối tác fulfillment",
        "Fulfillment giúp tăng trải nghiệm khách hàng thế nào",
    ],
    "Kho bãi": [
        "Tối ưu tồn kho không bắt đầu từ phần mềm",
        "Vì sao kho bãi chậm làm marketing mất khách",
        "Cách phân loại SKU để giảm thời gian xử lý đơn",
        "Dấu hiệu kho hàng đang làm đội sales chậm lại",
        "Checklist đánh giá hiệu quả vận hành kho",
    ],
    "Tối ưu tuyến": [
        "Tối ưu tuyến giao hàng giúp tiết kiệm gì",
        "Vì sao tài xế giỏi vẫn cần dữ liệu tuyến",
        "Sai lầm khi chia tuyến theo kinh nghiệm",
        "Cách giảm km rỗng trong vận tải",
        "Tuyến giao hàng nào nên tự động hóa trước",
    ],
    "Case Study Logistics": [
        "Case study giảm 18% chi phí giao hàng trong 60 ngày",
        "Case study tăng tỷ lệ giao thành công cho shop online",
        "Case study rút ngắn thời gian xử lý đơn tại kho",
        "Case study cải thiện SLA mùa cao điểm",
        "Case study dùng dashboard để giảm khiếu nại khách hàng",
    ],
    "ROI Logistics": [
        "Bao lâu hoàn vốn khi thuê 3PL",
        "ROI của hệ thống theo dõi đơn realtime",
        "Thuê kho ngoài hay tự mở kho",
        "Chi phí thật của giao hàng chậm",
        "Cách tính CAC bị ảnh hưởng bởi logistics",
    ],
    "Automation Logistics": [
        "Tự động hóa thông báo trạng thái đơn hàng",
        "AI Agent chăm sóc khách sau giao hàng",
        "Tự động phân loại khiếu nại giao nhận",
        "Workflow xử lý đơn lỗi không cần nhập tay",
        "Tự động nhắc khách xác nhận lịch nhận hàng",
    ],
    "Dashboard vận hành": [
        "CEO logistics nên xem dashboard nào mỗi sáng",
        "5 chỉ số vận hành cần có trên dashboard realtime",
        "Dashboard giúp sales hứa đúng với khách hàng",
        "Khi dữ liệu giao hàng trở thành lợi thế bán hàng",
        "Báo cáo vận hành nào nên gửi khách B2B",
    ],
    "E-commerce Logistics": [
        "Logistics quyết định trải nghiệm mua lại của shop online",
        "Vì sao livestream bán tốt vẫn thua ở khâu giao hàng",
        "Mùa sale cần chuẩn bị fulfillment thế nào",
        "Chủ shop nên đo chỉ số logistics nào",
        "Từ đơn hàng đến khách trung thành: vai trò của giao nhận",
    ],
    "Cross-border": [
        "Cross-border logistics cần chuẩn bị gì trước khi mở rộng",
        "Rủi ro chứng từ khi bán xuyên biên giới",
        "Chi phí ẩn trong logistics quốc tế",
        "Làm sao truyền thông dịch vụ cross-border dễ hiểu hơn",
        "Khi nào doanh nghiệp nên dùng đối tác forwarding",
    ],
    "Hậu trường vận hành": [
        "Một ngày xử lý đơn trong kho logistics",
        "Điều khách hàng không thấy phía sau một đơn giao đúng hẹn",
        "Hậu trường mùa cao điểm logistics",
        "Cách đội vận hành xử lý đơn lỗi",
        "Vì sao logistics cần con người và dữ liệu cùng lúc",
    ],
    "Cam kết dịch vụ": [
        "Cam kết dịch vụ logistics nên nói bằng số liệu nào",
        "Cách xây dựng niềm tin khi khách chưa từng dùng dịch vụ",
        "Bảo chứng SLA trong truyền thông B2B",
        "Từ minh bạch trạng thái đơn đến lòng tin khách hàng",
        "Điều làm một đối tác logistics đáng tin",
    ],
}

LOGISTICS_COMPANY_SEED = {
    "industry": "Logistics / Fulfillment / Supply Chain",
    "description": "Doanh nghiệp cung cấp giải pháp logistics, vận tải, kho bãi, fulfillment, giao nhận và tối ưu chuỗi cung ứng cho khách hàng B2B và thương mại điện tử.",
    "products": "- Vận chuyển nội địa và last-mile delivery\n- Dịch vụ kho bãi và fulfillment\n- Giao nhận hàng hóa B2B/B2C\n- Theo dõi đơn hàng và báo cáo SLA\n- Tư vấn tối ưu chi phí logistics\n- Tự động hóa thông báo trạng thái đơn hàng",
    "target_customers": "CEO, chủ doanh nghiệp thương mại điện tử, Supply Chain Manager, Procurement Manager, Operations Manager, chủ shop online, doanh nghiệp cần giảm chi phí vận chuyển và tăng tỷ lệ giao thành công.",
    "marketing_strategy": "Kênh ưu tiên: LinkedIn cho B2B/CEO, Facebook cho nhận diện và case study, Zalo OA cho chăm sóc khách hàng và nhắc lịch giao nhận. Nội dung tập trung vào ROI, SLA, tối ưu chi phí, case study vận hành, fulfillment và dashboard realtime.",
    "sales_guideline": "Sales pitch: giúp khách giảm chi phí logistics, tăng tỷ lệ giao thành công, minh bạch SLA và giảm tải vận hành. Xử lý từ chối: nếu khách chê giá cao, so sánh tổng chi phí sở hữu gồm hoàn hàng, giao thất bại, thời gian xử lý và khiếu nại. FAQ: khu vực phục vụ, SLA, bảng giá, tích hợp hệ thống, quy trình xử lý đơn lỗi.",
}

LOGISTICS_BRAND_KEYWORDS = [
    "logistics", "fulfillment", "vận chuyển", "kho bãi", "SLA", "last-mile", "chuỗi cung ứng", "tối ưu chi phí", "giao hàng đúng hẹn", "dashboard vận hành",
]

LOGISTICS_DEFAULT_CTA = "Bạn muốn kiểm tra chi phí logistics hiện tại đang thất thoát ở đâu? Hãy để lại thông tin để được tư vấn quy trình tối ưu phù hợp."

LOGISTICS_SAMPLE_30 = [
    "Chi phí vận chuyển", "SLA giao hàng", "Case study Logistics", "Giao thất bại", "Fulfillment", "Kho bãi", "Tối ưu tuyến", "ROI Logistics", "Automation Logistics", "Dashboard vận hành", "E-commerce Logistics", "Cross-border", "Hậu trường vận hành", "Cam kết dịch vụ", "Last-mile delivery", "Tối ưu tồn kho", "Chăm sóc khách sau giao hàng", "Báo cáo SLA", "So sánh 3PL và tự vận hành", "Mùa cao điểm", "Quy trình xử lý đơn lỗi", "Dữ liệu tuyến giao", "Giảm hoàn hàng", "Niềm tin khách B2B", "Kho fulfillment", "Logistics cho shop online", "Forwarding", "Dashboard CEO", "KPI vận hành", "Dự đoán logistics",
]
