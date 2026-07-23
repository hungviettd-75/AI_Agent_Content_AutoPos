import json
import os
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import database.connection as db_connection
from database.connection import get_db_connection, init_db
from database.migrations.content_strategy_center import down as migrate_down, up as migrate_up
from database.models.companies import CompanyModel
from database.models.users import UserModel
from database.models.workspaces import WorkspaceModel
from database.repositories.content_strategy_generation_repository import ContentStrategyGenerationRepository
from database.repositories.content_strategy_repository import ContentStrategyRepository
from services.content_strategy_service import ContentStrategyService, StrategyGenerationService
from services.content_strategy_validation import ContentStrategyJSONParser, ContentStrategyValidator, StrategyValidationError


def sample_payload(name="AI Strategy", calendar_title="Post A"):
    return {
        "schema_version": "content_strategy.v1",
        "task": "full_strategy",
        "strategy_summary": {
            "name": name,
            "description": "Plan description",
            "campaign_theme": "Trust and growth",
        },
        "business_goals": [
            {
                "name": "Generate leads",
                "description": "Build qualified demand",
                "target_metric": "leads",
                "target_value": 50,
                "timeframe": "30 days",
            }
        ],
        "kpis": [{"metric_name": "CTR", "target_value": 3.5, "unit": "%"}],
        "lead_magnets": [
            {
                "name": "AI checklist",
                "description": "Checklist for buyers",
                "asset_type": "checklist",
                "pillar_key": "education",
            }
        ],
        "pillars": [
            {
                "key": "education",
                "name": "Education",
                "description": "Teach buyers",
                "business_goal": "Generate leads",
                "target_persona": ["CEO"],
                "recommended_platforms": ["linkedin"],
                "priority": 1,
            }
        ],
        "subtopics": [
            {
                "key": "ai-basics",
                "pillar_key": "education",
                "name": "AI Basics",
                "description": "Explain foundations",
                "priority": 1,
            }
        ],
        "content_angles": [
            {
                "key": "avoid-mistakes",
                "pillar_key": "education",
                "subtopic_key": "ai-basics",
                "title": "Avoid costly AI mistakes",
                "description": "Mistake-led angle",
                "hook": "Most teams skip this step",
                "cta": "Ask for an audit",
                "goal": "lead_generation",
            }
        ],
        "content_formats": [
            {
                "angle_key": "avoid-mistakes",
                "platform": "linkedin",
                "format_type": "post",
                "name": "LinkedIn post",
                "description": "Short educational post",
                "specs": {"length": "1200 chars", "cadence": "weekly"},
            }
        ],
        "content_calendar": [
            {
                "planned_date": "2026-08-01",
                "platform": "linkedin",
                "title": calendar_title,
                "brief": "Explain a common mistake",
                "pillar_key": "education",
                "subtopic_key": "ai-basics",
                "angle_key": "avoid-mistakes",
                "content_type": "post",
                "cta": "Book a consult",
            }
        ],
    }


class StaticGenerationService:
    def __init__(self, payload):
        self.payload = payload

    def generate_json(self, prompt, task, workspace_id=None):
        data = dict(self.payload)
        data["task"] = task
        return ContentStrategyValidator.validate(data, expected_task=task)


class TestContentStrategyAIService(unittest.TestCase):
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
        self.user_id = UserModel.create(f"ai{suffix}@example.com", f"ai{suffix}", "secret")
        self.workspace_id = WorkspaceModel.create(f"Workspace {suffix}", owner_id=self.user_id)
        self.other_workspace_id = WorkspaceModel.create(f"Other Workspace {suffix}", owner_id=self.user_id)
        self.company_id = CompanyModel.create(self.workspace_id, f"Company {suffix}", industry="AI services")
        self.other_company_id = CompanyModel.create(self.other_workspace_id, f"Other Company {suffix}")

    def test_valid_json_object(self):
        data = ContentStrategyValidator.validate(sample_payload())
        self.assertEqual(data["pillars"][0]["name"], "Education")

    def test_json_markdown_fence(self):
        raw = "```json\n" + json.dumps(sample_payload()) + "\n```"
        data = ContentStrategyJSONParser.parse(raw)
        self.assertEqual(data["strategy_summary"]["name"], "AI Strategy")

    def test_missing_required_field(self):
        data = sample_payload()
        del data["pillars"][0]["name"]
        with self.assertRaises(StrategyValidationError):
            ContentStrategyValidator.validate(data)

    def test_wrong_type(self):
        data = sample_payload()
        data["content_calendar"] = {"bad": "type"}
        with self.assertRaises(StrategyValidationError):
            ContentStrategyValidator.validate(data)

    def test_duplicate_pillar(self):
        data = sample_payload()
        data["pillars"].append(dict(data["pillars"][0]))
        with self.assertRaises(StrategyValidationError):
            ContentStrategyValidator.validate(data)

    def test_ai_timeout(self):
        def slow_call(*args, **kwargs):
            time.sleep(0.05)
            return json.dumps(sample_payload())

        service = StrategyGenerationService(timeout_seconds=0.01, max_retries=0)
        with patch("services.content_strategy_service.get_gemini_client", return_value=object()):
            with patch("services.content_strategy_service._call_model", side_effect=slow_call):
                with self.assertRaises(Exception) as ctx:
                    service.generate_json("prompt", "full_strategy")
        self.assertIn("timeout", getattr(ctx.exception, "code", ""))

    def test_rate_limit_retry(self):
        service = StrategyGenerationService(timeout_seconds=1, max_retries=1, backoff_seconds=0)
        with patch("services.content_strategy_service.get_gemini_client", return_value=object()):
            with patch("services.content_strategy_service._call_model", side_effect=[Exception("429 rate limit"), json.dumps(sample_payload())]) as mocked:
                data = service.generate_json("prompt", "full_strategy")
        self.assertEqual(mocked.call_count, 2)
        self.assertEqual(data["pillars"][0]["key"], "education")

    def test_503_retry(self):
        service = StrategyGenerationService(timeout_seconds=1, max_retries=1, backoff_seconds=0)
        with patch("services.content_strategy_service.get_gemini_client", return_value=object()):
            with patch("services.content_strategy_service._call_model", side_effect=[Exception("503 unavailable"), json.dumps(sample_payload())]) as mocked:
                data = service.generate_json("prompt", "full_strategy")
        self.assertEqual(mocked.call_count, 2)
        self.assertEqual(data["content_calendar"][0]["title"], "Post A")

    def test_repair_markdown_json(self):
        bad = "not json"
        repaired = "```json\n" + json.dumps(sample_payload()) + "\n```"
        service = StrategyGenerationService(timeout_seconds=1, max_retries=0)
        with patch("services.content_strategy_service.get_gemini_client", return_value=object()):
            with patch("services.content_strategy_service._call_model", side_effect=[bad, repaired]) as mocked:
                data = service.generate_json("prompt", "full_strategy")
        self.assertEqual(mocked.call_count, 2)
        self.assertEqual(data["strategy_summary"]["campaign_theme"], "Trust and growth")

    def test_generate_persists_strategy(self):
        service = ContentStrategyService(generation_service=StaticGenerationService(sample_payload()))
        result = service.generate_strategy(self.workspace_id, self.company_id, {"preferred_platforms": ["linkedin"]}, created_by=self.user_id)
        self.assertTrue(result["ok"])
        strategy = ContentStrategyRepository.get_strategy(self.workspace_id, self.company_id, result["strategy_id"])
        self.assertEqual(len(strategy["pillars"]), 1)
        self.assertEqual(len(strategy["calendar_items"]), 1)

    def test_partial_generation_replaces_only_calendar(self):
        service = ContentStrategyService(generation_service=StaticGenerationService(sample_payload()))
        created = service.generate_strategy(self.workspace_id, self.company_id, {}, created_by=self.user_id)
        strategy_id = created["strategy_id"]

        regen_payload = sample_payload(calendar_title="Post B")
        regen_service = ContentStrategyService(generation_service=StaticGenerationService(regen_payload))
        result = regen_service.regenerate_section(
            self.workspace_id,
            self.company_id,
            strategy_id,
            "content_calendar",
            updated_by=self.user_id,
        )
        self.assertTrue(result["ok"])
        strategy = ContentStrategyRepository.get_strategy(self.workspace_id, self.company_id, strategy_id)
        self.assertEqual(len(strategy["pillars"]), 1)
        self.assertEqual(len(strategy["calendar_items"]), 1)
        self.assertEqual(strategy["calendar_items"][0]["title"], "Post B")

    def test_database_transaction_rollback(self):
        payload = ContentStrategyValidator.validate(sample_payload(name="Rollback Strategy"))
        payload["content_calendar"].append(dict(payload["content_calendar"][0]))
        with self.assertRaises(Exception):
            ContentStrategyGenerationRepository.create_strategy_with_sections(
                self.workspace_id,
                self.company_id,
                payload,
                created_by=self.user_id,
            )
        strategies = ContentStrategyRepository.list_strategies(self.workspace_id, self.company_id, include_archived=True)
        self.assertFalse([s for s in strategies if s["name"] == "Rollback Strategy"])

    def test_workspace_isolation(self):
        service = ContentStrategyService(generation_service=StaticGenerationService(sample_payload()))
        result = service.generate_strategy(self.workspace_id, self.company_id, {}, created_by=self.user_id)
        self.assertTrue(result["ok"])
        self.assertEqual(
            ContentStrategyRepository.get_strategy(self.other_workspace_id, self.company_id, result["strategy_id"]),
            {},
        )
        bad = service.generate_strategy(self.other_workspace_id, self.company_id, {}, created_by=self.user_id)
        self.assertFalse(bad["ok"])


if __name__ == "__main__":
    unittest.main()
