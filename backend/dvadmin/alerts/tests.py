"""
告警管理 — 模型测试
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from dvadmin.cloud.models import CloudPlatform
from dvadmin.alerts.models import AlertRule, AlertRuleUsers, AlertRecord

User = get_user_model()


class AlertRuleModelTest(TestCase):
    """告警规则模型测试"""

    def test_create_alert_rule(self):
        """测试创建告警规则"""
        rule = AlertRule.objects.create(
            name="余额不足告警",
            alert_type="balance_threshold",
            severity="critical",
            condition_config={"threshold": 1000, "operator": "lte"},
            channels=["in_app", "email"],
            is_enabled=True,
        )
        self.assertEqual(rule.name, "余额不足告警")
        self.assertEqual(rule.severity, "critical")
        self.assertTrue(rule.is_enabled)
        self.assertEqual(rule.cooldown_minutes, 120)

    def test_default_cooldown(self):
        """测试默认冷却时间"""
        rule = AlertRule.objects.create(
            name="测试规则", alert_type="sync_failure",
            severity="warning",
            condition_config={"consecutive_failures": 3},
            channels=["in_app"],
        )
        self.assertEqual(rule.cooldown_minutes, 120)

    def test_str_method(self):
        """测试 __str__ 方法"""
        rule = AlertRule.objects.create(
            name="资源到期告警", alert_type="resource_expire",
            severity="warning",
            condition_config={"days_before": [30, 15, 7], "resource_types": ["server", "domain"]},
            channels=["in_app"],
        )
        self.assertIn("资源到期告警", str(rule))

    def test_rule_with_cloud_platform(self):
        """测试关联云平台的告警规则"""
        platform = CloudPlatform.objects.create(name="腾讯云")
        rule = AlertRule.objects.create(
            name="指定账号告警", alert_type="balance_threshold",
            severity="warning", cloud_platform=platform,
            condition_config={"threshold": 500},
            channels=["in_app"],
        )
        self.assertEqual(rule.cloud_platform, platform)


class AlertRuleUsersModelTest(TestCase):
    """告警通知人模型测试"""

    def setUp(self):
        self.superuser = User.objects.create(
            username="admin", is_active=True
        )
        self.rule = AlertRule.objects.create(
            name="测试规则", alert_type="sync_failure",
            severity="warning",
            condition_config={"consecutive_failures": 3},
            channels=["in_app"],
        )

    def test_create_alert_rule_user(self):
        """测试创建告警通知人关联"""
        relation = AlertRuleUsers.objects.create(
            alert_rule=self.rule, user=self.superuser
        )
        self.assertEqual(relation.alert_rule, self.rule)
        self.assertEqual(relation.user, self.superuser)

    def test_unique_constraint(self):
        """测试 (alert_rule, user) 唯一约束"""
        AlertRuleUsers.objects.create(alert_rule=self.rule, user=self.superuser)
        with self.assertRaises(Exception):
            AlertRuleUsers.objects.create(alert_rule=self.rule, user=self.superuser)


class AlertRecordModelTest(TestCase):
    """告警记录模型测试"""

    def setUp(self):
        self.rule = AlertRule.objects.create(
            name="测试规则", alert_type="balance_threshold",
            severity="critical",
            condition_config={"threshold": 1000},
            channels=["in_app"],
        )

    def test_create_alert_record(self):
        """测试创建告警记录"""
        record = AlertRecord.objects.create(
            alert_rule=self.rule, alert_type="balance_threshold",
            severity="critical", title="余额不足",
            message="账号余额仅剩100元", triggered_at="2026-06-30T10:00:00Z",
        )
        self.assertEqual(record.status, "triggered")
        self.assertEqual(record.severity, "critical")

    def test_acknowledge_alert(self):
        """测试确认告警"""
        superuser = User.objects.create(
            username="admin", is_active=True
        )
        record = AlertRecord.objects.create(
            alert_rule=self.rule, alert_type="balance_threshold",
            severity="critical", title="测试告警", message="详情",
            triggered_at="2026-06-30T10:00:00Z",
        )
        record.status = "acknowledged"
        record.acknowledged_by = superuser
        record.save()
        self.assertEqual(record.status, "acknowledged")

    def test_str_method(self):
        """测试 __str__ 方法"""
        record = AlertRecord.objects.create(
            alert_rule=self.rule, alert_type="balance_threshold",
            severity="critical", title="测试告警",
            message="详情", triggered_at="2026-06-30T10:00:00Z",
        )
        self.assertIn("测试告警", str(record))
