"""
MCP 智能集成 — 模型测试
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from dvadmin.mcp_server.models import McpApiKey, McpAuditLog

User = get_user_model()


class McpApiKeyModelTest(TestCase):
    """MCP API Key 模型测试"""

    def setUp(self):
        self.superuser = User.objects.create(
            username="admin", is_active=True
        )

    def test_create_api_key(self):
        """测试创建 API Key"""
        key = McpApiKey.objects.create(
            name="测试Key",
            key_hash="abc123def456",
            key_prefix="abc123de",
            permission_level="readonly",
            created_by=self.superuser,
        )
        self.assertEqual(key.name, "测试Key")
        self.assertEqual(key.permission_level, "readonly")
        self.assertTrue(key.is_active)

    def test_default_permission_level(self):
        """测试默认权限为只读"""
        key = McpApiKey.objects.create(
            name="默认权限Key", key_hash="hash123", key_prefix="hash1234",
        )
        self.assertEqual(key.permission_level, "readonly")

    def test_deactivate_key(self):
        """测试停用 API Key"""
        key = McpApiKey.objects.create(
            name="待停用Key", key_hash="hash456", key_prefix="hash4567",
        )
        key.is_active = False
        key.save()
        self.assertFalse(key.is_active)

    def test_str_method(self):
        """测试 __str__ 方法"""
        key = McpApiKey.objects.create(
            name="显示测试Key", key_hash="hash789", key_prefix="hash7890",
        )
        self.assertIn("显示测试Key", str(key))
        self.assertIn("启用", str(key))


class McpAuditLogModelTest(TestCase):
    """MCP 调用审计日志模型测试"""

    def setUp(self):
        self.key = McpApiKey.objects.create(
            name="审计Key", key_hash="audit123", key_prefix="audit123",
        )

    def test_create_audit_log(self):
        """测试创建审计日志"""
        log = McpAuditLog.objects.create(
            api_key=self.key, tool_name="search_resources",
            tool_args={"query": "test"},
            tool_result_status="success",
            execution_time_ms=150,
        )
        self.assertEqual(log.tool_name, "search_resources")
        self.assertEqual(log.tool_result_status, "success")
        self.assertEqual(log.execution_time_ms, 150)

    def test_result_status_choices(self):
        """测试执行结果 choices"""
        log = McpAuditLog.objects.create(
            api_key=self.key, tool_name="list_projects",
            tool_args={}, tool_result_status="denied",
        )
        self.assertEqual(log.get_tool_result_status_display(), "拒绝")

    def test_str_method(self):
        """测试 __str__ 方法"""
        log = McpAuditLog.objects.create(
            api_key=self.key, tool_name="get_balance",
            tool_args={}, tool_result_status="success",
        )
        self.assertIn("get_balance", str(log))
