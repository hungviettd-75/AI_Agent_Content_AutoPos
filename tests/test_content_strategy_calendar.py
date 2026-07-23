import os
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import database.connection as db_connection
from database.connection import init_db
from database.migrations.content_strategy_center import down as migrate_down, up as migrate_up
from database.models.companies import CompanyModel
from database.models.users import UserModel
from database.models.workspaces import WorkspaceModel
from database.repositories.content_strategy_repository import ContentStrategyRepository
from services.content_strategy_service import (
    analyze_content_calendar,
    bulk_reschedule_calendar_items,
    generate_content_calendar,
    lock_calendar_items,
    normalize_business_goal,
    normalize_content_angle,
    normalize_content_pillar,
    normalize_format_variant,
    normalize_persona,
    normalize_subtopic,
)
from ui.tab_content_planning_wizard import _calendar_complete, _default_draft, validate_step, STEP_DEFINITIONS


class TestContentStrategyCalendar(unittest.TestCase):
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
        self.user_id = UserModel.create(f"cal{suffix}@example.com", f"cal{suffix}", "secret")
        self.workspace_id = WorkspaceModel.create(f"Workspace {suffix}", owner_id=self.user_id)
        self.other_workspace_id = WorkspaceModel.create(f"Other Workspace {suffix}", owner_id=self.user_id)
        self.company_id = CompanyModel.create(self.workspace_id, f"Company {suffix}", industry="AI services")
        self.other_company_id = CompanyModel.create(self.other_workspace_id, f"Other Company {suffix}")
        self.draft = self._draft()

    def _draft(self):
        first_pillar = normalize_content_pillar({"id": "p1", "name": "Education", "content_ratio": 60, "status": "active"}, 0)
        second_pillar = normalize_content_pillar({"id": "p2", "name": "Proof", "content_ratio": 40, "status": "active"}, 1)
        subtopics = [
            normalize_subtopic({"id": "s1", "pillar_id": "p1", "name": "AI Planning", "business_goal": "Reach", "funnel_stage": "awareness"}, 0),
            normalize_subtopic({"id": "s2", "pillar_id": "p1", "name": "Content Ops", "business_goal": "Trust", "funnel_stage": "consideration"}, 1),
            normalize_subtopic({"id": "s3", "pillar_id": "p2", "name": "Case Study", "business_goal": "Conversion", "funnel_stage": "decision"}, 2),
        ]
        angles = [
            normalize_content_angle({"id": "a1", "subtopic_id": "s1", "working_title": "Plan AI content safely", "hook_idea": "Most teams skip strategy", "cta_type": "learn_more"}, 0),
            normalize_content_angle({"id": "a2", "subtopic_id": "s2", "working_title": "Fix content bottlenecks", "hook_idea": "Approvals hide the real delay", "cta_type": "save"}, 1),
            normalize_content_angle({"id": "a3", "subtopic_id": "s3", "working_title": "Proof from a rollout", "hook_idea": "A small workflow change compounds", "cta_type": "book_call"}, 2),
        ]
        variants = [
            normalize_format_variant({"id": "f1", "angle_id": "a1", "platform": "linkedin", "format": "Long post", "cta": "Book a demo"}, 0),
            normalize_format_variant({"id": "f2", "angle_id": "a2", "platform": "facebook", "format": "Short post", "cta": "Save this"}, 1),
            normalize_format_variant({"id": "f3", "angle_id": "a3", "platform": "linkedin", "format": "Case Study", "cta": "Book a demo"}, 2),
        ]
        return {
            "strategy_name": "Calendar Strategy",
            "start_date": "2026-08-03",
            "end_date": "2026-08-30",
            "brand_identity": {"tone_of_voice": "clear", "standard_cta": "Book a demo"},
            "audience_personas": [normalize_persona({"name": "Founder", "role": "CEO", "goals": ["Growth"], "pain_points": ["Manual work"], "buying_triggers": ["Planning"], "decision_authority": "final", "preferred_channels": ["linkedin"], "customer_journey_stage": "decision"})],
            "business_goals": [
                normalize_business_goal({"name": "Reach", "priority": "high"}),
                normalize_business_goal({"name": "Trust", "priority": "medium"}),
                normalize_business_goal({"name": "Conversion", "priority": "high"}),
            ],
            "content_pillars": [first_pillar, second_pillar],
            "subtopics": subtopics,
            "content_angles": angles,
            "formats_channels": variants,
        }

    def test_7_day_calendar_and_timezone(self):
        result = generate_content_calendar(self.draft, {
            "start_date": "2026-08-03",
            "end_date": "2026-08-09",
            "posting_frequency": 3,
            "platforms": ["linkedin"],
            "preferred_days": ["Monday", "Wednesday", "Friday"],
            "time_slots": ["09:00"],
            "timezone": "America/New_York",
        })
        self.assertEqual(len(result["items"]), 3)
        self.assertTrue(all(item["timezone"] == "America/New_York" for item in result["items"]))
        self.assertTrue(all("2026-08-03" <= item["date"] <= "2026-08-09" for item in result["items"]))

    def test_30_day_ratio_distribution_and_promotional_limit(self):
        result = generate_content_calendar(self.draft, {
            "start_date": "2026-08-03",
            "end_date": "2026-09-01",
            "posting_frequency": 5,
            "platforms": ["linkedin"],
            "preferred_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            "time_slots": ["09:00"],
            "pillar_ratios": {"p1": 60, "p2": 40},
            "promotional_ratio": 20,
            "available_production_capacity": 100,
        })
        diagnostics = analyze_content_calendar(result["items"], result["settings"])
        self.assertGreaterEqual(len(result["items"]), 20)
        education = diagnostics["pillar_counts"].get("Education", 0)
        proof = diagnostics["pillar_counts"].get("Proof", 0)
        self.assertGreater(education, proof)
        self.assertLessEqual(diagnostics["promotional_ratio"], 25)

    def test_365_day_calendar_performance(self):
        started = time.time()
        result = generate_content_calendar(self.draft, {
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
            "posting_frequency": 7,
            "platforms": ["linkedin"],
            "preferred_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
            "time_slots": ["09:00"],
            "available_production_capacity": 400,
        })
        self.assertEqual(len(result["items"]), 365)
        self.assertLess(time.time() - started, 2.0)

    def test_locked_items_are_preserved_when_regenerating_unlocked(self):
        initial = generate_content_calendar(self.draft, {"start_date": "2026-08-03", "end_date": "2026-08-16", "posting_frequency": 5, "platforms": ["linkedin"], "time_slots": ["09:00"]})
        locked = lock_calendar_items(initial["items"], [initial["items"][0]["id"]], True)
        locked_title = locked[0]["working_title"] = "Manual locked title"
        regenerated = generate_content_calendar(self.draft, initial["settings"], existing_items=locked, regenerate_unlocked=True)
        self.assertEqual(regenerated["items"][0]["working_title"], locked_title)
        self.assertTrue(regenerated["items"][0]["locked"])

    def test_conflict_detection_and_batch_reschedule(self):
        result = generate_content_calendar(self.draft, {"start_date": "2026-08-03", "end_date": "2026-08-09", "posting_frequency": 2, "platforms": ["linkedin"], "time_slots": ["09:00"]})
        items = result["items"]
        items[1]["date"] = items[0]["date"]
        items[1]["time"] = items[0]["time"]
        diagnostics = analyze_content_calendar(items, result["settings"])
        self.assertTrue(any(c["type"] == "slot_conflict" for c in diagnostics["conflicts"]))
        shifted = bulk_reschedule_calendar_items(items, [items[1]["id"]], day_delta=7, timezone="Asia/Bangkok")
        self.assertEqual(shifted[1]["timezone"], "Asia/Bangkok")
        self.assertNotEqual(shifted[1]["date"], items[1]["date"])

    def test_calendar_step_validation(self):
        draft = _default_draft()
        step_index = [idx for idx, step in enumerate(STEP_DEFINITIONS) if step[0] == "content_calendar"][0]
        ok, errors = validate_step(step_index, draft)
        self.assertFalse(ok)
        self.assertTrue(errors)
        draft["content_calendar"] = generate_content_calendar(self.draft, {"start_date": "2026-08-03", "end_date": "2026-08-09", "posting_frequency": 1, "platforms": ["linkedin"]})
        self.assertTrue(_calendar_complete(draft["content_calendar"])[0])

    def test_repository_calendar_tenant_isolation(self):
        strategy_id = ContentStrategyRepository.create_strategy(self.workspace_id, self.company_id, "Calendar Repo")
        pillar_id = ContentStrategyRepository.create_pillar(self.workspace_id, self.company_id, strategy_id, "Education")
        subtopic_id = ContentStrategyRepository.create_subtopic(self.workspace_id, self.company_id, strategy_id, pillar_id, "AI Planning")
        item_ids = ContentStrategyRepository.create_calendar_items_batch(self.workspace_id, self.company_id, strategy_id, [{
            "pillar_id": pillar_id,
            "subtopic_id": subtopic_id,
            "title": "Calendar item",
            "planned_date": "2026-08-03",
            "scheduled_at": "2026-08-03T09:00:00+07:00",
            "platform": "linkedin",
            "metadata": {"timezone": "Asia/Bangkok", "locked": False},
        }], created_by=self.user_id)
        self.assertEqual(len(item_ids), 1)
        self.assertEqual(len(ContentStrategyRepository.list_calendar_items(self.workspace_id, self.company_id, strategy_id)), 1)
        with self.assertRaises(ValueError):
            ContentStrategyRepository.list_calendar_items(self.other_workspace_id, self.company_id, strategy_id)
        with self.assertRaises(ValueError):
            ContentStrategyRepository.create_calendar_items_batch(self.other_workspace_id, self.company_id, strategy_id, [{"title": "Bad", "planned_date": "2026-08-04"}])


if __name__ == "__main__":
    unittest.main()
