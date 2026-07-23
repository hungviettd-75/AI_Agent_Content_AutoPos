import requests
from config import settings
from config.config import logger

def post_to_facebook(message, page_id=None, access_token=None):
    pid = page_id or settings.FB_PAGE_ID
    token = access_token or settings.FB_ACCESS_TOKEN
    
    logger.info(f"[AUDIT] Thực hiện đăng bài viết lên Facebook Page ID: {pid}")
    if not pid or not token:
        logger.warning("Thất bại khi đăng bài Facebook: Thiếu thông tin Page ID hoặc Access Token.")
        return False, "Thiếu thông tin Facebook API."

    url = f"https://graph.facebook.com/{pid}/feed"
    payload = {'message': message, 'access_token': token}
    try:
        response = requests.post(url, data=payload)
        res_data = response.json()
        if "id" in res_data:
            logger.info(f"Đăng bài lên Facebook thành công! Post ID: {res_data['id']}")
            return True, f"Đã đăng lên Facebook! ID: {res_data['id']}"
        logger.error(f"Lỗi phản hồi từ Facebook API: {res_data.get('error', {}).get('message')}")
        return False, f"Lỗi FB: {res_data.get('error', {}).get('message')}"
    except Exception as e:
        logger.error(f"Lỗi kết nối khi đăng bài Facebook: {e}", exc_info=True)
        return False, str(e)

def post_to_zalo_oa(message, access_token=None):
    token = access_token or settings.ZALO_ACCESS_TOKEN
    
    logger.info("[AUDIT] Thực hiện đăng tin nhắn Broadcast lên Zalo OA.")
    if not token:
        logger.warning("Thất bại khi gửi tin nhắn Zalo OA: Thiếu Access Token.")
        return False, "Thiếu Zalo Access Token."

    url = "https://openapi.zalo.me/v2.0/oa/message"
    headers = {"access_token": token, "Content-Type": "application/json"}
    payload = {
        "recipient": {"target": "all"},
        "message": {"text": message}
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        res_data = response.json()
        if res_data.get("error") == 0:
            logger.info("Gửi tin nhắn Zalo OA thành công!")
            return True, "Đã gửi tin nhắn Broadcast Zalo thành công!"
        logger.error(f"Lỗi phản hồi từ Zalo OA API: {res_data.get('message')}")
        return False, f"Lỗi Zalo: {res_data.get('message')}"
    except Exception as e:
        logger.error(f"Lỗi kết nối khi gửi tin nhắn Zalo OA: {e}", exc_info=True)
        return False, str(e)

def post_to_linkedin(message, author_urn=None, access_token=None):
    urn = author_urn or settings.LINKEDIN_AUTHOR_URN
    token = access_token or settings.LINKEDIN_ACCESS_TOKEN
    
    logger.info(f"[AUDIT] Thực hiện đăng bài viết lên LinkedIn Author URN: {urn}")
    if not urn or not token:
        logger.warning("Thất bại khi đăng bài LinkedIn: Thiếu thông tin Author URN hoặc Access Token.")
        return False, "Thiếu thông tin LinkedIn API."

    url = "https://api.linkedin.com/v2/ugcPosts"
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json"
    }
    payload = {
        "author": urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": message},
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 201:
            res_data = response.json()
            logger.info(f"Đăng bài lên LinkedIn thành công! Post ID: {res_data.get('id')}")
            return True, f"Đã đăng lên LinkedIn! ID: {res_data.get('id')}"
        logger.error(f"Lỗi phản hồi từ LinkedIn API: {response.text}")
        return False, f"Lỗi LinkedIn: {response.text}"
    except Exception as e:
        logger.error(f"Lỗi kết nối khi đăng bài LinkedIn: {e}", exc_info=True)
        return False, str(e)
