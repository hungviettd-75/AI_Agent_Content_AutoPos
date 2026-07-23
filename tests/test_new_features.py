"""tests/test_new_features.py — Bộ kiểm thử tự động (Unit Tests & Integration Tests) cho các tính năng mới."""
import unittest
import sys
import os

# Thêm đường dẫn vào sys.path để import các module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.connection import init_db, get_db_connection
from database.models.learning_insights import LearningInsightModel
from database.models.ab_testing import ABTestModel
from database.models.ai_cost import AICostModel
from database.models.billing import BillingModel
from services.monitoring_service import MonitoringService
from workflow.learning_engine import run_learning_loop

class TestNewFeatures(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Khởi tạo database schema V2 và tạo các bảng cần thiết."""
        init_db()
        # Đảm bảo các bảng tính năng nâng cao đã được verify/tạo
        AICostModel.ensure_table()
        ABTestModel.ensure_tables()
        BillingModel.ensure_tables()

    def test_learning_insights_crud(self):
        """Kiểm tra quy trình tạo, lấy và cập nhật trạng thái của Learning Insights."""
        # 1. Tạo mới insight
        insight_id = LearningInsightModel.create(
            workspace_id=1,
            title="Test Insight",
            description="Mô tả thử nghiệm",
            recommendation="Đề xuất thử nghiệm",
            insight_type="content_pattern",
            confidence=0.85
        )
        self.assertIsNotNone(insight_id)
        self.assertTrue(insight_id > 0)

        # 2. Lấy danh sách active
        active = LearningInsightModel.get_active(workspace_id=1)
        self.assertTrue(len(active) > 0)
        
        # 3. Cập nhật trạng thái sang applied
        ok = LearningInsightModel.update_status(insight_id, "applied")
        self.assertTrue(ok)

        # 4. Tăng số lượng áp dụng
        ok_inc = LearningInsightModel.increment_applied(insight_id)
        self.assertTrue(ok_inc)

    def test_ab_testing_flow(self):
        """Kiểm tra luồng tạo test, thêm variant, cập nhật metric và hoàn thành A/B test."""
        # 1. Tạo test mới
        test_id = ABTestModel.create_test(
            workspace_id=1,
            name="Test A/B Headline",
            test_type="headline",
            topic="AI Portal"
        )
        self.assertIsNotNone(test_id)

        # 2. Thêm Variant A và B
        var_a = ABTestModel.add_variant(test_id, "Góc câu chuyện", "A", "Nội dung kể câu chuyện...")
        var_b = ABTestModel.add_variant(test_id, "Góc trực diện", "B", "Nội dung trực diện vào tính năng...")
        self.assertTrue(var_a > 0)
        self.assertTrue(var_b > 0)

        # 3. Ghi nhận tương tác
        ok_a = ABTestModel.update_variant_metrics(var_a, impressions=1000, clicks=50, conversions=5, leads=2)
        ok_b = ABTestModel.update_variant_metrics(var_b, impressions=1000, clicks=80, conversions=10, leads=5)
        self.assertTrue(ok_a)
        self.assertTrue(ok_b)

        # 4. Tuyên bố Winner
        ok_win = ABTestModel.update_test_status(test_id, "completed", winner_id=var_b)
        self.assertTrue(ok_win)

        # Kiểm tra lại thông tin test
        test_info = ABTestModel.get_test(test_id)
        self.assertEqual(test_info["status"], "completed")
        self.assertEqual(test_info["winner_id"], var_b)

    def test_ai_cost_logging(self):
        """Kiểm tra ghi nhận chi phí, token và độ trễ sử dụng API AI."""
        # 1. Ghi log thành công
        ok = AICostModel.log(
            workspace_id=1,
            provider="Gemini",
            model_name="gemini-2.5-flash",
            prompt_tokens=1500,
            completion_tokens=500,
            cost=0.0003,
            latency_ms=850,
            feature="Social Writer"
        )
        self.assertTrue(ok)

        # 2. Lấy dữ liệu thống kê
        summary = AICostModel.get_summary(workspace_id=1, days=1)
        self.assertTrue(len(summary) > 0)
        self.assertEqual(summary[0]["provider"], "Gemini")

    def test_monitoring_service(self):
        """Kiểm tra hoạt động của service giám sát hiệu năng hệ thống."""
        db_health = MonitoringService.check_db_health()
        self.assertEqual(db_health["status"], "healthy")
        self.assertTrue(db_health["latency_ms"] >= 0)

        sys_metrics = MonitoringService.check_system_metrics()
        self.assertIn("cpu_usage_pct", sys_metrics)
        self.assertIn("ram", sys_metrics)

        alerts = MonitoringService.get_active_alerts(sys_metrics, db_health, {})
        self.assertIsInstance(alerts, list)

if __name__ == "__main__":
    unittest.main()
