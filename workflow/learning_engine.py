"""
workflow/learning_engine.py
============================
Learning Loop Engine: Phân tích dữ liệu Analytics để học và
sinh ra các Insights giúp cải thiện nội dung tương lai.
"""
import json
from datetime import datetime, timedelta
from database.connection import get_db_connection, _adapt_sql
from database.models.learning_insights import LearningInsightModel
from config.config import logger


# ══════════════════════════════════════════════════════════
# PHẦN 1: THU THẬP DỮ LIỆU ANALYTICS
# ══════════════════════════════════════════════════════════

def _fetch_analytics_data(workspace_id: int, days: int = 30) -> list:
    """Lấy analytics chi tiết trong N ngày gần đây."""
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    conn = get_db_connection()
    try:
        query = """
            SELECT
                a.post_id, p.topic, p.content_type, p.title,
                a.platform, a.metric_date,
                a.impressions, a.reach, a.likes, a.comments,
                a.shares, a.clicks, a.link_clicks,
                a.engagement_rate, a.raw_data
            FROM analytics a
            JOIN posts p ON a.post_id = p.id
            WHERE a.workspace_id = ? AND a.metric_date >= ?
            ORDER BY a.metric_date DESC
        """
        cur = conn.cursor()
        cur.execute(_adapt_sql(query), (workspace_id, cutoff))
        cols = [d[0] for d in cur.description]
        rows = []
        for row in cur.fetchall():
            d = dict(zip(cols, row))
            try:
                raw = json.loads(d.get("raw_data") or "{}")
                d["leads"]    = raw.get("leads", 0)
                d["revenue"]  = raw.get("revenue", 0)
                d["ad_spend"] = raw.get("ad_spend", 0)
            except Exception:
                d["leads"] = d["revenue"] = d["ad_spend"] = 0
            rows.append(d)
        return rows
    finally:
        conn.close()


# ══════════════════════════════════════════════════════════
# PHẦN 2: PHÂN TÍCH THỐNG KÊ (Không cần AI)
# ══════════════════════════════════════════════════════════

def _analyze_platform_performance(rows: list) -> list:
    """So sánh hiệu quả giữa các nền tảng."""
    from collections import defaultdict
    plat_stats = defaultdict(lambda: {"reach": 0, "clicks": 0, "leads": 0,
                                      "impressions": 0, "revenue": 0, "ad_spend": 0,
                                      "count": 0})
    for r in rows:
        p = r.get("platform", "unknown")
        plat_stats[p]["reach"] += r.get("reach", 0)
        plat_stats[p]["clicks"] += r.get("clicks", 0)
        plat_stats[p]["leads"] += r.get("leads", 0)
        plat_stats[p]["impressions"] += r.get("impressions", 0)
        plat_stats[p]["revenue"] += r.get("revenue", 0)
        plat_stats[p]["ad_spend"] += r.get("ad_spend", 0)
        plat_stats[p]["count"] += 1

    insights = []
    for plat, s in plat_stats.items():
        if s["count"] < 2:
            continue
        ctr = (s["clicks"] / s["impressions"] * 100) if s["impressions"] > 0 else 0
        roi = ((s["revenue"] - s["ad_spend"]) / s["ad_spend"] * 100) if s["ad_spend"] > 0 else 0
        avg_leads = s["leads"] / s["count"]
        avg_reach = s["reach"] / s["count"]

        if ctr > 4.0:
            insights.append({
                "type": "platform_strategy",
                "platform": plat,
                "title": f"🏆 {plat.upper()} có CTR xuất sắc ({ctr:.1f}%)",
                "description": f"Nền tảng {plat.upper()} đang đạt CTR {ctr:.1f}% — vượt ngưỡng tốt 4%. Trung bình {avg_reach:.0f} reach/bài.",
                "recommendation": f"Tăng ngân sách và tần suất đăng bài trên {plat.upper()}. Ưu tiên định dạng và giờ đăng đang hiệu quả.",
                "metrics": {"avg_reach": avg_reach, "ctr": ctr, "avg_leads": avg_leads, "roi": roi},
                "confidence": min(0.95, 0.6 + ctr / 20),
                "sample_size": s["count"],
            })
        if roi > 100:
            insights.append({
                "type": "platform_strategy",
                "platform": plat,
                "title": f"💰 ROI {plat.upper()} đang cực kỳ tốt ({roi:.0f}%)",
                "description": f"Mỗi đồng chi vào {plat.upper()} đang mang về {roi/100+1:.1f}x. Tổng {s['leads']} leads với {s['count']} bài.",
                "recommendation": f"Tăng ngân sách quảng cáo trên {plat.upper()} thêm 20-30%. Nhân rộng định dạng nội dung đang hiệu quả.",
                "metrics": {"roi": roi, "total_leads": s["leads"], "revenue": s["revenue"]},
                "confidence": min(0.92, 0.65 + roi / 500),
                "sample_size": s["count"],
            })
    return insights


def _analyze_content_type_performance(rows: list) -> list:
    """Phân tích loại nội dung nào hiệu quả nhất."""
    from collections import defaultdict
    ctype_stats = defaultdict(lambda: {"er": 0, "reach": 0, "leads": 0,
                                       "clicks": 0, "impressions": 0, "count": 0})
    for r in rows:
        ct = r.get("content_type", "unknown")
        er = r.get("engagement_rate", 0) or 0
        ctype_stats[ct]["er"] += er
        ctype_stats[ct]["reach"] += r.get("reach", 0)
        ctype_stats[ct]["leads"] += r.get("leads", 0)
        ctype_stats[ct]["clicks"] += r.get("clicks", 0)
        ctype_stats[ct]["impressions"] += r.get("impressions", 0)
        ctype_stats[ct]["count"] += 1

    insights = []
    ct_list = [(ct, s) for ct, s in ctype_stats.items() if s["count"] >= 2]
    if not ct_list:
        return insights

    best_ct = max(ct_list, key=lambda x: x[1]["er"] / max(x[1]["count"], 1))
    ct, s = best_ct
    avg_er = s["er"] / s["count"]
    avg_leads = s["leads"] / s["count"]
    ctr = (s["clicks"] / s["impressions"] * 100) if s["impressions"] > 0 else 0

    label_map = {
        "marketing_viral": "Marketing Viral",
        "ai_knowledge": "AI Knowledge",
        "case_study": "Case Study",
        "reels": "Reels",
    }
    ct_label = label_map.get(ct, ct.title())

    insights.append({
        "type": "content_pattern",
        "content_type": ct,
        "title": f"✍️ Loại nội dung '{ct_label}' đang dẫn đầu Engagement",
        "description": f"'{ct_label}' đạt Engagement Rate trung bình {avg_er:.2f}% — cao nhất trong tất cả loại nội dung. Trung bình {avg_leads:.1f} leads/bài.",
        "recommendation": f"Tăng tỷ lệ bài '{ct_label}' trong lịch đăng. Đặt mục tiêu 40-50% content mix là loại này.",
        "metrics": {"avg_er": avg_er, "avg_leads": avg_leads, "ctr": ctr},
        "confidence": min(0.90, 0.55 + avg_er / 10),
        "sample_size": s["count"],
    })
    return insights


def _analyze_topic_patterns(rows: list) -> list:
    """Tìm các pattern chủ đề từ các bài có hiệu suất cao."""
    from collections import defaultdict
    sorted_rows = sorted(rows, key=lambda x: x.get("engagement_rate", 0) or 0, reverse=True)
    top20pct = sorted_rows[:max(3, int(len(sorted_rows) * 0.2))]

    if len(top20pct) < 2:
        return []

    # Keyword frequency trong topic của các bài top
    from collections import Counter
    words = []
    for r in top20pct:
        topic = str(r.get("topic", ""))
        words.extend([w.lower() for w in topic.split() if len(w) > 3])
    freq = Counter(words).most_common(5)

    if not freq:
        return []

    top_words = ", ".join([f"'{w}'" for w, _ in freq])
    avg_er = sum(r.get("engagement_rate", 0) or 0 for r in top20pct) / len(top20pct)
    avg_reach = sum(r.get("reach", 0) for r in top20pct) / len(top20pct)

    return [{
        "type": "topic_performance",
        "title": f"🔑 Từ khoá hot trong nội dung top: {top_words}",
        "description": f"Top {len(top20pct)} bài viết hiệu quả nhất đạt ER {avg_er:.2f}% và reach {avg_reach:.0f} thường chứa các từ khoá: {top_words}.",
        "recommendation": f"Ưu tiên sử dụng các chủ đề chứa {top_words} trong các bài viết tới. Kết hợp với loại nội dung mạnh nhất của workspace.",
        "metrics": {"avg_er": avg_er, "avg_reach": avg_reach, "sample_size": len(top20pct)},
        "confidence": 0.70,
        "sample_size": len(top20pct),
    }]


def _analyze_timing(rows: list) -> list:
    """Phân tích thời điểm đăng bài hiệu quả theo ngày trong tuần."""
    from collections import defaultdict
    day_map = {0: "Thứ 2", 1: "Thứ 3", 2: "Thứ 4", 3: "Thứ 5", 4: "Thứ 6", 5: "Thứ 7", 6: "Chủ nhật"}
    day_stats = defaultdict(lambda: {"er": 0, "count": 0})
    for r in rows:
        try:
            dt = datetime.strptime(r.get("metric_date", ""), "%Y-%m-%d")
            dow = dt.weekday()
            day_stats[dow]["er"] += r.get("engagement_rate", 0) or 0
            day_stats[dow]["count"] += 1
        except Exception:
            continue

    if not day_stats:
        return []

    best_day_idx = max(day_stats, key=lambda d: day_stats[d]["er"] / max(day_stats[d]["count"], 1))
    best_er = day_stats[best_day_idx]["er"] / max(day_stats[best_day_idx]["count"], 1)
    best_day_name = day_map.get(best_day_idx, "Không xác định")

    return [{
        "type": "timing",
        "title": f"📅 {best_day_name} là ngày đăng hiệu quả nhất (ER {best_er:.2f}%)",
        "description": f"Bài đăng vào {best_day_name} đạt Engagement Rate trung bình {best_er:.2f}% — cao nhất trong tuần.",
        "recommendation": f"Ưu tiên lên lịch các bài quan trọng vào {best_day_name}. Thử thêm 1-2 bài vào ngày này mỗi tuần.",
        "metrics": {"best_er": best_er, "day": best_day_name},
        "confidence": 0.75,
        "sample_size": day_stats[best_day_idx]["count"],
    }]


# ══════════════════════════════════════════════════════════
# PHẦN 3: AI GENERATE INSIGHTS (Dùng Gemini)
# ══════════════════════════════════════════════════════════

def generate_ai_insights(workspace_id: int, api_key: str, days: int = 30) -> tuple:
    """Dùng Gemini AI để phân tích sâu và sinh Insights từ Analytics."""
    from services.gemini_client import generate_with_gemini

    rows = _fetch_analytics_data(workspace_id, days)
    if not rows:
        return False, "Không có dữ liệu analytics để phân tích."

    # Tổng hợp dữ liệu gọn gửi cho AI
    total_imp  = sum(r.get("impressions", 0) for r in rows)
    total_reach = sum(r.get("reach", 0) for r in rows)
    total_clicks = sum(r.get("clicks", 0) for r in rows)
    total_leads  = sum(r.get("leads", 0) for r in rows)
    total_rev    = sum(r.get("revenue", 0) for r in rows)
    total_spend  = sum(r.get("ad_spend", 0) for r in rows)

    ctr = (total_clicks / total_imp * 100) if total_imp > 0 else 0
    roi = ((total_rev - total_spend) / max(total_spend, 1) * 100)

    # Top 10 bài hiệu quả nhất
    top_posts = sorted(rows, key=lambda x: x.get("engagement_rate", 0) or 0, reverse=True)[:10]
    top_summary = [{
        "topic": r.get("topic", "")[:60],
        "content_type": r.get("content_type"),
        "platform": r.get("platform"),
        "er": round(r.get("engagement_rate", 0) or 0, 2),
        "reach": r.get("reach", 0),
        "leads": r.get("leads", 0),
    } for r in top_posts]

    prompt = f"""
Bạn là AI Learning Engine — hệ thống tự học để cải thiện Marketing Content.
Nhiệm vụ: Phân tích dữ liệu analytics và sinh ra CÁC INSIGHTS CHẤT LƯỢNG CAO dạng JSON.

DỮ LIỆU TỔNG HỢP ({days} ngày gần đây):
- Tổng bài phân tích: {len(rows)}
- Reach: {total_reach:,} | Impressions: {total_imp:,}
- CTR: {ctr:.2f}% | ROI: {roi:.1f}%
- Tổng Leads: {total_leads:,}

TOP 10 BÀI HIỆU QUẢ NHẤT:
{json.dumps(top_summary, ensure_ascii=False, indent=2)}

Hãy trả về JSON array với 3-5 insights theo cấu trúc sau (KHÔNG thêm markdown, CHỈ JSON thuần):
[
  {{
    "insight_type": "content_pattern|platform_strategy|timing|audience|cta_effectiveness|topic_performance",
    "platform": "facebook|linkedin|zalo|null",
    "content_type": "marketing_viral|ai_knowledge|case_study|reels|null",
    "title": "Tên insight ngắn gọn, có emoji",
    "description": "Mô tả chi tiết insight dựa trên số liệu (2-3 câu)",
    "recommendation": "Hướng dẫn hành động cụ thể để áp dụng insight này (2-3 câu)",
    "confidence": 0.0-1.0
  }}
]
"""
    try:
        raw_response = generate_with_gemini(prompt, api_key=api_key)
        # Tìm JSON trong response
        start = raw_response.find("[")
        end = raw_response.rfind("]") + 1
        if start == -1 or end == 0:
            return False, "AI không trả về JSON hợp lệ."
        ai_insights = json.loads(raw_response[start:end])
        return True, ai_insights
    except json.JSONDecodeError as e:
        return False, f"Lỗi parse JSON: {e}"
    except Exception as e:
        return False, f"Lỗi Gemini: {e}"


# ══════════════════════════════════════════════════════════
# PHẦN 4: PUBLIC ENTRY POINT
# ══════════════════════════════════════════════════════════

def run_learning_loop(workspace_id: int, days: int = 30,
                      api_key: str = None, use_ai: bool = True) -> dict:
    """
    Chạy toàn bộ vòng lặp học:
    1. Thu thập analytics
    2. Phân tích thống kê (luôn chạy)
    3. Phân tích AI (nếu có api_key)
    4. Lưu tất cả insights vào DB
    Returns: dict với keys: statistical_count, ai_count, errors
    """
    result = {"statistical_count": 0, "ai_count": 0, "errors": []}

    rows = _fetch_analytics_data(workspace_id, days)
    if not rows:
        result["errors"].append("Không có dữ liệu analytics.")
        return result

    # ── Phân tích thống kê ──
    stat_insights = []
    stat_insights += _analyze_platform_performance(rows)
    stat_insights += _analyze_content_type_performance(rows)
    stat_insights += _analyze_topic_patterns(rows)
    stat_insights += _analyze_timing(rows)

    for ins in stat_insights:
        try:
            m = ins.get("metrics", {})
            LearningInsightModel.create(
                workspace_id=workspace_id,
                title=ins["title"],
                description=ins.get("description", ""),
                recommendation=ins.get("recommendation", ""),
                insight_type=ins.get("type", "content_pattern"),
                platform=ins.get("platform"),
                content_type=ins.get("content_type"),
                avg_reach=m.get("avg_reach", 0),
                avg_ctr=m.get("ctr", 0),
                avg_er=m.get("avg_er", 0),
                avg_leads=m.get("avg_leads", 0),
                avg_roi=m.get("roi", 0),
                sample_size=ins.get("sample_size", 0),
                confidence=ins.get("confidence", 0.7),
                data_snapshot=ins.get("metrics", {}),
            )
            result["statistical_count"] += 1
        except Exception as e:
            result["errors"].append(f"Stat insight lỗi: {e}")

    # ── Phân tích AI (nếu có key) ──
    if use_ai and api_key:
        ok, ai_result = generate_ai_insights(workspace_id, api_key, days)
        if ok and isinstance(ai_result, list):
            for ins in ai_result:
                try:
                    LearningInsightModel.create(
                        workspace_id=workspace_id,
                        title=ins.get("title", "AI Insight"),
                        description=ins.get("description", ""),
                        recommendation=ins.get("recommendation", ""),
                        insight_type=ins.get("insight_type", "content_pattern"),
                        platform=ins.get("platform"),
                        content_type=ins.get("content_type"),
                        confidence=float(ins.get("confidence", 0.75)),
                        data_snapshot={"source": "gemini_ai"},
                    )
                    result["ai_count"] += 1
                except Exception as e:
                    result["errors"].append(f"AI insight lỗi: {e}")
        else:
            result["errors"].append(str(ai_result))

    logger.info(f"[LEARNING] Vong lap hoc hoan tat: stat={result['statistical_count']}, ai={result['ai_count']}")
    return result


def get_insights_as_context(workspace_id: int, max_insights: int = 5) -> str:
    """
    Trả về context string từ các insights đang active để nhúng vào prompt tạo nội dung.
    Giúp AI tạo nội dung học từ kết quả thực tế.
    """
    active = LearningInsightModel.get_active(workspace_id)[:max_insights]
    if not active:
        return ""

    lines = ["=== LEARNING LOOP CONTEXT (Học từ Analytics) ==="]
    for ins in active:
        lines.append(f"• [{ins['insight_type'].upper()}] {ins['title']}")
        lines.append(f"  → {ins['recommendation']}")
    lines.append("=== KẾT THÚC CONTEXT ===")
    return "\n".join(lines)
