# 📊 THUMBNAIL ANALYTICS — Thiết Kế Hệ Thống Phân Tích Thumbnail

> **Dự án**: AI_Agent_Content_AutoPos  
> **Module**: Thumbnail Analytics Engine  
> **Phiên bản**: 1.0  
> **Ngày tạo**: 2026-07-12  
> **Phụ thuộc vào**: `THUMBNAIL_PUBLISHING.md` · `BRAND_THUMBNAIL_INTEGRATION.md` · `THUMBNAIL_PROMPT_ENGINE.md`  
> **Ràng buộc**: Không sửa schema hiện tại · Không sửa `social/publishers.py` · Không sửa `database/models/analytics.py`

---

## 📌 1. Tổng Quan

### 1.1 Bài Toán

Hệ thống hiện tại có bảng `analytics` theo dõi hiệu suất **bài viết** (impressions, reach, likes, comments, engagement_rate) nhưng **hoàn toàn không có** cơ chế đo lường riêng cho **Thumbnail**:

| Vấn đề | Hậu quả |
|--------|---------|
| Không biết thumbnail nào có CTR cao | Không tối ưu hóa được thiết kế |
| Không có A/B Testing cho thumbnail | Không chọn được variant thắng |
| Không theo dõi Heatmap điểm nhấp | Không biết vùng nào người dùng chú ý |
| Không xếp hạng template theo hiệu suất | Không tái sử dụng template tốt |
| Không đo Brand Performance qua thumbnail | Không đánh giá ROI thiết kế thương hiệu |

### 1.2 Mục Tiêu

Thiết kế **Thumbnail Analytics Module** hoàn chỉnh với 10 thành phần:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    THUMBNAIL ANALYTICS ECOSYSTEM                     │
├─────────────────┬───────────────────┬──────────────────────────────┤
│  TRACKING       │   TESTING         │   INTELLIGENCE               │
│                 │                   │                              │
│  • CTR          │  • A/B Testing    │  • Template Ranking          │
│  • Engagement   │  • Winning        │  • Brand Performance         │
│  • Reach        │    Thumbnail      │  • AI Recommendations        │
│  • Save         │                   │                              │
│  • Share        │  VISUALIZATION    │   EXPORT                     │
│  • Click        │                   │                              │
│                 │  • Heatmap        │  • Report PDF/CSV            │
│                 │                   │  • Dashboard                 │
└─────────────────┴───────────────────┴──────────────────────────────┘
```

### 1.3 Nguyên Tắc Thiết Kế

- ✅ **Không sửa schema** — Dùng bảng `analytics` hiện có + 3 bảng mới riêng biệt
- ✅ **Không sửa `analytics.py`** — Tạo model mới `ThumbnailAnalyticsModel`
- ✅ **Tương thích dual DB** — SQLite (local) và PostgreSQL (SaaS)
- ✅ **Liên kết với ABTestModel** — Mở rộng test_type cho thumbnail
- ✅ **Tích hợp Brand** — Đo lường hiệu suất theo brand profile

---

## 🗃️ 2. Schema Cơ Sở Dữ Liệu

### 2.1 Bảng `thumbnail_analytics` — Metrics Chính

```sql
CREATE TABLE IF NOT EXISTS thumbnail_analytics (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,

    -- 🔗 Liên kết
    workspace_id        INTEGER NOT NULL,
    asset_id            INTEGER NOT NULL,          -- FK → assets.id
    post_id             INTEGER,                   -- FK → posts.id (nullable)
    campaign_id         INTEGER,                   -- FK → campaigns.id (nullable)
    ab_test_id          INTEGER,                   -- FK → ab_tests.id (nullable)
    ab_variant_id       INTEGER,                   -- FK → ab_variants.id (nullable)

    -- 📐 Metadata Thumbnail
    platform            TEXT NOT NULL,             -- facebook | linkedin | zalo | instagram | tiktok
    template_id         TEXT,                      -- ID template từ THUMBNAIL_TEMPLATE_LIBRARY
    brand_status        TEXT DEFAULT 'unknown',    -- applied | proposed | unknown
    aspect_ratio        TEXT,                      -- 16:9 | 1:1 | 4:5 | 9:16
    style_tag           TEXT,                      -- corporate | lifestyle | 3d | editorial
    thumbnail_url       TEXT,

    -- 📊 Metrics Thu Thập (Raw)
    impressions         INTEGER DEFAULT 0,         -- Số lần hiển thị
    reach               INTEGER DEFAULT 0,         -- Số người xem độc lập
    clicks              INTEGER DEFAULT 0,         -- Tổng số click vào post
    thumbnail_clicks    INTEGER DEFAULT 0,         -- Click trực tiếp vào thumbnail (nếu platform hỗ trợ)
    saves               INTEGER DEFAULT 0,         -- Lưu / Bookmark
    shares              INTEGER DEFAULT 0,         -- Chia sẻ
    comments            INTEGER DEFAULT 0,         -- Bình luận
    likes               INTEGER DEFAULT 0,         -- Thích / React
    video_plays         INTEGER DEFAULT 0,         -- Lượt phát video (YouTube/TikTok)
    link_clicks         INTEGER DEFAULT 0,         -- Click vào link trong bài

    -- 📈 Metrics Tính Toán (Computed)
    ctr                 REAL DEFAULT 0.0,          -- Click-Through Rate = clicks / impressions * 100
    engagement_rate     REAL DEFAULT 0.0,          -- (likes + comments + shares) / reach * 100
    save_rate           REAL DEFAULT 0.0,          -- saves / reach * 100
    share_rate          REAL DEFAULT 0.0,          -- shares / reach * 100
    virality_score      REAL DEFAULT 0.0,          -- (shares * 3 + saves * 2 + comments) / reach * 100

    -- 🏆 Scoring
    thumbnail_score     REAL DEFAULT 0.0,          -- Điểm tổng hợp (0-100)
    score_breakdown     TEXT,                      -- JSON: {ctr: 30, engagement: 25, reach: 20, ...}

    -- 🕐 Thời Gian
    period_start        TEXT NOT NULL,             -- Bắt đầu kỳ đo (ISO datetime)
    period_end          TEXT NOT NULL,             -- Kết thúc kỳ đo
    granularity         TEXT DEFAULT 'daily',      -- hourly | daily | weekly | monthly
    collected_at        TEXT DEFAULT (datetime('now')),
    source              TEXT DEFAULT 'manual',     -- manual | api_sync | estimated

    FOREIGN KEY (asset_id)    REFERENCES assets(id),
    FOREIGN KEY (post_id)     REFERENCES posts(id),
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
);

CREATE INDEX IF NOT EXISTS idx_thumb_analytics_workspace ON thumbnail_analytics(workspace_id);
CREATE INDEX IF NOT EXISTS idx_thumb_analytics_asset     ON thumbnail_analytics(asset_id);
CREATE INDEX IF NOT EXISTS idx_thumb_analytics_platform  ON thumbnail_analytics(platform);
CREATE INDEX IF NOT EXISTS idx_thumb_analytics_period    ON thumbnail_analytics(period_start, period_end);
CREATE INDEX IF NOT EXISTS idx_thumb_analytics_ab_test   ON thumbnail_analytics(ab_test_id);
```

---

### 2.2 Bảng `thumbnail_heatmap` — Dữ Liệu Heatmap

```sql
CREATE TABLE IF NOT EXISTS thumbnail_heatmap (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id    INTEGER NOT NULL,
    asset_id        INTEGER NOT NULL,             -- FK → assets.id

    -- Vị trí click/attention (tọa độ chuẩn hóa 0.0–1.0)
    x_norm          REAL NOT NULL,                -- Vị trí X (0.0 = trái, 1.0 = phải)
    y_norm          REAL NOT NULL,                -- Vị trí Y (0.0 = trên, 1.0 = dưới)
    zone_label      TEXT,                         -- title | cta | subject | background | logo | badge
    attention_score REAL DEFAULT 0.0,             -- Điểm chú ý (0-1)
    interaction_type TEXT DEFAULT 'view',         -- view | click | hover | gaze (eye-tracking)
    device_type     TEXT DEFAULT 'mobile',        -- mobile | desktop | tablet
    session_count   INTEGER DEFAULT 1,

    recorded_at     TEXT DEFAULT (datetime('now')),

    FOREIGN KEY (asset_id) REFERENCES assets(id)
);

CREATE INDEX IF NOT EXISTS idx_heatmap_asset     ON thumbnail_heatmap(asset_id);
CREATE INDEX IF NOT EXISTS idx_heatmap_workspace ON thumbnail_heatmap(workspace_id);
```

---

### 2.3 Bảng `thumbnail_template_stats` — Xếp Hạng Template

```sql
CREATE TABLE IF NOT EXISTS thumbnail_template_stats (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id        INTEGER NOT NULL,
    template_id         TEXT NOT NULL,            -- ID từ THUMBNAIL_TEMPLATE_LIBRARY
    template_name       TEXT,
    template_category   TEXT,                     -- viral | educational | product | brand | event
    platform            TEXT,

    -- Thống kê tổng hợp
    usage_count         INTEGER DEFAULT 0,        -- Số lần đã dùng
    avg_ctr             REAL DEFAULT 0.0,
    avg_engagement      REAL DEFAULT 0.0,
    avg_reach           INTEGER DEFAULT 0,
    avg_saves           REAL DEFAULT 0.0,
    avg_shares          REAL DEFAULT 0.0,
    total_impressions   INTEGER DEFAULT 0,
    win_rate            REAL DEFAULT 0.0,         -- Tỷ lệ thắng A/B test (%)
    rank_score          REAL DEFAULT 0.0,         -- Điểm xếp hạng tổng hợp
    rank_position       INTEGER DEFAULT 0,        -- Vị trí xếp hạng

    -- Metadata
    last_used_at        TEXT,
    updated_at          TEXT DEFAULT (datetime('now')),

    UNIQUE (workspace_id, template_id, platform)
);

CREATE INDEX IF NOT EXISTS idx_tmpl_stats_workspace ON thumbnail_template_stats(workspace_id);
CREATE INDEX IF NOT EXISTS idx_tmpl_stats_rank      ON thumbnail_template_stats(rank_score DESC);
```

---

### 2.4 Quan Hệ Dữ Liệu (ERD)

```
workspaces (1) ────────────── (N) thumbnail_analytics
                                        │
                    ┌───────────────────┼───────────────────┐
                    │                   │                   │
                 assets (1)          posts (1)       ab_tests (1)
                    │                   │                   │
              thumbnail_heatmap    campaigns          ab_variants
                    │
         thumbnail_template_stats
```

---

## 📐 3. Định Nghĩa Metrics

### 3.1 CTR — Click-Through Rate

**Ý nghĩa**: Tỷ lệ người xem thumbnail và nhấp vào bài đăng.

```
CTR = (Clicks / Impressions) × 100 (%)
```

| Ngưỡng | Đánh Giá | Hành Động |
|--------|---------|-----------|
| CTR < 1.0% | 🔴 Kém | Thay thumbnail, đổi tiêu đề chồng |
| 1.0% – 2.5% | 🟡 Trung bình | Thử A/B với màu sắc khác |
| 2.5% – 5.0% | 🟢 Tốt | Giữ template, nhân rộng |
| > 5.0% | ⭐ Xuất sắc | Đưa vào Template Library ưu tiên cao |

**Benchmark theo Platform:**

| Platform | CTR Trung Bình Ngành | CTR Mục Tiêu |
|---------|---------------------|--------------|
| Facebook Post | 0.9% | 2.0%+ |
| LinkedIn | 0.5% | 1.5%+ |
| Zalo OA | 1.2% | 3.0%+ |
| YouTube | 4.0% | 6.0%+ |
| Instagram | 1.5% | 3.5%+ |
| TikTok | 2.0% | 5.0%+ |

---

### 3.2 Engagement Rate

**Ý nghĩa**: Mức độ tương tác tổng hợp của người dùng với bài viết sau khi xem thumbnail.

```
Engagement Rate = (Likes + Comments + Shares + Saves) / Reach × 100 (%)
```

**Trọng số thành phần:**

| Hành Động | Trọng Số | Lý Do |
|-----------|---------|-------|
| Share | 3.0× | Viral signal mạnh nhất |
| Save | 2.0× | Ý định truy cập lại cao |
| Comment | 1.5× | Tương tác sâu |
| Like / React | 1.0× | Tương tác nhanh |
| Video Play | 0.5× | Bắt đầu xem nhưng chưa commit |

**Engagement Score tổng hợp:**

```python
engagement_score = (
    shares  * 3.0 +
    saves   * 2.0 +
    comments * 1.5 +
    likes   * 1.0 +
    video_plays * 0.5
) / max(reach, 1) * 100
```

---

### 3.3 Reach

**Ý nghĩa**: Số người dùng độc lập đã nhìn thấy thumbnail.

```
Reach Rate = Reach / Total Followers × 100 (%)
```

**Chỉ số phụ:**
- **Organic Reach**: Reach không trả phí
- **Paid Reach**: Reach từ quảng cáo
- **Reach Growth %**: So sánh với kỳ trước

---

### 3.4 Save Rate

**Ý nghĩa**: Tỷ lệ người lưu bài — chỉ số chất lượng nội dung dài hạn.

```
Save Rate = Saves / Reach × 100 (%)
```

> **Lưu ý**: Save Rate cao chứng tỏ thumbnail **kích thích sự tò mò** và người dùng muốn xem lại. Đây là signal chất lượng quan trọng cho content giáo dục.

---

### 3.5 Share Rate

**Ý nghĩa**: Tỷ lệ người chia sẻ — chỉ số viral mạnh nhất.

```
Share Rate = Shares / Reach × 100 (%)
```

| Share Rate | Mức Viral |
|-----------|-----------|
| < 0.5% | Không viral |
| 0.5% – 2% | Viral nhẹ |
| 2% – 5% | Viral tốt |
| > 5% | Viral cao — Nhân rộng ngay |

---

### 3.6 Click (Thumbnail Click)

Phân biệt 2 loại click:

| Loại | Định Nghĩa | Tracking |
|------|-----------|---------|
| **Post Click** | Click vào bất kỳ phần nào của bài | Facebook/LinkedIn API |
| **Thumbnail Click** | Click trực tiếp vào ảnh thumbnail | UTM tracking + pixel |
| **Link Click** | Click vào link trong bài | Link tracker |
| **CTA Click** | Click vào nút CTA trong post | Button tracking |

---

### 3.7 Thumbnail Score — Điểm Tổng Hợp

```python
def calculate_thumbnail_score(metrics: dict) -> float:
    """
    Tính điểm tổng hợp Thumbnail (0–100).
    Trọng số được calibrate theo dữ liệu ngành marketing Việt Nam.
    """
    ctr_score        = min(metrics['ctr'] / 5.0, 1.0) * 30        # Max 30 điểm (CTR 5%+ = full)
    engagement_score = min(metrics['engagement_rate'] / 10.0, 1.0) * 25  # Max 25 điểm
    reach_score      = min(metrics['reach_rate'] / 20.0, 1.0) * 20       # Max 20 điểm
    save_score       = min(metrics['save_rate'] / 3.0, 1.0) * 15         # Max 15 điểm
    share_score      = min(metrics['share_rate'] / 2.0, 1.0) * 10        # Max 10 điểm

    total = ctr_score + engagement_score + reach_score + save_score + share_score

    return round(total, 2)  # 0.00 – 100.00
```

**Thang điểm:**

| Score | Hạng | Màu | Hành Động |
|-------|------|-----|-----------|
| 85 – 100 | 🥇 Xuất Sắc | Vàng | → Template Library (Top) |
| 70 – 84 | 🥈 Tốt | Xanh lá | → Lưu + nhân rộng |
| 50 – 69 | 🥉 Khá | Xanh dương | → Tối ưu thêm |
| 30 – 49 | ⚠️ Trung Bình | Vàng cam | → A/B test lại |
| 0 – 29 | 🔴 Kém | Đỏ | → Xóa / thay mới |

---

## 🔬 4. A/B Testing Thumbnail

### 4.1 Kiến Trúc A/B Testing Thumbnail

Mở rộng `ABTestModel` hiện có bằng `test_type = "thumbnail"`:

```python
# Mở rộng VALID_TEST_TYPES trong ABTestModel
VALID_TEST_TYPES = {
    "prompt", "headline", "cta", "full_post",
    "subject_line", "angle",
    "thumbnail",          # ← MỚI: A/B test thumbnail
    "thumbnail_color",    # ← MỚI: Test màu sắc
    "thumbnail_layout",   # ← MỚI: Test bố cục
    "thumbnail_text",     # ← MỚI: Test tiêu đề chồng
    "thumbnail_style",    # ← MỚI: Test phong cách nghệ thuật
}
```

### 4.2 Luồng Tạo A/B Test Thumbnail

```
┌──────────────────────────────────────────────────────────────┐
│              A/B TEST THUMBNAIL WORKFLOW                      │
│                                                              │
│  [1] Chọn bài viết cần test                                  │
│       ↓                                                      │
│  [2] Tạo Test (test_type = "thumbnail")                      │
│       name: "Test thumbnail – AI Agent post #42"             │
│       platform: "LinkedIn"                                    │
│       ↓                                                      │
│  [3] Thêm Variant A (thumbnail_asset_id_A)                   │
│       label: "Variant A – Corporate Navy"                    │
│       content: URL ảnh thumbnail A                           │
│       prompt_used: JSON prompt engine output A               │
│       ↓                                                      │
│  [4] Thêm Variant B (thumbnail_asset_id_B)                   │
│       label: "Variant B – Gradient Gold"                     │
│       content: URL ảnh thumbnail B                           │
│       prompt_used: JSON prompt engine output B               │
│       ↓                                                      │
│  [5] Chạy Test (status = "running")                          │
│       → Hệ thống theo dõi metrics theo từng variant          │
│       → Cập nhật ThumbnailAnalytics liên kết ab_variant_id   │
│       ↓                                                      │
│  [6] AI Phân Tích → Tuyên Bố Winner                         │
│       → update_test_status(status="completed", winner_id=X)  │
│       → Gắn badge "🏆 WINNER" cho variant thắng              │
└──────────────────────────────────────────────────────────────┘
```

### 4.3 Tiêu Chí Xác Định Winning Thumbnail

```python
class ThumbnailABDecider:
    """
    Xác định variant thắng trong A/B test thumbnail.
    Sử dụng thuật toán Multi-Criteria Decision Analysis (MCDA).
    """

    WEIGHTS = {
        'ctr':              0.35,   # CTR — quan trọng nhất
        'engagement_rate':  0.25,   # Engagement tổng hợp
        'save_rate':        0.15,   # Save — chất lượng dài hạn
        'share_rate':       0.15,   # Share — viral
        'reach_rate':       0.10,   # Reach — độ phủ
    }

    MIN_IMPRESSIONS = 500           # Ngưỡng tối thiểu để kết luận
    MIN_CONFIDENCE  = 0.80          # Độ tin cậy thống kê tối thiểu (80%)

    @classmethod
    def decide_winner(cls, variants_metrics: list[dict]) -> dict:
        """
        variants_metrics: List[{variant_id, label, ctr, engagement_rate, ...}]
        Trả về: {winner_id, winner_label, confidence, margin, reason}
        """
        if len(variants_metrics) < 2:
            return {"winner_id": None, "reason": "Cần ít nhất 2 variants"}

        for v in variants_metrics:
            if v.get('impressions', 0) < cls.MIN_IMPRESSIONS:
                return {
                    "winner_id": None,
                    "reason": f"Variant '{v['label']}' chưa đủ {cls.MIN_IMPRESSIONS} impressions để kết luận."
                }

        # Tính weighted score
        scores = []
        for v in variants_metrics:
            score = sum(
                v.get(metric, 0) * weight
                for metric, weight in cls.WEIGHTS.items()
            )
            scores.append({**v, 'weighted_score': score})

        scores.sort(key=lambda x: x['weighted_score'], reverse=True)
        winner, runner_up = scores[0], scores[1]

        # Kiểm tra khoảng cách đủ rõ ràng
        margin = winner['weighted_score'] - runner_up['weighted_score']
        confidence = min(margin / runner_up['weighted_score'], 1.0) if runner_up['weighted_score'] > 0 else 0

        if confidence < cls.MIN_CONFIDENCE:
            return {
                "winner_id": None,
                "reason": f"Chênh lệch {margin:.2f} chưa đủ để kết luận (cần ≥{cls.MIN_CONFIDENCE*100:.0f}% confidence)"
            }

        return {
            "winner_id":    winner['variant_id'],
            "winner_label": winner['label'],
            "confidence":   round(confidence * 100, 1),
            "margin":       round(margin, 4),
            "winner_score": round(winner['weighted_score'], 4),
            "reason": (
                f"Variant '{winner['label']}' thắng với CTR {winner['ctr']:.2f}% "
                f"vs {runner_up['ctr']:.2f}%, confidence {confidence*100:.1f}%"
            )
        }
```

### 4.4 Bảng So Sánh Variant

| Metric | Variant A | Variant B | Delta | Winner |
|--------|-----------|-----------|-------|--------|
| **CTR** | 3.2% | 4.8% | +1.6% | B ✅ |
| **Engagement Rate** | 8.5% | 7.2% | -1.3% | A |
| **Save Rate** | 2.1% | 2.9% | +0.8% | B ✅ |
| **Share Rate** | 1.4% | 2.1% | +0.7% | B ✅ |
| **Reach Rate** | 15% | 14% | -1.0% | A |
| **Thumbnail Score** | 62.4 | 74.1 | +11.7 | 🏆 **B** |

---

## 🔥 5. Heatmap Thumbnail

### 5.1 Kiến Trúc Heatmap

Heatmap theo dõi **vùng được chú ý** và **vùng được nhấp** trên thumbnail, giúp hiểu người dùng nhìn vào đâu trước khi quyết định click.

```
┌─────────────────────────────────────────────────────────┐
│                 THUMBNAIL HEATMAP ZONES                  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │  ZONE: header_area (y: 0.0 – 0.25)               │   │
│  │  → Badge, Tên thương hiệu, Logo                  │   │
│  ├──────────────────────────────────────────────────┤   │
│  │                                                  │   │
│  │  ZONE: title_area (y: 0.25 – 0.55)               │   │
│  │  → Tiêu đề chính — thường được nhìn nhiều nhất  │   │
│  │                                                  │   │
│  ├──────────────────────────────────────────────────┤   │
│  │  ZONE: subject_area (y: 0.2 – 0.8, x: 0.5–1.0)  │   │
│  │  → Nhân vật, sản phẩm, hình ảnh chủ đề          │   │
│  ├──────────────────────────────────────────────────┤   │
│  │  ZONE: cta_area (y: 0.75 – 1.0)                  │   │
│  │  → Nút CTA, Subtitle, Tag                        │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### 5.2 Zone Labels Chuẩn Hoá

```python
HEATMAP_ZONES = {
    "title":       {"x": (0.0, 0.6), "y": (0.2, 0.6),  "weight": 1.5},
    "cta":         {"x": (0.0, 1.0), "y": (0.7, 1.0),  "weight": 2.0},
    "subject":     {"x": (0.4, 1.0), "y": (0.1, 0.9),  "weight": 1.2},
    "logo":        {"x": (0.0, 0.2), "y": (0.75, 1.0), "weight": 0.8},
    "badge":       {"x": (0.0, 0.35),"y": (0.0, 0.2),  "weight": 1.3},
    "background":  {"x": (0.0, 1.0), "y": (0.0, 1.0),  "weight": 0.5},
}

def classify_zone(x_norm: float, y_norm: float) -> str:
    """Phân loại zone từ tọa độ chuẩn hóa (0.0–1.0)."""
    for zone_name, zone in HEATMAP_ZONES.items():
        xmin, xmax = zone["x"]
        ymin, ymax = zone["y"]
        if xmin <= x_norm <= xmax and ymin <= y_norm <= ymax:
            return zone_name
    return "background"
```

### 5.3 Phương Pháp Thu Thập Heatmap Data

| Phương Pháp | Độ Chính Xác | Cách Triển Khai |
|-------------|-------------|----------------|
| **Pixel Tracking** | ⭐⭐⭐ | Nhúng pixel 1×1 theo vùng thumbnail |
| **UTM per Zone** | ⭐⭐ | Link riêng cho từng vùng CTA |
| **AI Estimation** | ⭐⭐ | Gemini dự đoán vùng hot dựa trên thiết kế |
| **Survey Feedback** | ⭐ | Hỏi người dùng thủ công |
| **Session Replay** | ⭐⭐⭐⭐ | Tích hợp Hotjar / FullStory (nếu có website) |

**Trong hệ thống hiện tại**, sử dụng **AI Estimation** (khả thi nhất):

```python
class ThumbnailHeatmapEstimator:
    """
    Dùng Gemini để ước tính điểm attention theo từng zone.
    Dựa trên nguyên tắc thiết kế UX và eye-tracking research.
    """

    @staticmethod
    def estimate_from_design(thumbnail_prompt_output: dict,
                             api_key: str) -> list[dict]:
        """
        Input: Output JSON từ Thumbnail Prompt Engine
        Output: List[{zone, x_norm, y_norm, attention_score, rationale}]
        """
        composition = thumbnail_prompt_output.get("composition", "")
        text_overlay = thumbnail_prompt_output.get("text_overlay", {})
        style = thumbnail_prompt_output.get("style", "")

        prompt = f"""
Bạn là chuyên gia Eye-Tracking UX. Phân tích thiết kế thumbnail sau và ước tính
điểm chú ý (attention score 0.0–1.0) cho từng vùng theo nghiên cứu eye-tracking.

Thiết kế thumbnail:
- Bố cục (Composition): {composition}
- Tiêu đề chính: {text_overlay.get('title', '')}
- Tiêu đề phụ: {text_overlay.get('subtitle', '')}
- Badge: {text_overlay.get('badge', '')}
- CTA: {text_overlay.get('cta', '')}
- Phong cách: {style}

Trả về JSON array:
[
  {{"zone": "title",   "x_norm": 0.30, "y_norm": 0.40, "attention_score": 0.85, "rationale": "..."}},
  {{"zone": "cta",     "x_norm": 0.50, "y_norm": 0.85, "attention_score": 0.70, "rationale": "..."}},
  {{"zone": "subject", "x_norm": 0.70, "y_norm": 0.50, "attention_score": 0.75, "rationale": "..."}},
  {{"zone": "badge",   "x_norm": 0.15, "y_norm": 0.10, "attention_score": 0.60, "rationale": "..."}},
  {{"zone": "logo",    "x_norm": 0.10, "y_norm": 0.90, "attention_score": 0.40, "rationale": "..."}}
]

Chỉ trả về JSON thuần túy.
"""
        # Gọi Gemini → Parse JSON → Return
        ...
```

### 5.4 Hiển Thị Heatmap Trong UI

```
THUMBNAIL HEATMAP VISUALIZATION (Streamlit)

┌─────────────────────────────────────────────┐
│         Thumbnail Preview                    │
│  ┌───────────────────────────────────────┐   │
│  │  [BADGE: HIGH 🔴]                     │   │
│  │                                       │   │
│  │     [TITLE ZONE: HIGHEST 🔴🔴🔴]      │   │
│  │                                       │   │
│  │          [SUBJECT: HIGH 🔴🔴]  👤     │   │
│  │                                       │   │
│  │  [LOGO: LOW 🟡]     [CTA: HIGH 🔴🔴]  │   │
│  └───────────────────────────────────────┘   │
│                                              │
│  🔴 Very High (>0.8)  🟠 High (0.6-0.8)      │
│  🟡 Medium (0.4-0.6)  🟢 Low (<0.4)          │
└─────────────────────────────────────────────┘
```

**Code Streamlit hiển thị:**

```python
def render_heatmap_overlay(asset_id: int, workspace_id: int):
    """Hiển thị heatmap overlay trên thumbnail preview."""
    import streamlit as st
    import plotly.graph_objects as go

    heatmap_data = ThumbnailHeatmapModel.get_by_asset(asset_id, workspace_id)
    if not heatmap_data:
        st.info("ℹ️ Chưa có dữ liệu heatmap. Nhấn 'Ước Tính Heatmap' để phân tích.")
        return

    # Tạo scatter heatmap với plotly
    fig = go.Figure()

    x_vals   = [h['x_norm'] for h in heatmap_data]
    y_vals   = [1 - h['y_norm'] for h in heatmap_data]  # Invert Y (top=0)
    scores   = [h['attention_score'] for h in heatmap_data]
    zones    = [h['zone_label'] for h in heatmap_data]
    sizes    = [s * 80 for s in scores]

    fig.add_trace(go.Scatter(
        x=x_vals, y=y_vals,
        mode='markers+text',
        marker=dict(
            size=sizes,
            color=scores,
            colorscale='RdYlGn_r',  # Đỏ = cao, Xanh = thấp
            colorbar=dict(title="Attention"),
            opacity=0.65,
        ),
        text=zones,
        textposition='top center',
        hovertemplate='<b>%{text}</b><br>Score: %{marker.color:.2f}<extra></extra>'
    ))

    fig.update_layout(
        title="🔥 Thumbnail Attention Heatmap",
        xaxis=dict(range=[0, 1], showgrid=False, zeroline=False, visible=False),
        yaxis=dict(range=[0, 1], showgrid=False, zeroline=False, visible=False),
        height=400,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0.05)',
    )

    st.plotly_chart(fig, use_container_width=True)
```

---

## 🏆 6. Template Ranking

### 6.1 Thuật Toán Xếp Hạng Template

```python
class TemplateRanker:
    """
    Xếp hạng template thumbnail dựa trên hiệu suất thực tế.
    Cập nhật sau mỗi kỳ thu thập analytics.
    """

    RANK_WEIGHTS = {
        'avg_ctr':        0.30,
        'avg_engagement': 0.25,
        'win_rate':       0.20,   # Tỷ lệ thắng A/B test
        'avg_save_rate':  0.15,
        'avg_share_rate': 0.10,
    }

    FRESHNESS_DECAY = 0.95        # Giảm 5% trọng số mỗi tuần không dùng

    @classmethod
    def calculate_rank_score(cls, template_stats: dict) -> float:
        """Tính điểm xếp hạng chuẩn hóa (0–100)."""
        base_score = sum(
            template_stats.get(metric, 0) * weight
            for metric, weight in cls.RANK_WEIGHTS.items()
        )
        # Bonus cho template nhiều lần sử dụng (popularity bonus)
        usage_bonus = min(template_stats.get('usage_count', 0) / 50, 1.0) * 10

        # Freshness decay
        from datetime import datetime, timedelta
        last_used = template_stats.get('last_used_at')
        if last_used:
            days_since = (datetime.now() - datetime.fromisoformat(last_used)).days
            weeks_since = days_since // 7
            freshness = cls.FRESHNESS_DECAY ** weeks_since
        else:
            freshness = 0.5

        return round((base_score * freshness + usage_bonus) * 100, 2)

    @classmethod
    def update_all_ranks(cls, workspace_id: int) -> None:
        """Cập nhật xếp hạng tất cả templates trong workspace."""
        templates = ThumbnailTemplateStatsModel.list_by_workspace(workspace_id)
        ranked = []
        for t in templates:
            score = cls.calculate_rank_score(t)
            ranked.append((t['template_id'], t['platform'], score))

        ranked.sort(key=lambda x: x[2], reverse=True)
        for position, (template_id, platform, score) in enumerate(ranked, 1):
            ThumbnailTemplateStatsModel.update_rank(
                workspace_id, template_id, platform, score, position
            )
```

### 6.2 Bảng Xếp Hạng Template (Ví Dụ)

| Rank | Template | Loại | Platform | CTR TB | Engagement TB | Win Rate | Score |
|------|---------|------|---------|--------|--------------|---------|-------|
| 🥇 1 | Split-Screen Corporate | Corporate | LinkedIn | 4.8% | 9.2% | 75% | 91.4 |
| 🥈 2 | Gradient Dark Hook | Viral | Facebook | 4.2% | 11.5% | 68% | 87.2 |
| 🥉 3 | Zalo Lifestyle Local | Brand | Zalo OA | 3.9% | 8.8% | 60% | 79.6 |
| 4 | Bold News Breaking | News | Facebook | 3.5% | 7.1% | 55% | 71.3 |
| 5 | Minimal Educational | Educational | LinkedIn | 2.8% | 12.4% | 50% | 68.7 |

### 6.3 Tự Động Đề Xuất Template

```python
def suggest_best_template(platform: str, content_type: str,
                           audience: str, workspace_id: int) -> dict:
    """
    Đề xuất template tốt nhất dựa trên:
    - Lịch sử hiệu suất trong workspace
    - Platform + Content Type
    - Audience profile
    """
    top_templates = ThumbnailTemplateStatsModel.get_top_by_platform(
        workspace_id, platform, limit=5
    )

    if not top_templates:
        # Fallback: Đề xuất dựa trên lookup table toàn cầu
        return get_default_template(platform, content_type)

    # Lọc thêm theo content_type
    filtered = [t for t in top_templates
                if t.get('template_category') == content_type]

    return (filtered[0] if filtered else top_templates[0])
```

---

## 🎯 7. Brand Performance Analytics

### 7.1 Đo Lường Hiệu Quả Brand qua Thumbnail

So sánh hiệu suất thumbnail **có brand** vs **không có brand** (brand_status: applied vs proposed):

```python
class BrandPerformanceAnalyzer:
    """
    Phân tích tác động của Brand Identity lên hiệu suất thumbnail.
    """

    @staticmethod
    def compare_brand_vs_nobrand(workspace_id: int,
                                  platform: str = None,
                                  days: int = 30) -> dict:
        """
        So sánh metrics trung bình:
        - Thumbnail có Brand Profile → brand_status='applied'
        - Thumbnail không Brand Profile → brand_status='proposed'
        """
        ...
        return {
            "period_days": days,
            "with_brand": {
                "count": 45,
                "avg_ctr": 3.8,
                "avg_engagement": 9.5,
                "avg_save_rate": 2.4,
                "avg_share_rate": 1.8,
                "avg_thumbnail_score": 76.2,
            },
            "without_brand": {
                "count": 23,
                "avg_ctr": 2.1,
                "avg_engagement": 5.8,
                "avg_save_rate": 1.2,
                "avg_share_rate": 0.9,
                "avg_thumbnail_score": 52.4,
            },
            "brand_uplift": {
                "ctr_uplift":        "+81%",
                "engagement_uplift": "+64%",
                "save_uplift":       "+100%",
                "score_uplift":      "+45%",
            },
            "conclusion": "Brand Profile tăng CTR trung bình 81% và Engagement 64%."
        }
```

### 7.2 Brand Consistency Score

Đo lường mức độ nhất quán thương hiệu qua các thumbnail:

```python
def calculate_brand_consistency(workspace_id: int, days: int = 30) -> dict:
    """
    Tính Brand Consistency Score dựa trên:
    - % thumbnail dùng đúng màu thương hiệu
    - % thumbnail dùng đúng typography
    - % thumbnail có logo
    - % thumbnail tuân thủ brand_guidelines
    """
    thumbnails = ThumbnailAnalyticsModel.list_by_workspace(
        workspace_id,
        brand_status='applied',
        days=days
    )

    total = len(thumbnails)
    if total == 0:
        return {"score": 0, "message": "Chưa có dữ liệu"}

    scores = {
        "color_compliance":    sum(1 for t in thumbnails if t.get('brand_color_used')) / total,
        "typography_match":    sum(1 for t in thumbnails if t.get('brand_font_used')) / total,
        "logo_present":        sum(1 for t in thumbnails if t.get('logo_included')) / total,
        "guideline_followed":  sum(1 for t in thumbnails if t.get('guideline_ok')) / total,
    }

    consistency_score = sum(scores.values()) / len(scores) * 100

    return {
        "score": round(consistency_score, 1),
        "details": scores,
        "grade": (
            "A" if consistency_score >= 90 else
            "B" if consistency_score >= 75 else
            "C" if consistency_score >= 60 else "D"
        )
    }
```

### 7.3 Dashboard Brand Performance

```
┌────────────────────────────────────────────────────────────┐
│          🎨 BRAND PERFORMANCE ANALYTICS                     │
├──────────────┬─────────────┬──────────────┬───────────────┤
│  Brand Score │ Consistency │  CTR Uplift  │ Thumbnails    │
│    76.2 ✅   │   87% A     │   +81% 🚀    │   45 applied  │
├──────────────┴─────────────┴──────────────┴───────────────┤
│                                                            │
│  CTR Comparison:         Engagement Comparison:           │
│  ■ With Brand   3.8%     ■ With Brand   9.5%             │
│  □ Without      2.1%     □ Without      5.8%             │
│                                                            │
│  Color Usage:  ████████████░░  87%  ✅                    │
│  Typography:   ███████████░░░  82%  ✅                    │
│  Logo Present: █████████░░░░░  72%  ⚠️                    │
│  Guidelines:   ████████████░░  90%  ✅                    │
└────────────────────────────────────────────────────────────┘
```

---

## 🖥️ 8. Model Class — `ThumbnailAnalyticsModel`

```python
"""
database/models/thumbnail_analytics.py
=======================================
Model CRUD cho Thumbnail Analytics.
Module MỚI — Không sửa đổi analytics.py hiện có.
"""

import json
from datetime import datetime, timedelta
from typing import Optional, List
from database.connection import managed_connection, get_db_connection, _adapt_sql, _is_postgres
from config.config import logger


class ThumbnailAnalyticsModel:
    """CRUD và query nâng cao cho thumbnail_analytics."""

    @staticmethod
    def ensure_tables():
        """Tự tạo bảng nếu chưa tồn tại."""
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.executescript("""
                CREATE TABLE IF NOT EXISTS thumbnail_analytics ( ... );
                CREATE TABLE IF NOT EXISTS thumbnail_heatmap ( ... );
                CREATE TABLE IF NOT EXISTS thumbnail_template_stats ( ... );
            """)
            conn.commit()
        finally:
            conn.close()

    # ── CREATE ──────────────────────────────────────────────────────
    @staticmethod
    def record(workspace_id: int, asset_id: int, platform: str,
               period_start: str, period_end: str,
               impressions: int = 0, reach: int = 0,
               clicks: int = 0, saves: int = 0,
               shares: int = 0, likes: int = 0,
               comments: int = 0, post_id: int = None,
               ab_test_id: int = None, ab_variant_id: int = None,
               template_id: str = None, brand_status: str = 'unknown',
               thumbnail_url: str = None, source: str = 'manual') -> int:
        """Ghi nhận một bản ghi analytics cho thumbnail."""

        # Tính toán computed metrics
        ctr = (clicks / impressions * 100) if impressions > 0 else 0.0
        engagement = (likes + comments + shares) / max(reach, 1) * 100
        save_rate  = saves / max(reach, 1) * 100
        share_rate = shares / max(reach, 1) * 100
        virality   = (shares * 3 + saves * 2 + comments) / max(reach, 1) * 100

        # Tính thumbnail score
        from analytics.thumbnail_scorer import calculate_thumbnail_score
        score = calculate_thumbnail_score({
            'ctr': ctr, 'engagement_rate': engagement,
            'reach_rate': reach / 1000 * 100 if reach else 0,
            'save_rate': save_rate, 'share_rate': share_rate,
        })
        score_breakdown = json.dumps({
            'ctr_pts':   min(ctr / 5.0, 1.0) * 30,
            'eng_pts':   min(engagement / 10.0, 1.0) * 25,
            'save_pts':  min(save_rate / 3.0, 1.0) * 15,
            'share_pts': min(share_rate / 2.0, 1.0) * 10,
        })

        sql = _adapt_sql("""
            INSERT INTO thumbnail_analytics (
                workspace_id, asset_id, post_id, ab_test_id, ab_variant_id,
                platform, template_id, brand_status, thumbnail_url,
                impressions, reach, clicks, saves, shares, likes, comments,
                ctr, engagement_rate, save_rate, share_rate, virality_score,
                thumbnail_score, score_breakdown,
                period_start, period_end, source, collected_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """)
        now = datetime.now().isoformat()
        with managed_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (
                workspace_id, asset_id, post_id, ab_test_id, ab_variant_id,
                platform, template_id, brand_status, thumbnail_url,
                impressions, reach, clicks, saves, shares, likes, comments,
                round(ctr, 4), round(engagement, 4), round(save_rate, 4),
                round(share_rate, 4), round(virality, 4),
                round(score, 2), score_breakdown,
                period_start, period_end, source, now
            ))
            if _is_postgres():
                cur.execute("SELECT lastval()")
                return cur.fetchone()[0]
            return cur.lastrowid

    # ── READ ──────────────────────────────────────────────────────
    @staticmethod
    def get_by_asset(asset_id: int, workspace_id: int,
                     days: int = 30) -> list:
        """Lấy analytics của một thumbnail cụ thể."""
        since = (datetime.now() - timedelta(days=days)).isoformat()
        sql = _adapt_sql("""
            SELECT * FROM thumbnail_analytics
            WHERE asset_id=? AND workspace_id=? AND period_start >= ?
            ORDER BY period_start DESC
        """)
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute(sql, (asset_id, workspace_id, since))
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def get_workspace_summary(workspace_id: int, days: int = 30) -> dict:
        """Tổng hợp metrics của toàn workspace."""
        since = (datetime.now() - timedelta(days=days)).isoformat()
        sql = _adapt_sql("""
            SELECT
                COUNT(DISTINCT asset_id)        AS total_thumbnails,
                COALESCE(SUM(impressions), 0)   AS total_impressions,
                COALESCE(SUM(reach), 0)         AS total_reach,
                COALESCE(SUM(clicks), 0)        AS total_clicks,
                COALESCE(AVG(ctr), 0)           AS avg_ctr,
                COALESCE(AVG(engagement_rate),0) AS avg_engagement,
                COALESCE(AVG(save_rate), 0)     AS avg_save_rate,
                COALESCE(AVG(share_rate), 0)    AS avg_share_rate,
                COALESCE(AVG(thumbnail_score),0) AS avg_score,
                COALESCE(MAX(thumbnail_score),0) AS max_score,
                COALESCE(MIN(thumbnail_score),0) AS min_score
            FROM thumbnail_analytics
            WHERE workspace_id=? AND period_start >= ?
        """)
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute(sql, (workspace_id, since))
            cols = [d[0] for d in cur.description]
            row = cur.fetchone()
            return dict(zip(cols, row)) if row else {}
        finally:
            conn.close()

    @staticmethod
    def get_top_thumbnails(workspace_id: int, limit: int = 10,
                            platform: str = None, days: int = 30) -> list:
        """Lấy top thumbnail theo thumbnail_score."""
        since = (datetime.now() - timedelta(days=days)).isoformat()
        q = """
            SELECT ta.*, a.name, a.url
            FROM thumbnail_analytics ta
            LEFT JOIN assets a ON a.id = ta.asset_id
            WHERE ta.workspace_id=? AND ta.period_start >= ?
        """
        params = [workspace_id, since]
        if platform:
            q += _adapt_sql(" AND ta.platform=?")
            params.append(platform)
        q += " ORDER BY ta.thumbnail_score DESC"
        q += _adapt_sql(" LIMIT ?")
        params.append(limit)

        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute(_adapt_sql(q), params)
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def get_platform_breakdown(workspace_id: int, days: int = 30) -> list:
        """Phân tích theo từng platform."""
        since = (datetime.now() - timedelta(days=days)).isoformat()
        sql = _adapt_sql("""
            SELECT
                platform,
                COUNT(DISTINCT asset_id) AS thumbnail_count,
                AVG(ctr)                 AS avg_ctr,
                AVG(engagement_rate)     AS avg_engagement,
                AVG(thumbnail_score)     AS avg_score,
                SUM(impressions)         AS total_impressions,
                SUM(reach)               AS total_reach
            FROM thumbnail_analytics
            WHERE workspace_id=? AND period_start >= ?
            GROUP BY platform
            ORDER BY avg_score DESC
        """)
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute(sql, (workspace_id, since))
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]
        finally:
            conn.close()
```

---

## 🖥️ 9. UI Module — `ui/tab_thumbnail_analytics.py`

### 9.1 Cấu Trúc Tab

```
TAB: 📊 Thumbnail Analytics
│
├── 📈 Overview Dashboard
│   ├── KPI Cards: [Tổng Thumbnail] [Avg CTR] [Avg Score] [Top Performer]
│   ├── Trend Chart: CTR / Engagement theo thời gian (30 ngày)
│   └── Platform Breakdown: Bar chart theo platform
│
├── 🔥 Heatmap Viewer
│   ├── Dropdown: Chọn thumbnail
│   ├── Preview: Ảnh thumbnail + overlay heatmap
│   ├── Zone Table: Attention score từng vùng
│   └── Button: [🤖 Ước Tính Heatmap AI]
│
├── 🔬 A/B Testing
│   ├── List Tests đang chạy
│   ├── Bảng so sánh variant (side-by-side)
│   ├── Progress Bar: Tiến trình đến ngưỡng kết luận
│   └── Button: [🏆 Tuyên Bố Winner] [📊 Xem Chi Tiết]
│
├── 🏆 Template Ranking
│   ├── Bảng xếp hạng: [Rank] [Template] [CTR] [Score] [Usage]
│   ├── Filter: [Platform] [Category] [Thời gian]
│   └── Button: [📋 Dùng Template Này]
│
├── 🎨 Brand Performance
│   ├── Comparison Card: Brand vs No-Brand
│   ├── Brand Consistency Score
│   ├── Uplift Metrics
│   └── Khuyến nghị AI
│
└── 📤 Export
    ├── [📄 Xuất PDF Report]
    ├── [📊 Xuất CSV Data]
    └── [📋 Sao chép Báo Cáo Markdown]
```

### 9.2 KPI Cards Component

```python
def render_kpi_cards(summary: dict):
    """Hiển thị 4 KPI Cards chính."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="📊 Tổng Thumbnail",
            value=summary.get('total_thumbnails', 0),
            delta=f"+{summary.get('new_this_week', 0)} tuần này"
        )

    with col2:
        ctr = summary.get('avg_ctr', 0)
        st.metric(
            label="🎯 CTR Trung Bình",
            value=f"{ctr:.2f}%",
            delta=f"{summary.get('ctr_delta', 0):+.2f}% vs tuần trước",
            delta_color="normal"
        )

    with col3:
        score = summary.get('avg_score', 0)
        grade = "A" if score>=85 else "B" if score>=70 else "C" if score>=50 else "D"
        st.metric(
            label="⭐ Điểm TB Thumbnail",
            value=f"{score:.1f}/100 ({grade})",
            delta=f"{summary.get('score_delta', 0):+.1f} vs tuần trước"
        )

    with col4:
        st.metric(
            label="🚀 Top CTR",
            value=f"{summary.get('max_ctr', 0):.2f}%",
            delta="Thumbnail tốt nhất"
        )
```

---

## 📤 10. Export & Reporting

### 10.1 Cấu Trúc Báo Cáo PDF

```
THUMBNAIL ANALYTICS REPORT
===========================
Workspace: [Tên Workspace]
Kỳ báo cáo: [DD/MM/YYYY] → [DD/MM/YYYY]
Tạo lúc: [datetime]

1. TỔNG QUAN HIỆU SUẤT
   - Tổng thumbnail phân tích: X
   - CTR trung bình: X.XX%
   - Điểm thumbnail trung bình: XX.X/100
   - Thumbnail xuất sắc (Score ≥85): X

2. PHÂN TÍCH THEO PLATFORM
   [Bảng: Platform | CTR | Engagement | Score | Count]

3. TOP 5 THUMBNAIL HIỆU SUẤT CAO
   [Hình thumbnail + metrics chi tiết]

4. A/B TESTING SUMMARY
   [Kết quả các A/B test đã hoàn thành]
   [Winning thumbnails với % cải thiện]

5. HEATMAP INSIGHTS
   [Top 3 thumbnails với phân tích heatmap]

6. TEMPLATE RANKING
   [Bảng xếp hạng top 10 template]

7. BRAND PERFORMANCE
   [So sánh Brand vs No-Brand]
   [Brand Consistency Score]

8. KHUYẾN NGHỊ AI
   - [Khuyến nghị 1]
   - [Khuyến nghị 2]
   - [Khuyến nghị 3]
```

### 10.2 Export CSV Schema

```python
EXPORT_COLUMNS = [
    "thumbnail_id",       # asset_id
    "thumbnail_name",     # assets.name
    "thumbnail_url",      # URL ảnh
    "platform",
    "template_id",
    "brand_status",       # applied | proposed
    "period_start",
    "period_end",
    "impressions",
    "reach",
    "clicks",
    "saves",
    "shares",
    "likes",
    "comments",
    "ctr",
    "engagement_rate",
    "save_rate",
    "share_rate",
    "virality_score",
    "thumbnail_score",
    "ab_test_id",
    "ab_variant_id",
    "post_id",
    "campaign_id",
]
```

---

## 🤖 11. AI Recommendations Engine

```python
class ThumbnailAIAdvisor:
    """
    Sử dụng Gemini để phân tích analytics và đưa ra khuyến nghị hành động.
    """

    @staticmethod
    def generate_insights(workspace_id: int, api_key: str,
                          days: int = 30) -> list[dict]:
        """
        Phân tích toàn bộ dữ liệu analytics → sinh khuyến nghị hành động.
        """
        summary = ThumbnailAnalyticsModel.get_workspace_summary(workspace_id, days)
        platform_data = ThumbnailAnalyticsModel.get_platform_breakdown(workspace_id, days)
        top_thumbs = ThumbnailAnalyticsModel.get_top_thumbnails(workspace_id, limit=3, days=days)
        brand_perf = BrandPerformanceAnalyzer.compare_brand_vs_nobrand(workspace_id, days=days)

        prompt = f"""
Bạn là chuyên gia phân tích Marketing AI. Phân tích dữ liệu thumbnail analytics
và đưa ra 5 khuyến nghị hành động cụ thể, có thể thực hiện ngay.

DỮ LIỆU TỔNG QUAN ({days} ngày qua):
- Tổng thumbnail: {summary.get('total_thumbnails')}
- CTR trung bình: {summary.get('avg_ctr', 0):.2f}%
- Điểm trung bình: {summary.get('avg_score', 0):.1f}/100
- Engagement rate: {summary.get('avg_engagement', 0):.2f}%

PHÂN TÍCH THEO PLATFORM:
{json.dumps(platform_data, indent=2, ensure_ascii=False)}

BRAND PERFORMANCE:
- CTR với Brand Profile: {brand_perf['with_brand']['avg_ctr']:.2f}%
- CTR không Brand: {brand_perf['without_brand']['avg_ctr']:.2f}%
- Brand Uplift: {brand_perf['brand_uplift']['ctr_uplift']}

Trả về JSON array gồm 5 đối tượng:
[
  {{
    "priority": "high|medium|low",
    "title": "Tiêu đề khuyến nghị ngắn gọn",
    "insight": "Phân tích vấn đề phát hiện",
    "action": "Hành động cụ thể cần làm",
    "expected_impact": "CTR tăng khoảng X% hoặc Engagement tăng Y%",
    "icon": "Emoji phù hợp"
  }}
]

Ưu tiên những khuyến nghị có tác động cao nhất và dễ thực hiện nhất.
Chỉ trả về JSON thuần túy.
"""
        # Gọi Gemini → Parse → Return
        ...
```

---

## 🗺️ 12. Kiến Trúc Module Hoàn Chỉnh

```
analytics/
└── thumbnail/
    ├── __init__.py
    ├── thumbnail_scorer.py          # Tính điểm thumbnail
    ├── thumbnail_ab_decider.py      # Xác định winner A/B test
    ├── template_ranker.py           # Xếp hạng template
    ├── brand_performance.py         # Phân tích brand
    ├── heatmap_estimator.py         # Ước tính heatmap bằng AI
    └── ai_advisor.py                # Khuyến nghị AI

database/models/
├── thumbnail_analytics.py          # Model CRUD chính [MỚI]
├── thumbnail_heatmap.py            # Model heatmap [MỚI]
└── thumbnail_template_stats.py     # Model template ranking [MỚI]

ui/
└── tab_thumbnail_analytics.py      # Tab UI Analytics [MỚI]
```

---

## 📋 13. Kế Hoạch Triển Khai

### Phase 1 — Database & Core Analytics (Tuần 1)
- [ ] Tạo 3 bảng mới: `thumbnail_analytics`, `thumbnail_heatmap`, `thumbnail_template_stats`
- [ ] Viết `ThumbnailAnalyticsModel` với CRUD đầy đủ
- [ ] Viết `thumbnail_scorer.py` — công thức tính điểm
- [ ] Viết hàm nhập liệu thủ công từ UI

### Phase 2 — A/B Testing & Heatmap (Tuần 2)
- [ ] Mở rộng `ABTestModel.VALID_TEST_TYPES` cho thumbnail
- [ ] Viết `ThumbnailABDecider` — xác định winner
- [ ] Viết `ThumbnailHeatmapEstimator` — AI ước tính heatmap
- [ ] Tích hợp lưu heatmap vào DB

### Phase 3 — Template Ranking & Brand Performance (Tuần 3)
- [ ] Viết `TemplateRanker` — thuật toán xếp hạng
- [ ] Viết `BrandPerformanceAnalyzer` — so sánh brand vs no-brand
- [ ] Tạo job cron cập nhật ranking hàng ngày
- [ ] Viết `ThumbnailAIAdvisor` — tích hợp Gemini

### Phase 4 — UI & Export (Tuần 4)
- [ ] Viết `ui/tab_thumbnail_analytics.py` với Streamlit
- [ ] Thiết kế Overview Dashboard với Plotly
- [ ] Thiết kế Heatmap Viewer với overlay
- [ ] Tích hợp Export PDF/CSV
- [ ] Thêm tab vào `app/main.py`

---

## ✅ 14. Checklist Validation

### Database
- [ ] 3 bảng mới tạo thành công (SQLite + PostgreSQL)
- [ ] Index được tạo đúng cho các query phổ biến
- [ ] Dual DB compatibility (SQLite & PostgreSQL)
- [ ] Không sửa bất kỳ bảng hoặc model hiện có

### Analytics Engine
- [ ] `thumbnail_score` tính đúng theo công thức (0–100)
- [ ] `ctr = clicks/impressions*100` tính đúng
- [ ] `engagement_rate` có trọng số đúng
- [ ] Xử lý chia-cho-0 an toàn (division by zero guard)

### A/B Testing
- [ ] `test_type = "thumbnail"` hoạt động với `ABTestModel`
- [ ] `ThumbnailABDecider` trả về winner chính xác
- [ ] Ngưỡng confidence 80% được áp dụng
- [ ] `MIN_IMPRESSIONS = 500` trước khi kết luận

### Heatmap
- [ ] Tọa độ chuẩn hóa 0.0–1.0 đúng
- [ ] Zone classification logic chính xác
- [ ] AI estimation trả về JSON hợp lệ
- [ ] Visualization hiển thị đúng màu sắc

### Template Ranking
- [ ] Rank score tính đúng theo công thức MCDA
- [ ] Freshness decay hoạt động
- [ ] Top templates filter đúng theo platform
- [ ] Ranking cập nhật tự động sau mỗi ngày

### Brand Performance
- [ ] So sánh `brand_status = 'applied'` vs `'proposed'` đúng
- [ ] Brand uplift % tính đúng
- [ ] Brand consistency score (0–100) hợp lý

### UI & Export
- [ ] Tab analytics hiển thị đúng trong Streamlit
- [ ] KPI cards cập nhật real-time
- [ ] Heatmap overlay render chính xác
- [ ] PDF export có đủ 8 sections
- [ ] CSV export đúng schema 24 cột

---

## 🔗 15. Tích Hợp Hệ Sinh Thái

| Module | Quan Hệ | Loại |
|--------|---------|------|
| `THUMBNAIL_PROMPT_ENGINE.md` | Cung cấp `template_id`, `brand_status`, `style_tag` | Nguồn dữ liệu |
| `BRAND_THUMBNAIL_INTEGRATION.md` | Cung cấp `brand_status = applied/proposed` | Nguồn dữ liệu |
| `THUMBNAIL_PUBLISHING.md` | Cung cấp `asset_id`, `platform`, `post_id` sau publish | Nguồn dữ liệu |
| `database/models/ab_testing.py` | Mở rộng test_type, link `ab_test_id` | Tích hợp |
| `database/models/assets.py` | FK `asset_id` → thông tin ảnh | Tham chiếu |
| `ui/tab_analytics.py` | Cross-link sang Thumbnail Analytics | Navigation |
| `services/gemini_client.py` | AI Advisor + Heatmap Estimator | AI Engine |
| `core/doc_exporter.py` | Export PDF báo cáo | Export |

---

*Tài liệu này bổ sung cho hệ sinh thái Thumbnail Generator. Cập nhật lần cuối: 2026-07-12.*
