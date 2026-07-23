import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import database.connection as db_connection
from database.connection import get_db_connection, init_db
from database.migrations.content_strategy_center import down as migrate_down, up as migrate_up
from database.models.approvals import ApprovalModel
from database.models.companies import CompanyModel
from database.models.users import UserModel
from database.models.workspaces import WorkspaceModel
from database.repositories.content_strategy_repository import ContentStrategyRepository
from services.content_strategy_service import (
    handoff_calendar_item_to_content_studio_draft,
    recommend_lead_magnet,
    validate_campaign_missing_cta,
    validate_funnel_stage_balance,
    validate_sales_content_ratio,
)


class TestContentStrategyCampaignsLeadMagnets(unittest.TestCase):
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
        self.user_id = UserModel.create(f"step10{suffix}@example.com", f"step10{suffix}", "secret")
        self.workspace_id = WorkspaceModel.create(f"Workspace {suffix}", owner_id=self.user_id)
        self.other_workspace_id = WorkspaceModel.create(f"Other Workspace {suffix}", owner_id=self.user_id)
        self.company_id = CompanyModel.create(self.workspace_id, f"Company {suffix}", industry="AI services")
        self.other_company_id = CompanyModel.create(self.other_workspace_id, f"Other Company {suffix}")
        self.strategy_id = ContentStrategyRepository.create_strategy(self.workspace_id, self.company_id, "Step 10 Strategy")
        self.pillar_id = ContentStrategyRepository.create_pillar(self.workspace_id, self.company_id, self.strategy_id, "Education")
        self.subtopic_id = ContentStrategyRepository.create_subtopic(
            self.workspace_id,
            self.company_id,
            self.strategy_id,
            self.pillar_id,
            "AI Planning",
            funnel_stage="consideration",
        )
        self.item_ids = ContentStrategyRepository.create_calendar_items_batch(
            self.workspace_id,
            self.company_id,
            self.strategy_id,
            [
                {
                    "pillar_id": self.pillar_id,
                    "subtopic_id": self.subtopic_id,
                    "title": "Checklist launch post",
                    "brief": "Draft the launch angle.",
                    "platform": "linkedin",
                    "content_type": "marketing_viral",
                    "planned_date": "2026-08-03",
                    "metadata": {"funnel_stage": "consideration", "approval_status": "in_review", "publishing_status": "planned", "cta": "Download checklist"},
                },
                {
                    "pillar_id": self.pillar_id,
                    "subtopic_id": self.subtopic_id,
                    "title": "Demo booking post",
                    "brief": "Invite qualified buyers.",
                    "platform": "linkedin",
                    "content_type": "marketing_viral",
                    "planned_date": "2026-08-04",
                    "metadata": {"funnel_stage": "conversion", "approval_status": "draft", "publishing_status": "planned", "cta": "Book a demo", "promotion_type": "promotional"},
                },
            ],
            created_by=self.user_id,
        )

    def test_campaign_linking_duplication_and_cta_validation(self):
        campaign_id = ContentStrategyRepository.create_campaign_from_calendar_items(
            self.workspace_id,
            self.company_id,
            self.strategy_id,
            self.item_ids,
            "Q3 Lead Gen",
            objective="Lead generation",
            target_personas=["Founder"],
            business_goals=["Pipeline"],
            pillars=["Education"],
            platforms=["linkedin"],
            key_message="Plan AI content safely",
            offer="Checklist",
            cta="Download checklist",
            owner="Marketing",
            kpi="MQLs",
            created_by=self.user_id,
        )
        linked = ContentStrategyRepository.list_calendar_items(self.workspace_id, self.company_id, self.strategy_id)
        self.assertEqual({item["campaign_id"] for item in linked}, {campaign_id})
        self.assertEqual(ContentStrategyRepository.unlink_calendar_items_from_campaign(self.workspace_id, self.company_id, self.strategy_id, [self.item_ids[0]], updated_by=self.user_id), 1)
        self.assertEqual(ContentStrategyRepository.link_calendar_items_to_campaign(self.workspace_id, self.company_id, self.strategy_id, campaign_id, [self.item_ids[0]], updated_by=self.user_id), 1)
        copy_id = ContentStrategyRepository.duplicate_campaign(self.workspace_id, self.company_id, campaign_id, created_by=self.user_id)
        campaigns = ContentStrategyRepository.list_campaigns(self.workspace_id, self.company_id)
        self.assertIn(copy_id, [item["id"] for item in campaigns])
        self.assertTrue(validate_campaign_missing_cta(campaigns)["ok"])
        ContentStrategyRepository.update_campaign(self.workspace_id, self.company_id, campaign_id, cta="")
        self.assertFalse(validate_campaign_missing_cta(ContentStrategyRepository.list_campaigns(self.workspace_id, self.company_id))["ok"])

    def test_lead_magnet_creation_and_multi_post_link(self):
        campaign_id = ContentStrategyRepository.create_campaign(self.workspace_id, self.company_id, "Lead Magnet Campaign", cta="Download", created_by=self.user_id)
        lead_id = ContentStrategyRepository.create_lead_magnet(
            self.workspace_id,
            self.company_id,
            self.strategy_id,
            "AI Planning Checklist",
            type="Checklist",
            description="A practical checklist.",
            target_persona="Founder",
            pain_point="Manual planning",
            value_proposition="Plan faster",
            cta="Download",
            destination_url="",
            campaign_id=campaign_id,
            funnel_stage="consideration",
            created_by=self.user_id,
        )
        lead = ContentStrategyRepository.list_lead_magnets(self.workspace_id, self.company_id, self.strategy_id)[0]
        self.assertEqual(lead["status"], "planned")
        self.assertEqual(lead["asset_reference"], "")
        self.assertEqual(ContentStrategyRepository.link_lead_magnet_to_calendar_items(self.workspace_id, self.company_id, self.strategy_id, lead_id, self.item_ids, created_by=self.user_id), 2)
        self.assertEqual(len(ContentStrategyRepository.list_lead_magnet_calendar_links(self.workspace_id, self.company_id, self.strategy_id, lead_id)), 2)

    def test_funnel_and_sales_validations(self):
        items = [
            {"id": "a", "working_title": "Awareness", "funnel_stage": "awareness", "cta": "Read more"},
            {"id": "b", "working_title": "Buy", "funnel_stage": "conversion", "cta": "Book a demo", "promotion_type": "promotional"},
            {"id": "c", "working_title": "Buy again", "funnel_stage": "conversion", "cta": "Book a sales call"},
        ]
        self.assertFalse(validate_funnel_stage_balance(items, maximum_share=0.5)["ok"])
        self.assertFalse(validate_sales_content_ratio(items, maximum_ratio=0.3)["ok"])
        recommendation = recommend_lead_magnet({"audience_personas": [{"name": "Founder", "pain_points": ["Manual work"]}], "subtopics": [{"id": "s1", "name": "AI Planning", "funnel_stage": "evaluation"}]}, items)
        self.assertEqual(recommendation["status"], "planned")
        self.assertEqual(recommendation["asset_reference"], "")

    def test_draft_handoff_preserves_approval_flow_and_audit(self):
        result = handoff_calendar_item_to_content_studio_draft(self.workspace_id, self.company_id, self.strategy_id, self.item_ids[0], confirmed=True, created_by=self.user_id)
        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "draft")
        post_id = result["post_id"]
        approval_id = ApprovalModel.request(post_id, requested_by=self.user_id, workspace_id=self.workspace_id)
        self.assertGreater(approval_id, 0)
        latest = ApprovalModel.get_latest_by_post(post_id)
        self.assertEqual(latest["status"], "pending")
        linked_item = [item for item in ContentStrategyRepository.list_calendar_items(self.workspace_id, self.company_id, self.strategy_id) if item["id"] == self.item_ids[0]][0]
        self.assertEqual(linked_item["post_id"], post_id)
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM audit_logs WHERE action='HANDOFF_CALENDAR_ITEM_TO_DRAFT' AND workspace_id=?", (self.workspace_id,))
            self.assertEqual(cur.fetchone()[0], 1)
        finally:
            conn.close()

    def test_workspace_isolation_for_campaign_and_lead_magnet(self):
        campaign_id = ContentStrategyRepository.create_campaign(self.workspace_id, self.company_id, "Private Campaign", cta="Download")
        with self.assertRaises(ValueError):
            ContentStrategyRepository.link_calendar_items_to_campaign(self.other_workspace_id, self.company_id, self.strategy_id, campaign_id, self.item_ids)
        with self.assertRaises(ValueError):
            ContentStrategyRepository.create_lead_magnet(self.other_workspace_id, self.company_id, self.strategy_id, "Bad", type="Checklist")


if __name__ == "__main__":
    unittest.main()
