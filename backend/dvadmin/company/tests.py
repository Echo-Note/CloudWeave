"""
主体公司 App — 模型测试
"""
from django.test import TestCase
from dvadmin.company.models import CompanyEntity


class CompanyEntityModelTest(TestCase):
    """主体公司模型测试"""

    def test_create_company(self):
        """测试创建主体公司"""
        company = CompanyEntity.objects.create(
            name="XX科技有限公司",
            short_name="XX科技",
            status="active",
        )
        self.assertEqual(company.name, "XX科技有限公司")
        self.assertEqual(company.short_name, "XX科技")
        self.assertEqual(company.status, "active")
        self.assertIsNotNone(company.create_datetime)

    def test_create_company_with_parent(self):
        """测试创建带父级关系的公司（集团→子公司）"""
        parent = CompanyEntity.objects.create(name="集团总部", status="active")
        child = CompanyEntity.objects.create(
            name="子公司A", short_name="子公司A", status="active", parent=parent
        )
        self.assertEqual(child.parent, parent)
        self.assertEqual(child.parent.name, "集团总部")

    def test_name_unique_constraint(self):
        """测试公司名称唯一约束"""
        CompanyEntity.objects.create(name="唯一公司", status="active")
        with self.assertRaises(Exception):
            CompanyEntity.objects.create(name="唯一公司", status="active")

    def test_credit_code_unique_when_not_null(self):
        """测试社会信用代码不为空时唯一"""
        CompanyEntity.objects.create(
            name="公司A", credit_code="123456789012345678", status="active"
        )
        with self.assertRaises(Exception):
            CompanyEntity.objects.create(
                name="公司B", credit_code="123456789012345678", status="active"
            )

    def test_str_method(self):
        """测试 __str__ 方法"""
        company = CompanyEntity.objects.create(name="测试公司", status="active")
        self.assertEqual(str(company), "测试公司")

    def test_default_status(self):
        """测试默认状态为 active"""
        company = CompanyEntity.objects.create(name="默认状态公司")
        self.assertEqual(company.status, "active")

    def test_ordering(self):
        """测试按创建时间倒序排列"""
        co1 = CompanyEntity.objects.create(name="公司1", status="active")
        co2 = CompanyEntity.objects.create(name="公司2", status="active")
        companies = list(CompanyEntity.objects.all())
        # 后创建的排在前面
        self.assertEqual(companies[0].name, "公司2")
        self.assertEqual(companies[1].name, "公司1")

    def test_db_table_name(self):
        """测试数据库表名"""
        self.assertEqual(CompanyEntity._meta.db_table, "dvadmin_company_entity")

    def test_verbose_name(self):
        """测试 verbose_name"""
        self.assertEqual(CompanyEntity._meta.verbose_name, "主体公司")
