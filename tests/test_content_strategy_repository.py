import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import database.connection as db_connection
from database.connection import init_db, get_db_connection
from database.migrations.content_strategy_center import TABLES, up as migrate_up, down as migrate_down
from database.models.companies import CompanyModel
from database.models.users import UserModel
from database.models.workspaces import WorkspaceModel
from database.repositories.content_strategy_repository import ContentStrategyRepository


class TestContentStrategyRepository(unittest.TestCase):
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
        self.user_id = UserModel.create(f"user{suffix}@example.com", f"user{suffix}", "secret")
        self.workspace_id = WorkspaceModel.create(f"Workspace {suffix}", owner_id=self.user_id)
        self.other_workspace_id = WorkspaceModel.create(f"Other Workspace {suffix}", owner_id=self.user_id)
        self.company_id = CompanyModel.create(self.workspace_id, f"Company {suffix}")
        self.other_company_id = CompanyModel.create(self.other_workspace_id, f"Other Company {suffix}")

    def test_migration_sqlite_creates_tables_and_is_idempotent(self):
        migrate_up(engine="sqlite")
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            for table in TABLES:
                cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?", (table,))
                self.assertEqual(cur.fetchone()[0], 1, table)
        finally:
            conn.close()

    def test_crud_strategy(self):
        strategy_id = ContentStrategyRepository.create_strategy(
            self.workspace_id,
            self.company_id,
            "Q3 Content Strategy",
            description="Quarter plan",
            metadata={"source": "test"},
            created_by=self.user_id,
        )
        strategy = ContentStrategyRepository.get_strategy(self.workspace_id, self.company_id, strategy_id)
        self.assertEqual(strategy["name"], "Q3 Content Strategy")
        self.assertEqual(strategy["metadata"]["source"], "test")

        updated = ContentStrategyRepository.update_strategy(
            self.workspace_id,
            self.company_id,
            strategy_id,
            status="generated",
            description="Updated",
            updated_by=self.user_id,
        )
        self.assertTrue(updated)
        strategy = ContentStrategyRepository.get_strategy(self.workspace_id, self.company_id, strategy_id)
        self.assertEqual(strategy["status"], "generated")
        self.assertEqual(strategy["description"], "Updated")

        self.assertTrue(ContentStrategyRepository.archive_strategy(self.workspace_id, self.company_id, strategy_id))
        self.assertEqual(ContentStrategyRepository.list_strategies(self.workspace_id, self.company_id), [])
        archived = ContentStrategyRepository.list_strategies(self.workspace_id, self.company_id, include_archived=True)
        self.assertEqual(len(archived), 1)
        self.assertEqual(archived[0]["status"], "archived")

    def test_workspace_isolation(self):
        strategy_id = ContentStrategyRepository.create_strategy(self.workspace_id, self.company_id, "Isolation")
        self.assertEqual(
            ContentStrategyRepository.get_strategy(self.other_workspace_id, self.company_id, strategy_id),
            {},
        )
        with self.assertRaises(ValueError):
            ContentStrategyRepository.create_strategy(self.other_workspace_id, self.company_id, "Bad tenant")

    def test_company_isolation(self):
        strategy_id = ContentStrategyRepository.create_strategy(self.workspace_id, self.company_id, "Company scope")
        self.assertEqual(
            ContentStrategyRepository.get_strategy(self.workspace_id, self.other_company_id, strategy_id),
            {},
        )
        with self.assertRaises(ValueError):
            ContentStrategyRepository.create_pillar(self.workspace_id, self.other_company_id, strategy_id, "Wrong")

    def test_cascade_behavior(self):
        strategy_id = ContentStrategyRepository.create_strategy(self.workspace_id, self.company_id, "Cascade")
        pillar_id = ContentStrategyRepository.create_pillar(self.workspace_id, self.company_id, strategy_id, "Education")
        conn = get_db_connection()
        try:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("DELETE FROM content_strategies WHERE id=?", (strategy_id,))
            conn.commit()
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM content_pillars WHERE id=?", (pillar_id,))
            self.assertEqual(cur.fetchone()[0], 0)
        finally:
            conn.close()

    def test_version_creation(self):
        strategy_id = ContentStrategyRepository.create_strategy(self.workspace_id, self.company_id, "Versioned")
        ContentStrategyRepository.create_pillar(self.workspace_id, self.company_id, strategy_id, "Trust")
        version_id = ContentStrategyRepository.create_strategy_version(
            self.workspace_id,
            self.company_id,
            strategy_id,
            notes="baseline",
            created_by=self.user_id,
        )
        self.assertTrue(version_id > 0)
        strategy = ContentStrategyRepository.get_strategy(self.workspace_id, self.company_id, strategy_id)
        self.assertEqual(strategy["version"], 1)

    def test_restore_version(self):
        strategy_id = ContentStrategyRepository.create_strategy(self.workspace_id, self.company_id, "Restore")
        pillar_id = ContentStrategyRepository.create_pillar(
            self.workspace_id,
            self.company_id,
            strategy_id,
            "Original",
            description="before",
        )
        version_id = ContentStrategyRepository.create_strategy_version(self.workspace_id, self.company_id, strategy_id)
        ContentStrategyRepository.update_pillar(
            self.workspace_id,
            self.company_id,
            strategy_id,
            pillar_id,
            name="Changed",
            description="after",
        )
        self.assertTrue(
            ContentStrategyRepository.restore_strategy_version(
                self.workspace_id,
                self.company_id,
                strategy_id,
                version_id,
                updated_by=self.user_id,
            )
        )
        strategy = ContentStrategyRepository.get_strategy(self.workspace_id, self.company_id, strategy_id)
        self.assertEqual(strategy["pillars"][0]["name"], "Original")
        self.assertEqual(strategy["pillars"][0]["description"], "before")

    def test_reordering(self):
        strategy_id = ContentStrategyRepository.create_strategy(self.workspace_id, self.company_id, "Reorder")
        first = ContentStrategyRepository.create_pillar(self.workspace_id, self.company_id, strategy_id, "First")
        second = ContentStrategyRepository.create_pillar(self.workspace_id, self.company_id, strategy_id, "Second")
        self.assertTrue(ContentStrategyRepository.reorder_pillars(self.workspace_id, self.company_id, strategy_id, [second, first]))
        strategy = ContentStrategyRepository.get_strategy(self.workspace_id, self.company_id, strategy_id)
        self.assertEqual([pillar["id"] for pillar in strategy["pillars"]], [second, first])

    def test_batch_insert(self):
        strategy_id = ContentStrategyRepository.create_strategy(self.workspace_id, self.company_id, "Batch")
        pillar_id = ContentStrategyRepository.create_pillar(self.workspace_id, self.company_id, strategy_id, "How To")
        subtopic_id = ContentStrategyRepository.create_subtopic(
            self.workspace_id,
            self.company_id,
            strategy_id,
            pillar_id,
            "Automation",
        )
        angle_ids = ContentStrategyRepository.create_angles_batch(
            self.workspace_id,
            self.company_id,
            strategy_id,
            [
                {"pillar_id": pillar_id, "subtopic_id": subtopic_id, "title": "Save time"},
                {"pillar_id": pillar_id, "subtopic_id": subtopic_id, "title": "Reduce errors"},
            ],
        )
        self.assertEqual(len(angle_ids), 2)
        item_ids = ContentStrategyRepository.create_calendar_items_batch(
            self.workspace_id,
            self.company_id,
            strategy_id,
            [
                {"pillar_id": pillar_id, "subtopic_id": subtopic_id, "angle_id": angle_ids[0], "title": "Post A", "planned_date": "2026-08-01"},
                {"pillar_id": pillar_id, "subtopic_id": subtopic_id, "angle_id": angle_ids[1], "title": "Post B", "planned_date": "2026-08-02"},
            ],
        )
        self.assertEqual(len(item_ids), 2)
        self.assertEqual(len(ContentStrategyRepository.list_calendar_items(self.workspace_id, self.company_id, strategy_id)), 2)

    def test_deleted_calendar_children_are_not_loaded_with_strategy(self):
        strategy_id = ContentStrategyRepository.create_strategy(self.workspace_id, self.company_id, "Soft deleted child")
        item_ids = ContentStrategyRepository.create_calendar_items_batch(
            self.workspace_id,
            self.company_id,
            strategy_id,
            [{"title": "Visible Post", "planned_date": "2026-08-01"}, {"title": "Deleted Post", "planned_date": "2026-08-02"}],
        )
        self.assertTrue(ContentStrategyRepository.delete_calendar_item(self.workspace_id, self.company_id, strategy_id, item_ids[1], updated_by=self.user_id))
        strategy = ContentStrategyRepository.get_strategy(self.workspace_id, self.company_id, strategy_id)
        self.assertEqual([item["title"] for item in strategy["calendar_items"]], ["Visible Post"])

    def test_list_strategies_supports_limit_offset(self):
        for index in range(4):
            ContentStrategyRepository.create_strategy(self.workspace_id, self.company_id, f"Paged Repo {index}")
        first_page = ContentStrategyRepository.list_strategies(self.workspace_id, self.company_id, limit=2, offset=0)
        second_page = ContentStrategyRepository.list_strategies(self.workspace_id, self.company_id, limit=2, offset=2)
        self.assertEqual(len(first_page), 2)
        self.assertEqual(len(second_page), 2)
        self.assertNotEqual({row["id"] for row in first_page}, {row["id"] for row in second_page})

    def test_invalid_foreign_key(self):
        strategy_id = ContentStrategyRepository.create_strategy(self.workspace_id, self.company_id, "Invalid FK")
        with self.assertRaises(ValueError):
            ContentStrategyRepository.create_subtopic(
                self.workspace_id,
                self.company_id,
                strategy_id,
                pillar_id=999999,
                name="Missing pillar",
            )

    def test_duplicate_handling(self):
        strategy_id = ContentStrategyRepository.create_strategy(self.workspace_id, self.company_id, "Duplicates")
        ContentStrategyRepository.create_pillar(self.workspace_id, self.company_id, strategy_id, "Same")
        with self.assertRaises(ValueError):
            ContentStrategyRepository.create_pillar(self.workspace_id, self.company_id, strategy_id, "Same")


if __name__ == "__main__":
    unittest.main()

