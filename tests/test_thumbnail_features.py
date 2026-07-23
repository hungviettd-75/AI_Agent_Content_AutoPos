"""
tests/test_thumbnail_features.py
=================================
Unit Tests và Integration Tests cho các tính năng Thumbnail:
- Spec & Processing
- Generation Service
- Analytics & Heatmap CRUD
"""

import unittest
import sys
import os

# Thêm đường dẫn dự án
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.connection import init_db
from database.models.thumbnail_analytics import ThumbnailAnalyticsModel
from services.thumbnail_publishing_service import get_spec, ThumbnailProcessor
from services.thumbnail_generator_service import ThumbnailGeneratorService

class TestThumbnailFeatures(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Khởi tạo database schema và tạo bảng."""
        init_db()
        ThumbnailAnalyticsModel.ensure_tables()

    def test_spec_retrieval(self):
        """Kiểm tra lấy thông số kỹ thuật (spec) cho các nền tảng."""
        spec_fb = get_spec("facebook", "post")
        self.assertIsNotNone(spec_fb)
        self.assertEqual(spec_fb.width, 1200)
        self.assertEqual(spec_fb.height, 630)

        spec_li = get_spec("linkedin", "post")
        self.assertIsNotNone(spec_li)
        self.assertEqual(spec_li.width, 1200)
        self.assertEqual(spec_li.height, 627)

    def test_thumbnail_analytics_crud(self):
        """Kiểm tra ghi nhận và lấy dữ liệu phân tích hiệu suất Thumbnail."""
        # 1. Record analytics
        rec_id = ThumbnailAnalyticsModel.record(
            workspace_id=1,
            asset_id=99,
            platform="linkedin",
            period_start="2026-07-12T00:00:00",
            period_end="2026-07-12T23:59:59",
            impressions=1000,
            reach=900,
            clicks=45,
            saves=10,
            shares=5,
            likes=20,
            comments=8
        )
        self.assertTrue(rec_id > 0)

        # 2. Get summary
        summary = ThumbnailAnalyticsModel.get_workspace_summary(workspace_id=1, days=1)
        self.assertTrue(summary.get("total_impressions") >= 1000)
        self.assertTrue(summary.get("avg_ctr") > 0)

        # 3. Get platform breakdown
        breakdown = ThumbnailAnalyticsModel.get_platform_breakdown(workspace_id=1, days=1)
        self.assertTrue(len(breakdown) > 0)

    def test_heatmap_recording(self):
        """Kiểm tra ghi nhận tọa độ click và heatmap của thumbnail."""
        ok = ThumbnailAnalyticsModel.record_heatmap_click(
            workspace_id=1,
            asset_id=99,
            x_norm=0.25,
            y_norm=0.45,
            zone_label="title",
            attention_score=0.9
        )
        self.assertTrue(ok)

        heatmap = ThumbnailAnalyticsModel.get_heatmap_by_asset(asset_id=99, workspace_id=1)
        self.assertTrue(len(heatmap) > 0)
        self.assertEqual(heatmap[0]["zone_label"], "title")

    def test_template_usage_tracking(self):
        """Kiểm tra theo dõi số lần sử dụng của template."""
        ok = ThumbnailAnalyticsModel.increment_template_usage(
            workspace_id=1,
            template_id="split_corporate",
            platform="linkedin",
            template_name="Corporate Split",
            template_category="corporate"
        )
        self.assertTrue(ok)

        templates = ThumbnailAnalyticsModel.list_templates(workspace_id=1)
        self.assertTrue(len(templates) > 0)

if __name__ == "__main__":
    unittest.main()
