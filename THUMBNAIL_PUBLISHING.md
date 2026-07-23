# 🖼️📢 THUMBNAIL PUBLISHING — Thiết Kế Tích Hợp Thumbnail vào Publishing

> **Dự án**: AI_Agent_Content_AutoPos  
> **Phạm vi**: Tích hợp Thumbnail vào pipeline Publishing (Facebook · LinkedIn · Zalo OA)  
> **Ràng buộc**: Không thay đổi API (`social/publishers.py`), Không thay đổi Database  
> **Ngày tạo**: 2026-07-12  
> **Phiên bản**: 1.0

---

## 📌 1. Tổng Quan

### 1.1 Vấn đề hiện tại

`social/publishers.py` hiện chỉ gửi **text** lên mạng xã hội:

```python
# HIỆN TẠI — chỉ gửi message text
post_to_facebook(message, page_id, access_token)
post_to_zalo_oa(message, access_token)
post_to_linkedin(message, author_urn, access_token)
```

`tab_publishing.py` không có bất kỳ xử lý nào cho **thumbnail**:
- Không kiểm tra thumbnail trước khi publish
- Không crop / resize theo từng nền tảng
- Không preview trước khi đăng
- Không có safe zone guidance
- Không liên kết approval thumbnail với approval bài viết

### 1.2 Mục tiêu thiết kế

| Tính năng | Mô tả |
|-----------|-------|
| **Aspect Ratio** | Chuẩn kích thước thumbnail riêng cho mỗi platform |
| **Crop / Resize** | Tự động crop/resize ảnh về đúng kích thước platform |
| **Preview** | Hiển thị thumbnail preview trước khi publish |
| **Safe Zone** | Vùng an toàn — tránh text/logo bị cắt do UI platform |
| **Thumbnail Preview** | Mô phỏng card bài đăng thực tế trên mỗi platform |
| **Publish Queue** | Hàng chờ bao gồm trạng thái thumbnail |
| **Approval** | Duyệt thumbnail (độc lập hoặc kết hợp với bài viết) |
| **Retry** | Retry đăng kèm thumbnail khi thất bại |

### 1.3 Nguyên tắc

- ✅ **Không sửa `social/publishers.py`** — Tạo wrapper layer mới
- ✅ **Không sửa database schema** — Dùng cột `tags` (JSON) của `assets`
- ✅ Tương thích với hệ thống Approval và Schedule hiện có
- ✅ Pillow (PIL) cho xử lý ảnh — thư viện đã phổ biến trong Python

---

## 📐 2. Thông Số Kỹ Thuật Từng Nền Tảng

### 2.1 Facebook

```
┌───────────────────────────────────────────────────────────────┐
│  FACEBOOK THUMBNAIL SPECIFICATIONS                            │
├─────────────────────┬─────────────────────────────────────────┤
│ Post Image          │ 1200 × 630 px  (Ratio 1.91:1)          │
│ Link Preview Image  │ 1200 × 628 px  (Ratio ~1.91:1)         │
│ Story Image         │ 1080 × 1920 px (Ratio 9:16)            │
│ Profile/Ad Square   │ 1080 × 1080 px (Ratio 1:1)             │
├─────────────────────┼─────────────────────────────────────────┤
│ Format              │ JPG, PNG (< 4 MB)                       │
│ Min Resolution      │ 600 × 315 px                            │
├─────────────────────┼─────────────────────────────────────────┤
│ SAFE ZONE (Post)    │ Margin 60px top/bottom, 80px left/right │
│                     │ → Safe area: 1040 × 510 px              │
│ Text Overlay Limit  │ < 20% diện tích ảnh (Facebook policy)  │
└─────────────────────┴─────────────────────────────────────────┘
```

**Safe Zone diagram (Facebook Post 1200×630):**

```
┌─────────────────────────────────────────────────────────────────┐ ← 0px
│                    UNSAFE ZONE (60px)                           │
│  ┌───────────────────────────────────────────────────────────┐  │ ← 60px
│  │                                                           │  │
│  │                    SAFE ZONE                              │  │
│  │                  1040 × 510 px                            │  │
│  │              (đặt text, logo ở đây)                       │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │ ← 570px
│    ← 80px →                                         ← 80px →    │
│                    UNSAFE ZONE (60px)                           │
└─────────────────────────────────────────────────────────────────┘ ← 630px
```

### 2.2 LinkedIn

```
┌───────────────────────────────────────────────────────────────┐
│  LINKEDIN THUMBNAIL SPECIFICATIONS                            │
├─────────────────────┬─────────────────────────────────────────┤
│ Post with Image     │ 1200 × 627 px  (Ratio ~1.91:1)         │
│ Article Header      │ 1920 × 1080 px (Ratio 16:9)            │
│ Profile Banner      │ 1584 × 396  px (Ratio 4:1)             │
│ Square Post         │ 1080 × 1080 px (Ratio 1:1)             │
├─────────────────────┼─────────────────────────────────────────┤
│ Format              │ JPG, PNG, GIF (< 5 MB)                  │
│ Min Resolution      │ 552 × 289 px                            │
├─────────────────────┼─────────────────────────────────────────┤
│ SAFE ZONE (Post)    │ Margin 50px all sides                   │
│                     │ → Safe area: 1100 × 527 px              │
│ Mobile crop        │ LinkedIn crops bottom ~100px on mobile   │
└─────────────────────┴─────────────────────────────────────────┘
```

**Safe Zone diagram (LinkedIn Post 1200×627):**

```
┌─────────────────────────────────────────────────────────────────┐ ← 0px
│                    UNSAFE ZONE (50px)                           │
│  ┌───────────────────────────────────────────────────────────┐  │ ← 50px
│  │                                                           │  │
│  │                    SAFE ZONE                              │  │
│  │                  1100 × 527 px                            │  │
│  │                                                           │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │ ← 577px
│    ← 50px →                                         ← 50px →    │
│             UNSAFE / MOBILE CROP ZONE (50px)                    │ ← 627px
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 Zalo OA

```
┌───────────────────────────────────────────────────────────────┐
│  ZALO OA THUMBNAIL SPECIFICATIONS                             │
├─────────────────────┬─────────────────────────────────────────┤
│ Broadcast Image     │ 1040 × 585 px  (Ratio 16:9)            │
│ Article Thumbnail   │ 600  × 400 px  (Ratio 3:2)             │
│ Story Image         │ 1080 × 1920 px (Ratio 9:16)            │
│ Sticker/Inline      │ 512  × 512 px  (Ratio 1:1)             │
├─────────────────────┼─────────────────────────────────────────┤
│ Format              │ JPG, PNG (< 1 MB broadcast, < 3 MB OA) │
│ Min Resolution      │ 800 × 450 px                            │
├─────────────────────┼─────────────────────────────────────────┤
│ SAFE ZONE (Broad.)  │ Margin 40px top/bottom, 60px left/right │
│                     │ → Safe area: 920 × 505 px               │
│ Note                │ Zalo chat bubble crops ~20px trên mobile│
└─────────────────────┴─────────────────────────────────────────┘
```

**Safe Zone diagram (Zalo OA Broadcast 1040×585):**

```
┌─────────────────────────────────────────────────────────────────┐ ← 0px
│                    UNSAFE ZONE (40px)                           │
│  ┌───────────────────────────────────────────────────────────┐  │ ← 40px
│  │                                                           │  │
│  │                    SAFE ZONE                              │  │
│  │                   920 × 505 px                            │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │ ← 545px
│    ← 60px →                                         ← 60px →    │
│                    UNSAFE ZONE (40px)                           │
└─────────────────────────────────────────────────────────────────┘ ← 585px
```

### 2.4 Bảng So Sánh Tổng Hợp

| Platform | Post Image | Ratio | Max Size | Safe Zone |
|----------|-----------|-------|----------|-----------|
| **Facebook** | 1200 × 630 | 1.91:1 | 4 MB | 60/80px margin |
| **Facebook Story** | 1080 × 1920 | 9:16 | 4 MB | 120/80px margin |
| **LinkedIn Post** | 1200 × 627 | ~1.91:1 | 5 MB | 50px all sides |
| **LinkedIn Article** | 1920 × 1080 | 16:9 | 5 MB | 80px all sides |
| **Zalo OA Broadcast** | 1040 × 585 | 16:9 | 1 MB | 40/60px margin |
| **Zalo OA Article** | 600 × 400 | 3:2 | 3 MB | 30px all sides |

---

## 🏗️ 3. Kiến Trúc Tổng Thể

```
┌──────────────────────────────────────────────────────────────────────┐
│                   THUMBNAIL PUBLISHING PIPELINE                      │
│                                                                      │
│  UI Layer (tab_publishing.py mở rộng)                                │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  [1] Chọn bài viết  →  [2] Gắn Thumbnail  →  [3] Preview    │    │
│  │  [4] Approval Check →  [5] Platform Format →  [6] Publish   │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                           │                                          │
│  Service Layer (MỚI)      ▼                                          │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │        services/thumbnail_publishing_service.py              │    │
│  │                                                              │    │
│  │  ThumbnailSpec   │  ThumbnailProcessor  │  PublishQueue      │    │
│  │  PreviewRenderer │  ApprovalGate        │  RetryManager      │    │
│  └─────────────────────────────┬────────────────────────────────┘    │
│                                │                                     │
│  ┌─────────────────────────────┴────────────────────────────────┐    │
│  │              KHÔNG THAY ĐỔI (Existing)                       │    │
│  │                                                              │    │
│  │  social/publishers.py    database/models/assets.py           │    │
│  │  database/models/schedules.py  database/models/approvals.py  │    │
│  └──────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 🔧 4. Service Layer: `services/thumbnail_publishing_service.py`

```python
"""
services/thumbnail_publishing_service.py
=========================================
Thumbnail Publishing Service — Xử lý thumbnail trước khi publish.

Nguyên tắc:
- KHÔNG thay đổi social/publishers.py
- Dùng Pillow để crop/resize/annotate safe zone
- Metadata lưu trong assets.tags (JSON) — KHÔNG thay đổi schema
"""

import io
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum

from database.models.assets import AssetModel
from database.models.approvals import ApprovalModel
from database.models.schedules import ScheduleModel
from database.connection import managed_connection, _adapt_sql
from config.config import logger


# ============================================================
# PLATFORM SPECS
# ============================================================

@dataclass
class PlatformSpec:
    name: str
    width: int
    height: int
    max_bytes: int
    safe_margin_top: int
    safe_margin_bottom: int
    safe_margin_left: int
    safe_margin_right: int
    formats: List[str]
    notes: str = ""

    @property
    def ratio(self) -> float:
        return self.width / self.height

    @property
    def ratio_str(self) -> str:
        from math import gcd
        g = gcd(self.width, self.height)
        return f"{self.width // g}:{self.height // g}"

    @property
    def safe_width(self) -> int:
        return self.width - self.safe_margin_left - self.safe_margin_right

    @property
    def safe_height(self) -> int:
        return self.height - self.safe_margin_top - self.safe_margin_bottom

    @property
    def max_mb(self) -> float:
        return self.max_bytes / (1024 * 1024)


PLATFORM_SPECS: Dict[str, Dict[str, PlatformSpec]] = {
    "facebook": {
        "post": PlatformSpec(
            name="Facebook Post",
            width=1200, height=630,
            max_bytes=4 * 1024 * 1024,
            safe_margin_top=60, safe_margin_bottom=60,
            safe_margin_left=80, safe_margin_right=80,
            formats=["jpg", "jpeg", "png"],
            notes="Tốt nhất: 1200×630. Text < 20% diện tích ảnh."
        ),
        "story": PlatformSpec(
            name="Facebook Story",
            width=1080, height=1920,
            max_bytes=4 * 1024 * 1024,
            safe_margin_top=120, safe_margin_bottom=120,
            safe_margin_left=80, safe_margin_right=80,
            formats=["jpg", "jpeg", "png"],
            notes="Story: 9:16. UI overlay top/bottom 120px."
        ),
        "square": PlatformSpec(
            name="Facebook Square",
            width=1080, height=1080,
            max_bytes=4 * 1024 * 1024,
            safe_margin_top=60, safe_margin_bottom=60,
            safe_margin_left=60, safe_margin_right=60,
            formats=["jpg", "jpeg", "png"],
        ),
    },
    "linkedin": {
        "post": PlatformSpec(
            name="LinkedIn Post",
            width=1200, height=627,
            max_bytes=5 * 1024 * 1024,
            safe_margin_top=50, safe_margin_bottom=50,
            safe_margin_left=50, safe_margin_right=50,
            formats=["jpg", "jpeg", "png", "gif"],
            notes="Mobile crop ~100px bottom. Giữ nội dung quan trọng ở trên."
        ),
        "article": PlatformSpec(
            name="LinkedIn Article",
            width=1920, height=1080,
            max_bytes=5 * 1024 * 1024,
            safe_margin_top=80, safe_margin_bottom=80,
            safe_margin_left=80, safe_margin_right=80,
            formats=["jpg", "jpeg", "png"],
            notes="16:9 fullscreen header."
        ),
        "square": PlatformSpec(
            name="LinkedIn Square",
            width=1080, height=1080,
            max_bytes=5 * 1024 * 1024,
            safe_margin_top=60, safe_margin_bottom=60,
            safe_margin_left=60, safe_margin_right=60,
            formats=["jpg", "jpeg", "png"],
        ),
    },
    "zalo": {
        "broadcast": PlatformSpec(
            name="Zalo OA Broadcast",
            width=1040, height=585,
            max_bytes=1 * 1024 * 1024,
            safe_margin_top=40, safe_margin_bottom=40,
            safe_margin_left=60, safe_margin_right=60,
            formats=["jpg", "jpeg", "png"],
            notes="Max 1MB. Chat bubble crops 20px top mobile."
        ),
        "article": PlatformSpec(
            name="Zalo OA Article",
            width=600, height=400,
            max_bytes=3 * 1024 * 1024,
            safe_margin_top=30, safe_margin_bottom=30,
            safe_margin_left=30, safe_margin_right=30,
            formats=["jpg", "jpeg", "png"],
        ),
        "square": PlatformSpec(
            name="Zalo OA Square",
            width=512, height=512,
            max_bytes=1 * 1024 * 1024,
            safe_margin_top=30, safe_margin_bottom=30,
            safe_margin_left=30, safe_margin_right=30,
            formats=["jpg", "jpeg", "png"],
        ),
    },
}


def get_spec(platform: str, post_type: str = "post") -> Optional[PlatformSpec]:
    """Lấy spec theo platform + post_type."""
    plat = platform.lower().replace(" oa", "").replace(" ", "")
    if plat == "zaloa": plat = "zalo"
    return PLATFORM_SPECS.get(plat, {}).get(post_type)


# ============================================================
# THUMBNAIL PROCESSOR (Pillow-based, no API changes)
# ============================================================

class ThumbnailProcessor:
    """
    Xử lý ảnh thumbnail: load từ URL hoặc bytes,
    crop/resize về đúng kích thước platform, annotate safe zone.
    Không gọi bất kỳ social API nào.
    """

    @staticmethod
    def load_from_url(url: str) -> "PIL.Image.Image":
        """Download ảnh từ URL → PIL Image."""
        import requests
        from PIL import Image
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return Image.open(io.BytesIO(resp.content)).convert("RGB")

    @staticmethod
    def load_from_bytes(data: bytes) -> "PIL.Image.Image":
        from PIL import Image
        return Image.open(io.BytesIO(data)).convert("RGB")

    @staticmethod
    def smart_crop(img: "PIL.Image.Image", spec: PlatformSpec,
                   anchor: str = "center") -> "PIL.Image.Image":
        """
        Smart crop: resize giữ tỷ lệ, rồi crop về đúng kích thước.
        anchor: "center" | "top" | "bottom"
        """
        from PIL import Image
        target_w, target_h = spec.width, spec.height
        src_w, src_h = img.size

        # Scale to cover target
        scale = max(target_w / src_w, target_h / src_h)
        new_w = int(src_w * scale)
        new_h = int(src_h * scale)
        img = img.resize((new_w, new_h), Image.LANCZOS)

        # Crop
        left = (new_w - target_w) // 2
        if anchor == "top":
            top = 0
        elif anchor == "bottom":
            top = new_h - target_h
        else:
            top = (new_h - target_h) // 2

        return img.crop((left, top, left + target_w, top + target_h))

    @staticmethod
    def add_safe_zone_overlay(img: "PIL.Image.Image",
                              spec: PlatformSpec,
                              opacity: int = 60) -> "PIL.Image.Image":
        """
        Vẽ overlay bán trong suốt để hiển thị safe zone khi preview.
        opacity: 0-255 (60 ≈ 24% opacity, đủ thấy rõ nhưng không che nội dung)
        """
        from PIL import Image, ImageDraw, ImageFont
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # Vùng UNSAFE (tô mờ đỏ)
        color_unsafe = (255, 50, 50, opacity)
        # Top
        draw.rectangle([0, 0, img.width, spec.safe_margin_top], fill=color_unsafe)
        # Bottom
        draw.rectangle([0, img.height - spec.safe_margin_bottom,
                        img.width, img.height], fill=color_unsafe)
        # Left
        draw.rectangle([0, 0, spec.safe_margin_left, img.height], fill=color_unsafe)
        # Right
        draw.rectangle([img.width - spec.safe_margin_right, 0,
                        img.width, img.height], fill=color_unsafe)

        # Viền safe zone (xanh lá)
        sx1 = spec.safe_margin_left
        sy1 = spec.safe_margin_top
        sx2 = img.width - spec.safe_margin_right
        sy2 = img.height - spec.safe_margin_bottom
        draw.rectangle([sx1, sy1, sx2, sy2],
                       outline=(0, 220, 80, 200), width=3)

        # Label
        draw.text((sx1 + 8, sy1 + 8), f"SAFE ZONE  {spec.safe_width}×{spec.safe_height}px",
                  fill=(0, 220, 80, 220))

        base = img.convert("RGBA")
        combined = Image.alpha_composite(base, overlay)
        return combined.convert("RGB")

    @staticmethod
    def resize_to_spec(img: "PIL.Image.Image",
                       spec: PlatformSpec) -> "PIL.Image.Image":
        """Resize về đúng kích thước (không crop, dùng letterbox nếu cần)."""
        from PIL import Image
        img.thumbnail((spec.width, spec.height), Image.LANCZOS)
        # Letterbox nếu tỷ lệ không khớp
        if img.size != (spec.width, spec.height):
            canvas = Image.new("RGB", (spec.width, spec.height), (0, 0, 0))
            offset = ((spec.width - img.width) // 2,
                      (spec.height - img.height) // 2)
            canvas.paste(img, offset)
            return canvas
        return img

    @staticmethod
    def to_bytes(img: "PIL.Image.Image",
                 fmt: str = "JPEG",
                 quality: int = 88) -> bytes:
        buf = io.BytesIO()
        img.save(buf, format=fmt, quality=quality, optimize=True)
        return buf.getvalue()

    @staticmethod
    def validate(img_bytes: bytes, spec: PlatformSpec) -> Dict[str, Any]:
        """Kiểm tra ảnh đã đúng spec chưa. Trả về dict kết quả."""
        from PIL import Image
        img = Image.open(io.BytesIO(img_bytes))
        size_ok = len(img_bytes) <= spec.max_bytes
        dim_ok  = img.width == spec.width and img.height == spec.height
        return {
            "ok": size_ok and dim_ok,
            "width":  img.width,
            "height": img.height,
            "size_mb": len(img_bytes) / (1024 * 1024),
            "size_ok": size_ok,
            "dim_ok":  dim_ok,
            "format": img.format,
            "issues": [
                *([f"Kích thước file {len(img_bytes)/(1024*1024):.2f}MB vượt {spec.max_mb:.1f}MB"] if not size_ok else []),
                *([f"Kích thước ảnh {img.width}×{img.height} ≠ {spec.width}×{spec.height}"] if not dim_ok else []),
            ]
        }

    @classmethod
    def prepare_for_platform(cls, url: str, spec: PlatformSpec,
                             crop_anchor: str = "center") -> Tuple[bytes, Dict]:
        """
        Pipeline đầy đủ:
        1. Load từ URL
        2. Smart crop về đúng kích thước
        3. Validate
        Trả về (image_bytes, validation_result)
        """
        img = cls.load_from_url(url)
        img = cls.smart_crop(img, spec, anchor=crop_anchor)
        fmt = spec.formats[0].upper().replace("JPG", "JPEG")
        img_bytes = cls.to_bytes(img, fmt=fmt)
        validation = cls.validate(img_bytes, spec)
        return img_bytes, validation


# ============================================================
# APPROVAL GATE
# ============================================================

class ThumbnailApprovalGate:
    """
    Kiểm tra trạng thái approval của thumbnail trước khi publish.
    Sử dụng ApprovalModel và MediaLibraryService (assets.tags).
    """

    @staticmethod
    def get_post_thumbnails(post_id: int, workspace_id: int) -> List[dict]:
        """Lấy tất cả assets là thumbnail của bài viết."""
        assets = AssetModel.list_by_post(post_id)
        thumbnails = []
        for asset in assets:
            tags = asset.get("tags", {})
            if isinstance(tags, str):
                try:
                    tags = json.loads(tags)
                except Exception:
                    tags = {}
            if isinstance(tags, dict):
                thumb_meta = tags.get("thumbnail", {})
                if thumb_meta.get("is_thumbnail"):
                    asset["_thumb_meta"] = thumb_meta
                    asset["_lifecycle"] = tags.get("lifecycle", {})
                    thumbnails.append(asset)
        return thumbnails

    @staticmethod
    def check_thumbnail_approved(post_id: int, workspace_id: int) -> Dict[str, Any]:
        """
        Kiểm tra xem bài viết có thumbnail đã được approve chưa.
        Returns: { ok, thumbnails, unapproved, message }
        """
        thumbnails = ThumbnailApprovalGate.get_post_thumbnails(post_id, workspace_id)
        if not thumbnails:
            return {
                "ok": False,
                "thumbnails": [],
                "unapproved": [],
                "message": "⚠️ Bài viết chưa có thumbnail. Vui lòng thêm thumbnail trước khi publish."
            }

        unapproved = []
        for t in thumbnails:
            status = t.get("_lifecycle", {}).get("status", "draft")
            if status not in ("approved", "published"):
                unapproved.append(t)

        if unapproved:
            names = [u["name"] for u in unapproved]
            return {
                "ok": False,
                "thumbnails": thumbnails,
                "unapproved": unapproved,
                "message": f"⚠️ {len(unapproved)} thumbnail chưa được approve: {', '.join(names)}"
            }

        return {
            "ok": True,
            "thumbnails": thumbnails,
            "unapproved": [],
            "message": f"✅ {len(thumbnails)} thumbnail đã được approve."
        }

    @staticmethod
    def quick_approve_thumbnail(asset_id: int, workspace_id: int,
                                approved_by: int, note: str = "") -> bool:
        """Approve nhanh thumbnail trực tiếp từ Publishing UI."""
        from database.connection import managed_connection, _adapt_sql
        asset = AssetModel.get_by_id(asset_id)
        if not asset:
            return False
        tags = asset.get("tags", {})
        if isinstance(tags, str):
            try: tags = json.loads(tags)
            except: tags = {}
        if not isinstance(tags, dict):
            tags = {}
        lc = tags.setdefault("lifecycle", {})
        lc["status"] = "approved"
        lc["approved_by"] = approved_by
        lc["approved_at"] = datetime.now().isoformat()
        history = tags.setdefault("history", [])
        history.append({
            "action": "approved_from_publishing",
            "by": approved_by,
            "at": datetime.now().isoformat(),
            "note": note or "Quick-approve từ Publishing tab"
        })
        tags["history"] = history[-50:]
        sql = _adapt_sql("UPDATE assets SET tags=? WHERE id=? AND workspace_id=?")
        with managed_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (json.dumps(tags, ensure_ascii=False), asset_id, workspace_id))
            return cur.rowcount > 0


# ============================================================
# PUBLISH QUEUE ITEM
# ============================================================

@dataclass
class PublishQueueItem:
    schedule_id: int
    post_id: int
    platform: str
    post_type: str              # post | story | article | broadcast
    scheduled_at: str
    content: str
    thumbnail_asset_id: Optional[int]
    thumbnail_url: Optional[str]
    thumbnail_status: str       # not_set | pending_approval | approved | ready | error
    thumbnail_validated: bool
    validation_result: Optional[Dict]
    retry_count: int
    status: str                 # pending | processing | published | failed | cancelled
    error_message: Optional[str]


class PublishQueue:
    """
    Quản lý hàng chờ publish bao gồm thông tin thumbnail.
    Wrap ScheduleModel + enrichment thumbnail metadata.
    """

    @staticmethod
    def get_enriched_queue(workspace_id: int,
                           status: str = "pending") -> List[PublishQueueItem]:
        """
        Lấy hàng chờ publish đã được enriched với thumbnail info.
        """
        schedules = ScheduleModel.list_by_workspace(workspace_id, status=status, limit=100)
        items = []
        for sched in schedules:
            post_id = sched["post_id"]
            platform = sched.get("platform", "facebook")

            # Lấy thumbnail
            thumbnails = ThumbnailApprovalGate.get_post_thumbnails(post_id, workspace_id)
            thumb_asset = thumbnails[0] if thumbnails else None
            thumb_status = "not_set"
            thumb_validated = False
            validation = None
            thumb_url = None
            thumb_id = None

            if thumb_asset:
                thumb_id = thumb_asset["id"]
                thumb_url = thumb_asset.get("url", "")
                lc_status = thumb_asset.get("_lifecycle", {}).get("status", "draft")
                if lc_status in ("approved", "published"):
                    thumb_status = "approved"
                    # Validate nhanh (không crop, chỉ check size)
                    spec = get_spec(platform)
                    if spec and thumb_url:
                        try:
                            import requests
                            resp = requests.head(thumb_url, timeout=3)
                            content_len = int(resp.headers.get("content-length", 0))
                            thumb_validated = content_len <= spec.max_bytes
                            validation = {
                                "size_ok": thumb_validated,
                                "size_mb": content_len / (1024 * 1024),
                            }
                            thumb_status = "ready" if thumb_validated else "error"
                        except Exception:
                            thumb_status = "approved"  # Assume OK nếu không check được
                else:
                    thumb_status = "pending_approval"

            items.append(PublishQueueItem(
                schedule_id=sched["id"],
                post_id=post_id,
                platform=platform,
                post_type=sched.get("post_type", "post"),
                scheduled_at=sched["scheduled_at"],
                content=sched.get("content", ""),
                thumbnail_asset_id=thumb_id,
                thumbnail_url=thumb_url,
                thumbnail_status=thumb_status,
                thumbnail_validated=thumb_validated,
                validation_result=validation,
                retry_count=sched.get("retry_count", 0),
                status=sched["status"],
                error_message=sched.get("error_message"),
            ))
        return items

    @staticmethod
    def get_queue_summary(workspace_id: int) -> Dict[str, int]:
        """Thống kê nhanh hàng chờ."""
        items = PublishQueue.get_enriched_queue(workspace_id)
        return {
            "total": len(items),
            "ready":            sum(1 for i in items if i.thumbnail_status == "ready"),
            "pending_approval": sum(1 for i in items if i.thumbnail_status == "pending_approval"),
            "no_thumbnail":     sum(1 for i in items if i.thumbnail_status == "not_set"),
            "error":            sum(1 for i in items if i.thumbnail_status == "error"),
        }


# ============================================================
# RETRY MANAGER
# ============================================================

class RetryManager:
    """
    Quản lý retry logic khi đăng bài kèm thumbnail thất bại.
    Không gọi API trực tiếp — điều phối lại qua ScheduleModel.
    """

    MAX_RETRIES = 3
    RETRY_STRATEGIES = {
        1: "Thử lại với ảnh gốc",
        2: "Thử lại với ảnh nén thêm (quality=70)",
        3: "Thử lại chỉ text (không kèm thumbnail)",
    }

    @staticmethod
    def should_retry(retry_count: int, error_message: str = "") -> bool:
        """Quyết định có retry không."""
        if retry_count >= RetryManager.MAX_RETRIES:
            return False
        # Một số lỗi không nên retry (auth error, permission denied)
        no_retry_keywords = ["access_token", "permission", "unauthorized", "403"]
        if any(kw in (error_message or "").lower() for kw in no_retry_keywords):
            return False
        return True

    @staticmethod
    def get_strategy(retry_count: int) -> str:
        """Lấy chiến lược retry theo lần."""
        return RetryManager.RETRY_STRATEGIES.get(retry_count + 1,
               "Không còn retry — kiểm tra lỗi thủ công")

    @staticmethod
    def schedule_retry(schedule_id: int, error_message: str,
                       workspace_id: int) -> bool:
        """
        Đánh dấu failed + tăng retry_count để scheduler xử lý lần sau.
        Không gọi API ngay lập tức.
        """
        sched = ScheduleModel.get_by_id(schedule_id)
        if not sched:
            return False
        retry_count = sched.get("retry_count", 0)

        if not RetryManager.should_retry(retry_count, error_message):
            ScheduleModel.update_status(
                schedule_id, "failed",
                error_message=f"[MAX_RETRY] {error_message}"
            )
            logger.error(f"[PublishRetry] Schedule #{schedule_id} đã hết retry ({retry_count}/{RetryManager.MAX_RETRIES})")
            return False

        ScheduleModel.update_status(
            schedule_id, "pending",
            error_message=f"[Retry {retry_count+1}/{RetryManager.MAX_RETRIES}] {error_message}"
        )
        logger.info(f"[PublishRetry] Schedule #{schedule_id} → Retry {retry_count+1}, strategy: {RetryManager.get_strategy(retry_count)}")
        return True

    @staticmethod
    def get_fallback_strategy(retry_count: int,
                              original_url: str,
                              spec: PlatformSpec) -> Dict[str, Any]:
        """
        Trả về config cho lần retry:
        - retry 1: ảnh gốc không đổi
        - retry 2: nén thêm (quality=70)
        - retry 3: không kèm thumbnail (text-only)
        """
        if retry_count == 0:
            return {"use_thumbnail": True, "quality": 88, "url": original_url}
        elif retry_count == 1:
            return {"use_thumbnail": True, "quality": 70, "url": original_url}
        else:
            return {"use_thumbnail": False, "quality": 88, "url": None,
                    "note": "Text-only fallback sau khi thumbnail retry thất bại"}
```

---

## 🖥️ 5. Thiết Kế UI — `ui/tab_publishing.py` (Mở Rộng)

### 5.1 Luồng Publishing Mới

```
Bước 1: Chọn bài viết + nền tảng
         ↓
Bước 2: Kiểm tra & Gắn thumbnail
         ↓
Bước 3: Preview thumbnail trên platform mock-up
         ↓
Bước 4: Approval Gate (thumbnail phải approved)
         ↓
Bước 5: Format + Validate (crop nếu cần)
         ↓
Bước 6: Publish Queue → Publish Now hoặc Schedule
         ↓
Bước 7: Kết quả + Retry nếu thất bại
```

### 5.2 Layout Publish Queue Mới

```
┌─────────────────────────────────────────────────────────────────────┐
│  📢 Publishing Agent — Quản Lý & Đăng Bài                          │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  📊 THUMBNAIL QUEUE SUMMARY                                          │
│  ┌────────────┬──────────────┬────────────┬────────────┬─────────┐  │
│  │ Tổng: 12   │ ✅ Ready: 7  │ ⏳ Chờ: 3 │ ❌ Lỗi: 1 │ ➕ Mới │  │
│  └────────────┴──────────────┴────────────┴────────────┴─────────┘  │
│                                                                      │
│  HÀNG CHỜ PUBLISH (Pending Queue)                                    │
│  ┌───┬──────┬──────────┬──────────┬──────────────┬─────────┬──────┐ │
│  │ # │ Post │ Platform │ Lịch đăng│ Thumbnail    │ Status  │ Act. │ │
│  ├───┼──────┼──────────┼──────────┼──────────────┼─────────┼──────┤ │
│  │ 1 │  #42 │ Facebook │ 14:00    │ ✅ Ready     │ pending │[👁️]│ │
│  │ 2 │  #45 │ LinkedIn │ 15:30    │ ⏳ Cần duyệt │ pending │[👁️]│ │
│  │ 3 │  #48 │ Zalo OA  │ 16:00    │ ➕ Chưa gắn │ pending │[👁️]│ │
│  │ 4 │  #51 │ Facebook │ 18:00    │ ❌ Lỗi size  │ pending │[👁️]│ │
│  └───┴──────┴──────────┴──────────┴──────────────┴─────────┴──────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.3 Platform Mock-up Preview

```
FACEBOOK PREVIEW                    LINKEDIN PREVIEW
┌──────────────────────────────┐    ┌──────────────────────────────┐
│ 👤 Page Name                 │    │ 👤 Your Name                 │
│    Vừa xong · 🌐              │    │    1st · Vừa xong            │
├──────────────────────────────┤    ├──────────────────────────────┤
│ [TEXT CONTENT preview...]    │    │ [TEXT CONTENT preview...]    │
│ [TEXT CONTENT...]            │    │ [TEXT CONTENT...]            │
├──────────────────────────────┤    ├──────────────────────────────┤
│ ┌────────────────────────┐   │    │ ┌────────────────────────┐   │
│ │                        │   │    │ │                        │   │
│ │   THUMBNAIL PREVIEW    │   │    │ │   THUMBNAIL PREVIEW    │   │
│ │     1200 × 630 px      │   │    │ │     1200 × 627 px      │   │
│ │    [SAFE ZONE grid]    │   │    │ │    [SAFE ZONE grid]    │   │
│ │                        │   │    │ │                        │   │
│ └────────────────────────┘   │    └────────────────────────────┘ │
│ 👍 Thích  💬 Bình luận  ↗️   │    │ 👍 Like  💬 Comment  🔄 Re.│ │
└──────────────────────────────┘    └──────────────────────────────┘

ZALO OA PREVIEW
┌──────────────────────────────┐
│ Official Account             │
│ ┌────────────────────────┐   │
│ │   THUMBNAIL PREVIEW    │   │
│ │     1040 × 585 px      │   │
│ │    (16:9 Broadcast)    │   │
│ └────────────────────────┘   │
│ Tiêu đề bài viết...          │
│ Nội dung preview text...     │
│                [Xem thêm →]  │
└──────────────────────────────┘
```

### 5.4 Code skeleton: Phần Thumbnail trong Publishing Tab

```python
# Thêm vào tab_publishing.py — PHẦN MỚI: THUMBNAIL MANAGEMENT
# (Không xóa code cũ, chỉ thêm section mới)

def _render_thumbnail_section(post_id: int, workspace_id: int,
                               platform: str, user_id: int,
                               user_role: str):
    """
    Section quản lý thumbnail cho bài viết trong Publishing tab.
    Gọi sau khi user chọn bài viết và platform.
    """
    from services.thumbnail_publishing_service import (
        ThumbnailApprovalGate, ThumbnailProcessor,
        get_spec, PLATFORM_SPECS
    )
    from database.models.assets import AssetModel

    st.markdown("#### 🖼️ Thumbnail Management")

    # ── Chọn post_type ──────────────────────────────────────
    plat_types = list(PLATFORM_SPECS.get(platform.lower(), {}).keys())
    post_type = st.selectbox(
        "Loại bài đăng:",
        plat_types,
        format_func=lambda x: PLATFORM_SPECS[platform.lower()][x].name
    )
    spec = get_spec(platform, post_type)
    if not spec:
        st.warning("Không tìm thấy thông số kỹ thuật cho platform này.")
        return

    # ── Hiển thị spec ───────────────────────────────────────
    with st.expander(f"📐 Thông số: {spec.name}", expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Chiều rộng", f"{spec.width}px")
        c2.metric("Chiều cao",  f"{spec.height}px")
        c3.metric("Tỷ lệ",      spec.ratio_str)
        c4.metric("Max size",   f"{spec.max_mb:.1f}MB")

        st.info(f"""
        🟢 **Safe Zone**: {spec.safe_width}×{spec.safe_height}px
           (Margin: Top {spec.safe_margin_top}px · Bottom {spec.safe_margin_bottom}px ·
           Left {spec.safe_margin_left}px · Right {spec.safe_margin_right}px)

        ℹ️ {spec.notes}
        """)

    # ── Kiểm tra thumbnail hiện tại ──────────────────────────
    approval_check = ThumbnailApprovalGate.check_thumbnail_approved(post_id, workspace_id)
    thumbnails = approval_check["thumbnails"]

    col_thumb, col_actions = st.columns([3, 2])

    with col_thumb:
        if thumbnails:
            thumb = thumbnails[0]
            thumb_url = thumb.get("url", "")
            thumb_status = thumb.get("_lifecycle", {}).get("status", "draft")

            # Status badge
            status_colors = {
                "draft":     ("📝 Draft",    "#FFA500"),
                "approved":  ("✅ Approved", "#28A745"),
                "published": ("🚀 Published","#007BFF"),
                "archived":  ("🗄️ Archived","#6C757D"),
            }
            label, color = status_colors.get(thumb_status, ("❓", "#999"))
            st.markdown(
                f"<span style='background:{color};color:white;padding:4px 10px;"
                f"border-radius:6px;font-size:0.85rem'>{label}</span>",
                unsafe_allow_html=True
            )
            st.caption(f"**{thumb['name']}** · v{thumb.get('_lifecycle',{}).get('version',1)}")

            # Preview ảnh
            if thumb_url:
                try:
                    st.image(thumb_url, use_container_width=True,
                             caption=f"{spec.width}×{spec.height} · {spec.ratio_str}")
                except Exception:
                    st.warning("Không tải được ảnh preview.")
        else:
            st.info("➕ Chưa có thumbnail cho bài viết này.")

    with col_actions:
        if thumbnails:
            thumb = thumbnails[0]
            thumb_status = thumb.get("_lifecycle", {}).get("status", "draft")

            # Quick approve (cho admin/super_admin)
            if thumb_status not in ("approved", "published") and \
               user_role in ("admin", "super_admin"):
                if st.button("✅ Approve Thumbnail", type="primary",
                             key=f"quick_approve_{post_id}"):
                    ok = ThumbnailApprovalGate.quick_approve_thumbnail(
                        thumb["id"], workspace_id, user_id,
                        "Quick-approve từ Publishing"
                    )
                    if ok:
                        st.success("Đã approve thumbnail!")
                        st.rerun()

            # Crop & Validate
            if thumb.get("url"):
                if st.button("✂️ Crop & Validate", key=f"crop_{post_id}"):
                    with st.spinner(f"Đang xử lý ảnh cho {spec.name}..."):
                        try:
                            img_bytes, validation = ThumbnailProcessor.prepare_for_platform(
                                thumb["url"], spec
                            )
                            if validation["ok"]:
                                st.success(
                                    f"✅ Ảnh hợp lệ!\n"
                                    f"Kích thước: {validation['width']}×{validation['height']}px · "
                                    f"{validation['size_mb']:.2f}MB"
                                )
                            else:
                                for issue in validation.get("issues", []):
                                    st.error(f"❌ {issue}")
                        except Exception as e:
                            st.error(f"Lỗi xử lý ảnh: {e}")

            # Preview với Safe Zone
            if thumb.get("url"):
                if st.button("🔍 Preview Safe Zone", key=f"sz_{post_id}"):
                    with st.spinner("Đang tạo safe zone overlay..."):
                        try:
                            img = ThumbnailProcessor.load_from_url(thumb["url"])
                            img = ThumbnailProcessor.smart_crop(img, spec)
                            img_with_sz = ThumbnailProcessor.add_safe_zone_overlay(img, spec)
                            import io
                            buf = io.BytesIO()
                            img_with_sz.save(buf, format="JPEG", quality=85)
                            st.session_state[f"sz_preview_{post_id}"] = buf.getvalue()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Lỗi tạo safe zone: {e}")

        # Gắn thumbnail mới
        st.divider()
        all_assets = AssetModel.list_by_workspace(workspace_id, file_type="image")
        if all_assets:
            asset_options = {a["id"]: a["name"] for a in all_assets}
            selected_asset_id = st.selectbox(
                "Gắn thumbnail khác:",
                options=[None] + list(asset_options.keys()),
                format_func=lambda x: "— Chọn asset —" if x is None else asset_options[x]
            )
            if selected_asset_id and st.button("📌 Gắn Thumbnail", key=f"attach_{post_id}"):
                AssetModel.attach_to_post(selected_asset_id, post_id)
                st.success("Đã gắn thumbnail!")
                st.rerun()

    # Safe zone preview modal
    sz_key = f"sz_preview_{post_id}"
    if sz_key in st.session_state:
        st.image(st.session_state[sz_key], caption="Safe Zone Preview",
                 use_container_width=True)
        if st.button("✕ Đóng preview", key=f"close_sz_{post_id}"):
            del st.session_state[sz_key]

    # Approval gate warning
    st.divider()
    if not approval_check["ok"]:
        st.warning(approval_check["message"])
        return False   # Chặn publish
    else:
        st.success(approval_check["message"])
        return True    # Cho phép publish


def _render_platform_mockup(platform: str, content: str,
                             thumbnail_url: str = None):
    """
    Mô phỏng giao diện card bài đăng theo từng nền tảng.
    Pure HTML/CSS — không gọi API.
    """
    platform = platform.lower()

    # Rút gọn content
    content_preview = content[:200] + "..." if len(content) > 200 else content

    thumb_html = ""
    if thumbnail_url:
        thumb_html = f'<img src="{thumbnail_url}" style="width:100%;border-radius:4px;margin-top:8px"/>'
    else:
        thumb_html = '<div style="width:100%;height:120px;background:#e9ecef;border-radius:4px;display:flex;align-items:center;justify-content:center;margin-top:8px;color:#999">🖼️ Chưa có thumbnail</div>'

    if platform == "facebook":
        html = f"""
        <div style="font-family:'Segoe UI',sans-serif;max-width:480px;
                    border:1px solid #ddd;border-radius:8px;overflow:hidden;
                    background:#fff;box-shadow:0 1px 3px rgba(0,0,0,.1)">
            <div style="padding:12px;display:flex;align-items:center;gap:10px">
                <div style="width:40px;height:40px;background:#1877f2;border-radius:50%;
                            display:flex;align-items:center;justify-content:center;color:#fff">P</div>
                <div>
                    <div style="font-weight:700;color:#050505">Tên Page</div>
                    <div style="font-size:12px;color:#65676b">Vừa xong · 🌐</div>
                </div>
            </div>
            <div style="padding:0 12px 8px;color:#050505;font-size:15px">{content_preview}</div>
            {thumb_html}
            <div style="padding:8px 12px;border-top:1px solid #e4e6ea;
                        display:flex;gap:16px;color:#65676b;font-size:14px">
                <span>👍 Thích</span><span>💬 Bình luận</span><span>↗️ Chia sẻ</span>
            </div>
        </div>"""

    elif platform == "linkedin":
        html = f"""
        <div style="font-family:'Segoe UI',sans-serif;max-width:520px;
                    border:1px solid #e0dfde;border-radius:8px;overflow:hidden;
                    background:#fff;box-shadow:0 1px 3px rgba(0,0,0,.08)">
            <div style="padding:12px;display:flex;align-items:center;gap:10px">
                <div style="width:48px;height:48px;background:#0a66c2;border-radius:50%;
                            display:flex;align-items:center;justify-content:center;color:#fff">U</div>
                <div>
                    <div style="font-weight:700;color:#000">Tên Người Dùng</div>
                    <div style="font-size:12px;color:#666">1st · Vừa xong</div>
                </div>
            </div>
            <div style="padding:0 12px 8px;color:#000;font-size:14px;line-height:1.4">{content_preview}</div>
            {thumb_html}
            <div style="padding:8px 12px;border-top:1px solid #e0dfde;
                        display:flex;gap:12px;color:#666;font-size:13px">
                <span>👍 Like</span><span>💬 Comment</span>
                <span>🔄 Repost</span><span>✉️ Send</span>
            </div>
        </div>"""

    elif "zalo" in platform:
        html = f"""
        <div style="font-family:'Roboto',sans-serif;max-width:420px;
                    border:1px solid #ddd;border-radius:12px;overflow:hidden;
                    background:#fff;box-shadow:0 2px 8px rgba(0,0,0,.12)">
            <div style="background:#0068ff;padding:10px 16px;
                        display:flex;align-items:center;gap:8px">
                <div style="width:36px;height:36px;background:#fff;border-radius:50%;
                            display:flex;align-items:center;justify-content:center;
                            font-weight:700;color:#0068ff">Z</div>
                <div style="color:#fff;font-weight:600">Official Account</div>
            </div>
            {thumb_html}
            <div style="padding:10px 14px">
                <div style="font-weight:700;margin-bottom:4px;color:#111">Tiêu đề bài viết</div>
                <div style="color:#555;font-size:13px;line-height:1.4">{content_preview}</div>
                <div style="color:#0068ff;font-size:13px;margin-top:6px;text-align:right">
                    Xem thêm →
                </div>
            </div>
        </div>"""

    else:
        html = f"<div>{content_preview}</div>"

    st.markdown(html, unsafe_allow_html=True)


def _render_thumbnail_publish_queue(workspace_id: int, user_id: int,
                                     user_role: str):
    """
    Render hàng chờ publish với thông tin thumbnail đầy đủ.
    Thêm vào tab_publishing.py — gọi trước Pending Queue cũ.
    """
    from services.thumbnail_publishing_service import PublishQueue, RetryManager

    st.subheader("🖼️📋 Publish Queue — Trạng thái Thumbnail")

    summary = PublishQueue.get_queue_summary(workspace_id)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("✅ Ready",       summary["ready"])
    c2.metric("⏳ Chờ duyệt",   summary["pending_approval"])
    c3.metric("➕ Chưa gắn",    summary["no_thumbnail"])
    c4.metric("❌ Lỗi",         summary["error"])

    items = PublishQueue.get_enriched_queue(workspace_id)
    if not items:
        st.caption("Hàng chờ trống.")
        return

    thumb_status_labels = {
        "ready":            "✅ Ready",
        "approved":         "✅ Approved",
        "pending_approval": "⏳ Chờ duyệt",
        "not_set":          "➕ Chưa gắn",
        "error":            "❌ Lỗi",
    }

    for item in items:
        status_label = thumb_status_labels.get(item.thumbnail_status, "❓")
        retry_info = ""
        if item.retry_count > 0:
            retry_info = f" · 🔄 Retry {item.retry_count}/{RetryManager.MAX_RETRIES}"
            if not RetryManager.should_retry(item.retry_count, item.error_message):
                retry_info += " · ⛔ Hết retry"

        with st.expander(
            f"📌 Schedule #{item.schedule_id} · Post #{item.post_id} · "
            f"**{item.platform.upper()}** · {item.scheduled_at[:16]} · "
            f"{status_label}{retry_info}",
            expanded=(item.thumbnail_status in ("error", "pending_approval"))
        ):
            c_info, c_action = st.columns([2, 1])
            with c_info:
                st.caption(f"**Thumbnail**: {thumb_status_labels.get(item.thumbnail_status)}")
                if item.thumbnail_url:
                    try:
                        st.image(item.thumbnail_url, width=200)
                    except Exception:
                        st.caption(f"URL: {item.thumbnail_url[:60]}...")
                if item.error_message:
                    st.error(f"Lỗi: {item.error_message[:120]}")
                if item.validation_result:
                    val = item.validation_result
                    st.caption(
                        f"Size: {val.get('size_mb', 0):.2f}MB · "
                        f"{'✅' if val.get('size_ok') else '❌'} Size"
                    )

            with c_action:
                # Retry button
                if item.status == "failed":
                    strategy = RetryManager.get_strategy(item.retry_count)
                    st.info(f"Chiến lược retry: {strategy}")
                    if RetryManager.should_retry(item.retry_count, item.error_message):
                        if st.button(f"🔄 Retry", key=f"retry_{item.schedule_id}",
                                     type="primary"):
                            RetryManager.schedule_retry(
                                item.schedule_id, item.error_message or "", workspace_id
                            )
                            st.success("Đã đặt lịch retry!")
                            st.rerun()

                # Quick approve thumbnail
                if item.thumbnail_status == "pending_approval" and \
                   user_role in ("admin", "super_admin") and item.thumbnail_asset_id:
                    if st.button(f"✅ Approve Thumb",
                                 key=f"qa_{item.schedule_id}_{item.thumbnail_asset_id}"):
                        from services.thumbnail_publishing_service import ThumbnailApprovalGate
                        ThumbnailApprovalGate.quick_approve_thumbnail(
                            item.thumbnail_asset_id, workspace_id, user_id,
                            "Quick approve từ Publish Queue"
                        )
                        st.success("Đã approve!")
                        st.rerun()
```

---

## 🔄 6. Luồng Approval Chi Tiết

### 6.1 State Machine Thumbnail trong Publishing

```
                    [Bài viết Draft]
                          │
                    Gắn thumbnail
                          │
                    [Thumbnail Draft]
                          │
                Editor gửi duyệt → ApprovalModel.request(post_id)
                          │
                ┌─────────┴──────────┐
                │                    │
           Admin approve       Admin reject/revise
                │                    │
        [Thumbnail Approved]    [Về Draft lại]
                │
    ┌───────────┴──────────────┐
    │                          │
  Publish Now             Schedule
    │                          │
    ▼                          ▼
  [Published]           [In Queue → Auto-publish]
    │                          │
    └──────── Thất bại ────────┘
                  │
           [Retry Strategy]
           retry_count++
                  │
          ┌───────┴─────────┐
          │                 │
       Retry 1           Retry 2
     (ảnh gốc)         (nén thêm)
          │                 │
          └────────┬────────┘
                   │
              Retry 3
           (text-only)
                   │
             Vẫn thất bại
                   │
              [FAILED] ← Thông báo admin
```

### 6.2 Approval Workflow Integration

```python
# LUỒNG APPROVAL THUMBNAIL KHI PUBLISH
# (Gọi trong tab_publishing.py trước khi cho phép bấm "Đăng bài")

def check_publish_readiness(post_id: int, workspace_id: int,
                            user_role: str) -> Dict[str, Any]:
    """
    Kiểm tra toàn bộ điều kiện publish:
    1. Bài viết đã approved?   ← ApprovalModel.get_latest_by_post()
    2. Thumbnail đã approved?  ← ThumbnailApprovalGate.check_thumbnail_approved()
    3. Thumbnail hợp lệ spec?  ← ThumbnailProcessor.validate()
    """
    from services.thumbnail_publishing_service import ThumbnailApprovalGate

    issues = []
    warnings = []

    # Check 1: Post approval
    latest_approval = ApprovalModel.get_latest_by_post(post_id)
    post_approved = latest_approval.get("status") == "approved"
    if not post_approved:
        if user_role in ("admin", "super_admin"):
            warnings.append("⚠️ Bài viết chưa qua quy trình phê duyệt (bạn có thể override)")
        else:
            issues.append("❌ Bài viết chưa được Admin approve")

    # Check 2: Thumbnail approval
    thumb_check = ThumbnailApprovalGate.check_thumbnail_approved(post_id, workspace_id)
    if not thumb_check["ok"]:
        if user_role in ("admin", "super_admin"):
            warnings.append(thumb_check["message"] + " (admin có thể override)")
        else:
            issues.append(thumb_check["message"])

    can_publish = len(issues) == 0
    return {
        "can_publish": can_publish,
        "issues":   issues,
        "warnings": warnings,
        "post_approved": post_approved,
        "thumb_check": thumb_check,
    }
```

---

## 📦 7. Cấu Trúc File Mới

```
AI_Agent_Content_AutoPos/
│
├── services/
│   └── thumbnail_publishing_service.py   ← [MỚI] Service chính
│
├── ui/
│   └── tab_publishing.py                 ← [MỞ RỘNG] Thêm section mới
│                                            (KHÔNG xóa code cũ)
│
└── docs/
    └── THUMBNAIL_PUBLISHING.md           ← [MỚI] Tài liệu này
```

**Thêm vào `requirements.txt`:**
```
Pillow>=10.0.0          # Image processing (crop, resize, safe zone)
```

---

## 🚀 8. Lộ Trình Triển Khai

### Phase 1 — Service & Specs (1 ngày)

```
[ ] Tạo services/thumbnail_publishing_service.py
    [ ] PLATFORM_SPECS dict (Facebook · LinkedIn · Zalo OA)
    [ ] ThumbnailProcessor (load_from_url, smart_crop, add_safe_zone_overlay, validate)
    [ ] ThumbnailApprovalGate (check, quick_approve)
    [ ] PublishQueue (get_enriched_queue, get_queue_summary)
    [ ] RetryManager (should_retry, get_strategy, schedule_retry)
    [ ] check_publish_readiness()
```

### Phase 2 — UI Integration (2 ngày)

```
[ ] Mở rộng tab_publishing.py
    [ ] _render_thumbnail_section() — gắn sau chọn bài
    [ ] _render_platform_mockup() — FB/LI/Zalo mock UI
    [ ] _render_thumbnail_publish_queue() — queue mới
    [ ] Tích hợp check_publish_readiness() trước nút "Đăng bài"
    [ ] Retry button trong queue view
    [ ] Safe zone overlay preview popup
    [ ] Quick approve thumbnail (admin role)
```

### Phase 3 — Verification (0.5 ngày)

```
[ ] Kiểm tra social/publishers.py KHÔNG bị thay đổi
[ ] Test với ảnh thật từ URL
[ ] Test retry flow (fake error)
[ ] Test RBAC (editor không approve được)
[ ] Kiểm tra database schema KHÔNG bị thay đổi
```

### Phase 4 — Nâng cao (Tùy chọn)

```
[ ] Auto-crop khi lên lịch (batch process)
[ ] Notification email khi thumbnail bị reject
[ ] Thumbnail preview side-by-side 3 platform
[ ] AI-powered safe zone detection (Gemini Vision)
[ ] Lưu ảnh đã crop vào storage mới (không ghi đè ảnh gốc)
[ ] Watermark tự động theo brand colors
```

---

## ✅ 9. Ràng Buộc & Đảm Bảo

| Ràng buộc | Trạng thái | Cách đảm bảo |
|-----------|-----------|--------------|
| Không sửa `social/publishers.py` | ✅ | Tạo `thumbnail_publishing_service.py` riêng biệt |
| Không sửa database schema | ✅ | Dùng `assets.tags` (JSON) làm metadata store |
| Tương thích SQLite + PostgreSQL | ✅ | Chỉ dùng `managed_connection()` và `_adapt_sql()` |
| Tương thích RBAC hiện có | ✅ | Kiểm tra `user_role` theo bảng phân quyền |
| Tương thích Approval hiện có | ✅ | Wrap `ApprovalModel` — không sửa model |
| Tương thích Schedule hiện có | ✅ | Wrap `ScheduleModel` — không sửa model |
| Pillow không ảnh hưởng production | ✅ | Chỉ dùng locally, không phải Pillow server |

---

## 📊 10. Bảng Tính Năng Theo Nền Tảng

| Tính năng | Facebook | LinkedIn | Zalo OA |
|-----------|:--------:|:--------:|:-------:|
| Aspect Ratio spec | ✅ 1.91:1 / 1:1 / 9:16 | ✅ 1.91:1 / 16:9 / 1:1 | ✅ 16:9 / 3:2 / 1:1 |
| Smart Crop | ✅ | ✅ | ✅ |
| Safe Zone Overlay | ✅ 60/80px | ✅ 50px | ✅ 40/60px |
| Platform Mockup Preview | ✅ Facebook card | ✅ LinkedIn card | ✅ Zalo OA card |
| Thumbnail Approval Gate | ✅ | ✅ | ✅ |
| Quick Approve (admin) | ✅ | ✅ | ✅ |
| Publish Queue với thumb status | ✅ | ✅ | ✅ |
| Retry với Fallback Strategy | ✅ | ✅ | ✅ |
| Size Validation | ✅ < 4MB | ✅ < 5MB | ✅ < 1MB broadcast |
| Format Validation | ✅ JPG/PNG | ✅ JPG/PNG/GIF | ✅ JPG/PNG |
| Mobile Crop Warning | ✅ | ✅ bottom 100px | ✅ top 20px |

---

*Tài liệu này được tạo bởi Antigravity AI Assistant — 2026-07-12*  
*Không thay đổi: `social/publishers.py` · Database Schema · `database/models/*.py`*
