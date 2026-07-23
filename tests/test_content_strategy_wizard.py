import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import database.connection as db_connection
from database.connection import init_db
from database.migrations.content_strategy_center import down as migrate_down, up as migrate_up
from database.models.companies import CompanyModel
from database.models.brand import BrandModel
from database.models.users import UserModel
from database.models.workspaces import WorkspaceModel
from services.content_strategy_service import ContentStrategyService, _is_retryable, normalize_business_goal, normalize_content_pillar, normalize_persona, recommend_format_variant, validate_business_goals, validate_content_pillars
from ui.tab_content_planning_wizard import (
    STEP_DEFINITIONS,
    _default_draft,
    audience_personas_complete,
    business_context_complete,
    brand_identity_complete,
    _draft_from_strategy,
    draft_hash,
    next_step_index,
    previous_step_index,
    _friendly_error_message,
    _merge_pillars,
    _move_item,
    _new_state,
    _saved_caption,
    step_completion_rows,
    user_can_edit,
    user_can_manage,
    validate_step,
)


class TestContentStrategyWizardHelpers(unittest.TestCase):
    def test_step_definitions_match_strategy_center_shell(self):
        self.assertEqual(len(STEP_DEFINITIONS), 12)
        self.assertEqual(STEP_DEFINITIONS[0][1], "Business Context")
        self.assertEqual(STEP_DEFINITIONS[-1][1], "Review and Activate")

    def test_step_validation_blocks_incomplete_current_step(self):
        draft = _default_draft()
        ok, errors = validate_step(0, draft)
        self.assertFalse(ok)
        self.assertIn("Strategy name is required.", errors)

        draft["strategy_name"] = "Q3 Strategy"
        draft["business_context"].update({
            "company_name": "B2B AI Co",
            "industry": "AI consulting",
            "market": "Vietnam SMB",
            "business_model": "retainer",
            "services": "AI consulting",
        })
        next_index, errors = next_step_index(0, draft)
        self.assertEqual(next_index, 1)
        self.assertEqual(errors, [])

        next_index, errors = next_step_index(1, draft)
        self.assertEqual(next_index, 1)
        self.assertTrue(errors)

    def test_structured_step_completeness_helpers(self):
        draft = _default_draft()
        draft["business_context"].update({
            "company_name": "A",
            "industry": "SaaS",
            "market": "US",
            "business_model": "subscription",
            "products": "Platform",
        })
        self.assertTrue(business_context_complete(draft["business_context"])[0])
        draft["brand_identity"].update({
            "tone_of_voice": "clear",
            "personality": "pragmatic",
            "writing_style": "concise",
            "standard_cta": "Book a demo",
            "communication_principles": "No hype",
        })
        self.assertTrue(brand_identity_complete(draft["brand_identity"])[0])
        persona = normalize_persona({
            "name": "Marketing Lead",
            "role": "Head of Marketing",
            "goals": ["Improve pipeline"],
            "pain_points": ["Manual content ops"],
            "buying_triggers": ["New growth target"],
            "decision_authority": "recommender",
            "preferred_channels": ["linkedin"],
            "customer_journey_stage": "consideration",
        })
        self.assertTrue(audience_personas_complete([persona])[0])

    def test_business_goal_and_pillar_validation(self):
        goal = normalize_business_goal({
            "name": "Lead Generation",
            "priority": "high",
            "description": "Build qualified demand",
            "target_metric": "MQL",
            "target_value": "50",
            "time_period": "Q3",
            "target_personas": ["Founder"],
            "preferred_platforms": ["linkedin"],
        })
        self.assertEqual(validate_business_goals([goal])[0], [])

        persona = normalize_persona({
            "name": "Founder",
            "role": "CEO",
            "goals": ["Growth"],
            "pain_points": ["Limited team"],
            "buying_triggers": ["Planning"],
            "decision_authority": "final",
            "preferred_channels": ["linkedin"],
            "customer_journey_stage": "decision",
        })
        first = normalize_content_pillar({
            "name": "Education",
            "description": "Teach buyers",
            "strategic_purpose": "Move buyers from problem-aware to solution-aware",
            "business_goals": ["Lead Generation"],
            "target_personas": ["Founder"],
            "recommended_channels": ["linkedin"],
            "content_ratio": 60,
            "priority": "high",
            "differentiation_angle": "Practical operator examples",
            "do_guidance": ["Show tradeoffs"],
            "dont_guidance": ["Avoid hype"],
        })
        second = normalize_content_pillar({**first, "id": "p2", "name": "Proof", "content_ratio": 40})
        errors, warnings = validate_content_pillars([first, second], [goal], [persona])
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

        duplicate = normalize_content_pillar({**first, "id": "p3"})
        errors, _ = validate_content_pillars([first, duplicate], [goal], [persona])
        self.assertTrue(any("Duplicate pillar name" in error for error in errors))

        bad_ratio = normalize_content_pillar({**second, "id": "p4", "name": "Proof 2", "content_ratio": 20})
        errors, _ = validate_content_pillars([first, bad_ratio], [goal], [persona])
        self.assertTrue(any("total 100%" in error for error in errors))

    def test_pillar_merge_and_reorder_helpers(self):
        first = normalize_content_pillar({"name": "A", "description": "One", "content_ratio": 40, "business_goals": ["Lead Generation"]}, 0)
        second = normalize_content_pillar({"name": "B", "description": "Two", "content_ratio": 60, "target_personas": ["Founder"]}, 1)
        moved = _move_item([first, second], 0, 1)
        self.assertEqual([item["name"] for item in moved], ["B", "A"])
        merged = _merge_pillars([first, second], 1)
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["content_ratio"], 100)
        self.assertIn("Founder", merged[0]["target_personas"])
    def test_previous_navigation_never_goes_below_zero(self):
        self.assertEqual(previous_step_index(0), 0)
        self.assertEqual(previous_step_index(3), 2)

    def test_draft_hash_is_stable_for_same_content(self):
        draft_a = {"strategy_name": "A", "business_context": "B"}
        draft_b = {"business_context": "B", "strategy_name": "A"}
        self.assertEqual(draft_hash(draft_a), draft_hash(draft_b))

    def test_rbac_strategy_center_permissions(self):
        self.assertFalse(user_can_edit("viewer"))
        self.assertTrue(user_can_edit("editor"))
        self.assertTrue(user_can_edit("marketing"))
        self.assertTrue(user_can_manage("owner"))
        self.assertTrue(user_can_manage("admin"))
        self.assertFalse(user_can_manage("editor"))

    def test_autosave_caption_and_step_completion_rows_are_actionable(self):
        state = _new_state()
        self.assertEqual(_saved_caption(state), "Autosave: draft not created yet")
        state.update({"strategy_id": 10, "last_saved_at": "2026-07-20T10:00:00", "dirty": False})
        self.assertIn("2026-07-20T10:00:00", _saved_caption(state))
        state["dirty"] = True
        self.assertEqual(_saved_caption(state), "Autosave: pending changes")

        rows = step_completion_rows(_default_draft(), 0)
        self.assertEqual(rows[0]["Status"], "Current")
        self.assertIn("Strategy name", rows[0]["Issue"])
        self.assertEqual(rows[1]["Status"], "Needs work")

    def test_friendly_error_messages_cover_retryable_provider_and_db_errors(self):
        msg = _friendly_error_message({"code": "provider_unavailable", "message": "Gemini 503 unavailable", "retryable": True}, "Generate")
        self.assertIn("temporarily unavailable", msg)
        self.assertIn("retryable", msg.lower())
        self.assertIn("database is busy", _friendly_error_message("database is locked", "Save").lower())
        self.assertTrue(_is_retryable(RuntimeError("database is locked")))
        self.assertTrue(_is_retryable(RuntimeError("lost connection to server")))



class PillarStaticGenerationService:
    def __init__(self, names=None):
        self.names = names or ["Education", "Proof"]
        self.prompts = []

    def generate_pillars(self, prompt, workspace_id=None):
        self.prompts.append(prompt)
        ratios = [60, 40] if len(self.names) == 2 else [100]
        return {"pillars": [
            {
                "name": name,
                "description": f"{name} description",
                "strategic_purpose": f"{name} purpose",
                "business_goals": ["Lead Generation"],
                "target_personas": ["Founder"],
                "recommended_channels": ["linkedin"],
                "content_ratio": ratios[index],
                "priority": "high" if index == 0 else "medium",
                "differentiation_angle": f"{name} angle",
                "do_guidance": ["Be useful"],
                "dont_guidance": ["Avoid hype"],
                "status": "active",
            }
            for index, name in enumerate(self.names)
        ]}

class PersonaFailureGenerationService:
    def generate_personas(self, prompt, workspace_id=None):
        raise RuntimeError("503 unavailable")


class PersonaStaticGenerationService:
    def generate_personas(self, prompt, workspace_id=None):
        return {"personas": [{
            "name": "AI Draft CEO",
            "role": "CEO",
            "goals": ["Grow revenue"],
            "pain_points": ["Low content consistency"],
            "buying_triggers": ["New quarter planning"],
            "decision_authority": "final approver",
            "preferred_channels": ["linkedin"],
            "customer_journey_stage": "decision",
        }]}


class TestContentStrategyWizardServiceFacade(unittest.TestCase):
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
        self.user_id = UserModel.create(f"wizard{suffix}@example.com", f"wizard{suffix}", "secret")
        self.workspace_id = WorkspaceModel.create(f"Workspace {suffix}", owner_id=self.user_id)
        self.other_workspace_id = WorkspaceModel.create(f"Other Workspace {suffix}", owner_id=self.user_id)
        self.company_id = CompanyModel.create(self.workspace_id, f"Company {suffix}")
        self.other_company_id = CompanyModel.create(self.other_workspace_id, f"Other Company {suffix}")
        self.service = ContentStrategyService(generation_service=object())


    def test_load_existing_business_and_brand_seed(self):
        BrandModel.create(
            workspace_id=self.workspace_id,
            company_id=self.company_id,
            tone_of_voice="professional",
            cta="Book a call",
            mission="Help teams scale content",
            vision="Better marketing systems",
            keywords=["AI", "automation"],
            blacklist_words=["guaranteed"],
        )
        company_seed = ContentStrategyService.get_business_context_seed(self.workspace_id, self.company_id)
        self.assertEqual(company_seed["company_name"], f"Company {id(self)}")
        brand_seed = ContentStrategyService.get_brand_identity_seed(self.workspace_id, self.company_id)
        self.assertEqual(brand_seed["tone_of_voice"], "professional")
        self.assertIn("AI", brand_seed["brand_keywords"])

    def test_strategy_specific_brand_override_does_not_save_without_confirmation(self):
        draft = _default_draft()
        draft["brand_identity"].update({
            "mode": "custom",
            "tone_of_voice": "direct",
            "personality": "expert",
            "writing_style": "brief",
            "standard_cta": "Start now",
            "communication_principles": "Be specific",
        })
        result = ContentStrategyService.save_brand_identity_customization(
            self.workspace_id,
            self.company_id,
            draft["brand_identity"],
            confirmed=False,
            updated_by=self.user_id,
        )
        self.assertFalse(result["ok"])
        self.assertEqual(BrandModel.get_by_workspace(self.workspace_id), {})

        confirmed = ContentStrategyService.save_brand_identity_customization(
            self.workspace_id,
            self.company_id,
            draft["brand_identity"],
            confirmed=True,
            updated_by=self.user_id,
        )
        self.assertTrue(confirmed["ok"])
        self.assertEqual(BrandModel.get_by_workspace(self.workspace_id)["tone_of_voice"], "direct")

    def test_multiple_personas_reorder_save_and_reload(self):
        first = normalize_persona({
            "name": "Founder",
            "role": "CEO",
            "goals": ["Growth"],
            "pain_points": ["Limited team"],
            "buying_triggers": ["Funding"],
            "decision_authority": "final",
            "preferred_channels": ["linkedin"],
            "customer_journey_stage": "decision",
        }, 0)
        second = normalize_persona({
            "name": "Marketing Manager",
            "role": "Manager",
            "goals": ["Pipeline"],
            "pain_points": ["Slow production"],
            "buying_triggers": ["Campaign launch"],
            "decision_authority": "recommender",
            "preferred_channels": ["email"],
            "customer_journey_stage": "consideration",
        }, 1)
        draft = _default_draft()
        draft.update({"strategy_name": "Persona Strategy"})
        draft["business_context"].update({"company_name": "A", "industry": "SaaS", "market": "US", "business_model": "subscription", "products": "App"})
        draft["brand_identity"].update({"tone_of_voice": "clear", "personality": "expert", "writing_style": "concise", "standard_cta": "Book", "communication_principles": "Useful"})
        draft["audience_personas"] = [second, first]
        created = self.service.create_draft_strategy(self.workspace_id, self.company_id, "Persona Strategy", draft, created_by=self.user_id)
        self.assertTrue(created["ok"])
        opened = self.service.open_strategy(self.workspace_id, self.company_id, created["strategy_id"])
        restored = _draft_from_strategy(opened["strategy"])
        self.assertEqual([p["name"] for p in restored["audience_personas"]], ["Marketing Manager", "Founder"])

    def test_ai_persona_generation_error_and_draft_marking(self):
        failing = ContentStrategyService(generation_service=PersonaFailureGenerationService())
        failed = failing.generate_persona_drafts(self.workspace_id, self.company_id, _default_draft(), count=1, created_by=self.user_id)
        self.assertFalse(failed["ok"])
        self.assertEqual(failed["error"]["code"], "persona_generation_failed")

        ok_service = ContentStrategyService(generation_service=PersonaStaticGenerationService())
        generated = ok_service.generate_persona_drafts(self.workspace_id, self.company_id, _default_draft(), count=1, created_by=self.user_id)
        self.assertTrue(generated["ok"])
        self.assertTrue(generated["personas"][0]["ai_generated_draft"])
        self.assertEqual(generated["personas"][0]["status"], "draft")

    def test_ai_pillar_generation_and_regenerate_preserves_manual_edits(self):
        draft = _default_draft()
        draft["business_context"].update({"company_name": "A", "industry": "SaaS", "market": "US", "business_model": "subscription", "products": "App"})
        draft["brand_identity"].update({"tone_of_voice": "clear", "personality": "expert", "writing_style": "concise", "standard_cta": "Book", "communication_principles": "Useful"})
        draft["audience_personas"] = [normalize_persona({
            "name": "Founder",
            "role": "CEO",
            "goals": ["Growth"],
            "pain_points": ["Limited team"],
            "buying_triggers": ["Planning"],
            "decision_authority": "final",
            "preferred_channels": ["linkedin"],
            "customer_journey_stage": "decision",
        })]
        draft["business_goals"] = [normalize_business_goal({
            "name": "Lead Generation",
            "priority": "high",
            "description": "Build demand",
            "target_metric": "MQL",
            "target_value": "50",
            "time_period": "Q3",
            "target_personas": ["Founder"],
            "preferred_platforms": ["linkedin"],
        })]
        generator = PillarStaticGenerationService()
        service = ContentStrategyService(generation_service=generator)
        result = service.generate_pillar_drafts(self.workspace_id, self.company_id, draft, count=10, created_by=self.user_id)
        self.assertTrue(result["ok"])
        self.assertEqual([p["name"] for p in result["pillars"]], ["Education", "Proof"])
        self.assertIn("existing_pillars", generator.prompts[0])

        draft["content_pillars"] = result["pillars"]
        draft["content_pillars"][1]["description"] = "Manual edit to preserve"
        regen_service = ContentStrategyService(generation_service=PillarStaticGenerationService(["Education 2"]))
        regenerated = regen_service.generate_pillar_drafts(self.workspace_id, self.company_id, draft, count=1, regenerate_index=0, created_by=self.user_id)
        self.assertTrue(regenerated["ok"])
        merged = list(draft["content_pillars"])
        merged[0] = regenerated["pillars"][0]
        self.assertEqual(merged[0]["name"], "Education 2")
        self.assertEqual(merged[1]["description"], "Manual edit to preserve")

    def test_ai_pillar_generation_tenant_isolation(self):
        service = ContentStrategyService(generation_service=PillarStaticGenerationService())
        result = service.generate_pillar_drafts(self.other_workspace_id, self.company_id, _default_draft(), count=2, created_by=self.user_id)
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "pillar_generation_failed")
    def test_formats_channels_save_reload_in_draft(self):
        draft = _default_draft()
        draft.update({"strategy_name": "Formats Draft"})
        draft["business_context"].update({"company_name": "A", "industry": "SaaS", "market": "US", "business_model": "subscription", "products": "App"})
        draft["brand_identity"].update({"tone_of_voice": "clear", "personality": "expert", "writing_style": "concise", "standard_cta": "Book", "communication_principles": "Useful"})
        angle = {
            "id": "angle1",
            "subtopic_id": "sub1",
            "working_title": "Reduce approval delays",
            "hook_idea": "Approval delays hide in plain sight",
            "core_insight": "Map approval bottlenecks before automation",
            "intended_emotion": "clarity",
            "target_persona": "Founder",
            "evidence_requirement": "workflow example",
        }
        draft["content_angles"] = [angle]
        draft["formats_channels"] = [recommend_format_variant(angle, "facebook", "Short post", draft["brand_identity"])]
        created = self.service.create_draft_strategy(self.workspace_id, self.company_id, "Formats Draft", draft, created_by=self.user_id)
        self.assertTrue(created["ok"])
        opened = self.service.open_strategy(self.workspace_id, self.company_id, created["strategy_id"])
        restored = _draft_from_strategy(opened["strategy"])
        self.assertEqual(restored["formats_channels"][0]["platform"], "facebook")
        self.assertIn("do not write", restored["formats_channels"][0]["brief"].lower())

    def test_save_draft_open_restore_and_duplicate(self):
        draft = _default_draft()
        draft.update({
            "strategy_name": "Shell Strategy",
            "business_context": "Tenant scoped context",
            "brand_identity": "Clear, pragmatic, expert",
        })
        created = self.service.create_draft_strategy(self.workspace_id, self.company_id, draft["strategy_name"], draft, created_by=self.user_id)
        self.assertTrue(created["ok"])

        draft["brand_identity"] = "Updated brand identity"
        saved = self.service.save_draft(self.workspace_id, self.company_id, created["strategy_id"], draft, updated_by=self.user_id)
        self.assertTrue(saved["ok"])
        self.assertIsNotNone(saved["version_id"])

        opened = self.service.open_strategy(self.workspace_id, self.company_id, created["strategy_id"])
        restored_draft = _draft_from_strategy(opened["strategy"])
        self.assertEqual(restored_draft["brand_identity"]["communication_principles"], "Updated brand identity")

        duplicate = self.service.duplicate_strategy(self.workspace_id, self.company_id, created["strategy_id"], created_by=self.user_id)
        self.assertTrue(duplicate["ok"])
        self.assertNotEqual(duplicate["strategy_id"], created["strategy_id"])

    def test_workspace_isolation_on_open_and_save(self):
        draft = _default_draft()
        draft.update({"strategy_name": "Private", "business_context": "Only one workspace"})
        created = self.service.create_draft_strategy(self.workspace_id, self.company_id, "Private", draft, created_by=self.user_id)
        self.assertTrue(created["ok"])

        opened = self.service.open_strategy(self.other_workspace_id, self.company_id, created["strategy_id"])
        self.assertFalse(opened["ok"])

        saved = self.service.save_draft(self.other_workspace_id, self.company_id, created["strategy_id"], draft, updated_by=self.user_id)
        self.assertFalse(saved["ok"])

    def test_strategy_list_pagination_returns_has_more_without_loading_all_rows(self):
        draft = _default_draft()
        draft.update({"strategy_name": "Paged", "business_context": "Paged context"})
        for index in range(3):
            created = self.service.create_draft_strategy(self.workspace_id, self.company_id, f"Paged {index}", {**draft, "strategy_name": f"Paged {index}"}, created_by=self.user_id)
            self.assertTrue(created["ok"])

        first_page = self.service.list_strategies(self.workspace_id, self.company_id, limit=2, offset=0)
        self.assertTrue(first_page["ok"])
        self.assertEqual(len(first_page["strategies"]), 2)
        self.assertTrue(first_page["pagination"]["has_more"])
        second_page = self.service.list_strategies(self.workspace_id, self.company_id, limit=2, offset=2)
        self.assertTrue(second_page["ok"])
        self.assertFalse(second_page["pagination"]["has_more"])


if __name__ == "__main__":
    unittest.main()




