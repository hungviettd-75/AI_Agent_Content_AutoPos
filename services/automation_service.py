"""
services/automation_service.py
==============================
Service thực hiện kết nối và đẩy nội dung, thông báo hoặc dữ liệu
tới các nền tảng bên ngoài (CRM, Email, WordPress, Google Drive, Notion, Slack, Webhook).
"""
import requests
import json
from config.config import logger

class AutomationService:

    # 1. SLACK INTEGRATION
    @staticmethod
    def send_to_slack(webhook_url: str, text: str, title: str = "AI Agent Notification") -> bool:
        """Gửi thông báo hoặc nội dung bài viết đến kênh Slack qua Webhook."""
        if not webhook_url:
            logger.warning("[AUTOMATION] Thiếu Slack Webhook URL")
            return False
        
        payload = {
            "text": f"*{title}*\n{text}"
        }
        try:
            res = requests.post(webhook_url, json=payload, timeout=10)
            if res.status_code == 200:
                logger.info("[AUTOMATION] Đã gửi thông báo tới Slack thành công.")
                return True
            logger.error(f"[AUTOMATION] Lỗi gửi Slack: {res.status_code} - {res.text}")
            return False
        except Exception as e:
            logger.error(f"[AUTOMATION] Ngoại lệ gửi Slack: {e}")
            return False

    # 2. EMAIL INTEGRATION (Mocked SMTP/API)
    @staticmethod
    def send_email(api_key: str, to_email: str, subject: str, body: str, provider: str = "SendGrid") -> bool:
        """Gửi email bản tin hoặc bài viết nháp tới Client/Subscriber."""
        if not to_email or not api_key:
            logger.warning("[AUTOMATION] Thiếu thông tin Email nhận hoặc API Key.")
            return False
        
        logger.info(f"[AUTOMATION] Gửi email qua {provider} tới: {to_email} với chủ đề: {subject}")
        # Giả lập call API SendGrid/Mailgun hoặc SMTP
        # Trong thực tế, bạn sẽ dùng thư viện email hoặc request tới endpoint
        return True

    # 3. WORDPRESS PUBLISHING
    @staticmethod
    def publish_to_wordpress(wp_url: str, username: str, application_pass: str, title: str, content: str, status: str = "draft") -> dict:
        """Đăng tải bài viết trực tiếp lên WordPress qua REST API."""
        if not wp_url or not username or not application_pass:
            logger.warning("[AUTOMATION] Thiếu cấu hình kết nối WordPress.")
            return {"success": False, "message": "Thiếu thông tin đăng nhập WordPress"}

        # Đảm bảo đường dẫn API chuẩn xác
        api_url = wp_url.rstrip("/") + "/wp-json/wp/v2/posts"
        import base64
        credentials = f"{username}:{application_pass}"
        token = base64.b64encode(credentials.encode()).decode("utf-8")
        
        headers = {
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json"
        }
        payload = {
            "title": title,
            "content": content,
            "status": status  # draft hoặc publish
        }

        try:
            # Mock để chạy demo mượt mà nếu wp_url là giả lập, thực tế sẽ gọi post thật
            if "localhost" not in wp_url and "http" not in wp_url:
                logger.info(f"[AUTOMATION] WordPress Mock Publish: {title}")
                return {"success": True, "message": "Đăng bài WordPress thử nghiệm thành công (Mock Mode)", "id": 999}

            res = requests.post(api_url, json=payload, headers=headers, timeout=15)
            if res.status_code in [200, 201]:
                data = res.json()
                logger.info(f"[AUTOMATION] WordPress đăng bài thành công. ID: {data.get('id')}")
                return {"success": True, "message": "Đã đăng bài viết lên WordPress thành công", "id": data.get("id")}
            return {"success": False, "message": f"WordPress API Error: {res.status_code} - {res.text}"}
        except Exception as e:
            logger.error(f"[AUTOMATION] Lỗi kết nối WordPress: {e}")
            return {"success": False, "message": str(e)}

    # 4. NOTION INTEGRATION
    @staticmethod
    def create_notion_page(token: str, database_id: str, title: str, content: str, properties: dict = None) -> bool:
        """Đẩy bài viết nháp vào Database của Notion làm Content Calendar."""
        if not token or not database_id:
            logger.warning("[AUTOMATION] Thiếu Notion API Token hoặc Database ID.")
            return False

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
        payload = {
            "parent": {"database_id": database_id},
            "properties": {
                "Title": {
                    "title": [
                        {"text": {"content": title}}
                    ]
                }
            },
            "children": [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": content[:2000]}}]
                    }
                }
            ]
        }
        
        try:
            # Mock if not real DSN
            if len(token) < 10 or len(database_id) < 10:
                logger.info(f"[AUTOMATION] Notion Page Mock Created: {title}")
                return True
                
            res = requests.post("https://api.notion.com/v1/pages", json=payload, headers=headers, timeout=12)
            return res.status_code == 200
        except Exception as e:
            logger.error(f"[AUTOMATION] Lỗi Notion: {e}")
            return False

    # 5. GOOGLE DRIVE UPLOAD (Mocked)
    @staticmethod
    def upload_to_drive(api_key_or_token: str, file_name: str, content: str, folder_id: str = "") -> bool:
        """Upload bài viết dạng tài liệu txt/docx lưu trữ lên Google Drive."""
        logger.info(f"[AUTOMATION] Lưu trữ tài liệu lên Google Drive: {file_name}")
        return True

    # 6. CRM INTEGRATION (HubSpot/Salesforce Mock API)
    @staticmethod
    def sync_lead_to_crm(api_key: str, lead_data: dict, provider: str = "HubSpot") -> bool:
        """Đồng bộ thông tin khách hàng tiềm năng (Leads) thu được từ chiến dịch sang CRM."""
        logger.info(f"[AUTOMATION] Đang đồng bộ lead sang {provider}: {lead_data.get('email')}")
        return True

    # 7. CUSTOM WEBHOOKS
    @staticmethod
    def trigger_webhook(webhook_url: str, payload: dict) -> bool:
        """Bắn dữ liệu JSON bài viết/leads ra webhook ngoại vi để tích hợp với Make/Zapier."""
        if not webhook_url:
            logger.warning("[AUTOMATION] Thiếu Webhook URL")
            return False
        try:
            res = requests.post(webhook_url, json=payload, timeout=10)
            return res.status_code in [200, 201, 202]
        except Exception as e:
            logger.error(f"[AUTOMATION] Lỗi Webhook: {e}")
            return False
