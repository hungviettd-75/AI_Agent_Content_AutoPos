import json
from datetime import date, datetime, timedelta
from config.config import CONTENT_MIX, AI_TOOLS, TARGETS, DIFFICULTIES, FORMATS, TOPIC_BANK, GOALS
from database.models.schedules import ScheduleModel
from database.models.posts import PostModel
from social.publishers import post_to_facebook, post_to_zalo_oa, post_to_linkedin

def _parse_start_date(start_date=None):
    if start_date is None:
        return date.today()
    if isinstance(start_date, date):
        return start_date
    return datetime.strptime(str(start_date), "%Y-%m-%d").date()

def _pick(items, index):
    return items[index % len(items)]

def generate_30_day_knowledge_plan(start_date=None):
    current_date = _parse_start_date(start_date)
    plan = []
    day_index = 0

    for category, count in CONTENT_MIX:
        for category_index in range(count):
            plan.append({
                "date": (current_date + timedelta(days=day_index)).isoformat(),
                "topic": _pick(TOPIC_BANK[category], category_index),
                "tool": _pick(AI_TOOLS, day_index),
                "target": _pick(TARGETS, day_index + category_index),
                "difficulty": _pick(DIFFICULTIES, category_index),
                "format": _pick(FORMATS, day_index + len(category)),
                "goal": GOALS[category],
            })
            day_index += 1

    return plan

def generate_30_day_knowledge_plan_json(start_date=None, ensure_ascii=False, indent=2):
    return json.dumps(
        generate_30_day_knowledge_plan(start_date),
        ensure_ascii=ensure_ascii,
        indent=indent,
    )

def execute_pending_schedules(workspace_id: int, fb_page_id=None, fb_access_token=None,
                              zalo_access_token=None, linkedin_author_urn=None, linkedin_access_token=None):
    """Quét và thực thi đăng các bài viết đã lên lịch đến hạn hoặc các bài đăng lỗi cần thử lại."""
    now_str = datetime.now().isoformat()
    pending = ScheduleModel.get_pending(workspace_id=workspace_id, before=now_str)
    
    # Lấy thêm danh sách bài lỗi để thử lại
    failed_list = ScheduleModel.list_by_workspace(workspace_id=workspace_id, status="failed")
    to_retry = [s for s in failed_list if s.get("retry_count", 0) < 3]
    
    # Gộp danh sách hàng chờ và hàng thử lại
    all_schedules = pending + to_retry
    
    results = []
    for sched in all_schedules:
        sched_id = sched["id"]
        post_id = sched["post_id"]
        sched_workspace_id = sched.get("workspace_id") or workspace_id
        platform = sched["platform"].lower()
        retry_count = sched.get("retry_count", 0)
        is_retry = sched.get("status") == "failed"
        
        # Cập nhật trạng thái đang xử lý
        ScheduleModel.update_status(sched_id, "processing", workspace_id=sched_workspace_id)
        
        post_data = PostModel.get_by_id(post_id, workspace_id=sched_workspace_id)
        content = post_data.get("content", "")
        
        success = False
        msg = "Chưa kết nối nền tảng"
        
        prefix = f"[Thử lại lần {retry_count+1}] " if is_retry else ""
        
        if platform == "facebook":
            success, msg = post_to_facebook(content, fb_page_id, fb_access_token)
        elif platform == "zalo":
            success, msg = post_to_zalo_oa(content, zalo_access_token)
        elif platform == "linkedin":
            success, msg = post_to_linkedin(content, linkedin_author_urn, linkedin_access_token)
        elif platform == "all":
            # Đăng lên cả 3
            fb_ok, fb_msg = post_to_facebook(content, fb_page_id, fb_access_token)
            zalo_ok, zalo_msg = post_to_zalo_oa(content, zalo_access_token)
            li_ok, li_msg = post_to_linkedin(content, linkedin_author_urn, linkedin_access_token)
            success = fb_ok or zalo_ok or li_ok
            msg = f"FB: {fb_msg} | Zalo: {zalo_msg} | LI: {li_msg}"
            
        if success:
            ScheduleModel.update_status(sched_id, "published", published_at=datetime.now().isoformat(), workspace_id=sched_workspace_id)
            PostModel.update_status(post_id, "published", workspace_id=sched_workspace_id)
            results.append({"id": sched_id, "status": "Thành công", "message": prefix + msg})
        else:
            # update_status sẽ tự tăng retry_count nếu status="failed"
            ScheduleModel.update_status(sched_id, "failed", error_message=prefix + msg, workspace_id=sched_workspace_id)
            results.append({"id": sched_id, "status": "Thất bại", "message": prefix + msg})
            
    return results


