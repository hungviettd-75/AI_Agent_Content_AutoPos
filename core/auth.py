import base64
import json
import hmac
import hashlib
import time
from config.settings import SECRET_KEY

# Sử dụng SECRET_KEY mặc định nếu không được định nghĩa hoặc trống
JWT_SECRET = SECRET_KEY or "super-secret-key-for-ai-agent-marketing"

def _base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')

def _base64url_decode(data: str) -> bytes:
    padding = '=' * (4 - len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)

def encode_jwt(payload: dict, expires_in: int = 86400) -> str:
    """Tạo JWT token tự xây dựng sử dụng HS256."""
    header = {"alg": "HS256", "typ": "JWT"}
    
    # Thiết lập thời gian hết hạn
    payload_copy = payload.copy()
    payload_copy["exp"] = int(time.time()) + expires_in
    
    header_b64 = _base64url_encode(json.dumps(header, separators=(',', ':')).encode('utf-8'))
    payload_b64 = _base64url_encode(json.dumps(payload_copy, separators=(',', ':')).encode('utf-8'))
    
    signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')
    signature = hmac.new(JWT_SECRET.encode('utf-8'), signing_input, hashlib.sha256).digest()
    signature_b64 = _base64url_encode(signature)
    
    return f"{header_b64}.{payload_b64}.{signature_b64}"

def decode_jwt(token: str) -> dict:
    """Xác minh và giải mã JWT token. Trả về payload nếu hợp lệ, nếu không trả về None."""
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
            
        header_b64, payload_b64, signature_b64 = parts
        
        # Xác minh chữ ký
        signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')
        expected_signature = hmac.new(JWT_SECRET.encode('utf-8'), signing_input, hashlib.sha256).digest()
        expected_signature_b64 = _base64url_encode(expected_signature)
        
        if not hmac.compare_digest(signature_b64, expected_signature_b64):
            return None
            
        # Giải mã payload
        payload = json.loads(_base64url_decode(payload_b64).decode('utf-8'))
        
        # Kiểm tra thời gian hết hạn
        if payload.get("exp", 0) < time.time():
            return None
            
        return payload
    except Exception:
        return None
