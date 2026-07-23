# 🖼️ MEDIA LIBRARY UPGRADE — Thiết Kế Mở Rộng

> **Dự án**: AI_Agent_Content_AutoPos  
> **Phiên bản hiện tại**: Schema V2 (14 bảng)  
> **Tài liệu này**: Thiết kế mở rộng Media Library — KHÔNG thay đổi database  
> **Ngày tạo**: 2026-07-12  
> **Trạng thái**: Đề xuất thiết kế (Design Proposal)

---

## 📌 1. Tổng Quan

### 1.1 Vấn đề hiện tại

Bảng `assets` trong Schema V2 chỉ lưu metadata cơ bản:

```
assets: id, workspace_id, post_id, name, file_type, url,
        storage_path, size_bytes, mime_type, alt_text,
        tags (JSON), uploaded_by, created_at
```

**Các điểm thiếu sót:**

| Tính năng | Hiện tại | Cần có |
|-----------|----------|--------|
| Trạng thái vòng đời | ❌ | Version / Draft / Approved / Published / Archived |
| Quản lý thumbnail | ❌ | Upload, preview, approve riêng cho thumbnail |
| Tìm kiếm & Filter | ❌ | Full-text search, filter đa tiêu chí |
| Nhân bản (Duplicate) | ❌ | Clone asset sang post/campaign khác |
| Yêu thích (Favorite) | ❌ | Đánh dấu & lọc theo favorite |
| Lịch sử thay đổi | ❌ | Audit trail mọi hành động trên asset |
| Tag & Phân loại | ❌ | Phân cấp tag + taxonomy |
| Liên kết Campaign | ❌ | Gắn asset vào campaign cụ thể |
| Liên kết Project | ❌ | Gắn asset vào project |
| Workspace scope | Cơ bản | Phân quyền đa-workspace đầy đủ |

### 1.2 Nguyên tắc thiết kế

- ✅ **Không thay đổi database schema** — Mọi mở rộng được thực hiện qua:
  - **Cột `tags` (JSON)** — lưu metadata phong phú
  - **Service layer** — logic nghiệp vụ mới
  - **UI layer** — giao diện Media Library hoàn chỉnh
  - **In-memory / file-based state** — cho draft/history session
- ✅ Tương thích hoàn toàn với SQLite và PostgreSQL
- ✅ Tuân thủ RBAC hiện có (super_admin / admin / editor / viewer)

---

## 📐 2. Kiến Trúc Mở Rộng (Không Đổi DB)

### 2.1 Chiến lược lưu metadata mở rộng vào cột `tags` (JSON)

Cột `tags` hiện là `TEXT` (SQLite) hoặc `JSONB` (PostgreSQL).  
Chúng ta sẽ dùng nó như một **metadata envelope** với cấu trúc chuẩn:

```json
{
  "labels": ["banner", "hero", "youtube-thumbnail"],
  "lifecycle": {
    "status": "approved",
    "version": 3,
    "is_favorite": true,
    "is_archived": false,
    "approved_by": 12,
    "approved_at": "2026-07-12T10:00:00",
    "published_at": "2026-07-12T12:00:00",
    "archived_at": null
  },
  "relations": {
    "campaign_ids": [5, 8],
    "project_ids": [2],
    "duplicate_of": null,
    "original_id": null
  },
  "history": [
    {
      "action": "uploaded",
      "by": 7,
      "at": "2026-07-10T09:00:00",
      "note": "Upload thumbnail ban đầu"
    },
    {
      "action": "status_changed",
      "from": "draft",
      "to": "approved",
      "by": 12,
      "at": "2026-07-12T10:00:00",
      "note": "Đã duyệt thumbnail campaign Q3"
    }
  ],
  "thumbnail": {
    "is_thumbnail": true,
    "width": 1280,
    "height": 720,
    "aspect_ratio": "16:9",
    "platform_variants": {
      "facebook": "https://...",
      "youtube": "https://...",
      "instagram": "https://..."
    },
    "color_palette": ["#FF6B35", "#004E89", "#FFFFFF"],
    "dominant_color": "#FF6B35"
  }
}
```

> **Tại sao an toàn?** Cột `tags` đã là JSON/TEXT trong schema, không cần ALTER TABLE.  
> `AssetModel.create()` và các method hiện tại đã nhận/serialize `tags` dưới dạng dict/list.

---

## 🏗️ 3. Thiết Kế Service Layer

### 3.1 `services/media_library_service.py` — Service mới

```python
"""services/media_library_service.py
Media Library Service — Quản lý vòng đời, version, metadata mở rộng.
Không thay đổi database schema — dùng cột tags (JSON) làm metadata store.
"""

import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from database.models.assets import AssetModel
from config.config import logger


# ============================================================
# CONSTANTS — Vòng đời Asset
# ============================================================

class AssetStatus:
    DRAFT     = "draft"
    APPROVED  = "approved"
    PUBLISHED = "published"
    ARCHIVED  = "archived"

    ALL = [DRAFT, APPROVED, PUBLISHED, ARCHIVED]
    VALID_TRANSITIONS = {
        DRAFT:     [APPROVED, ARCHIVED],
        APPROVED:  [PUBLISHED, DRAFT, ARCHIVED],
        PUBLISHED: [ARCHIVED],
        ARCHIVED:  [DRAFT],
    }

    LABELS = {
        DRAFT:     ("📝 Draft",     "#FFA500"),
        APPROVED:  ("✅ Approved",  "#28A745"),
        PUBLISHED: ("🚀 Published", "#007BFF"),
        ARCHIVED:  ("🗄️ Archived", "#6C757D"),
    }

    @classmethod
    def can_transition(cls, current: str, target: str) -> bool:
        return target in cls.VALID_TRANSITIONS.get(current, [])


# ============================================================
# META HELPERS
# ============================================================

def _read_meta(asset: dict) -> dict:
    """Đọc metadata từ trường tags JSON."""
    raw = asset.get("tags", [])
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except Exception:
            raw = {}
    if isinstance(raw, list):
        # Backward-compat: nếu tags là list strings cũ → đổi sang dict
        return {"labels": raw, "lifecycle": {}, "relations": {}, "history": [], "thumbnail": {}}
    return raw if isinstance(raw, dict) else {}


def _write_meta(asset_id: int, workspace_id: int, meta: dict):
    """Ghi metadata trở lại vào assets.tags (dùng UPDATE trực tiếp)."""
    from database.connection import managed_connection, _adapt_sql
    sql = _adapt_sql("UPDATE assets SET tags=? WHERE id=? AND workspace_id=?")
    with managed_connection() as conn:
        cur = conn.cursor()
        cur.execute(sql, (json.dumps(meta, ensure_ascii=False), asset_id, workspace_id))
    return cur.rowcount > 0


def _add_history_entry(meta: dict, action: str, by: int,
                       note: str = "", extra: dict = None) -> dict:
    """Thêm 1 entry vào lịch sử của meta."""
    entry = {
        "action": action,
        "by": by,
        "at": datetime.now().isoformat(),
        "note": note,
    }
    if extra:
        entry.update(extra)
    history = meta.get("history", [])
    history.append(entry)
    meta["history"] = history[-50:]   # Giữ tối đa 50 bản ghi
    return meta


# ============================================================
# LIFECYCLE MANAGEMENT
# ============================================================

class MediaLibraryService:

    # ── Status / Lifecycle ──────────────────────────────────

    @staticmethod
    def get_status(asset: dict) -> str:
        meta = _read_meta(asset)
        return meta.get("lifecycle", {}).get("status", AssetStatus.DRAFT)

    @staticmethod
    def set_status(asset_id: int, workspace_id: int, new_status: str,
                   changed_by: int, note: str = "") -> bool:
        """Chuyển trạng thái lifecycle. Kiểm tra transition hợp lệ."""
        asset = AssetModel.get_by_id(asset_id)
        if not asset:
            return False

        meta = _read_meta(asset)
        lc = meta.setdefault("lifecycle", {})
        current = lc.get("status", AssetStatus.DRAFT)

        if not AssetStatus.can_transition(current, new_status):
            logger.warning(f"[MediaLib] Không thể chuyển {current} → {new_status}")
            return False

        lc["status"] = new_status
        lc[f"{new_status}_at"] = datetime.now().isoformat()
        lc[f"{new_status}_by"] = changed_by

        _add_history_entry(meta, action="status_changed", by=changed_by,
                           note=note or f"Chuyển {current} → {new_status}",
                           extra={"from": current, "to": new_status})

        return _write_meta(asset_id, workspace_id, meta)

    @staticmethod
    def approve(asset_id: int, workspace_id: int, approved_by: int,
                note: str = "") -> bool:
        return MediaLibraryService.set_status(
            asset_id, workspace_id, AssetStatus.APPROVED, approved_by, note)

    @staticmethod
    def publish(asset_id: int, workspace_id: int, published_by: int,
                note: str = "") -> bool:
        return MediaLibraryService.set_status(
            asset_id, workspace_id, AssetStatus.PUBLISHED, published_by, note)

    @staticmethod
    def archive(asset_id: int, workspace_id: int, archived_by: int,
                note: str = "") -> bool:
        return MediaLibraryService.set_status(
            asset_id, workspace_id, AssetStatus.ARCHIVED, archived_by, note)

    @staticmethod
    def revert_to_draft(asset_id: int, workspace_id: int, by: int,
                        note: str = "") -> bool:
        return MediaLibraryService.set_status(
            asset_id, workspace_id, AssetStatus.DRAFT, by, note)

    # ── Version ────────────────────────────────────────────

    @staticmethod
    def bump_version(asset_id: int, workspace_id: int,
                     changed_by: int, note: str = "") -> int:
        """Tăng version số, thêm lịch sử."""
        asset = AssetModel.get_by_id(asset_id)
        if not asset:
            return -1
        meta = _read_meta(asset)
        lc = meta.setdefault("lifecycle", {})
        ver = lc.get("version", 1) + 1
        lc["version"] = ver
        _add_history_entry(meta, "version_bumped", changed_by,
                           note or f"Cập nhật lên v{ver}")
        _write_meta(asset_id, workspace_id, meta)
        return ver

    @staticmethod
    def get_version(asset: dict) -> int:
        meta = _read_meta(asset)
        return meta.get("lifecycle", {}).get("version", 1)

    # ── Favorite ───────────────────────────────────────────

    @staticmethod
    def toggle_favorite(asset_id: int, workspace_id: int,
                        by: int) -> bool:
        asset = AssetModel.get_by_id(asset_id)
        if not asset:
            return False
        meta = _read_meta(asset)
        lc = meta.setdefault("lifecycle", {})
        lc["is_favorite"] = not lc.get("is_favorite", False)
        action = "favorited" if lc["is_favorite"] else "unfavorited"
        _add_history_entry(meta, action, by)
        _write_meta(asset_id, workspace_id, meta)
        return lc["is_favorite"]

    @staticmethod
    def is_favorite(asset: dict) -> bool:
        meta = _read_meta(asset)
        return bool(meta.get("lifecycle", {}).get("is_favorite", False))

    # ── Duplicate ──────────────────────────────────────────

    @staticmethod
    def duplicate(asset_id: int, workspace_id: int,
                  new_name: str, created_by: int,
                  target_post_id: int = None,
                  target_campaign_ids: List[int] = None,
                  target_project_ids: List[int] = None) -> int:
        """Nhân bản asset — tạo bản copy với meta mới, status=draft."""
        original = AssetModel.get_by_id(asset_id)
        if not original:
            return -1

        orig_meta = _read_meta(original)
        new_meta = {
            "labels": list(orig_meta.get("labels", [])),
            "lifecycle": {
                "status": AssetStatus.DRAFT,
                "version": 1,
                "is_favorite": False,
                "is_archived": False,
            },
            "relations": {
                "campaign_ids": target_campaign_ids or [],
                "project_ids": target_project_ids or [],
                "duplicate_of": asset_id,
                "original_id": orig_meta.get("relations", {}).get("original_id") or asset_id,
            },
            "history": [],
            "thumbnail": dict(orig_meta.get("thumbnail", {})),
        }
        _add_history_entry(new_meta, "created_as_duplicate", created_by,
                           f"Nhân bản từ asset #{asset_id}")

        new_id = AssetModel.create(
            workspace_id=workspace_id,
            name=new_name or f"Copy of {original['name']}",
            url=original["url"],
            file_type=original["file_type"],
            post_id=target_post_id,
            storage_path=original.get("storage_path", ""),
            size_bytes=original.get("size_bytes", 0),
            mime_type=original.get("mime_type", ""),
            alt_text=original.get("alt_text", ""),
            tags=new_meta,
            uploaded_by=created_by,
        )
        return new_id

    # ── History ────────────────────────────────────────────

    @staticmethod
    def get_history(asset: dict) -> List[dict]:
        meta = _read_meta(asset)
        return list(reversed(meta.get("history", [])))

    @staticmethod
    def add_note(asset_id: int, workspace_id: int,
                 by: int, note: str) -> bool:
        asset = AssetModel.get_by_id(asset_id)
        if not asset:
            return False
        meta = _read_meta(asset)
        _add_history_entry(meta, "note_added", by, note)
        return _write_meta(asset_id, workspace_id, meta)

    # ── Tags / Labels ──────────────────────────────────────

    @staticmethod
    def set_labels(asset_id: int, workspace_id: int,
                   labels: List[str], by: int) -> bool:
        asset = AssetModel.get_by_id(asset_id)
        if not asset:
            return False
        meta = _read_meta(asset)
        old = meta.get("labels", [])
        meta["labels"] = [t.strip().lower() for t in labels if t.strip()]
        _add_history_entry(meta, "labels_updated", by,
                           f"Tags: {old} → {meta['labels']}")
        return _write_meta(asset_id, workspace_id, meta)

    @staticmethod
    def get_labels(asset: dict) -> List[str]:
        meta = _read_meta(asset)
        return meta.get("labels", [])

    # ── Campaign / Project relations ───────────────────────

    @staticmethod
    def link_to_campaign(asset_id: int, workspace_id: int,
                         campaign_id: int, by: int) -> bool:
        asset = AssetModel.get_by_id(asset_id)
        if not asset:
            return False
        meta = _read_meta(asset)
        rels = meta.setdefault("relations", {})
        ids = rels.get("campaign_ids", [])
        if campaign_id not in ids:
            ids.append(campaign_id)
        rels["campaign_ids"] = ids
        _add_history_entry(meta, "linked_campaign", by,
                           f"Gắn vào Campaign #{campaign_id}")
        return _write_meta(asset_id, workspace_id, meta)

    @staticmethod
    def unlink_from_campaign(asset_id: int, workspace_id: int,
                             campaign_id: int, by: int) -> bool:
        asset = AssetModel.get_by_id(asset_id)
        if not asset:
            return False
        meta = _read_meta(asset)
        rels = meta.setdefault("relations", {})
        rels["campaign_ids"] = [i for i in rels.get("campaign_ids", [])
                                if i != campaign_id]
        _add_history_entry(meta, "unlinked_campaign", by,
                           f"Gỡ khỏi Campaign #{campaign_id}")
        return _write_meta(asset_id, workspace_id, meta)

    @staticmethod
    def link_to_project(asset_id: int, workspace_id: int,
                        project_id: int, by: int) -> bool:
        asset = AssetModel.get_by_id(asset_id)
        if not asset:
            return False
        meta = _read_meta(asset)
        rels = meta.setdefault("relations", {})
        ids = rels.get("project_ids", [])
        if project_id not in ids:
            ids.append(project_id)
        rels["project_ids"] = ids
        _add_history_entry(meta, "linked_project", by,
                           f"Gắn vào Project #{project_id}")
        return _write_meta(asset_id, workspace_id, meta)

    # ── Thumbnail metadata ─────────────────────────────────

    @staticmethod
    def set_thumbnail_meta(asset_id: int, workspace_id: int,
                           width: int, height: int,
                           platform_variants: dict = None,
                           color_palette: list = None,
                           dominant_color: str = None,
                           by: int = None) -> bool:
        asset = AssetModel.get_by_id(asset_id)
        if not asset:
            return False
        meta = _read_meta(asset)
        thumb = meta.setdefault("thumbnail", {})
        thumb["is_thumbnail"] = True
        thumb["width"] = width
        thumb["height"] = height
        if width and height and height > 0:
            from math import gcd
            g = gcd(width, height)
            thumb["aspect_ratio"] = f"{width//g}:{height//g}"
        if platform_variants:
            thumb["platform_variants"] = platform_variants
        if color_palette:
            thumb["color_palette"] = color_palette
        if dominant_color:
            thumb["dominant_color"] = dominant_color
        if by:
            _add_history_entry(meta, "thumbnail_meta_updated", by,
                               f"Kích thước {width}x{height}")
        return _write_meta(asset_id, workspace_id, meta)

    @staticmethod
    def is_thumbnail(asset: dict) -> bool:
        meta = _read_meta(asset)
        return bool(meta.get("thumbnail", {}).get("is_thumbnail", False))

    @staticmethod
    def get_thumbnail_meta(asset: dict) -> dict:
        meta = _read_meta(asset)
        return meta.get("thumbnail", {})

    # ── Search & Filter ────────────────────────────────────

    @staticmethod
    def search_and_filter(
        workspace_id: int,
        query: str = "",
        file_type: str = None,
        status: str = None,
        labels: List[str] = None,
        is_favorite: bool = None,
        is_thumbnail: bool = None,
        campaign_id: int = None,
        project_id: int = None,
        sort_by: str = "created_at",       # created_at | name | size_bytes | status
        sort_order: str = "desc",          # asc | desc
        page: int = 1,
        page_size: int = 24,
    ) -> Dict[str, Any]:
        """
        Tìm kiếm & lọc assets theo nhiều tiêu chí.
        Tất cả xử lý in-memory (không cần ALTER TABLE).
        """
        all_assets = AssetModel.list_by_workspace(workspace_id, file_type)

        results = []
        for asset in all_assets:
            meta = _read_meta(asset)
            lc = meta.get("lifecycle", {})
            rels = meta.get("relations", {})
            thumb = meta.get("thumbnail", {})
            asset_labels = meta.get("labels", [])
            asset_status = lc.get("status", AssetStatus.DRAFT)

            # ── Filter: trạng thái
            if status and asset_status != status:
                continue

            # ── Filter: favorite
            if is_favorite is not None:
                if bool(lc.get("is_favorite", False)) != is_favorite:
                    continue

            # ── Filter: thumbnail
            if is_thumbnail is not None:
                if bool(thumb.get("is_thumbnail", False)) != is_thumbnail:
                    continue

            # ── Filter: campaign
            if campaign_id is not None:
                if campaign_id not in rels.get("campaign_ids", []):
                    continue

            # ── Filter: project
            if project_id is not None:
                if project_id not in rels.get("project_ids", []):
                    continue

            # ── Filter: labels (AND logic)
            if labels:
                if not all(lbl.lower() in [x.lower() for x in asset_labels]
                           for lbl in labels):
                    continue

            # ── Filter: full-text search
            if query:
                q = query.lower()
                searchable = " ".join([
                    asset.get("name", ""),
                    asset.get("alt_text", ""),
                    asset.get("mime_type", ""),
                    " ".join(asset_labels),
                ]).lower()
                if q not in searchable:
                    continue

            # Đính kèm meta đã parse
            asset["_meta"]   = meta
            asset["_status"] = asset_status
            asset["_version"] = lc.get("version", 1)
            asset["_favorite"] = bool(lc.get("is_favorite", False))
            asset["_is_thumbnail"] = bool(thumb.get("is_thumbnail", False))
            asset["_labels"] = asset_labels
            results.append(asset)

        # ── Sort
        reverse = sort_order == "desc"
        key_map = {
            "created_at": lambda a: a.get("created_at", ""),
            "name":       lambda a: a.get("name", "").lower(),
            "size_bytes": lambda a: a.get("size_bytes") or 0,
            "status":     lambda a: a.get("_status", ""),
        }
        sort_fn = key_map.get(sort_by, key_map["created_at"])
        results.sort(key=sort_fn, reverse=reverse)

        # ── Phân trang
        total = len(results)
        start = (page - 1) * page_size
        end = start + page_size
        paginated = results[start:end]

        return {
            "items": paginated,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": max(1, (total + page_size - 1) // page_size),
        }

    # ── Workspace-wide stats ───────────────────────────────

    @staticmethod
    def get_stats(workspace_id: int) -> dict:
        all_assets = AssetModel.list_by_workspace(workspace_id)
        stats = {
            "total": len(all_assets),
            "by_status": {s: 0 for s in AssetStatus.ALL},
            "by_type": {},
            "favorites": 0,
            "thumbnails": 0,
            "total_size_mb": 0.0,
        }
        for asset in all_assets:
            meta = _read_meta(asset)
            lc = meta.get("lifecycle", {})
            status = lc.get("status", AssetStatus.DRAFT)
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1

            ft = asset.get("file_type", "other")
            stats["by_type"][ft] = stats["by_type"].get(ft, 0) + 1

            if lc.get("is_favorite"):
                stats["favorites"] += 1
            if meta.get("thumbnail", {}).get("is_thumbnail"):
                stats["thumbnails"] += 1

            sz = asset.get("size_bytes") or 0
            stats["total_size_mb"] += sz / (1024 * 1024)

        stats["total_size_mb"] = round(stats["total_size_mb"], 2)
        return stats
```

---

## 🗂️ 4. Cấu Trúc Dữ Liệu Chi Tiết

### 4.1 Asset Lifecycle State Machine

```
          ┌─────────────────────────────────────────────┐
          │                                             │
          ▼                                             │
      [DRAFT] ──────── approve ──────► [APPROVED]       │
          ▲                               │             │
          │                         publish │           │
          │                               ▼             │
          │               ┌────────── [PUBLISHED]       │
          │               │               │             │
          └── revert ─────┘           archive │         │
                                           ▼             │
                                      [ARCHIVED] ────────┘
                                          │
                                    revert_to_draft
                                          │
                                          ▼
                                       [DRAFT]
```

**Quy tắc chuyển trạng thái:**

| Từ | Đến | Điều kiện RBAC |
|----|-----|----------------|
| `draft` | `approved` | `admin` hoặc `super_admin` |
| `draft` | `archived` | `editor` trở lên |
| `approved` | `published` | `admin` hoặc `super_admin` |
| `approved` | `draft` | `editor` trở lên |
| `approved` | `archived` | `editor` trở lên |
| `published` | `archived` | `admin` hoặc `super_admin` |
| `archived` | `draft` | `admin` hoặc `super_admin` |

### 4.2 Version Control Logic

```
Asset ID #42
├── v1 (uploaded)          → Draft
├── v2 (content updated)   → Draft
├── v3 (approved)          → Approved  ← approved_by: user#12
└── v4 (thumbnail updated) → Approved  ← bump_version()
```

- Version không tạo bản sao file — chỉ tăng số đếm trong metadata
- Mỗi lần `bump_version()` ghi entry vào `history`
- Để duy trì file snapshot thực sự → dùng `duplicate()` với `original_id`

### 4.3 Schema Metadata Envelope (`tags` field)

```
tags (JSON)
│
├── labels: List[str]                 ← #hashtag, keyword tự do
│
├── lifecycle
│   ├── status: str                   ← draft|approved|published|archived
│   ├── version: int                  ← tăng dần từ 1
│   ├── is_favorite: bool
│   ├── approved_by: int (user_id)
│   ├── approved_at: ISO datetime
│   ├── published_at: ISO datetime
│   └── archived_at: ISO datetime
│
├── relations
│   ├── campaign_ids: List[int]       ← FK → campaigns.id
│   ├── project_ids: List[int]        ← FK → projects.id
│   ├── duplicate_of: int|null        ← ID asset gốc nếu là bản sao
│   └── original_id: int|null         ← ID gốc sâu nhất trong chuỗi
│
├── history: List[HistoryEntry]       ← tối đa 50 entries
│   └── {action, by, at, note, ...}
│
└── thumbnail
    ├── is_thumbnail: bool
    ├── width: int
    ├── height: int
    ├── aspect_ratio: str             ← "16:9", "1:1", etc.
    ├── platform_variants: dict       ← {facebook: url, youtube: url}
    ├── color_palette: List[str]      ← hex colors
    └── dominant_color: str
```

---

## 🖥️ 5. Thiết Kế Giao Diện (UI Layer)

### 5.1 File mới: `ui/tab_media_library.py`

#### Layout tổng thể

```
┌─────────────────────────────────────────────────────────────────────┐
│  🖼️ MEDIA LIBRARY                        [+ Upload] [⚙️ Settings]  │
├──────────┬──────────────────────────────────────────────────────────┤
│ SIDEBAR  │  MAIN PANEL                                              │
│          │                                                          │
│ 🔍 Search│  [📝 All] [✅ Approved] [🚀 Published] [🗄️ Archived]    │
│          │  [❤️ Favorites] [🖼️ Thumbnails Only]                    │
│ Filter:  │  ─────────────────────────────────────────────────────  │
│ Type ▼   │  Sort: Mới nhất ▼    View: [⊞ Grid] [≡ List]           │
│ Status ▼ │                                                          │
│ Campaign▼│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐│
│ Project ▼│  │ img  │ │ img  │ │ img  │ │ img  │ │ img  │ │ img  ││
│ Labels ▼ │  │      │ │      │ │      │ │      │ │      │ │      ││
│          │  │✅ v3 │ │📝 v1 │ │🚀 v2 │ │✅ v1 │ │📝 v2 │ │🗄️ v1││
│ [Reset]  │  │❤️    │ │      │ │      │ │❤️    │ │      │ │      ││
│          │  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘│
│          │                                                          │
│          │  Hiển thị 1–24 / 87 kết quả    [< 1 2 3 4 >]           │
└──────────┴──────────────────────────────────────────────────────────┘
```

#### Asset Detail Panel (Modal / Sidebar mở rộng)

```
┌──────────────────────────────────────────────────────┐
│ 🖼️ thumbnail_hero_q3.jpg                [✕ Đóng]    │
├──────────────────────────────────────────────────────┤
│                                                      │
│         [Preview Image / Video]                      │
│                    1280 × 720 | 16:9                 │
│                                                      │
├──────────────────────────────────────────────────────┤
│ Trạng thái:  [✅ Approved]  →  [Publish] [Archive]   │
│ Phiên bản:   v3  [+ Bump Version]                    │
│ Yêu thích:   ❤️ [Bỏ yêu thích]                      │
├──────────────────────────────────────────────────────┤
│ THÔNG TIN                                            │
│ ├── Tên: thumbnail_hero_q3.jpg                       │
│ ├── Loại: image/jpeg | 245 KB                        │
│ ├── Upload bởi: Nguyễn Văn A                         │
│ └── Tạo lúc: 10/07/2026 09:00                        │
├──────────────────────────────────────────────────────┤
│ TAGS / LABELS                                        │
│ [banner] [hero] [q3-2026] [+ Thêm tag]               │
├──────────────────────────────────────────────────────┤
│ LIÊN KẾT                                             │
│ Campaign: [Campaign Q3 Marketing] [+ Thêm]           │
│ Project:  [Website Relaunch 2026] [+ Thêm]           │
├──────────────────────────────────────────────────────┤
│ THUMBNAIL                                            │
│ Platform variants:                                   │
│   • Facebook: [🔗 Link] [✏️ Sửa]                    │
│   • YouTube:  [🔗 Link] [✏️ Sửa]                    │
│   • Instagram: — [+ Thêm]                            │
│ Màu chủ đạo: ■ #FF6B35  Palette: ■■■                │
├──────────────────────────────────────────────────────┤
│ LỊCH SỬ THAY ĐỔI              [🔽 Xem tất cả 8]     │
│ ─────────────────────────────────────────────────    │
│ ✅ 12/07 10:00 · Approved bởi Trần Thị B             │
│    "Đã duyệt thumbnail campaign Q3"                  │
│ 📤 11/07 15:30 · Version bumped v2→v3 bởi Admin     │
│ 📝 10/07 09:00 · Uploaded bởi Nguyễn Văn A           │
├──────────────────────────────────────────────────────┤
│ [📋 Nhân bản]  [✏️ Sửa tên]  [🗑️ Xóa]              │
└──────────────────────────────────────────────────────┘
```

### 5.2 Code skeleton: `ui/tab_media_library.py`

```python
"""ui/tab_media_library.py — Tab Media Library mở rộng."""

import streamlit as st
from services.media_library_service import (
    MediaLibraryService, AssetStatus, _read_meta
)
from database.models.assets import AssetModel
from database.models.campaigns import CampaignModel
from database.models.projects import ProjectModel
from core.rbac import require_role
from config.config import logger


def render_tab_media_library():
    st.markdown("## 🖼️ Media Library")

    workspace_id = st.session_state.get("workspace_id", 1)
    user_id      = st.session_state.get("user_id", 1)
    user_role    = st.session_state.get("role", "viewer")

    # ── Stats bar ──────────────────────────────────────────
    stats = MediaLibraryService.get_stats(workspace_id)
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("📁 Tổng", stats["total"])
    c2.metric("📝 Draft", stats["by_status"]["draft"])
    c3.metric("✅ Approved", stats["by_status"]["approved"])
    c4.metric("🚀 Published", stats["by_status"]["published"])
    c5.metric("❤️ Favorites", stats["favorites"])

    st.divider()

    # ── Layout: sidebar filter + main panel ───────────────
    with st.sidebar:
        st.markdown("### 🔍 Tìm kiếm & Lọc")
        query = st.text_input("Tìm kiếm", placeholder="Nhập tên, tag...")
        file_type = st.selectbox(
            "Loại file", ["Tất cả", "image", "video", "document", "audio"]
        )
        status_filter = st.selectbox(
            "Trạng thái", ["Tất cả"] + AssetStatus.ALL
        )
        only_favorites  = st.checkbox("❤️ Chỉ Favorites")
        only_thumbnails = st.checkbox("🖼️ Chỉ Thumbnails")

        # Campaign filter
        campaigns = CampaignModel.list_by_workspace(workspace_id)
        camp_names = {c["name"]: c["id"] for c in campaigns}
        camp_sel = st.selectbox("Campaign", ["Tất cả"] + list(camp_names))
        camp_id = camp_names.get(camp_sel) if camp_sel != "Tất cả" else None

        # Project filter
        projects = ProjectModel.list_by_workspace(workspace_id)
        proj_names = {p["name"]: p["id"] for p in projects}
        proj_sel = st.selectbox("Project", ["Tất cả"] + list(proj_names))
        proj_id = proj_names.get(proj_sel) if proj_sel != "Tất cả" else None

        labels_input = st.text_input("Labels (phân cách bằng dấu phẩy)")
        label_list = [x.strip() for x in labels_input.split(",") if x.strip()]

        sort_by    = st.selectbox("Sắp xếp", ["created_at", "name", "size_bytes"])
        sort_order = st.radio("Thứ tự", ["desc", "asc"], horizontal=True)

        if st.button("🔄 Reset bộ lọc"):
            st.rerun()

    # ── Search ─────────────────────────────────────────────
    result = MediaLibraryService.search_and_filter(
        workspace_id=workspace_id,
        query=query,
        file_type=None if file_type == "Tất cả" else file_type,
        status=None if status_filter == "Tất cả" else status_filter,
        labels=label_list or None,
        is_favorite=True if only_favorites else None,
        is_thumbnail=True if only_thumbnails else None,
        campaign_id=camp_id,
        project_id=proj_id,
        sort_by=sort_by,
        sort_order=sort_order,
        page=st.session_state.get("media_page", 1),
        page_size=24,
    )

    # ── Upload button ──────────────────────────────────────
    col_top1, col_top2 = st.columns([8, 2])
    with col_top2:
        if user_role in ["editor", "admin", "super_admin"]:
            if st.button("⬆️ Upload Asset", use_container_width=True):
                _render_upload_form(workspace_id, user_id)

    # ── Grid view ──────────────────────────────────────────
    items = result["items"]
    if not items:
        st.info("Không tìm thấy asset nào phù hợp với bộ lọc.")
        return

    st.caption(f"Hiển thị {len(items)} / {result['total']} kết quả "
               f"(Trang {result['page']}/{result['total_pages']})")

    cols = st.columns(4)
    for idx, asset in enumerate(items):
        col = cols[idx % 4]
        with col:
            _render_asset_card(asset, workspace_id, user_id, user_role)

    # ── Pagination ─────────────────────────────────────────
    _render_pagination(result, "media_page")


def _render_asset_card(asset: dict, workspace_id: int,
                       user_id: int, user_role: str):
    """Card thumbnail nhỏ trong grid view."""
    status = asset.get("_status", "draft")
    label_str, color = AssetStatus.LABELS.get(status, ("❓", "#999"))
    version = asset.get("_version", 1)
    fav_icon = "❤️" if asset.get("_favorite") else ""
    thumb_icon = "🖼️" if asset.get("_is_thumbnail") else ""
    tags = asset.get("_labels", [])

    with st.container(border=True):
        # Ảnh preview
        if asset.get("file_type") == "image" and asset.get("url"):
            try:
                st.image(asset["url"], use_container_width=True)
            except Exception:
                st.markdown("🖼️ *Không tải được ảnh*")
        else:
            icon_map = {
                "video": "🎬", "document": "📄",
                "audio": "🎵", "image": "🖼️"
            }
            st.markdown(
                f"<div style='text-align:center;font-size:2.5rem;padding:20px'>"
                f"{icon_map.get(asset.get('file_type',''), '📁')}</div>",
                unsafe_allow_html=True
            )

        st.caption(
            f"{fav_icon}{thumb_icon} **{asset['name'][:20]}...**"
            f"\n`v{version}` · "
            f"<span style='color:{color}'>{label_str}</span>",
            unsafe_allow_html=True
        )
        if tags:
            st.caption(" ".join([f"`{t}`" for t in tags[:3]]))

        # Quick actions
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("👁️", key=f"view_{asset['id']}",
                         help="Xem chi tiết"):
                st.session_state[f"selected_asset"] = asset["id"]
                st.rerun()
        with btn_col2:
            new_fav = MediaLibraryService.toggle_favorite(
                asset["id"], workspace_id, user_id
            ) if st.button(
                "❤️" if not asset.get("_favorite") else "💔",
                key=f"fav_{asset['id']}", help="Yêu thích"
            ) else None


def _render_upload_form(workspace_id: int, user_id: int):
    """Form upload asset mới."""
    with st.form("upload_asset_form"):
        st.subheader("⬆️ Upload Asset Mới")
        name = st.text_input("Tên asset *", placeholder="hero-banner-q3")
        url  = st.text_input("URL hoặc đường dẫn *")
        file_type = st.selectbox("Loại", ["image", "video", "document", "audio"])
        alt_text  = st.text_input("Alt text (SEO)")
        labels    = st.text_input("Labels (phân cách bằng dấu phẩy)")
        is_thumb  = st.checkbox("🖼️ Đây là Thumbnail")
        width  = st.number_input("Chiều rộng (px)", 0, step=1) if is_thumb else 0
        height = st.number_input("Chiều cao (px)",  0, step=1) if is_thumb else 0

        submitted = st.form_submit_button("✅ Upload")
        if submitted:
            if not name or not url:
                st.error("Vui lòng điền đủ Tên và URL.")
                return
            label_list = [x.strip() for x in labels.split(",") if x.strip()]
            init_meta = {
                "labels": label_list,
                "lifecycle": {"status": AssetStatus.DRAFT, "version": 1},
                "relations": {"campaign_ids": [], "project_ids": []},
                "history": [{"action": "uploaded", "by": user_id,
                              "at": __import__("datetime").datetime.now().isoformat(),
                              "note": "Upload mới"}],
                "thumbnail": {"is_thumbnail": is_thumb,
                              "width": int(width), "height": int(height)} if is_thumb else {},
            }
            asset_id = AssetModel.create(
                workspace_id=workspace_id,
                name=name, url=url, file_type=file_type,
                alt_text=alt_text, tags=init_meta, uploaded_by=user_id
            )
            if asset_id:
                st.success(f"✅ Upload thành công! Asset ID: #{asset_id}")
            else:
                st.error("❌ Upload thất bại.")


def _render_pagination(result: dict, state_key: str):
    """Render phân trang."""
    total_pages = result["total_pages"]
    current = result["page"]
    if total_pages <= 1:
        return
    cols = st.columns(min(total_pages, 7))
    for i, col in enumerate(cols):
        page_num = i + 1
        with col:
            if st.button(
                str(page_num),
                key=f"page_{page_num}_{state_key}",
                type="primary" if page_num == current else "secondary"
            ):
                st.session_state[state_key] = page_num
                st.rerun()
```

---

## 🔐 6. Phân Quyền RBAC Cho Media Library

| Hành động | viewer | editor | admin | super_admin |
|-----------|:------:|:------:|:-----:|:-----------:|
| Xem danh sách assets | ✅ | ✅ | ✅ | ✅ |
| Tìm kiếm & Filter | ✅ | ✅ | ✅ | ✅ |
| Upload asset mới | ❌ | ✅ | ✅ | ✅ |
| Sửa tên / alt text | ❌ | ✅ | ✅ | ✅ |
| Thêm/xóa labels | ❌ | ✅ | ✅ | ✅ |
| Toggle favorite | ❌ | ✅ | ✅ | ✅ |
| Nhân bản (Duplicate) | ❌ | ✅ | ✅ | ✅ |
| Thêm note vào history | ❌ | ✅ | ✅ | ✅ |
| Gắn vào Campaign/Project | ❌ | ✅ | ✅ | ✅ |
| Cập nhật thumbnail meta | ❌ | ✅ | ✅ | ✅ |
| Bump version | ❌ | ✅ | ✅ | ✅ |
| **Draft → Approved** | ❌ | ❌ | ✅ | ✅ |
| **Approved → Published** | ❌ | ❌ | ✅ | ✅ |
| Revert về Draft | ❌ | ❌ | ✅ | ✅ |
| Archive asset | ❌ | ✅ | ✅ | ✅ |
| Xóa vĩnh viễn | ❌ | ❌ | ✅ | ✅ |

---

## 🔗 7. Tích Hợp Với Hệ Thống Hiện Tại

### 7.1 Tích hợp vào `app/main.py`

```python
# Thêm vào danh sách tabs trong main.py
from ui.tab_media_library import render_tab_media_library

# Trong phần render tabs:
with tabs[X]:  # Tab mới "Media Library"
    render_tab_media_library()
```

### 7.2 Tích hợp với Thumbnail Generator

Khi AI tạo thumbnail mới (từ `THUMBNAIL_GENERATOR_ARCHITECTURE.md`):

```python
# Sau khi generate ảnh thành công:
asset_id = AssetModel.create(
    workspace_id=workspace_id,
    name=f"thumb_{post_id}_{datetime.now():%Y%m%d_%H%M%S}.jpg",
    url=generated_url,
    file_type="image",
    post_id=post_id,
    tags={
        "labels": ["ai-generated", "thumbnail"],
        "lifecycle": {"status": "draft", "version": 1},
        "history": [{"action": "ai_generated", "by": user_id, "at": ..., "note": prompt}],
        "thumbnail": {"is_thumbnail": True, "width": 1280, "height": 720}
    },
    uploaded_by=user_id,
)

# Tự động gắn vào campaign nếu có
if campaign_id:
    MediaLibraryService.link_to_campaign(asset_id, workspace_id, campaign_id, user_id)
```

### 7.3 Tích hợp với Approval Workflow

```python
# Khi admin approve bài viết → tự động gợi ý approve thumbnail đính kèm
assets_of_post = AssetModel.list_by_post(post_id)
for asset in assets_of_post:
    status = MediaLibraryService.get_status(asset)
    if status == AssetStatus.DRAFT:
        st.warning(f"⚠️ Thumbnail '{asset['name']}' chưa được Approve!")
        if st.button(f"✅ Approve thumbnail này"):
            MediaLibraryService.approve(asset["id"], workspace_id,
                                        user_id, "Auto-approve cùng bài viết")
```

### 7.4 Tích hợp với Campaign Tab

```python
# Trong tab_campaign.py: hiển thị assets của campaign
from services.media_library_service import MediaLibraryService

result = MediaLibraryService.search_and_filter(
    workspace_id=workspace_id,
    campaign_id=selected_campaign_id,
    status="approved",
)
# render grid nhỏ các assets đã approved
```

---

## 📊 8. Tính Năng Chi Tiết Từng Module

### 8.1 🔍 Search (Tìm kiếm)

| Tính năng | Mô tả | Cách triển khai |
|-----------|-------|-----------------|
| Full-text search | Tìm trong `name`, `alt_text`, `labels` | In-memory string matching |
| Tìm theo tag | Filter theo 1+ label cụ thể | AND logic trên `labels[]` |
| Tìm theo trạng thái | Draft / Approved / Published / Archived | Filter `lifecycle.status` |
| Tìm theo type | image / video / document / audio | Query DB `file_type` |
| Tìm theo campaign | Lọc assets gắn với campaign_id | Filter `relations.campaign_ids` |
| Tìm theo project | Lọc assets gắn với project_id | Filter `relations.project_ids` |
| Tìm favorites | Chỉ hiện asset yêu thích | Filter `lifecycle.is_favorite` |
| Tìm thumbnails | Chỉ hiện assets là thumbnail | Filter `thumbnail.is_thumbnail` |

### 8.2 🔎 Filter

```
Bộ lọc kết hợp (AND logic):
  [file_type=image]
  AND [status=approved]
  AND [is_favorite=true]
  AND [campaign_id=5]
  AND [labels contains "banner"]
  AND [query="hero"]
```

Sắp xếp theo: `created_at` · `name` · `size_bytes` · `status`  
Thứ tự: `asc` / `desc`  
Phân trang: 24 items/trang (cấu hình được)

### 8.3 📋 Duplicate (Nhân bản)

```
Original Asset #42 [Approved, v3]
      │
      ├── Duplicate → New Asset #55 [Draft, v1]
      │   ├── URL: cùng URL gốc
      │   ├── duplicate_of: 42
      │   ├── original_id: 42
      │   ├── campaign_ids: [10]   ← campaign mới
      │   └── history: ["created_as_duplicate from #42"]
      │
      └── Original vẫn nguyên vẹn [Approved, v3]
```

**Use cases:**
- Tái sử dụng thumbnail cho campaign mới
- Tạo biến thể để A/B test
- Copy sang workspace khác (đổi workspace_id)

### 8.4 ❤️ Favorite

- Toggle bằng 1 click
- Filter `is_favorite=True` để xem bộ sưu tập yêu thích
- Ghi vào history: `"favorited"` / `"unfavorited"`
- Hiển thị icon ❤️ trên card trong grid view

### 8.5 📜 History (Lịch sử)

Mỗi action tự động ghi entry:

| Action | Khi nào |
|--------|---------|
| `uploaded` | Khi tạo asset mới |
| `ai_generated` | Khi AI generate thumbnail |
| `status_changed` | Mỗi lần đổi lifecycle status |
| `version_bumped` | Khi bump_version() |
| `favorited` / `unfavorited` | Toggle favorite |
| `labels_updated` | Thay đổi labels |
| `linked_campaign` | Gắn vào campaign |
| `unlinked_campaign` | Gỡ khỏi campaign |
| `linked_project` | Gắn vào project |
| `thumbnail_meta_updated` | Cập nhật kích thước/màu |
| `created_as_duplicate` | Khi nhân bản |
| `note_added` | User thêm ghi chú thủ công |

### 8.6 🏷️ Tag / Labels

- Mảng string tự do: `["banner", "hero", "q3-2026", "facebook"]`
- Hiển thị dưới dạng badge/chip trong UI
- Tìm kiếm AND logic (asset phải có **tất cả** labels được chọn)
- Đề xuất auto-complete từ labels phổ biến trong workspace

### 8.7 🎯 Campaign Linking

```python
# Gắn 1 asset vào nhiều campaigns
MediaLibraryService.link_to_campaign(asset_id=42, workspace_id=1, campaign_id=5, by=user_id)
MediaLibraryService.link_to_campaign(asset_id=42, workspace_id=1, campaign_id=8, by=user_id)

# Lọc tất cả assets của Campaign #5
result = MediaLibraryService.search_and_filter(workspace_id=1, campaign_id=5)
```

### 8.8 📁 Project Linking

```python
# Tương tự Campaign
MediaLibraryService.link_to_project(asset_id=42, workspace_id=1, project_id=2, by=user_id)
result = MediaLibraryService.search_and_filter(workspace_id=1, project_id=2)
```

### 8.9 🏢 Workspace Scope

- Mọi asset đều thuộc 1 `workspace_id`
- Multi-tenant: User chỉ thấy assets của workspace mình đang hoạt động
- `session_state["workspace_id"]` kiểm soát toàn bộ query
- Admin có thể xem nhiều workspace

---

## 📦 9. Cấu Trúc File Mới

```
AI_Agent_Content_AutoPos/
│
├── services/
│   └── media_library_service.py     ← [MỚI] Service chính
│
├── ui/
│   └── tab_media_library.py         ← [MỚI] Tab giao diện
│
└── docs/
    └── MEDIA_LIBRARY_UPGRADE.md     ← [MỚI] Tài liệu này
```

**Không có file nào bị xóa. Không có database bị thay đổi.**

---

## 🚀 10. Lộ Trình Triển Khai

### Phase 1 — Service Layer (Ưu tiên cao, ~1 ngày)

```
[ ] Tạo services/media_library_service.py
    [ ] AssetStatus constants + transition table
    [ ] _read_meta() / _write_meta() helpers
    [ ] set_status() + approve() + publish() + archive()
    [ ] toggle_favorite()
    [ ] duplicate()
    [ ] get_history() + add_note()
    [ ] set_labels()
    [ ] link_to_campaign() + link_to_project()
    [ ] set_thumbnail_meta()
    [ ] search_and_filter() (full implementation)
    [ ] get_stats()
```

### Phase 2 — UI Layer (~2 ngày)

```
[ ] Tạo ui/tab_media_library.py
    [ ] Stats bar (5 metrics)
    [ ] Sidebar filter panel
    [ ] Grid view 4 cột
    [ ] Asset card với status badge + version + favorite icon
    [ ] Asset detail panel (modal hoặc expander)
    [ ] Upload form
    [ ] Pagination
    [ ] Lifecycle action buttons (Approve, Publish, Archive)
    [ ] History timeline view
    [ ] Duplicate dialog
    [ ] Campaign/Project linking dropdowns
    [ ] Thumbnail meta editor
```

### Phase 3 — Tích hợp (~1 ngày)

```
[ ] Thêm tab Media Library vào app/main.py
[ ] Tích hợp với Thumbnail Generator (auto-create asset sau generate)
[ ] Tích hợp với Approval Workflow (check thumbnail status)
[ ] Tích hợp với Campaign tab (hiển thị assets của campaign)
[ ] Viết unit tests cho MediaLibraryService
```

### Phase 4 — Nâng cao (Tùy chọn)

```
[ ] Bulk actions (chọn nhiều → approve/archive/tag cùng lúc)
[ ] Export asset list (CSV/PDF)
[ ] Notification khi thumbnail được approve
[ ] AI auto-tag (dùng Gemini Vision để tạo labels tự động)
[ ] Color palette extraction tự động từ ảnh (Pillow)
[ ] Recycle bin (archive → recover trước khi xóa hẳn)
```

---

## ✅ 11. Tóm Tắt Kiến Trúc

```
┌─────────────────────────────────────────────────────────────┐
│                   MEDIA LIBRARY V2                          │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              ui/tab_media_library.py                 │   │
│  │  Search │ Filter │ Grid │ Detail │ Upload │ Paginate  │   │
│  └────────────────────────┬─────────────────────────────┘   │
│                           │                                 │
│  ┌────────────────────────▼─────────────────────────────┐   │
│  │         services/media_library_service.py            │   │
│  │                                                      │   │
│  │  AssetStatus  │  Lifecycle    │  Duplicate           │   │
│  │  Favorite     │  History      │  Tags/Labels         │   │
│  │  Campaign Link│  Project Link │  Thumbnail Meta      │   │
│  │  Search Filter│  Stats        │  Pagination          │   │
│  └────────────────────────┬─────────────────────────────┘   │
│                           │                                 │
│  ┌────────────────────────▼─────────────────────────────┐   │
│  │            database/models/assets.py                 │   │
│  │         (Không thay đổi — dùng nguyên hiện tại)      │   │
│  │                                                      │   │
│  │  assets.tags (JSON) ← Metadata Envelope mở rộng     │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Nguyên tắc cốt lõi**: Mọi tính năng mới đều được triển khai qua **Service Layer** và **UI Layer** — cột `tags` (JSON) đóng vai trò là **metadata store linh hoạt** mà không cần thay đổi database schema.

---

*Tài liệu này được tạo bởi Antigravity AI Assistant — 2026-07-12*
