import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import database.connection as db_connection
from database.connection import init_db, managed_connection
from database.models.prompt_versions import PromptVersionModel
from database.models.users import UserModel
from database.models.workspaces import WorkspaceModel
from database.repositories.audit_repository import AuditRepository
from database.repositories.knowledge_repository import KnowledgeRepository
from database.repositories.post_repository import PostRepository
from database.repositories.weekly_schedule_repository import WeeklyScheduleRepository


class TestRepositoryWorkspaceGuards(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        cls.tmp.close()
        cls.original_db_path = db_connection.DB_PATH
        cls.original_engine = db_connection.DB_ENGINE
        db_connection.DB_PATH = cls.tmp.name
        db_connection.DB_ENGINE = "sqlite"
        init_db()

    @classmethod
    def tearDownClass(cls):
        db_connection.DB_PATH = cls.original_db_path
        db_connection.DB_ENGINE = cls.original_engine
        if os.path.exists(cls.tmp.name):
            os.unlink(cls.tmp.name)

    def setUp(self):
        suffix = str(id(self))
        self.user_id = UserModel.create(f"guard{suffix}@example.com", f"guard{suffix}", "secret")
        self.workspace_id = WorkspaceModel.create(f"Guard Workspace {suffix}", owner_id=self.user_id)
        self.other_workspace_id = WorkspaceModel.create(f"Other Guard Workspace {suffix}", owner_id=self.user_id)

    def test_repositories_require_workspace(self):
        guarded_calls = [
            lambda: PostRepository.get_all_posts(),
            lambda: PostRepository.add_post("2026-01-01", "facebook", "Topic", "Content", "draft", "marketing_viral"),
            lambda: KnowledgeRepository.get_knowledge_posts(),
            lambda: KnowledgeRepository.delete_knowledge_post(1),
            lambda: WeeklyScheduleRepository.get_latest_weekly_schedule(),
            lambda: WeeklyScheduleRepository.add_weekly_schedule("2026-01-01", "{}"),
            lambda: AuditRepository.get_logs(),
            lambda: AuditRepository.get_summary(),
        ]
        for call in guarded_calls:
            with self.assertRaises(ValueError):
                call()

    def test_audit_repository_does_not_include_global_logs(self):
        with managed_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO audit_logs (timestamp, user_id, user_email, workspace_id, action, description)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                ("2026-01-01T00:00:00", self.user_id, "guard@example.com", None, "GLOBAL_ACTION", "global"),
            )
            cur.execute(
                """
                INSERT INTO audit_logs (timestamp, user_id, user_email, workspace_id, action, description)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                ("2026-01-01T00:01:00", self.user_id, "guard@example.com", self.workspace_id, "WORKSPACE_ACTION", "workspace"),
            )

        logs = AuditRepository.get_logs(workspace_id=self.workspace_id, limit=20)
        self.assertEqual(set(logs["action"]), {"WORKSPACE_ACTION"})
        self.assertEqual(AuditRepository.get_summary(workspace_id=self.workspace_id), {"WORKSPACE_ACTION": 1})

    def test_prompt_active_does_not_fallback_to_global_when_workspace_is_present(self):
        PromptVersionModel.create("guard_prompt", "global content", workspace_id=None, created_by=self.user_id)
        self.assertEqual(PromptVersionModel.get_active("guard_prompt", workspace_id=self.workspace_id), {})

        PromptVersionModel.create("guard_prompt", "workspace content", workspace_id=self.workspace_id, created_by=self.user_id)
        active = PromptVersionModel.get_active("guard_prompt", workspace_id=self.workspace_id)
        self.assertEqual(active.get("content"), "workspace content")


if __name__ == "__main__":
    unittest.main()
