"""
办公资产管理 — 模型测试

覆盖资产类型、办公资产、SIM卡实名、借用/归还/调拨/操作流水。
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from dvadmin.company.models import CompanyEntity
from dvadmin.office.models import (
    AssetCategory, OfficeAsset, SimCardInfo,
    AssetBorrowRecord, AssetTransferRecord, AssetOperationLog,
)

User = get_user_model()


class AssetCategoryModelTest(TestCase):
    """资产类型模型测试"""

    def test_create_category(self):
        """测试创建资产类型"""
        cat = AssetCategory.objects.create(name="笔记本", icon="laptop")
        self.assertEqual(cat.name, "笔记本")
        self.assertTrue(cat.is_enabled)
        self.assertFalse(cat.is_preset)

    def test_default_custom_fields_schema(self):
        """测试默认自定义字段为空列表"""
        cat = AssetCategory.objects.create(name="显示器")
        self.assertEqual(cat.custom_fields_schema, [])

    def test_name_unique(self):
        """测试名称唯一"""
        AssetCategory.objects.create(name="手机")
        with self.assertRaises(Exception):
            AssetCategory.objects.create(name="手机")

    def test_preset_category(self):
        """测试预置类型"""
        cat = AssetCategory.objects.create(name="台式机", is_preset=True)
        self.assertTrue(cat.is_preset)

    def test_str_method(self):
        """测试 __str__ 方法"""
        cat = AssetCategory.objects.create(name="平板")
        self.assertEqual(str(cat), "平板")


class OfficeAssetModelTest(TestCase):
    """办公资产模型测试"""

    def setUp(self):
        self.company = CompanyEntity.objects.create(name="子公司A", status="active")
        self.category = AssetCategory.objects.create(name="笔记本")
        self.user = User.objects.create(username="admin", is_active=True)

    def test_create_asset(self):
        """测试创建办公资产"""
        asset = OfficeAsset.objects.create(
            asset_code="ZC-20260630-0001", name="ThinkPad X1",
            category=self.category, company=self.company, status="in_stock"
        )
        self.assertEqual(asset.name, "ThinkPad X1")
        self.assertEqual(asset.status, "in_stock")

    def test_default_status(self):
        """测试默认状态为在库"""
        asset = OfficeAsset.objects.create(
            asset_code="ZC-DEFAULT-0001", name="测试设备",
            category=self.category, company=self.company
        )
        self.assertEqual(asset.status, "in_stock")

    def test_asset_code_unique(self):
        """测试资产编号唯一"""
        OfficeAsset.objects.create(
            asset_code="ZC-UNIQUE-0001", name="设备A",
            category=self.category, company=self.company
        )
        with self.assertRaises(Exception):
            OfficeAsset.objects.create(
                asset_code="ZC-UNIQUE-0001", name="设备B",
                category=self.category, company=self.company
            )

    def test_soft_delete(self):
        """测试软删除"""
        asset = OfficeAsset.objects.create(
            asset_code="ZC-DEL-0001", name="待删除设备",
            category=self.category, company=self.company
        )
        asset.is_deleted = True
        asset.save()
        self.assertEqual(OfficeAsset.objects.filter(asset_code="ZC-DEL-0001").count(), 0)

    def test_str_method(self):
        """测试 __str__ 方法"""
        asset = OfficeAsset.objects.create(
            asset_code="ZC-STR-0001", name="测试资产",
            category=self.category, company=self.company
        )
        self.assertIn("ZC-STR-0001", str(asset))
        self.assertIn("测试资产", str(asset))


class SimCardInfoModelTest(TestCase):
    """SIM卡实名信息模型测试"""

    def setUp(self):
        self.company = CompanyEntity.objects.create(name="子公司A", status="active")
        self.category = AssetCategory.objects.create(name="手机卡")
        self.asset = OfficeAsset.objects.create(
            asset_code="ZC-SIM-0001", name="移动SIM卡",
            category=self.category, company=self.company
        )

    def test_create_sim_info(self):
        """测试创建SIM卡信息"""
        sim = SimCardInfo.objects.create(
            asset=self.asset,
            phone_number="13800138000",
            real_name="张三",
            id_number="encrypted_id_123",
            id_number_hash="hash_abc123",
            carrier="china_mobile",
        )
        self.assertEqual(sim.phone_number, "13800138000")
        self.assertEqual(sim.real_name, "张三")

    def test_one_to_one_asset(self):
        """测试资产一对一关系"""
        SimCardInfo.objects.create(
            asset=self.asset, phone_number="13800138000",
            real_name="张三", id_number="enc_123",
            id_number_hash="hash_123", carrier="china_mobile",
        )
        with self.assertRaises(Exception):
            SimCardInfo.objects.create(
                asset=self.asset, phone_number="13900139000",
                real_name="李四", id_number="enc_456",
                id_number_hash="hash_456", carrier="china_unicom",
            )

    def test_str_method(self):
        """测试 __str__ 方法"""
        sim = SimCardInfo.objects.create(
            asset=self.asset, phone_number="13800138000",
            real_name="张三", id_number="enc_123",
            id_number_hash="hash_123", carrier="china_mobile",
        )
        self.assertIn("13800138000", str(sim))
        self.assertIn("张三", str(sim))


class AssetBorrowRecordModelTest(TestCase):
    """借用记录模型测试"""

    def setUp(self):
        self.company = CompanyEntity.objects.create(name="子公司A", status="active")
        self.category = AssetCategory.objects.create(name="笔记本")
        self.asset = OfficeAsset.objects.create(
            asset_code="ZC-BORROW-0001", name="测试笔记本",
            category=self.category, company=self.company
        )
        self.user = User.objects.create(username="admin", is_active=True)

    def test_create_borrow_record(self):
        """测试创建借用记录"""
        record = AssetBorrowRecord.objects.create(
            asset=self.asset, borrower=self.user,
            borrow_reason="项目开发需要",
            expected_return_date="2026-07-15",
        )
        self.assertEqual(record.approval_status, "pending")
        self.assertFalse(record.is_overdue)

    def test_approval_workflow(self):
        """测试审批流程"""
        record = AssetBorrowRecord.objects.create(
            asset=self.asset, borrower=self.user,
            borrow_reason="测试", expected_return_date="2026-07-15",
        )
        record.approval_status = "approved"
        record.approved_by = self.user
        record.save()
        self.assertEqual(record.approval_status, "approved")

    def test_return_workflow(self):
        """测试归还流程"""
        record = AssetBorrowRecord.objects.create(
            asset=self.asset, borrower=self.user,
            borrow_reason="测试", expected_return_date="2026-07-15",
        )
        record.return_status = "normal"
        record.return_note = "设备正常"
        record.save()
        self.assertEqual(record.return_status, "normal")

    def test_str_method(self):
        """测试 __str__ 方法"""
        record = AssetBorrowRecord.objects.create(
            asset=self.asset, borrower=self.user,
            borrow_reason="测试", expected_return_date="2026-07-15",
        )
        self.assertIn(str(self.user), str(record))


class AssetTransferRecordModelTest(TestCase):
    """资产调拨记录模型测试"""

    def setUp(self):
        self.company_a = CompanyEntity.objects.create(name="子公司A", status="active")
        self.company_b = CompanyEntity.objects.create(name="子公司B", status="active")
        self.category = AssetCategory.objects.create(name="显示器")
        self.asset = OfficeAsset.objects.create(
            asset_code="ZC-TRANS-0001", name="戴尔显示器",
            category=self.category, company=self.company_a
        )
        self.user = User.objects.create(username="admin", is_active=True)

    def test_create_transfer(self):
        """测试创建调拨记录"""
        transfer = AssetTransferRecord.objects.create(
            asset=self.asset, from_company=self.company_a,
            to_company=self.company_b, transfer_reason="业务需要",
            status="pending"
        )
        self.assertEqual(transfer.from_company, self.company_a)
        self.assertEqual(transfer.to_company, self.company_b)
        self.assertEqual(transfer.status, "pending")

    def test_str_method(self):
        """测试 __str__ 方法"""
        transfer = AssetTransferRecord.objects.create(
            asset=self.asset, from_company=self.company_a,
            to_company=self.company_b, transfer_reason="测试",
        )
        self.assertIn("子公司A", str(transfer))
        self.assertIn("子公司B", str(transfer))


class AssetOperationLogModelTest(TestCase):
    """资产操作流水模型测试"""

    def setUp(self):
        self.company = CompanyEntity.objects.create(name="子公司A", status="active")
        self.category = AssetCategory.objects.create(name="笔记本")
        self.asset = OfficeAsset.objects.create(
            asset_code="ZC-LOG-0001", name="操作日志测试机",
            category=self.category, company=self.company
        )
        self.user = User.objects.create(username="admin", is_active=True)

    def test_create_operation_log(self):
        """测试创建操作日志"""
        log = AssetOperationLog.objects.create(
            asset=self.asset, operation_type="purchase",
            from_status=None, to_status="in_stock",
            operator=self.user,
        )
        self.assertEqual(log.operation_type, "purchase")
        self.assertEqual(log.to_status, "in_stock")

    def test_status_transition(self):
        """测试状态变更日志"""
        log = AssetOperationLog.objects.create(
            asset=self.asset, operation_type="borrow",
            from_status="in_stock", to_status="borrowed",
            operator=self.user,
            detail={"borrow_record_id": 1},
        )
        self.assertEqual(log.from_status, "in_stock")
        self.assertEqual(log.to_status, "borrowed")

    def test_str_method(self):
        """测试 __str__ 方法"""
        log = AssetOperationLog.objects.create(
            asset=self.asset, operation_type="scrap",
            from_status="in_stock", to_status="scrapped",
            operator=self.user,
        )
        self.assertIn(str(self.asset), str(log))
