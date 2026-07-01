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
        self.assertEqual(CompanyEntity._meta.db_table, "company_entity")

    def test_verbose_name(self):
        """测试 verbose_name"""
        self.assertEqual(CompanyEntity._meta.verbose_name, "主体公司")


class BusinessLicenseStorageTest(TestCase):
    """
    营业执照字段 — 对象存储（S3/腾讯云 COS）集成测试

    验证 .env 配置正确时，FileField 上传/读取/删除/列出的全流程。
    实际连接到腾讯云 COS 桶 yunwei-1328164982。

    每个测试用例自行创建临时文件并在 finally 中清理，互不干扰。
    """

    TEST_PREFIX = "files/license/_test"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        from django.conf import settings
        from django.core.files.storage import default_storage
        cls.storage = default_storage
        cls.bucket = getattr(settings, "AWS_STORAGE_BUCKET_NAME", "")
        cls.region = getattr(settings, "AWS_S3_REGION_NAME", "")
        cls.endpoint = getattr(settings, "AWS_S3_ENDPOINT_URL", "")

    @classmethod
    def tearDownClass(cls):
        """清理测试前缀下的所有残留文件"""
        try:
            dirs, files = cls.storage.listdir(cls.TEST_PREFIX)
            for f in files:
                cls.storage.delete(f"{cls.TEST_PREFIX}/{f}")
        except Exception:
            pass
        super().tearDownClass()

    # ---------- 存储后端验证 ----------

    def test_storage_backend_is_s3(self):
        """验证默认存储后端是 S3Storage（凭证已加载）"""
        backend_name = self.storage.__class__.__name__
        self.assertEqual(backend_name, "S3Storage",
                         f"期望 S3Storage，实际为 {backend_name}")

    def test_storage_config(self):
        """验证腾讯云 COS 配置已正确加载"""
        from django.conf import settings
        self.assertEqual(settings.AWS_STORAGE_BUCKET_NAME, "yunwei-1328164982")
        self.assertEqual(settings.AWS_S3_REGION_NAME, "ap-guangzhou")
        self.assertIn("myqcloud.com", settings.AWS_S3_ENDPOINT_URL)
        self.assertEqual(settings.STORAGE_PROVIDER, "cos")

    # ---------- 上传 ----------

    def test_upload_business_license(self):
        """测试通过模型 FileField 上传营业执照到 COS"""
        from dvadmin.company.models import CompanyEntity
        from django.core.files.uploadedfile import SimpleUploadedFile

        company = CompanyEntity.objects.create(name="测试上传公司", status="active")
        try:
            upload = SimpleUploadedFile(
                "license.png", b"fake-png-data", content_type="image/png"
            )
            company.business_license.save("license.png", upload, save=True)
            company.refresh_from_db()

            self.assertTrue(company.business_license)
            self.assertIn("license", company.business_license.name)
            self.assertTrue(
                company.business_license.name.startswith("files/license/"),
                f"期望路径以 files/license/ 开头，实际: {company.business_license.name}"
            )
        finally:
            if company.pk and company.business_license:
                company.business_license.delete(save=False)
            company.delete()

    def test_upload_single_file(self):
        """测试直接通过 storage.save 上传单个文件"""
        from django.core.files.base import ContentFile

        path = f"{self.TEST_PREFIX}/upload_test.txt"
        content = b"hello-cos-upload"
        try:
            saved = self.storage.save(path, ContentFile(content))
            self.assertTrue(self.storage.exists(saved))
            self.assertEqual(saved, path)
        finally:
            if self.storage.exists(path):
                self.storage.delete(path)

    # ---------- 获取单个文件 ----------

    def test_get_file_read_content(self):
        """测试读取已上传文件的内容"""
        from django.core.files.base import ContentFile

        path = f"{self.TEST_PREFIX}/read_test.txt"
        content = b"hello-from-cos-read-test"
        try:
            self.storage.save(path, ContentFile(content))
            with self.storage.open(path, "rb") as f:
                read_back = f.read()
            self.assertEqual(read_back, content)
        finally:
            if self.storage.exists(path):
                self.storage.delete(path)

    def test_get_file_size(self):
        """测试获取文件大小"""
        from django.core.files.base import ContentFile

        path = f"{self.TEST_PREFIX}/size_test.txt"
        content = b"A" * 1024  # 1KB
        try:
            self.storage.save(path, ContentFile(content))
            file_size = self.storage.size(path)
            self.assertEqual(file_size, 1024)
        finally:
            if self.storage.exists(path):
                self.storage.delete(path)

    def test_get_file_modified_time(self):
        """测试获取文件最后修改时间"""
        from django.core.files.base import ContentFile
        from datetime import datetime, timedelta

        path = f"{self.TEST_PREFIX}/mtime_test.txt"
        try:
            self.storage.save(path, ContentFile(b"mtime-test"))
            mtime = self.storage.get_modified_time(path)
            self.assertIsInstance(mtime, datetime)
            # 修改时间应在最近 1 分钟内
            self.assertGreater(mtime, datetime.now() - timedelta(minutes=1))
        finally:
            if self.storage.exists(path):
                self.storage.delete(path)

    # ---------- 列出文件 ----------

    def test_listdir_empty_prefix(self):
        """测试列出空目录下的文件"""
        from django.core.files.base import ContentFile

        paths = [
            f"{self.TEST_PREFIX}/list_a.txt",
            f"{self.TEST_PREFIX}/list_b.txt",
            f"{self.TEST_PREFIX}/list_c.txt",
        ]
        try:
            for p in paths:
                self.storage.save(p, ContentFile(b"list-test"))

            dirs, files = self.storage.listdir(self.TEST_PREFIX)
            self.assertEqual(dirs, [], "测试目录下不应有子目录")
            for p in paths:
                filename = p.rsplit("/", 1)[-1]
                self.assertIn(filename, files, f"文件 {filename} 应在列表中")
        finally:
            for p in paths:
                if self.storage.exists(p):
                    self.storage.delete(p)

    # ---------- 文件存在性 ----------

    def test_file_exists(self):
        """测试 exists 方法正确判断文件存在/不存在"""
        from django.core.files.base import ContentFile

        path = f"{self.TEST_PREFIX}/exists_test.txt"
        self.assertFalse(self.storage.exists(path), "未上传前不应存在")
        try:
            self.storage.save(path, ContentFile(b"exists-test"))
            self.assertTrue(self.storage.exists(path), "上传后应存在")
        finally:
            if self.storage.exists(path):
                self.storage.delete(path)
            self.assertFalse(self.storage.exists(path), "删除后不应存在")

    # ---------- URL 生成 ----------

    def test_file_url_generation(self):
        """测试文件访问 URL 正确生成，桶名仅在域名中出现一次"""
        from django.core.files.base import ContentFile

        path = f"{self.TEST_PREFIX}/url_test.txt"
        try:
            self.storage.save(path, ContentFile(b"url-test"))
            url = self.storage.url(path)
            self.assertIn("yunwei-1328164982", url)
            self.assertIn("myqcloud.com", url)
            # 桶名仅在域名中出现一次，不在路径中重复
            path_part = url.split("myqcloud.com/", 1)[1] if "myqcloud.com/" in url else ""
            self.assertNotIn("yunwei-1328164982", path_part,
                             "桶名不应在 URL 路径中重复")
        finally:
            if self.storage.exists(path):
                self.storage.delete(path)

    # ---------- 删除 ----------

    def test_delete_file(self):
        """测试从 COS 删除单个文件"""
        from django.core.files.base import ContentFile

        path = f"{self.TEST_PREFIX}/delete_test.txt"
        self.storage.save(path, ContentFile(b"to-be-deleted"))
        self.assertTrue(self.storage.exists(path))

        self.storage.delete(path)
        self.assertFalse(self.storage.exists(path), "删除后文件不应存在")

    def test_delete_batch_files(self):
        """测试批量删除多个文件"""
        from django.core.files.base import ContentFile

        paths = [
            f"{self.TEST_PREFIX}/batch_del_a.txt",
            f"{self.TEST_PREFIX}/batch_del_b.txt",
        ]
        for p in paths:
            self.storage.save(p, ContentFile(b"batch-delete"))

        # 逐个删除
        for p in paths:
            self.storage.delete(p)
            self.assertFalse(self.storage.exists(p), f"{p} 应已删除")

    # ---------- 完整生命周期 ----------

    def test_full_lifecycle(self):
        """测试完整生命周期：上传 → 读取 → 列目录 → URL → 删除"""
        from django.core.files.base import ContentFile
        from datetime import datetime

        folder = f"{self.TEST_PREFIX}/lifecycle"
        path = f"{folder}/full_test.txt"
        content = f"lifecycle-{datetime.now().isoformat()}".encode()
        try:
            # 1. 上传
            saved = self.storage.save(path, ContentFile(content))
            self.assertTrue(self.storage.exists(saved))

            # 2. 读取内容
            with self.storage.open(path, "rb") as f:
                self.assertEqual(f.read(), content)

            # 3. 获取大小
            self.assertEqual(self.storage.size(path), len(content))

            # 4. 列目录看得到文件
            _dirs, files = self.storage.listdir(folder)
            self.assertIn("full_test.txt", files)

            # 5. URL 正确生成
            url = self.storage.url(path)
            self.assertIn("myqcloud.com", url)

            # 6. 删除
            self.storage.delete(path)
            self.assertFalse(self.storage.exists(path))

            # 7. 删除后列目录为空
            _dirs2, files2 = self.storage.listdir(folder)
            self.assertNotIn("full_test.txt", files2)
        finally:
            if self.storage.exists(path):
                self.storage.delete(path)
