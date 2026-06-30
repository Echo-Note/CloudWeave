"""
云平台管理 — 模型测试
"""
from django.test import TestCase
from dvadmin.company.models import CompanyEntity
from dvadmin.cloud.models import CloudPlatform, Registrar, SyncLog, BalanceRecord


class CloudPlatformModelTest(TestCase):
    """云平台账号模型测试"""

    def setUp(self):
        self.company = CompanyEntity.objects.create(name="测试公司", status="active")

    def test_create_cloud_platform(self):
        """测试创建云平台账号"""
        platform = CloudPlatform.objects.create(
            name="腾讯云", account_alias="生产账号", company=self.company
        )
        self.assertEqual(platform.name, "腾讯云")
        self.assertEqual(platform.account_alias, "生产账号")
        self.assertEqual(platform.company, self.company)
        self.assertFalse(platform.sync_enabled)

    def test_default_sync_interval(self):
        """测试默认同步间隔"""
        platform = CloudPlatform.objects.create(name="阿里云")
        self.assertEqual(platform.sync_interval_minutes, 360)

    def test_str_method(self):
        """测试 __str__ 方法"""
        platform = CloudPlatform.objects.create(
            name="腾讯云", account_alias="生产账号"
        )
        self.assertIn("腾讯云", str(platform))
        self.assertIn("生产账号", str(platform))

    def test_last_sync_status_choices(self):
        """测试同步状态 choices"""
        platform = CloudPlatform.objects.create(
            name="华为云", last_sync_status="success"
        )
        self.assertEqual(platform.last_sync_status, "success")
        self.assertEqual(platform.get_last_sync_status_display(), "成功")

    def test_sync_enabled_default_false(self):
        """测试默认不同步"""
        platform = CloudPlatform.objects.create(name="AWS")
        self.assertFalse(platform.sync_enabled)


class RegistrarModelTest(TestCase):
    """域名注册商模型测试"""

    def setUp(self):
        self.company = CompanyEntity.objects.create(name="测试公司", status="active")

    def test_create_registrar(self):
        """测试创建注册商"""
        registrar = Registrar.objects.create(
            name="腾讯云", account_alias="注册账户", company=self.company
        )
        self.assertEqual(registrar.name, "腾讯云")
        self.assertEqual(registrar.company, self.company)

    def test_str_method(self):
        """测试 __str__ 方法"""
        registrar = Registrar.objects.create(name="GoDaddy")
        self.assertIn("GoDaddy", str(registrar))


class SyncLogModelTest(TestCase):
    """同步日志模型测试"""

    def test_create_sync_log(self):
        """测试创建同步日志"""
        platform = CloudPlatform.objects.create(name="腾讯云")
        log = SyncLog.objects.create(
            cloud_platform=platform,
            sync_type="full",
            trigger="manual",
            status="running",
            started_at="2026-06-30T10:00:00Z",
        )
        self.assertEqual(log.sync_type, "full")
        self.assertEqual(log.status, "running")

    def test_ordering_by_started_at_desc(self):
        """测试按开始时间倒序排列"""
        from datetime import datetime, timezone
        platform = CloudPlatform.objects.create(name="腾讯云")
        t1 = datetime(2026, 6, 30, 10, 0, 0, tzinfo=timezone.utc)
        t2 = datetime(2026, 6, 30, 12, 0, 0, tzinfo=timezone.utc)
        SyncLog.objects.create(
            cloud_platform=platform, sync_type="full", trigger="scheduled",
            status="success", started_at=t1,
        )
        SyncLog.objects.create(
            cloud_platform=platform, sync_type="full", trigger="scheduled",
            status="success", started_at=t2,
        )
        logs = list(SyncLog.objects.all())
        # 后创建的排在前面
        self.assertGreater(logs[0].started_at, logs[1].started_at)


class BalanceRecordModelTest(TestCase):
    """余额记录模型测试"""

    def test_create_balance_record(self):
        """测试创建余额记录"""
        platform = CloudPlatform.objects.create(name="腾讯云")
        record = BalanceRecord.objects.create(
            cloud_platform=platform,
            cash_balance=1000.00,
            total_balance=1200.00,
            recorded_at="2026-06-30T10:00:00Z",
        )
        self.assertEqual(record.cash_balance, 1000.00)
        self.assertEqual(record.total_balance, 1200.00)
        self.assertEqual(record.currency, "CNY")

    def test_default_currency(self):
        """测试默认币种为 CNY"""
        platform = CloudPlatform.objects.create(name="腾讯云")
        record = BalanceRecord.objects.create(
            cloud_platform=platform, total_balance=100.00,
            recorded_at="2026-06-30T10:00:00Z",
        )
        self.assertEqual(record.currency, "CNY")
