import unittest

from core.rbac import can_perform, has_permission, normalize_role


class RbacPermissionTests(unittest.TestCase):
    def test_viewer_is_read_only_across_action_tabs(self):
        self.assertEqual(normalize_role("viewer"), "viewer")
        self.assertTrue(can_perform("viewer", "view_history"))
        self.assertFalse(can_perform("viewer", "create_post"))
        self.assertFalse(can_perform("viewer", "manage_knowledge"))
        self.assertFalse(can_perform("viewer", "export_data"))
        self.assertFalse(can_perform("viewer", "publish_post"))
        self.assertFalse(can_perform("viewer", "schedule_post"))
        self.assertFalse(can_perform("viewer", "run_scheduler"))
        self.assertFalse(can_perform("viewer", "cancel_schedule"))

    def test_editor_can_create_but_not_publish_or_export(self):
        self.assertTrue(can_perform("editor", "create_post"))
        self.assertTrue(can_perform("editor", "manage_knowledge"))
        self.assertFalse(can_perform("editor", "publish_post"))
        self.assertFalse(can_perform("editor", "schedule_post"))
        self.assertFalse(can_perform("editor", "export_data"))

    def test_super_admin_has_runtime_permissions(self):
        self.assertTrue(has_permission("super_admin", "auto_post"))
        self.assertTrue(can_perform("super_admin", "publish_post"))
        self.assertTrue(can_perform("super_admin", "run_scheduler"))
        self.assertTrue(can_perform("super_admin", "approve_thumbnail"))
        self.assertTrue(can_perform("super_admin", "export_data"))


if __name__ == "__main__":
    unittest.main()
