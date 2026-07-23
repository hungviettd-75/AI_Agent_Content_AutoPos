import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import database.connection as db_connection
from database.connection import init_db
from database.migrations.content_strategy_center import down as migrate_down, up as migrate_up
from database.models.analytics import AnalyticsModel
from database.models.companies import CompanyModel
from database.models.learning_insights import LearningInsightModel
from database.models.posts import PostModel
from database.models.users import UserModel
from database.models.workspaces import WorkspaceModel
from database.repositories.content_strategy_repository import ContentStrategyRepository
from services.content_strategy_learning_service import ContentStrategyLearningService


class TestContentStrategyLearningLoop(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        cls.tmp.close()
        cls.original_db_path = db_connection.DB_PATH
        cls.original_engine = db_connection.DB_ENGINE
        db_connection.DB_PATH = cls.tmp.name
        db_connection.DB_ENGINE = "sqlite"
        init_db()
        migrate_up(engine="sqlite")

    @classmethod
    def tearDownClass(cls):
        try:
            migrate_down(engine="sqlite")
        finally:
            db_connection.DB_PATH = cls.original_db_path
            db_connection.DB_ENGINE = cls.original_engine
            if os.path.exists(cls.tmp.name):
                os.unlink(cls.tmp.name)

    def setUp(self):
        suffix = str(id(self))
        self.user_id = UserModel.create(f"learn{suffix}@example.com", f"learn{suffix}", "secret")
        self.workspace_id = WorkspaceModel.create(f"Learning Workspace {suffix}", owner_id=self.user_id)
        self.other_workspace_id = WorkspaceModel.create(f"Other Learning Workspace {suffix}", owner_id=self.user_id)
        self.company_id = CompanyModel.create(self.workspace_id, f"Learning Company {suffix}")
        self.other_company_id = CompanyModel.create(self.other_workspace_id, f"Other Company {suffix}")
        self.strategy_id = ContentStrategyRepository.create_strategy(self.workspace_id, self.company_id, "Learning Strategy")
        self.pillar_id = ContentStrategyRepository.create_pillar(self.workspace_id, self.company_id, self.strategy_id, "Education")
        self.other_pillar_id = ContentStrategyRepository.create_pillar(self.workspace_id, self.company_id, self.strategy_id, "Product")
        self.subtopic_id = ContentStrategyRepository.create_subtopic(self.workspace_id, self.company_id, self.strategy_id, self.pillar_id, "AI Planning", target_persona="Founder", funnel_stage="consideration")
        self.other_subtopic_id = ContentStrategyRepository.create_subtopic(self.workspace_id, self.company_id, self.strategy_id, self.other_pillar_id, "Product Demo", target_persona="Ops Lead", funnel_stage="conversion")
        self.angle_ids = ContentStrategyRepository.create_angles_batch(
            self.workspace_id,
            self.company_id,
            self.strategy_id,
            [
                {"pillar_id": self.pillar_id, "subtopic_id": self.subtopic_id, "title": "Planning mistake", "cta": "Book a demo", "target_persona": "Founder", "funnel_stage": "consideration"},
                {"pillar_id": self.other_pillar_id, "subtopic_id": self.other_subtopic_id, "title": "Product walkthrough", "cta": "Download checklist", "target_persona": "Ops Lead", "funnel_stage": "conversion"},
            ],
            created_by=self.user_id,
        )
        self.format_ids = ContentStrategyRepository.create_format_variants_batch(
            self.workspace_id,
            self.company_id,
            self.strategy_id,
            [
                {"angle_id": self.angle_ids[0], "platform": "linkedin", "format": "Carousel", "cta": "Book a demo"},
                {"angle_id": self.angle_ids[1], "platform": "facebook", "format": "Short post", "cta": "Download checklist"},
            ],
            created_by=self.user_id,
        )
        self.campaign_id = ContentStrategyRepository.create_campaign(self.workspace_id, self.company_id, "Launch Campaign", cta="Book a demo", created_by=self.user_id)
        self.lead_magnet_id = ContentStrategyRepository.create_lead_magnet(self.workspace_id, self.company_id, self.strategy_id, "AI Checklist", cta="Download checklist", target_persona="Founder", created_by=self.user_id)

    def _create_mapped_post(self, platform="linkedin", high=True, index=0):
        pillar_id = self.pillar_id if high else self.other_pillar_id
        subtopic_id = self.subtopic_id if high else self.other_subtopic_id
        angle_id = self.angle_ids[0] if high else self.angle_ids[1]
        format_id = self.format_ids[0] if high else self.format_ids[1]
        post_id = PostModel.create(
            content=f"Content {platform} {index}",
            platform=platform,
            content_type="marketing_viral",
            topic="AI Planning" if high else "Product Demo",
            title=f"Post {index}",
            status="published",
            campaign_id=self.campaign_id,
            workspace_id=self.workspace_id,
            viral_score=8 if high else 4,
            created_by=self.user_id,
        )
        item_id = ContentStrategyRepository.create_calendar_items_batch(
            self.workspace_id,
            self.company_id,
            self.strategy_id,
            [
                {
                    "post_id": post_id,
                    "pillar_id": pillar_id,
                    "subtopic_id": subtopic_id,
                    "angle_id": angle_id,
                    "format_variant_id": format_id,
                    "campaign_id": self.campaign_id,
                    "title": f"Calendar {index}",
                    "platform": platform,
                    "content_type": "marketing_viral",
                    "planned_date": f"2026-07-{10 + index:02d}",
                    "scheduled_at": f"2026-07-{10 + index:02d}T09:00:00+07:00",
                }
            ],
            created_by=self.user_id,
        )[0]
        if high:
            ContentStrategyRepository.link_lead_magnet_to_calendar_items(self.workspace_id, self.company_id, self.strategy_id, self.lead_magnet_id, [item_id], created_by=self.user_id)
        AnalyticsModel.upsert(
            post_id=post_id,
            platform=platform,
            metric_date=f"2026-07-{10 + index:02d}",
            impressions=1000,
            reach=800,
            likes=120 if high else 20,
            comments=20 if high else 2,
            shares=10 if high else 1,
            saves=5 if high else 0,
            clicks=90 if high else 15,
            link_clicks=70 if high else 5,
            raw_data={"leads": 8 if high else 1, "revenue": 0, "ad_spend": 0},
            workspace_id=self.workspace_id,
        )
        return post_id, item_id

    def _seed_valid_analytics(self):
        for i in range(3):
            self._create_mapped_post("linkedin", high=True, index=i)
        for i in range(3, 6):
            self._create_mapped_post("facebook", high=False, index=i)

    def test_no_data_does_not_create_insight(self):
        result = ContentStrategyLearningService.generate_recommendations(self.workspace_id, self.company_id, self.strategy_id, days=30)
        self.assertTrue(result["ok"])
        self.assertEqual(result["sample_size"], 0)
        self.assertEqual(result.get("created"), 0)
        self.assertEqual(LearningInsightModel.list_by_workspace(self.workspace_id, company_id=self.company_id, strategy_id=self.strategy_id), [])

    def test_insufficient_sample_reports_warning_without_creating(self):
        self._create_mapped_post("linkedin", high=True, index=1)
        self._create_mapped_post("facebook", high=False, index=2)
        result = ContentStrategyLearningService.generate_recommendations(self.workspace_id, self.company_id, self.strategy_id, days=30)
        self.assertEqual(result["sample_size"], 2)
        self.assertEqual(result["created"], 0)
        self.assertTrue(any("Insufficient" in warning for warning in result["warnings"]))

    def test_valid_insight_contains_evidence_sample_and_mapping(self):
        self._seed_valid_analytics()
        result = ContentStrategyLearningService.generate_recommendations(self.workspace_id, self.company_id, self.strategy_id, days=30, metric="engagement_rate", created_by=self.user_id)
        self.assertGreater(result["created"], 0)
        insights = LearningInsightModel.list_by_workspace(self.workspace_id, company_id=self.company_id, strategy_id=self.strategy_id)
        platform = next(item for item in insights if item["insight_type"] == "platform_strategy")
        self.assertEqual(platform["affected_platform"], "linkedin")
        self.assertEqual(platform["sample_size"], 3)
        self.assertIn("2026-07-10", platform["evidence_period"])
        self.assertEqual(platform["metric"], "engagement_rate")
        self.assertIn("correlated", platform["observation"])
        self.assertTrue(platform["data_quality"].get("is_reliable"))

    def test_accept_reject_version_creation_and_rollback(self):
        self._seed_valid_analytics()
        generated = ContentStrategyLearningService.generate_recommendations(self.workspace_id, self.company_id, self.strategy_id, days=30)
        insight_id = generated["insight_ids"][0]
        rejected_id = generated["insight_ids"][1]
        reject = ContentStrategyLearningService.reject_recommendation(self.workspace_id, self.company_id, rejected_id, user_id=self.user_id, reason="Not aligned")
        self.assertTrue(reject["ok"])
        self.assertEqual(LearningInsightModel.get_by_id(rejected_id)["status"], "rejected")

        accept = ContentStrategyLearningService.accept_recommendation(self.workspace_id, self.company_id, insight_id, user_id=self.user_id)
        self.assertTrue(accept["ok"])
        applied = ContentStrategyLearningService.create_revised_version(self.workspace_id, self.company_id, self.strategy_id, insight_id, user_id=self.user_id)
        self.assertTrue(applied["ok"])
        strategy = ContentStrategyRepository.get_strategy(self.workspace_id, self.company_id, self.strategy_id, include_children=False)
        self.assertEqual(strategy["metadata"]["strategy_revision_source"], "learning_loop")
        self.assertEqual(strategy["metadata"]["applied_learning_insights"][0]["insight_id"], insight_id)

        version_after_apply = ContentStrategyRepository.create_strategy_version(self.workspace_id, self.company_id, self.strategy_id, notes="After apply", created_by=self.user_id)
        compare = ContentStrategyLearningService.compare_versions(self.workspace_id, self.company_id, self.strategy_id, applied["version_id"], version_after_apply)
        self.assertTrue(compare["ok"])
        self.assertTrue(compare["metadata_changed"])

        restored = ContentStrategyLearningService.restore_previous_version(self.workspace_id, self.company_id, self.strategy_id, applied["version_id"], user_id=self.user_id)
        self.assertTrue(restored["ok"])
        restored_strategy = ContentStrategyRepository.get_strategy(self.workspace_id, self.company_id, self.strategy_id, include_children=False)
        self.assertNotIn("applied_learning_insights", restored_strategy.get("metadata") or {})

    def test_workspace_isolation_and_analytics_mapping(self):
        self._seed_valid_analytics()
        unmapped_post_id = PostModel.create("Unmapped", platform="linkedin", workspace_id=self.workspace_id, status="published")
        AnalyticsModel.upsert(unmapped_post_id, "linkedin", "2026-07-16", impressions=1000, reach=900, likes=500, comments=0, shares=0, workspace_id=self.workspace_id)
        rows = ContentStrategyLearningService.fetch_mapped_analytics(self.workspace_id, self.company_id, self.strategy_id, days=30)
        self.assertEqual(len(rows), 6)

        isolated = ContentStrategyLearningService.analyze_strategy(self.other_workspace_id, self.company_id, self.strategy_id, days=30)
        self.assertFalse(isolated["ok"])


if __name__ == "__main__":
    unittest.main()
