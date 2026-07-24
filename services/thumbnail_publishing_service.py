"""
services/thumbnail_publishing_service.py
=========================================
Thumbnail Publishing Service — Xử lý, validate và quản lý thumbnail
trước khi publish lên Facebook, LinkedIn, Zalo OA.

Nguyên tắc thiết kế:
- KHÔNG thay đổi social/publishers.py
- KHÔNG thay đổi database schema
- Metadata mở rộng lưu vào assets.tags (JSON)
- Pillow (PIL) cho xử lý ảnh local
"""

import io
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from math import gcd
from typing import Any, Dict, List, Optional, Tuple

from config.config import logger
from database.connection import _adapt_sql, managed_connection
from database.models.assets import AssetModel
from database.models.approvals import ApprovalModel
from database.models.schedules import ScheduleModel


# ============================================================
# 1. PLATFORM SPECIFICATIONS
# ============================================================

@dataclass
class PlatformSpec:
    """Thông số kỹ thuật thumbnail cho 1 loại bài đăng / nền tảng."""
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
        return self.width / self.height if self.height else 0

    @property
    def ratio_str(self) -> str:
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

    @property
    def pil_format(self) -> str:
        """Format string dùng cho PIL Image.save()"""
        fmt = self.formats[0].upper()
        return "JPEG" if fmt in ("JPG", "JPEG") else fmt


# ----------------------------------------------------------
# Danh sách spec theo platform → post_type
# ----------------------------------------------------------
PLATFORM_SPECS: Dict[str, Dict[str, PlatformSpec]] = {

    "facebook": {
        "post": PlatformSpec(
            name="Facebook Post",
            width=1200, height=630,
            max_bytes=4 * 1024 * 1024,
            safe_margin_top=60, safe_margin_bottom=60,
            safe_margin_left=80, safe_margin_right=80,
            formats=["jpg", "png"],
            notes="Tỷ lệ 1.91:1. Text < 20% diện tích ảnh (Facebook policy).",
        ),
        "story": PlatformSpec(
            name="Facebook Story",
            width=1080, height=1920,
            max_bytes=4 * 1024 * 1024,
            safe_margin_top=120, safe_margin_bottom=120,
            safe_margin_left=80, safe_margin_right=80,
            formats=["jpg", "png"],
            notes="Tỷ lệ 9:16. UI overlay che top/bottom 120px.",
        ),
        "square": PlatformSpec(
            name="Facebook Square",
            width=1080, height=1080,
            max_bytes=4 * 1024 * 1024,
            safe_margin_top=60, safe_margin_bottom=60,
            safe_margin_left=60, safe_margin_right=60,
            formats=["jpg", "png"],
            notes="Tỷ lệ 1:1. Dùng cho quảng cáo feed.",
        ),
    },

    "linkedin": {
        "post": PlatformSpec(
            name="LinkedIn Post",
            width=1200, height=627,
            max_bytes=5 * 1024 * 1024,
            safe_margin_top=50, safe_margin_bottom=50,
            safe_margin_left=50, safe_margin_right=50,
            formats=["jpg", "png", "gif"],
            notes="Tỷ lệ ~1.91:1. Mobile crop ~100px bottom — đặt nội dung quan trọng ở trên.",
        ),
        "article": PlatformSpec(
            name="LinkedIn Article",
            width=1920, height=1080,
            max_bytes=5 * 1024 * 1024,
            safe_margin_top=80, safe_margin_bottom=80,
            safe_margin_left=80, safe_margin_right=80,
            formats=["jpg", "png"],
            notes="Tỷ lệ 16:9. Header fullscreen cho bài viết dài.",
        ),
        "square": PlatformSpec(
            name="LinkedIn Square",
            width=1080, height=1080,
            max_bytes=5 * 1024 * 1024,
            safe_margin_top=60, safe_margin_bottom=60,
            safe_margin_left=60, safe_margin_right=60,
            formats=["jpg", "png"],
            notes="Tỷ lệ 1:1.",
        ),
    },

    "zalo": {
        "broadcast": PlatformSpec(
            name="Zalo OA Broadcast",
            width=1040, height=585,
            max_bytes=1 * 1024 * 1024,
            safe_margin_top=40, safe_margin_bottom=40,
            safe_margin_left=60, safe_margin_right=60,
            formats=["jpg", "png"],
            notes="Tỷ lệ 16:9. Max 1MB. Chat bubble crop ~20px top trên mobile.",
        ),
        "article": PlatformSpec(
            name="Zalo OA Article",
            width=600, height=400,
            max_bytes=3 * 1024 * 1024,
            safe_margin_top=30, safe_margin_bottom=30,
            safe_margin_left=30, safe_margin_right=30,
            formats=["jpg", "png"],
            notes="Tỷ lệ 3:2. Thumbnail bài đăng bài viết dài.",
        ),
        "square": PlatformSpec(
            name="Zalo OA Square",
            width=512, height=512,
            max_bytes=1 * 1024 * 1024,
            safe_margin_top=30, safe_margin_bottom=30,
            safe_margin_left=30, safe_margin_right=30,
            formats=["jpg", "png"],
            notes="Tỷ lệ 1:1. Sticker / inline image.",
        ),
    },
}

# Alias nhanh
PLATFORM_ALIASES = {
    "facebook": "facebook",
    "fb":       "facebook",
    "linkedin": "linkedin",
    "li":       "linkedin",
    "zalo":     "zalo",
    "zalo oa":  "zalo",
    "zaloa":    "zalo",
}

# Default post_type theo platform
PLATFORM_DEFAULT_TYPE = {
    "facebook": "post",
    "linkedin": "post",
    "zalo":     "broadcast",
}


def get_spec(platform: str, post_type: str = None) -> Optional[PlatformSpec]:
    """Lấy PlatformSpec. Tự động resolve alias và default type."""
    plat_key = PLATFORM_ALIASES.get(platform.lower().strip())
    if not plat_key:
        return None
    ptype = post_type or PLATFORM_DEFAULT_TYPE.get(plat_key, "post")
    return PLATFORM_SPECS.get(plat_key, {}).get(ptype)


def list_post_types(platform: str) -> List[str]:
    """Liệt kê các post_type hợp lệ cho platform."""
    plat_key = PLATFORM_ALIASES.get(platform.lower().strip(), platform.lower())
    return list(PLATFORM_SPECS.get(plat_key, {}).keys())


# ============================================================
# 2. THUMBNAIL PROCESSOR (Pillow-based)
# ============================================================

class ThumbnailProcessor:
    """
    Xử lý ảnh thumbnail: load, crop, resize, validate, safe zone overlay.
    Sử dụng Pillow (PIL). Không gọi bất kỳ social API nào.
    """

    # ── Load ────────────────────────────────────────────────

    @staticmethod
    def load_from_url(url: str, timeout: int = 10) -> "PIL.Image.Image":
        """Download ảnh từ URL → PIL Image (RGB)."""
        import requests
        from PIL import Image
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        return Image.open(io.BytesIO(resp.content)).convert("RGB")

    @staticmethod
    def load_from_bytes(data: bytes) -> "PIL.Image.Image":
        """Load ảnh từ bytes → PIL Image (RGB)."""
        from PIL import Image
        return Image.open(io.BytesIO(data)).convert("RGB")

    @staticmethod
    def load_from_uploaded_file(uploaded_file) -> "PIL.Image.Image":
        """Load từ st.file_uploader object → PIL Image."""
        from PIL import Image
        return Image.open(uploaded_file).convert("RGB")

    # ── Crop / Resize ────────────────────────────────────────

    @staticmethod
    def smart_crop(
        img: "PIL.Image.Image",
        spec: PlatformSpec,
        anchor: str = "center",
    ) -> "PIL.Image.Image":
        """
        Smart crop: scale để cover target size → crop về đúng kích thước.
        anchor: "center" | "top" | "bottom"
        """
        from PIL import Image
        target_w, target_h = spec.width, spec.height
        src_w, src_h = img.size

        scale = max(target_w / src_w, target_h / src_h)
        new_w = max(int(src_w * scale), target_w)
        new_h = max(int(src_h * scale), target_h)
        img = img.resize((new_w, new_h), Image.LANCZOS)

        left = (new_w - target_w) // 2
        top = {
            "top":    0,
            "bottom": new_h - target_h,
            "center": (new_h - target_h) // 2,
        }.get(anchor, (new_h - target_h) // 2)

        return img.crop((left, top, left + target_w, top + target_h))

    @staticmethod
    def letterbox_resize(
        img: "PIL.Image.Image",
        spec: PlatformSpec,
        bg_color: Tuple[int, int, int] = (0, 0, 0),
    ) -> "PIL.Image.Image":
        """
        Resize giữ nguyên tỷ lệ, thêm letterbox (viền đen/bg) để fill kích thước.
        Dùng khi không muốn mất nội dung ở rìa.
        """
        from PIL import Image
        img.thumbnail((spec.width, spec.height), Image.LANCZOS)
        canvas = Image.new("RGB", (spec.width, spec.height), bg_color)
        offset = (
            (spec.width  - img.width)  // 2,
            (spec.height - img.height) // 2,
        )
        canvas.paste(img, offset)
        return canvas

    # ── Safe Zone Overlay ────────────────────────────────────

    @staticmethod
    def add_safe_zone_overlay(
        img: "PIL.Image.Image",
        spec: PlatformSpec,
        unsafe_opacity: int = 80,
    ) -> "PIL.Image.Image":
        """
        Vẽ overlay safe zone để preview:
        - Vùng UNSAFE: tô mờ đỏ (opacity = unsafe_opacity)
        - Viền SAFE ZONE: viền xanh lá + label
        Trả về ảnh RGB (không phải RGBA) để hiển thị trực tiếp.
        """
        from PIL import Image, ImageDraw

        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        color_unsafe = (220, 38, 38, unsafe_opacity)    # Đỏ mờ
        color_safe   = (22, 163, 74, 200)               # Xanh lá đường viền
        color_label  = (22, 163, 74, 230)               # Xanh lá text

        w, h = img.size
        mt = spec.safe_margin_top
        mb = spec.safe_margin_bottom
        ml = spec.safe_margin_left
        mr = spec.safe_margin_right

        # 4 vùng unsafe
        rects_unsafe = [
            (0, 0, w, mt),                   # Top
            (0, h - mb, w, h),               # Bottom
            (0, mt, ml, h - mb),             # Left
            (w - mr, mt, w, h - mb),         # Right
        ]
        for rect in rects_unsafe:
            draw.rectangle(rect, fill=color_unsafe)

        # Viền safe zone
        sx1, sy1 = ml, mt
        sx2, sy2 = w - mr, h - mb
        draw.rectangle([sx1, sy1, sx2, sy2], outline=color_safe, width=3)

        # Label safe zone
        label = f"SAFE ZONE  {spec.safe_width}×{spec.safe_height}px"
        draw.text((sx1 + 8, sy1 + 8), label, fill=color_label)
        draw.text((sx1 + 8, sy1 + 28),
                  f"Margin T:{mt} B:{mb} L:{ml} R:{mr}",
                  fill=color_label)

        # Merge
        base = img.convert("RGBA")
        combined = Image.alpha_composite(base, overlay)
        return combined.convert("RGB")

    # ── Encode ───────────────────────────────────────────────

    @staticmethod
    def to_bytes(
        img: "PIL.Image.Image",
        pil_format: str = "JPEG",
        quality: int = 88,
    ) -> bytes:
        """Encode PIL Image → bytes."""
        buf = io.BytesIO()
        img.save(buf, format=pil_format, quality=quality, optimize=True)
        return buf.getvalue()

    @staticmethod
    def compress(
        img_bytes: bytes,
        spec: PlatformSpec,
        quality: int = 70,
    ) -> bytes:
        """Nén ảnh xuống thêm để đáp ứng max_bytes của spec."""
        from PIL import Image
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format=spec.pil_format, quality=quality, optimize=True)
        return buf.getvalue()

    # ── Validate ─────────────────────────────────────────────

    @staticmethod
    def validate_bytes(img_bytes: bytes, spec: PlatformSpec) -> Dict[str, Any]:
        """
        Kiểm tra ảnh đã đúng spec chưa.
        Returns dict: { ok, width, height, size_mb, size_ok, dim_ok, issues }
        """
        from PIL import Image, UnidentifiedImageError
        try:
            img = Image.open(io.BytesIO(img_bytes))
        except UnidentifiedImageError:
            return {
                "ok": False, "width": 0, "height": 0,
                "size_mb": 0, "size_ok": False, "dim_ok": False,
                "format": "UNKNOWN",
                "issues": ["❌ File không phải ảnh hợp lệ"],
            }

        size_bytes = len(img_bytes)
        size_ok = size_bytes <= spec.max_bytes
        dim_ok  = (img.width == spec.width and img.height == spec.height)

        issues = []
        if not size_ok:
            issues.append(
                f"❌ Kích thước file {size_bytes/(1024*1024):.2f}MB vượt giới hạn {spec.max_mb:.1f}MB"
            )
        if not dim_ok:
            issues.append(
                f"❌ Kích thước ảnh {img.width}×{img.height}px ≠ yêu cầu {spec.width}×{spec.height}px"
            )

        return {
            "ok":       size_ok and dim_ok,
            "width":    img.width,
            "height":   img.height,
            "size_mb":  round(size_bytes / (1024 * 1024), 3),
            "size_ok":  size_ok,
            "dim_ok":   dim_ok,
            "format":   img.format or "UNKNOWN",
            "issues":   issues,
        }

    @staticmethod
    def validate_url_quick(url: str, spec: PlatformSpec,
                           timeout: int = 5) -> Dict[str, Any]:
        """
        Validate nhanh (chỉ check Content-Length header, không download toàn bộ).
        Dùng cho queue display để tránh tốn bandwidth.
        """
        import requests
        try:
            resp = requests.head(url, timeout=timeout, allow_redirects=True)
            content_len = int(resp.headers.get("content-length", 0))
            size_ok = (content_len == 0) or (content_len <= spec.max_bytes)
            return {
                "ok":      size_ok,
                "size_mb": round(content_len / (1024 * 1024), 3),
                "size_ok": size_ok,
                "dim_ok":  None,   # Không kiểm tra được dimension qua HEAD
                "issues":  [] if size_ok else [
                    f"⚠️ Ước tính file {content_len/(1024*1024):.2f}MB có thể vượt {spec.max_mb:.1f}MB"
                ],
            }
        except Exception as e:
            return {"ok": None, "size_mb": 0, "issues": [f"⚠️ Không check được: {e}"]}

    # ── Full pipeline ────────────────────────────────────────

    @classmethod
    def prepare_for_platform(
        cls,
        url: str,
        spec: PlatformSpec,
        crop_anchor: str = "center",
        quality: int = 88,
    ) -> Tuple[bytes, Dict[str, Any]]:
        """
        Pipeline đầy đủ:
        1. Load từ URL
        2. Smart crop → đúng kích thước
        3. Encode → bytes
        4. Validate
        Trả về (image_bytes, validation_result)
        """
        img = cls.load_from_url(url)
        img = cls.smart_crop(img, spec, anchor=crop_anchor)
        img_bytes = cls.to_bytes(img, pil_format=spec.pil_format, quality=quality)

        # Nếu vượt max_bytes, tự động nén thêm
        if len(img_bytes) > spec.max_bytes:
            logger.warning(
                f"[ThumbnailProcessor] Ảnh {len(img_bytes)/(1024*1024):.2f}MB > "
                f"{spec.max_mb:.1f}MB, tự động nén quality=70"
            )
            img_bytes = cls.compress(img_bytes, spec, quality=70)

        validation = cls.validate_bytes(img_bytes, spec)
        return img_bytes, validation

    @classmethod
    def generate_safe_zone_preview_bytes(
        cls, url: str, spec: PlatformSpec
    ) -> bytes:
        """Tải ảnh → crop → vẽ safe zone → trả về bytes JPEG để hiển thị."""
        img = cls.load_from_url(url)
        img = cls.smart_crop(img, spec)
        img = cls.add_safe_zone_overlay(img, spec)
        return cls.to_bytes(img, pil_format="JPEG", quality=85)


# ============================================================
# 3. THUMBNAIL APPROVAL GATE
# ============================================================

def _read_asset_tags(asset: dict) -> dict:
    """Parse trường tags (JSON string hoặc dict) → dict."""
    raw = asset.get("tags", {})
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except Exception:
            raw = {}
    if isinstance(raw, list):
        # Backward compat: tags là list string cũ
        return {"labels": raw, "lifecycle": {}, "thumbnail": {}, "history": []}
    return raw if isinstance(raw, dict) else {}


def _write_asset_tags(asset_id: int, workspace_id: int, tags: dict) -> bool:
    """Ghi tags dict trở lại vào DB (assets.tags)."""
    sql = _adapt_sql("UPDATE assets SET tags=? WHERE id=? AND workspace_id=?")
    with managed_connection() as conn:
        cur = conn.cursor()
        cur.execute(sql, (
            json.dumps(tags, ensure_ascii=False),
            asset_id, workspace_id
        ))
        return cur.rowcount > 0


class ThumbnailApprovalGate:
    """
    Kiểm tra và quản lý trạng thái approval của thumbnail.
    Dùng assets.tags (JSON) làm lifecycle store — KHÔNG thay đổi schema.
    """

    APPROVED_STATUSES = {"approved", "published"}

    @staticmethod
    def get_post_thumbnails(post_id: int, workspace_id: int) -> List[dict]:
        """
        Lấy tất cả assets là thumbnail của bài viết.
        Nhận biết qua tags.thumbnail.is_thumbnail == True.
        """
        all_assets = AssetModel.list_by_post(post_id, workspace_id=workspace_id)
        thumbnails = []
        for asset in all_assets:
            tags = _read_asset_tags(asset)
            if tags.get("thumbnail", {}).get("is_thumbnail"):
                asset["_tags"]      = tags
                asset["_lifecycle"] = tags.get("lifecycle", {})
                asset["_thumb"]     = tags.get("thumbnail", {})
                asset["_status"]    = tags.get("lifecycle", {}).get("status", "draft")
                thumbnails.append(asset)
        return thumbnails

    @staticmethod
    def check_thumbnail_approved(
        post_id: int, workspace_id: int,
    ) -> Dict[str, Any]:
        """
        Kiểm tra bài viết có thumbnail đã approve chưa.
        Returns: { ok, thumbnails, unapproved, message }
        """
        thumbnails = ThumbnailApprovalGate.get_post_thumbnails(post_id, workspace_id)

        if not thumbnails:
            return {
                "ok": False,
                "thumbnails": [],
                "unapproved": [],
                "message": "⚠️ Bài viết chưa có thumbnail. Hãy gắn thumbnail trước khi publish.",
            }

        unapproved = [
            t for t in thumbnails
            if t["_status"] not in ThumbnailApprovalGate.APPROVED_STATUSES
        ]

        if unapproved:
            names = ", ".join(u["name"] for u in unapproved)
            return {
                "ok": False,
                "thumbnails": thumbnails,
                "unapproved": unapproved,
                "message": f"⚠️ {len(unapproved)} thumbnail chưa approved: {names}",
            }

        return {
            "ok": True,
            "thumbnails": thumbnails,
            "unapproved": [],
            "message": f"✅ {len(thumbnails)} thumbnail đã được approve.",
        }

    @staticmethod
    def quick_approve(
        asset_id: int, workspace_id: int,
        approved_by: int, note: str = "",
    ) -> bool:
        """
        Approve thumbnail nhanh từ Publishing UI (dành cho admin/super_admin).
        Ghi lifecycle.status = 'approved' vào assets.tags.
        """
        asset = AssetModel.get_by_id(asset_id, workspace_id=workspace_id)
        if not asset:
            logger.warning(f"[ApprovalGate] Asset #{asset_id} không tồn tại.")
            return False

        tags = _read_asset_tags(asset)
        lc = tags.setdefault("lifecycle", {})
        lc["status"]      = "approved"
        lc["approved_by"] = approved_by
        lc["approved_at"] = datetime.now().isoformat()

        history = tags.setdefault("history", [])
        history.append({
            "action": "quick_approved_from_publishing",
            "by":     approved_by,
            "at":     datetime.now().isoformat(),
            "note":   note or "Quick-approve từ Publishing tab",
        })
        tags["history"] = history[-50:]

        ok = _write_asset_tags(asset_id, workspace_id, tags)
        if ok:
            logger.info(f"[AUDIT] Quick-approve thumbnail asset#{asset_id} bởi user#{approved_by}")
        return ok

    @staticmethod
    def reject_thumbnail(
        asset_id: int, workspace_id: int,
        rejected_by: int, reason: str = "",
    ) -> bool:
        """Reject thumbnail — trả về draft."""
        asset = AssetModel.get_by_id(asset_id, workspace_id=workspace_id)
        if not asset:
            return False
        tags = _read_asset_tags(asset)
        lc = tags.setdefault("lifecycle", {})
        lc["status"]      = "draft"
        lc["rejected_by"] = rejected_by
        lc["rejected_at"] = datetime.now().isoformat()

        history = tags.setdefault("history", [])
        history.append({
            "action": "rejected_from_publishing",
            "by":     rejected_by,
            "at":     datetime.now().isoformat(),
            "note":   reason or "Từ chối từ Publishing tab",
        })
        tags["history"] = history[-50:]
        return _write_asset_tags(asset_id, workspace_id, tags)


# ============================================================
# 4. PUBLISH READINESS CHECK
# ============================================================

def check_publish_readiness(
    post_id: int,
    workspace_id: int,
    platform: str,
    user_role: str,
    post_type: str = None,
    require_thumbnail: bool = True,
    require_post_approval: bool = True,
) -> Dict[str, Any]:
    """
    Kiểm tra tổng thể trước khi publish:
    1. Post đã được approve?      ← ApprovalModel
    2. Thumbnail đã tồn tại?      ← AssetModel
    3. Thumbnail đã approved?     ← ThumbnailApprovalGate
    4. Thumbnail hợp lệ spec?     ← ThumbnailProcessor.validate_url_quick()

    Returns:
        can_publish: bool
        issues: List[str]         — Lỗi chặn publish
        warnings: List[str]       — Cảnh báo (admin có thể bỏ qua)
        thumb_check: dict
        post_approved: bool
    """
    issues   = []
    warnings = []

    # --- Check 1: Post Approval ---
    post_approved = False
    if require_post_approval:
        latest_approval = ApprovalModel.get_latest_by_post(post_id, workspace_id=workspace_id)
        post_approved = latest_approval.get("status") == "approved"
        if not post_approved:
            if user_role in ("admin", "super_admin"):
                warnings.append("⚠️ Bài viết chưa qua quy trình phê duyệt (admin có thể bỏ qua)")
            else:
                issues.append("❌ Bài viết chưa được Admin approve")

    # --- Check 2 & 3: Thumbnail Approval ---
    thumb_check = {"ok": True, "thumbnails": [], "message": "Không yêu cầu thumbnail"}
    if require_thumbnail:
        thumb_check = ThumbnailApprovalGate.check_thumbnail_approved(post_id, workspace_id)
        if not thumb_check["ok"]:
            if user_role in ("admin", "super_admin"):
                warnings.append(thumb_check["message"] + " (admin có thể override)")
            else:
                issues.append(thumb_check["message"])

    # --- Check 4: Spec Validation (nếu thumbnail đã approved) ---
    spec_issues = []
    if thumb_check.get("thumbnails") and platform:
        spec = get_spec(platform, post_type)
        if spec:
            for thumb in thumb_check["thumbnails"]:
                url = thumb.get("url", "")
                if url:
                    val = ThumbnailProcessor.validate_url_quick(url, spec)
                    if val.get("ok") is False:
                        for iss in val.get("issues", []):
                            spec_issues.append(f"Thumbnail '{thumb['name']}': {iss}")
        if spec_issues:
            warnings.extend(spec_issues)  # Cảnh báo, không chặn hoàn toàn

    can_publish = len(issues) == 0
    return {
        "can_publish":   can_publish,
        "issues":        issues,
        "warnings":      warnings,
        "post_approved": post_approved,
        "thumb_check":   thumb_check,
        "spec_issues":   spec_issues,
    }


# ============================================================
# 5. PUBLISH QUEUE (Enriched)
# ============================================================

@dataclass
class PublishQueueItem:
    """Một item trong hàng chờ publish, đã được enriched với thumbnail info."""
    schedule_id:          int
    post_id:              int
    platform:             str
    post_type:            str
    scheduled_at:         str
    status:               str
    retry_count:          int
    error_message:        Optional[str]
    thumbnail_asset_id:   Optional[int]
    thumbnail_name:       Optional[str]
    thumbnail_url:        Optional[str]
    thumbnail_status:     str            # not_set | pending_approval | approved | ready | error
    thumbnail_size_mb:    float
    validation_ok:        Optional[bool]
    validation_issues:    List[str] = field(default_factory=list)


class PublishQueue:
    """
    Hàng chờ publish được làm giàu (enriched) với thông tin thumbnail.
    Wrap ScheduleModel + ThumbnailApprovalGate.
    """

    THUMB_STATUS_LABELS = {
        "not_set":          ("➕ Chưa gắn",    "#6B7280"),
        "pending_approval": ("⏳ Chờ duyệt",   "#F59E0B"),
        "approved":         ("✅ Approved",     "#10B981"),
        "ready":            ("🚀 Ready",        "#3B82F6"),
        "error":            ("❌ Lỗi",          "#EF4444"),
    }

    @staticmethod
    def get_enriched(
        workspace_id: int,
        status: str = "pending",
        limit: int = 50,
        quick_validate: bool = False,
    ) -> List[PublishQueueItem]:
        """
        Lấy danh sách schedule từ DB + enrich thumbnail metadata.
        quick_validate: nếu True, gọi validate_url_quick cho từng thumbnail.
        """
        schedules = ScheduleModel.list_by_workspace(
            workspace_id, status=status, limit=limit
        )
        items = []
        for sched in schedules:
            post_id  = sched["post_id"]
            platform = sched.get("platform", "facebook")

            thumbs = ThumbnailApprovalGate.get_post_thumbnails(post_id, workspace_id)
            thumb  = thumbs[0] if thumbs else None

            t_id, t_name, t_url, t_status = None, None, None, "not_set"
            t_size_mb, t_val_ok = 0.0, None
            t_issues: List[str] = []

            if thumb:
                t_id   = thumb["id"]
                t_name = thumb["name"]
                t_url  = thumb.get("url", "")
                lc_st  = thumb["_status"]
                spec   = get_spec(platform)

                if lc_st in ThumbnailApprovalGate.APPROVED_STATUSES:
                    t_status = "approved"
                    if quick_validate and spec and t_url:
                        try:
                            val = ThumbnailProcessor.validate_url_quick(t_url, spec)
                            t_size_mb = val.get("size_mb", 0)
                            t_val_ok  = val.get("ok")
                            t_issues  = val.get("issues", [])
                            t_status  = "ready" if (t_val_ok is not False) else "error"
                        except Exception as e:
                            logger.warning(f"[Queue] Validate thumbnail lỗi: {e}")
                else:
                    t_status = "pending_approval"

            items.append(PublishQueueItem(
                schedule_id=sched["id"],
                post_id=post_id,
                platform=platform,
                post_type=sched.get("post_type", PLATFORM_DEFAULT_TYPE.get(platform, "post")),
                scheduled_at=sched.get("scheduled_at", ""),
                status=sched.get("status", "pending"),
                retry_count=sched.get("retry_count", 0),
                error_message=sched.get("error_message"),
                thumbnail_asset_id=t_id,
                thumbnail_name=t_name,
                thumbnail_url=t_url,
                thumbnail_status=t_status,
                thumbnail_size_mb=t_size_mb,
                validation_ok=t_val_ok,
                validation_issues=t_issues,
            ))
        return items

    @staticmethod
    def get_summary(workspace_id: int) -> Dict[str, int]:
        """Thống kê nhanh hàng chờ theo thumbnail status."""
        items = PublishQueue.get_enriched(workspace_id, quick_validate=False)
        summary: Dict[str, int] = {
            "total":            len(items),
            "ready":            0,
            "approved":         0,
            "pending_approval": 0,
            "not_set":          0,
            "error":            0,
        }
        for item in items:
            ts = item.thumbnail_status
            if ts in summary:
                summary[ts] += 1
        return summary


# ============================================================
# 6. RETRY MANAGER
# ============================================================

class RetryManager:
    """
    Quản lý retry logic khi publish thất bại.
    Không gọi social API trực tiếp — chỉ cập nhật schedule status.
    """

    MAX_RETRIES = 3

    STRATEGIES = {
        1: ("Thử lại nguyên bản",        {"quality": 88, "use_thumbnail": True}),
        2: ("Nén ảnh thêm (quality=65)", {"quality": 65, "use_thumbnail": True}),
        3: ("Đăng chỉ text",             {"quality": 88, "use_thumbnail": False}),
    }

    # Lỗi không nên retry (auth / permission)
    NO_RETRY_KEYWORDS = [
        "access_token", "permission", "unauthorized",
        "403", "401", "invalid_token", "expired",
    ]

    @classmethod
    def should_retry(cls, retry_count: int, error_message: str = "") -> bool:
        if retry_count >= cls.MAX_RETRIES:
            return False
        err_lower = (error_message or "").lower()
        if any(kw in err_lower for kw in cls.NO_RETRY_KEYWORDS):
            return False
        return True

    @classmethod
    def get_strategy(cls, retry_count: int) -> Tuple[str, Dict[str, Any]]:
        """Trả về (label, config) cho lần retry tiếp theo."""
        next_attempt = retry_count + 1
        return cls.STRATEGIES.get(
            next_attempt,
            (f"Hết retry ({retry_count}/{cls.MAX_RETRIES})", {})
        )

    @classmethod
    def mark_for_retry(
        cls,
        schedule_id: int,
        error_message: str,
        workspace_id: int = None,
    ) -> bool:
        """
        Đánh dấu schedule để retry:
        - Nếu còn retry: increment retry_count, status=pending, ghi error
        - Nếu hết retry: status=failed, KHÔNG tăng retry_count thêm
        """
        sched = ScheduleModel.get_by_id(schedule_id, workspace_id=workspace_id)
        if not sched:
            return False

        retry_count = sched.get("retry_count", 0)

        if not cls.should_retry(retry_count, error_message):
            ScheduleModel.update_status(
                schedule_id, "failed",
                error_message=f"[MAX_RETRY_{retry_count}/{cls.MAX_RETRIES}] {error_message}",
                workspace_id=workspace_id,
            )
            logger.error(
                f"[RetryManager] Schedule #{schedule_id} FAILED — "
                f"hết retry ({retry_count}/{cls.MAX_RETRIES})"
            )
            return False

        # Tăng retry_count trước
        new_retry_count = ScheduleModel.increment_retry(schedule_id, workspace_id=workspace_id)
        strategy_label, _ = cls.get_strategy(retry_count)
        new_error_msg = (
            f"[Retry {new_retry_count}/{cls.MAX_RETRIES} · {strategy_label}] "
            f"{error_message}"
        )
        ScheduleModel.update_status(
            schedule_id, "pending",
            error_message=new_error_msg,
            workspace_id=workspace_id,
        )
        logger.info(
            f"[RetryManager] Schedule #{schedule_id} → "
            f"Retry {new_retry_count}/{cls.MAX_RETRIES} ({strategy_label})"
        )
        return True

    @classmethod
    def get_thumbnail_config_for_retry(
        cls,
        retry_count: int,
        original_url: str,
        spec: Optional[PlatformSpec],
    ) -> Dict[str, Any]:
        """
        Trả về config xử lý thumbnail cho lần retry:
        - retry 0→1: quality cao, có thumbnail
        - retry 1→2: quality thấp, có thumbnail
        - retry 2→3: không thumbnail
        """
        _, config = cls.get_strategy(retry_count)
        return {
            "use_thumbnail": config.get("use_thumbnail", True),
            "quality":       config.get("quality", 88),
            "url":           original_url if config.get("use_thumbnail") else None,
            "spec":          spec,
        }


# ============================================================
# 7. PLATFORM MOCK-UP HTML RENDERER
# ============================================================

def build_platform_mockup_html(
    platform: str,
    content: str,
    thumbnail_url: str = None,
    page_name: str = "Tên Page / Brand",
) -> str:
    """
    Trả về HTML string mô phỏng card bài đăng của từng nền tảng.
    Pure HTML/CSS — không gọi API, chạy trực tiếp trong st.markdown().
    """
    platform_key = PLATFORM_ALIASES.get(platform.lower().strip(), platform.lower())
    preview_text = content[:220] + "…" if len(content) > 220 else content

    if thumbnail_url:
        thumb_html = (
            f'<img src="{thumbnail_url}" '
            f'style="width:100%;display:block;border-radius:4px;margin-top:6px" '
            f'onerror="this.style.display=\'none\'">'
        )
    else:
        thumb_html = (
            '<div style="width:100%;height:110px;background:#e9ecef;'
            'border-radius:4px;display:flex;align-items:center;'
            'justify-content:center;margin-top:6px;color:#aaa;font-size:13px">'
            '🖼️ Chưa có thumbnail</div>'
        )

    if platform_key == "facebook":
        return f"""
<div style="font-family:'Segoe UI',system-ui,sans-serif;max-width:460px;
            border:1px solid #ddd;border-radius:8px;overflow:hidden;
            background:#fff;box-shadow:0 1px 4px rgba(0,0,0,.12)">
  <div style="padding:12px 16px;display:flex;align-items:center;gap:10px">
    <div style="width:40px;height:40px;background:#1877f2;border-radius:50%;
                display:flex;align-items:center;justify-content:center;
                color:#fff;font-weight:700;font-size:17px;flex-shrink:0">f</div>
    <div>
      <div style="font-weight:700;color:#050505;font-size:15px">{page_name}</div>
      <div style="font-size:12px;color:#65676b">Vừa xong · 🌐</div>
    </div>
  </div>
  <div style="padding:0 16px 8px;color:#050505;font-size:15px;line-height:1.45">{preview_text}</div>
  {thumb_html}
  <div style="padding:8px 16px;border-top:1px solid #e4e6ea;
              display:flex;gap:16px;color:#65676b;font-size:13px;font-weight:600">
    <span>👍 Thích</span><span>💬 Bình luận</span><span>↗️ Chia sẻ</span>
  </div>
</div>"""

    elif platform_key == "linkedin":
        return f"""
<div style="font-family:'Segoe UI',system-ui,sans-serif;max-width:500px;
            border:1px solid #e0dfde;border-radius:8px;overflow:hidden;
            background:#fff;box-shadow:0 1px 4px rgba(0,0,0,.08)">
  <div style="padding:12px 16px;display:flex;align-items:center;gap:10px">
    <div style="width:48px;height:48px;background:#0a66c2;border-radius:50%;
                display:flex;align-items:center;justify-content:center;
                color:#fff;font-weight:700;font-size:18px;flex-shrink:0">in</div>
    <div>
      <div style="font-weight:700;color:#000;font-size:15px">{page_name}</div>
      <div style="font-size:12px;color:#666">1st · Vừa xong</div>
    </div>
  </div>
  <div style="padding:0 16px 8px;color:#000;font-size:14px;line-height:1.45">{preview_text}</div>
  {thumb_html}
  <div style="padding:8px 16px;border-top:1px solid #e0dfde;
              display:flex;gap:14px;color:#666;font-size:12px;font-weight:600">
    <span>👍 Like</span><span>💬 Comment</span><span>🔄 Repost</span><span>✉️ Send</span>
  </div>
</div>"""

    elif platform_key == "zalo":
        return f"""
<div style="font-family:'Roboto',system-ui,sans-serif;max-width:400px;
            border:1px solid #ddd;border-radius:12px;overflow:hidden;
            background:#fff;box-shadow:0 2px 8px rgba(0,0,0,.12)">
  <div style="background:#0068ff;padding:10px 16px;
              display:flex;align-items:center;gap:10px">
    <div style="width:36px;height:36px;background:#fff;border-radius:50%;
                display:flex;align-items:center;justify-content:center;
                font-weight:700;color:#0068ff;font-size:14px;flex-shrink:0">OA</div>
    <div style="color:#fff;font-weight:600;font-size:14px">{page_name}</div>
  </div>
  {thumb_html}
  <div style="padding:10px 14px">
    <div style="font-weight:700;margin-bottom:4px;color:#111;font-size:14px">Tiêu đề bài viết</div>
    <div style="color:#555;font-size:13px;line-height:1.45">{preview_text}</div>
    <div style="color:#0068ff;font-size:12px;margin-top:8px;text-align:right;font-weight:600">
      Xem thêm →
    </div>
  </div>
</div>"""

    else:
        return f"<div style='padding:12px;border:1px solid #ddd;border-radius:8px'>{preview_text}</div>"
