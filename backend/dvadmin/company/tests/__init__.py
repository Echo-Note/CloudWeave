"""
主体公司 App — 测试套件入口

将所有子模块中的测试类重新导出，Django 测试运行器可自动发现。
"""
from dvadmin.company.tests.test_models import CompanyEntityModelTest
from dvadmin.company.tests.test_storage import BusinessLicenseStorageTest
from dvadmin.company.tests.test_api import CompanyEntityAPITest

__all__ = [
    "CompanyEntityModelTest",
    "BusinessLicenseStorageTest",
    "CompanyEntityAPITest",
]
