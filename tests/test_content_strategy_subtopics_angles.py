import os
import sys
import tempfile
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
    ContentStrategyService,
    merge_subtopics,
    normalize_content_angle,
    create_format_variants_from_angles,
    normalize_content_angles,
    normalize_content_pillar,
    normalize_format_variants,
    normalize_subtopic,
    normalize_subtopics,
    split_subtopic,
    validate_content_angles,
    validate_format_variants,
    validate_subtopics,
)
from ui.tab_content_planning_wizard import _bulk_approve


class BatchGenerationStub:
    def __init__(self, pillar_ids=None, subtopic_ids=None, fail_subtopic_calls=None, fail_angle_calls=None):
        self.pillar_ids = pillar_ids or []
        self.subtopic_ids = subtopic_ids or []
        self.fail_subtopic_calls = set(fail_subtopic_calls or [])
        self.fail_angle_calls = set(fail_angle_calls or [])
        self.subtopic_calls = 0
        self.angle_calls = 0

    def generate_subtopics(self, prompt, workspace_id=None):
        self.subtopic_calls += 1
        if self.subtopic_calls in self.fail_subtopic_calls:
            raise RuntimeError("503 unavailable")
        pillar_id = self.pillar_ids[min(self.subtopic_calls - 1, len(self.pillar_ids) - 1)]
        return {"subtopics": [{
            "pillar_id": pillar_id,
            "name": f"Automation Playbook {self.subtopic_calls}",
            "description": "Explain a practical automation topic",
            "target_persona": "Founder",
            "business_goal": "Lead Generation",
            "intent": "learn automation implementation",
            "funnel_stage": "consideration",
            "priority": "high",
            "trend_classification": "evergreen",
            "suggested_channels": ["linkedin"],
            "status": "draft",
        }]}

    def generate_angles(self, prompt, workspace_id=None):
        self.angle_calls += 1
        if self.angle_calls in self.fail_angle_calls:
            raise RuntimeError("429 rate limit")
        subtopic_id = self.subtopic_ids[min(self.angle_calls - 1, len(self.subtopic_ids) - 1)]
        return {"content_angles": [{
            "subtopic_id": subtopic_id,
            "category": "How-to",
            "working_title": f"How to automate safely {self.angle_calls}",
            "hook_idea": "Most teams automate the wrong step first",
            "core_insight": "Start from the approval bottleneck before tooling",
            "intended_emotion": "clarity",
            "target_persona": "Founder",
            "funnel_stage": "consideration",
            "cta_type": "consultation",
            "evidence_requirement": "internal workflow example",
            "trend_classification": "evergreen",
            "priority": "high",
            "risk_level": "low",
            "status": "draft",
        }]}


class TestContentStrategySubtopicsAngles(unittest.TestCase):
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
        self.user_id = UserModel.create(f"s67{suffix}@example.com", f"s67{suffix}", "secret")
        self.workspace_id = WorkspaceModel.create(f"Workspace {suffix}", owner_id=self.user_id)
        self.other_workspace_id = WorkspaceModel.create(f"Other Workspace {suffix}", owner_id=self.user_id)
        self.company_id = CompanyModel.create(self.workspace_id, f"Company {suffix}", industry="AI services")
        self.other_company_id = CompanyModel.create(self.other_workspace_id, f"Other Company {suffix}")
        self.pillars = [
            normalize_content_pillar({"id": "p1", "name": "Education", "description": "Teach", "strategic_purpose": "Educate", "content_ratio": 50}, 0),
            normalize_content_pillar({"id": "p2", "name": "Proof", "description": "Prove", "strategic_purpose": "Trust", "content_ratio": 50}, 1),
            normalize_content_pillar({"id": "p3", "name": "Conversion", "description": "Convert", "strategic_purpose": "Sell", "content_ratio": 0, "status": "inactive"}, 2),
        ]
        self.draft = {
            "business_context": {"company_name": "A", "industry": "AI", "market": "US", "business_model": "service", "services": "Consulting"},
            "brand_identity": {"tone_of_voice": "clear", "personality": "expert", "writing_style": "concise", "standard_cta": "Book", "communication_principles": "Useful"},
            "audience_personas": [],
            "business_goals": [],
            "content_pillars": self.pillars,
            "subtopics": [],
            "content_angles": [],
        }

    def test_batch_generation_partial_failure_and_resume(self):
        stub = BatchGenerationStub(pillar_ids=["p1", "p2"], fail_subtopic_calls={2})
        service = ContentStrategyService(generation_service=stub)
        result = service.generate_subtopic_batches(self.workspace_id, self.company_id, self.draft, subtopics_per_pillar=1, batch_size=1, selected_pillar_ids=["p1", "p2"], created_by=self.user_id)
        self.assertTrue(result["ok"])
        self.assertEqual([b["status"] for b in result["batches"]], ["success", "failed"])
        self.assertEqual(len(result["subtopics"]), 1)

        retry = ContentStrategyService(generation_service=BatchGenerationStub(pillar_ids=["p2"])).generate_subtopic_batches(
            self.workspace_id, self.company_id, {**self.draft, "subtopics": result["subtopics"]}, subtopics_per_pillar=1, batch_size=1, selected_pillar_ids=["p1", "p2"], resume_from_batch=1, created_by=self.user_id
        )
        self.assertTrue(retry["ok"])
        self.assertEqual(len(retry["subtopics"]), 2)

    def test_preserve_manual_edits_and_duplicate_detection(self):
        manual = normalize_subtopic({
            "id": "manual1", "pillar_id": "p1", "name": "Automation Playbook 1", "description": "Manual edit",
            "target_persona": "Founder", "business_goal": "Lead Generation", "intent": "learn automation implementation",
            "suggested_channels": ["linkedin"], "source": "manual", "manual_edits": True,
        })
        draft = {**self.draft, "subtopics": [manual]}
        result = ContentStrategyService(generation_service=BatchGenerationStub(pillar_ids=["p1"])).generate_subtopic_batches(
            self.workspace_id, self.company_id, draft, subtopics_per_pillar=1, batch_size=1, selected_pillar_ids=["p1"], created_by=self.user_id
        )
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["subtopics"]), 1)
        self.assertEqual(result["subtopics"][0]["description"], "Manual edit")
        self.assertTrue(result["batches"][0]["duplicates"])

        generated = normalize_subtopic({**manual, "source": "ai_generated", "manual_edits": False})
        unchanged = normalize_subtopic(generated)
        changed = normalize_subtopic({**generated, "description": "Edited by user"})
        self.assertFalse(unchanged["manual_edits"])
        self.assertTrue(changed["manual_edits"])

    def test_angle_batch_generation_and_validation(self):
        subtopic = normalize_subtopic({
            "id": "s1", "pillar_id": "p1", "name": "Automation", "description": "Desc", "target_persona": "Founder",
            "business_goal": "Lead Generation", "intent": "learn", "suggested_channels": ["linkedin"],
        })
        draft = {**self.draft, "subtopics": [subtopic]}
        result = ContentStrategyService(generation_service=BatchGenerationStub(subtopic_ids=["s1"])).generate_angle_batches(
            self.workspace_id, self.company_id, draft, angles_per_subtopic=1, batch_size=1, created_by=self.user_id
        )
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["content_angles"]), 1)
        self.assertEqual(validate_content_angles(result["content_angles"], [subtopic])[0], [])

    def test_merge_split_bulk_approve_helpers(self):
        first = normalize_subtopic({"id": "s1", "pillar_id": "p1", "name": "A", "description": "One", "target_persona": "Founder", "business_goal": "Lead", "intent": "learn", "suggested_channels": ["linkedin"]}, 0)
        second = normalize_subtopic({"id": "s2", "pillar_id": "p1", "name": "B", "description": "Two", "suggested_channels": ["blog"]}, 1)
        merged = merge_subtopics([first, second], 1)
        self.assertEqual(len(merged), 1)
        self.assertIn("Two", merged[0]["description"])
        split = split_subtopic(merged[0])
        self.assertEqual(len(split), 2)
        approved = _bulk_approve(split, [split[0]["id"]])
        self.assertEqual(approved[0]["status"], "approved")

    def test_repository_move_subtopic_and_tenant_isolation(self):
        strategy_id = ContentStrategyRepository.create_strategy(self.workspace_id, self.company_id, "Move Step 6")
        first_pillar = ContentStrategyRepository.create_pillar(self.workspace_id, self.company_id, strategy_id, "First")
        second_pillar = ContentStrategyRepository.create_pillar(self.workspace_id, self.company_id, strategy_id, "Second")
        subtopic_id = ContentStrategyRepository.create_subtopic(
            self.workspace_id, self.company_id, strategy_id, first_pillar, "Automation", target_persona="Founder", suggested_channels=["linkedin"], source="manual"
        )
        self.assertTrue(ContentStrategyRepository.move_subtopic(self.workspace_id, self.company_id, strategy_id, subtopic_id, second_pillar, updated_by=self.user_id))
        strategy = ContentStrategyRepository.get_strategy(self.workspace_id, self.company_id, strategy_id)
        self.assertEqual(strategy["subtopics"][0]["pillar_id"], second_pillar)
        with self.assertRaises(ValueError):
            ContentStrategyRepository.move_subtopic(self.other_workspace_id, self.company_id, strategy_id, subtopic_id, second_pillar)

    def test_tenant_isolation_for_batch_generation(self):
        service = ContentStrategyService(generation_service=BatchGenerationStub(pillar_ids=["p1"]))
        result = service.generate_subtopic_batches(self.other_workspace_id, self.company_id, self.draft, subtopics_per_pillar=1, batch_size=1)
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "subtopic_generation_failed")

    def test_format_variants_multi_platform_brand_and_unsupported_publisher(self):
        angle = normalize_content_angle({
            "id": "a1",
            "subtopic_id": "s1",
            "working_title": "Automation bottleneck",
            "hook_idea": "Stop automating the loudest task",
            "core_insight": "Start from approval bottlenecks",
            "intended_emotion": "clarity",
            "target_persona": "Founder",
            "evidence_requirement": "workflow example",
            "priority": "high",
        })
        brand = {"tone_of_voice": "clear", "standard_cta": "Book a demo", "forbidden_words": ["guaranteed"]}
        variants = create_format_variants_from_angles([angle], ["facebook", "linkedin", "tiktok", "zalo_oa"], brand=brand)
        self.assertEqual(len(variants), 4)
        self.assertTrue(next(v for v in variants if v["platform"] == "facebook")["publishing_enabled"])
        self.assertFalse(next(v for v in variants if v["platform"] == "tiktok")["publishing_enabled"])
        self.assertEqual(next(v for v in variants if v["platform"] == "tiktok")["status"], "export_only")
        self.assertTrue(all(v["repurposing_source"] == "a1" for v in variants))
        self.assertIn("discussion", next(v for v in variants if v["platform"] == "facebook")["adaptation_guidance"])
        self.assertIn("B2B", next(v for v in variants if v["platform"] == "linkedin")["adaptation_guidance"])

        errors, warnings = validate_format_variants(variants, [angle], brand)
        self.assertEqual(errors, [])
        self.assertFalse(any("No angle is repurposed" in warning for warning in warnings))

        bad = normalize_format_variants([{**variants[0], "brief": "guaranteed result"}], brand=brand)
        errors, _ = validate_format_variants(bad, [angle], brand)
        self.assertTrue(any("forbidden" in error for error in errors))

        zalo_bad = normalize_format_variants([{**next(v for v in variants if v["platform"] == "zalo_oa"), "adaptation_guidance": "Add #automation"}], brand=brand)
        errors, _ = validate_format_variants(zalo_bad, [angle], brand)
        self.assertTrue(any("Zalo hashtags" in error for error in errors))

    def test_format_variant_repository_save_reload_and_workspace_isolation(self):
        strategy_id = ContentStrategyRepository.create_strategy(self.workspace_id, self.company_id, "Formats Step 8")
        pillar_id = ContentStrategyRepository.create_pillar(self.workspace_id, self.company_id, strategy_id, "Education")
        subtopic_id = ContentStrategyRepository.create_subtopic(self.workspace_id, self.company_id, strategy_id, pillar_id, "Automation")
        angle_id = ContentStrategyRepository.create_angles_batch(self.workspace_id, self.company_id, strategy_id, [{"pillar_id": pillar_id, "subtopic_id": subtopic_id, "title": "Save time", "hook": "Short hook"}])[0]
        variant_ids = ContentStrategyRepository.create_format_variants_batch(self.workspace_id, self.company_id, strategy_id, [{
            "angle_id": angle_id,
            "platform": "linkedin",
            "format": "Long post",
            "target_length": "150-300 words",
            "tone_override": "expert",
            "cta": "Book a demo",
            "visual_requirement": "proof chart",
            "hook_style": "B2B insight hook",
            "publishing_objective": "thought leadership",
            "repurposing_source": str(angle_id),
            "priority": "high",
            "publishing_enabled": True,
            "production_effort": "medium",
            "adaptation_guidance": "Adapt as B2B insight",
            "brief": "Hook, body, CTA plan only",
        }], created_by=self.user_id)
        self.assertEqual(len(variant_ids), 1)
        variants = ContentStrategyRepository.list_format_variants(self.workspace_id, self.company_id, strategy_id)
        self.assertEqual(variants[0]["platform"], "linkedin")
        self.assertEqual(variants[0]["cta"], "Book a demo")
        with self.assertRaises(ValueError):
            ContentStrategyRepository.list_format_variants(self.other_workspace_id, self.company_id, strategy_id)
        with self.assertRaises(ValueError):
            ContentStrategyRepository.create_format_variants_batch(self.other_workspace_id, self.company_id, strategy_id, [{"angle_id": angle_id, "platform": "facebook", "format": "Short post"}])


if __name__ == "__main__":
    unittest.main()


