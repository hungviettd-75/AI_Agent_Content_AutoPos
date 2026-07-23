from config.config import COMPANY_SIZE_PROFILES, INDUSTRY_CONTEXT

def _normalize_key(value):
    return str(value or "").strip().lower().replace(" ", "_")

def _get_company_profile(company_size):
    key = _normalize_key(company_size)
    aliases = {
        "nhỏ": "small",
        "nho": "small",
        "small": "small",
        "sme": "small",
        "vừa": "medium",
        "vua": "medium",
        "medium": "medium",
        "mid": "medium",
        "lớn": "large",
        "lon": "large",
        "large": "large",
    }
    return COMPANY_SIZE_PROFILES.get(aliases.get(key, key), {
        "label": str(company_size).strip() or "doanh nghiệp",
        "employees": "30-150 nhân sự",
        "monthly_volume": "1.000-5.000 tác vụ/tháng",
        "implementation_weeks": "6-10 tuần",
        "roi_range": "130-240% sau 6-9 tháng",
    })

def _get_industry_profile(industry):
    key = _normalize_key(industry)
    aliases = {
        "ban_le": "retail",
        "bán_lẻ": "retail",
        "giao_duc": "education",
        "giáo_dục": "education",
        "tai_chinh": "finance",
        "tài_chính": "finance",
        "san_xuat": "manufacturing",
        "sản_xuất": "manufacturing",
        "dich_vu": "service",
        "dịch_vụ": "service",
    }
    return INDUSTRY_CONTEXT.get(aliases.get(key, key), {
        "label": str(industry).strip() or "doanh nghiệp Việt Nam",
        "workflow": "tiếp nhận yêu cầu, xử lý dữ liệu, soạn nội dung, tổng hợp báo cáo",
        "kpi": ["thời gian xử lý", "tỷ lệ lỗi", "chi phí vận hành", "mức hài lòng nội bộ"],
    })

def generate_ai_case_study(industry, company_size, problem, ai_tool):
    industry_profile = _get_industry_profile(industry)
    company_profile = _get_company_profile(company_size)
    problem_text = str(problem).strip() or "quy trình thủ công tốn thời gian và khó kiểm soát chất lượng"
    tool_name = str(ai_tool).strip() or "AI tool"

    return f"""# Case Study AI: {tool_name} trong ngành {industry_profile['label']}

## 1. Tình trạng trước
Một {company_profile['label']} tại Việt Nam, quy mô khoảng {company_profile['employees']}, đang xử lý khoảng {company_profile['monthly_volume']} liên quan đến {industry_profile['workflow']}.

Vấn đề chính: {problem_text}.

Các dấu hiệu trước triển khai:
- Nhiều thao tác lặp lại vẫn làm thủ công trên file, chat nội bộ hoặc email.
- Thời gian phản hồi không ổn định, đặc biệt vào giờ cao điểm.
- Dữ liệu rải rác, khó tổng hợp thành báo cáo quản trị.
- Chất lượng đầu ra phụ thuộc nhiều vào kinh nghiệm từng nhân sự.

## 2. Giải pháp AI
Doanh nghiệp triển khai {tool_name} để hỗ trợ các bước có tính lặp lại và cần xử lý ngôn ngữ/dữ liệu.

Phạm vi hợp lý trong giai đoạn đầu:
- Chuẩn hóa đầu vào trước khi xử lý.
- Gợi ý nội dung phản hồi hoặc phương án xử lý.
- Tóm tắt dữ liệu và phân loại mức độ ưu tiên.
- Tạo báo cáo ngắn cho quản lý theo ngày/tuần.

Lưu ý: AI không thay thế hoàn toàn nhân sự. Các quyết định quan trọng vẫn cần người phụ trách kiểm tra.

## 3. Quy trình triển khai
1. Khảo sát quy trình hiện tại và chọn 1-2 điểm nghẽn có dữ liệu rõ ràng.
2. Chuẩn hóa biểu mẫu đầu vào, tiêu chí phân loại và mẫu đầu ra.
3. Thiết kế prompt/workflow cho {tool_name} theo từng tình huống sử dụng.
4. Chạy thử với dữ liệu cũ trong 1-2 tuần để so sánh kết quả.
5. Đào tạo nhóm vận hành cách kiểm tra, sửa lỗi và phản hồi lại cho hệ thống.
6. Đo KPI hằng tuần, chỉ mở rộng khi kết quả ổn định.

## 4. Thời gian
Thời gian triển khai phù hợp: {company_profile['implementation_weeks']}.

Phân bổ tham khảo:
- Tuần 1-2: khảo sát, chọn use case, làm sạch dữ liệu mẫu.
- Tuần 3-4: xây prompt/workflow, chạy thử nội bộ.
- Tuần 5-8: áp dụng có kiểm soát, đo KPI, tinh chỉnh.
- Sau giai đoạn thử nghiệm: mở rộng sang nhóm hoặc quy trình liên quan.

## 5. ROI
ROI kỳ vọng hợp lý: {company_profile['roi_range']} nếu quy trình có đủ tần suất sử dụng và đội ngũ thật sự áp dụng.

Nguồn tạo ROI thường đến từ:
- Giảm 20-35% thời gian cho các tác vụ lặp lại.
- Giảm 10-25% lỗi do nhập liệu, bỏ sót thông tin hoặc phản hồi thiếu nhất quán.
- Tăng năng suất nhóm vận hành khoảng 15-30% trong các việc có quy trình rõ.

Không nên kỳ vọng ROI cao nếu dữ liệu đầu vào lộn xộn, quy trình chưa thống nhất hoặc thiếu người chịu trách nhiệm kiểm tra.

## 6. KPI
Các KPI nên theo dõi:
- {industry_profile['kpi'][0]}: mục tiêu cải thiện 20-35%.
- {industry_profile['kpi'][1]}: mục tiêu cải thiện 10-25%.
- {industry_profile['kpi'][2]}: mục tiêu cải thiện 10-20%.
- {industry_profile['kpi'][3]}: mục tiêu cải thiện 5-15%.

KPI bổ sung:
- Tỷ lệ đầu ra AI cần sửa nhiều: nên dưới 20-30% sau giai đoạn tinh chỉnh.
- Tỷ lệ nhân sự sử dụng đều hằng tuần: nên trên 70% với nhóm tham gia thử nghiệm.
- Số giờ tiết kiệm mỗi tuần: nên đo bằng log thao tác hoặc khảo sát nội bộ.

## 7. Bài học kinh nghiệm
- Bắt đầu từ một quy trình nhỏ nhưng lặp lại nhiều lần sẽ dễ có kết quả hơn làm quá rộng.
- Prompt tốt chưa đủ; cần dữ liệu đầu vào sạch và tiêu chí đánh giá rõ.
- Nên có người kiểm duyệt trong giai đoạn đầu để tránh sai lệch nghiệp vụ.
- Doanh nghiệp Việt Nam nên ưu tiên use case tiết kiệm thời gian, giảm lỗi và tăng tốc báo cáo trước khi nghĩ đến tự động hóa phức tạp.
- Hiệu quả bền vững đến từ việc biến AI thành một bước trong quy trình, không phải một công cụ dùng tùy hứng.
"""
