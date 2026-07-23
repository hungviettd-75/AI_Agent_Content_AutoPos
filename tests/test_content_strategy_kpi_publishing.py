import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import database.connection as db_connection
from config import settings
from database.connection import init_db
from database.migrations.content_strategy_center import down as migrate_down, up as migrate_up
from database.models.companies import CompanyModel
from database.models.posts import PostModel
from database.models.schedules import ScheduleModel
from database.models.users import UserModel
from database.models.workspaces import WorkspaceModel
from database.repositories.content_strategy_repository import ContentStrategyRepository
from services.content_strategy_service import (
    check_publishing_readiness,
    create_strategy_kpi,
    handoff_calendar_item_to_content_studio_draft,
    list_strategy_kpis,
    send_selected_calendar_items_to_content_studio,
    sync_calendar_publishing_status,
)


class TestContentStrategyKpiPublishing(unittest.TestCase):
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
        cls.original_tokens = {
            "FB_PAGE_ID": settings.FB_PAGE_ID,
            "FB_ACCESS_TOKEN": settings.FB_ACCESS_TOKEN,
            "ZALO_ACCESS_TOKEN": settings.ZALO_ACCESS_TOKEN,
            "LINKEDIN_AUTHOR_URN": settings.LINKEDIN_AUTHOR_URN,
            "LINKEDIN_ACCESS_TOKEN": settings.LINKEDIN_ACCESS_TOKEN,
        }

    @classmethod
    def tearDownClass(cls):
        for key, value in cls.original_tokens.items():
            setattr(settings, key, value)
        try:
            migrate_down(engine="sqlite")
        finally:
            db_connection.DB_PATH = cls.original_db_path
            db_connection.DB_ENGINE = cls.original_engine
            if os.path.exists(cls.tmp.name):
                os.unlink(cls.tmp.name)

    def setUp(self):
        for key in self.original_tokens:
            setattr(settings, key, "")
        suffix = str(id(self))
        self.user_id = UserModel.create(f"step11{suffix}@example.com", f"step11{suffix}", "secret")
        self.workspace_id = WorkspaceModel.create(f"Workspace {suffix}", owner_id=self.user_id)
        self.other_workspace_id = WorkspaceModel.create(f"Other Workspace {suffix}", owner_id=self.user_id)
        self.company_id = CompanyModel.create(self.workspace_id, f"Company {suffix}", industry="AI services")
        self.other_company_id = CompanyModel.create(self.other_workspace_id, f"Other Company {suffix}")
        self.strategy_id = ContentStrategyRepository.create_strategy(self.workspace_id, self.company_id, "Step 11 Strategy")
        self.pillar_id = ContentStrategyRepository.create_pillar(self.workspace_id, self.company_id, self.strategy_id, "Education")
        self.subtopic_id = ContentStrategyRepository.create_subtopic(self.workspace_id, self.company_id, self.strategy_id, self.pillar_id, "AI Planning")
        self.campaign_id = ContentStrategyRepository.create_campaign(self.workspace_id, self.company_id, "Launch Campaign", cta="Register", created_by=self.user_id)
        self.item_ids = ContentStrategyRepository.create_calendar_items_batch(
            self.workspace_id,
            self.company_id,
            self.strategy_id,
            [
                {
                    "pillar_id": self.pillar_id,
                    "subtopic_id": self.subtopic_id,
                    "campaign_id": self.campaign_id,
                    "title": "LinkedIn launch draft",
                    "brief": "Draft the LinkedIn launch post.",
                    "platform": "linkedin",
                    "content_type": "marketing_viral",
                    "planned_date": "2026-08-03",
                    "scheduled_at": "2026-08-03T09:00:00+07:00",
                    "metadata": {"approval_status": "draft", "publishing_status": "planned"},
                },
                {
                    "pillar_id": self.pillar_id,
                    "subtopic_id": self.subtopic_id,
                    "campaign_id": self.campaign_id,
                    "title": "Facebook reminder draft",
                    "brief": "Draft the Facebook reminder post.",
                    "platform": "facebook",
                    "content_type": "marketing_viral",
                    "planned_date": "2026-08-04",
                    "metadata": {"approval_status": "draft", "publishing_status": "planned"},
                },
            ],
            created_by=self.user_id,
        )

    def test_kpi_planning_scopes(self):
        strategy_kpi = create_strategy_kpi(self.workspace_id, self.company_id, self.strategy_id, "Reach", scope_level="strategy", baseline=100, target=1000, period="Monthly", data_source="Native analytics", owner="Marketing", created_by=self.user_id)
        campaign_kpi = create_strategy_kpi(self.workspace_id, self.company_id, self.strategy_id, "Leads", scope_level="campaign", campaign_id=self.campaign_id, baseline=0, target=50, period="Campaign", data_source="CRM", owner="Sales", created_by=self.user_id)
        item_kpi = create_strategy_kpi(self.workspace_id, self.company_id, self.strategy_id, "CTR", scope_level="calendar_item", calendar_item_id=self.item_ids[0], baseline=1.5, target=3.0, period="Post", data_source="LinkedIn", owner="Marketing", created_by=self.user_id)
        platform_kpi = create_strategy_kpi(self.workspace_id, self.company_id, self.strategy_id, "Impressions", scope_level="platform", platform="linkedin", target=5000, period="Monthly", data_source="LinkedIn", owner="Marketing", created_by=self.user_id)
        self.assertTrue(all(result["ok"] for result in [strategy_kpi, campaign_kpi, item_kpi, platform_kpi]))
        listed = list_strategy_kpis(self.workspace_id, self.company_id, self.strategy_id)
        self.assertEqual(len(listed["kpis"]), 4)
        self.assertEqual(len(list_strategy_kpis(self.workspace_id, self.company_id, self.strategy_id, scope_level="campaign")["kpis"]), 1)

    def test_draft_handoff_approval_required_and_duplicate_prevention(self):
        first = handoff_calendar_item_to_content_studio_draft(self.workspace_id, self.company_id, self.strategy_id, self.item_ids[0], confirmed=True, created_by=self.user_id, approval_required=True)
        self.assertTrue(first["ok"])
        self.assertEqual(first["status"], "pending_manager_approval")
        post = PostModel.get_by_id(first["post_id"])
        self.assertEqual(post["status"], "pending_manager_approval")
        linked = ContentStrategyRepository.list_calendar_items(self.workspace_id, self.company_id, self.strategy_id)[0]
        self.assertEqual(linked["approval_status"], "in_review")
        second = handoff_calendar_item_to_content_studio_draft(self.workspace_id, self.company_id, self.strategy_id, self.item_ids[0], confirmed=True, created_by=self.user_id, approval_required=True)
        self.assertTrue(second["duplicate_prevented"])
        posts = PostModel.list_by_workspace(self.workspace_id)
        self.assertEqual(len(posts[posts["id"] == first["post_id"]]), 1)

    def test_token_missing_readiness_reports_configuration_required(self):
        result = check_publishing_readiness(self.workspace_id, self.company_id, self.strategy_id, self.item_ids[1])
        self.assertTrue(result["ok"])
        self.assertFalse(result["ready"])
        self.assertEqual(result["issues"][0]["code"], "configuration_required")
        self.assertNotIn("token", result["issues"][0].get("value", "").lower())

    def test_publishing_failure_mapping_and_status_sync(self):
        handoff = handoff_calendar_item_to_content_studio_draft(self.workspace_id, self.company_id, self.strategy_id, self.item_ids[1], confirmed=True, created_by=self.user_id)
        schedule_id = ScheduleModel.create(handoff["post_id"], "2026-08-04T09:00:00+07:00", platform="facebook", workspace_id=self.workspace_id, created_by=self.user_id)
        ContentStrategyRepository.update_calendar_item(self.workspace_id, self.company_id, self.strategy_id, self.item_ids[1], schedule_id=schedule_id, updated_by=self.user_id)
        ScheduleModel.update_status(schedule_id, "failed", error_message="HTTP 500 from provider")
        sync = sync_calendar_publishing_status(self.workspace_id, self.company_id, self.strategy_id, self.item_ids[1], updated_by=self.user_id)
        self.assertTrue(sync["ok"])
        self.assertEqual(sync["publishing_status"], "failed")
        post = PostModel.get_by_id(handoff["post_id"])
        self.assertNotEqual(post["status"], "published")

    def test_batch_handoff_and_tenant_isolation(self):
        batch = send_selected_calendar_items_to_content_studio(self.workspace_id, self.company_id, self.strategy_id, self.item_ids, confirmed=True, created_by=self.user_id)
        self.assertTrue(batch["ok"])
        self.assertEqual(batch["created"], 2)
        other = check_publishing_readiness(self.other_workspace_id, self.company_id, self.strategy_id)
        self.assertFalse(other["ok"])
        with self.assertRaises(ValueError):
            ContentStrategyRepository.create_kpi(self.other_workspace_id, self.company_id, self.strategy_id, "Reach", scope_level="strategy")


if __name__ == "__main__":
    unittest.main()
