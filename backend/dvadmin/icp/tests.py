"""
ICP备案管理 — 模型测试
"""
from django.test import TestCase
from dvadmin.company.models import CompanyEntity
from dvadmin.assets.models import Domain
from dvadmin.icp.models import IcpRecord, IcpChangeLog


class IcpRecordModelTest(TestCase):
    """备案记录模型测试"""

    def setUp(self):
        self.company = CompanyEntity.objects.create(name="备案主体公司", status="active")
        self.domain = Domain.objects.create(name="example.com", icp_status="filed")

    def test_create_icp_record(self):
        """测试创建备案记录"""
        record = IcpRecord.objects.create(
            domain=self.domain, company=self.company, company_type="enterprise",
            contact_person="张三", contact_phone="13800138000",
            icp_number="京ICP备2024XXXXXX号",
        )
        self.assertEqual(record.domain, self.domain)
        self.assertEqual(record.company, self.company)
        self.assertEqual(record.icp_number, "京ICP备2024XXXXXX号")
        self.assertEqual(record.status, "active")

    def test_one_to_one_domain(self):
        """测试域名与备案记录一对一关系"""
        IcpRecord.objects.create(
            domain=self.domain, company=self.company, company_type="enterprise",
            contact_person="张三", contact_phone="13800138000",
        )
        domain2 = Domain.objects.create(name="example2.com")
        with self.assertRaises(Exception):
            # 同一个 domain 不能有两个备案记录
            IcpRecord.objects.create(
                domain=self.domain, company=self.company, company_type="enterprise",
                contact_person="李四", contact_phone="13900139000",
            )

    def test_str_method(self):
        """测试 __str__ 方法"""
        record = IcpRecord.objects.create(
            domain=self.domain, company=self.company, company_type="enterprise",
            contact_person="张三", contact_phone="13800138000",
        )
        self.assertIn("example.com", str(record))


class IcpChangeLogModelTest(TestCase):
    """备案变更历史模型测试"""

    def setUp(self):
        self.company = CompanyEntity.objects.create(name="备案主体公司", status="active")
        self.domain = Domain.objects.create(name="example.com", icp_status="filed")
        self.record = IcpRecord.objects.create(
            domain=self.domain, company=self.company, company_type="enterprise",
            contact_person="张三", contact_phone="13800138000",
        )

    def test_create_change_log(self):
        """测试创建变更记录"""
        log = IcpChangeLog.objects.create(
            icp_record=self.record,
            field_name="contact_person",
            old_value="张三",
            new_value="李四",
            status="draft",
        )
        self.assertEqual(log.field_name, "contact_person")
        self.assertEqual(log.old_value, "张三")
        self.assertEqual(log.new_value, "李四")
        self.assertEqual(log.status, "draft")

    def test_status_choices(self):
        """测试变更状态 choices"""
        log = IcpChangeLog.objects.create(
            icp_record=self.record, field_name="contact_phone",
            old_value="13800138000", new_value="13900139000",
            status="pending",
        )
        self.assertEqual(log.get_status_display(), "待审核")
        log.status = "approved"
        log.save()
        self.assertEqual(log.get_status_display(), "已通过")

    def test_str_method(self):
        """测试 __str__ 方法"""
        log = IcpChangeLog.objects.create(
            icp_record=self.record, field_name="contact_person",
            old_value="张三", new_value="李四", status="draft",
        )
        self.assertIn("contact_person", str(log))
        self.assertIn("张三", str(log))
        self.assertIn("李四", str(log))
