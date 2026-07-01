"""
主体公司 — API 接口测试

覆盖 CompanyEntityViewSet 的全部端点：
  - 认证：未登录 401
  - CRUD：新增 / 列表（分页/过滤/搜索）/ 详情 / 修改 / 删除
  - 自定义 action：parent_options / tree / batch_set_status / multiple_delete
  - 边界：排序、parent_name 字段、名称唯一等
"""
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from dvadmin.system.models import Users, Role


# ========== 工具函数 ==========

def _make_token(user: Users) -> str:
    """为指定用户生成 JWT access token（项目使用 JWT 前缀，非 Bearer）"""
    refresh = RefreshToken.for_user(user)
    return f"JWT {refresh.access_token}"


class CompanyEntityAPITest(APITestCase):
    """
    主体公司 — API 接口测试

    覆盖端点:
      GET    /api/company/entity/              → 列表（分页/过滤/搜索）
      POST   /api/company/entity/              → 新增
      GET    /api/company/entity/{id}/         → 详情
      PUT    /api/company/entity/{id}/         → 修改
      DELETE /api/company/entity/{id}/         → 删除
      DELETE /api/company/entity/multiple_delete/ → 批量删除
      GET    /api/company/entity/parent_options/  → 上级选项
      GET    /api/company/entity/tree/            → 树形结构
      POST   /api/company/entity/batch_set_status/ → 批量设置状态
    """

    @classmethod
    def setUpTestData(cls):
        """创建测试用基础数据（类级别，所有测试方法共享）"""
        # 1. 创建"管理员"角色（create_superuser 依赖该角色）
        cls.admin_role, _ = Role.objects.get_or_create(
            name="管理员", defaults={"key": "admin", "sort": 1, "status": True}
        )
        # 2. 创建超级管理员（自动关联管理员角色，绕过 CustomPermission）
        cls.user = Users.objects.create_superuser(
            username="api_test_admin",
            password="TestPass123",
            name="API Test Admin",
            is_active=True,
        )
        cls.token = _make_token(cls.user)

    def setUp(self):
        """每个测试方法执行前：注入 JWT 认证头及必要请求头"""
        self.client.credentials(
            HTTP_AUTHORIZATION=self.token,
            HTTP_USER_AGENT="Mozilla/5.0 (Test) pytest/0.0",
        )

    # ========== 认证 ==========

    def test_unauthenticated_request_is_rejected(self):
        """未登录请求应被拒绝（返回 code 4000，非 HTTP 401）"""
        client = self.client_class()
        response = client.get(
            "/api/company/entity/",
            HTTP_USER_AGENT="Mozilla/5.0 (Test)",
        )
        self.assertEqual(response.json()["code"], 4000)
        self.assertIn("认证", response.json()["msg"])

    # ========== 新增 ==========

    def test_create_company(self):
        """测试新增主体公司"""
        payload = {
            "name": "测试科技有限公司",
            "short_name": "测试科技",
            "credit_code": "91350100MA32ABCDEF",
            "legal_person": "张三",
            "status": "active",
        }
        response = self.client.post(
            "/api/company/entity/", data=payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["code"], 2000)
        self.assertEqual(data["data"]["name"], payload["name"])
        self.assertEqual(data["data"]["short_name"], payload["short_name"])
        self.assertEqual(data["data"]["credit_code"], payload["credit_code"])
        self.assertEqual(data["data"]["status"], "active")
        self.assertIsNotNone(data["data"]["id"])

    def test_create_company_requires_name(self):
        """公司全称为必填字段"""
        response = self.client.post(
            "/api/company/entity/",
            data={"status": "active"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(response.json()["code"], 2000)

    def test_create_company_with_parent(self):
        """测试创建带上级主体的子公司"""
        parent = self.client.post(
            "/api/company/entity/",
            data={"name": "集团总部", "status": "active"},
            format="json",
        )
        parent_id = parent.json()["data"]["id"]

        child = self.client.post(
            "/api/company/entity/",
            data={"name": "子公司A", "status": "active", "parent": parent_id},
            format="json",
        )
        self.assertEqual(child.status_code, status.HTTP_200_OK)
        self.assertEqual(child.json()["data"]["parent"], parent_id)
        self.assertEqual(child.json()["data"]["parent_name"], "集团总部")

    def test_create_company_name_unique(self):
        """公司全称不可重复"""
        self.client.post(
            "/api/company/entity/",
            data={"name": "唯一公司", "status": "active"},
            format="json",
        )
        response = self.client.post(
            "/api/company/entity/",
            data={"name": "唯一公司", "status": "active"},
            format="json",
        )
        self.assertNotEqual(response.json()["code"], 2000)

    def test_create_company_default_status(self):
        """未传 status 时应默认为 active"""
        response = self.client.post(
            "/api/company/entity/",
            data={"name": "默认状态公司"},
            format="json",
        )
        self.assertEqual(response.json()["data"]["status"], "active")

    def test_create_company_full_fields(self):
        """测试新增公司时填写全部字段"""
        payload = {
            "name": "完整字段科技有限公司",
            "short_name": "完整科技",
            "credit_code": "91440300MA5EFGH123",
            "legal_person": "李四",
            "registered_capital": "500.00",
            "established_date": "2020-06-15",
            "business_scope": "软件开发、技术服务、技术咨询",
            "address": "深圳市南山区科技园路1号",
            "contact_person": "王五",
            "contact_phone": "13800138000",
            "contact_email": "contact@example.com",
            "status": "active",
            "remark": "测试备注",
        }
        response = self.client.post(
            "/api/company/entity/", data=payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()["data"]
        self.assertEqual(data["name"], payload["name"])
        self.assertEqual(data["registered_capital"], payload["registered_capital"])
        self.assertEqual(data["established_date"], payload["established_date"])
        self.assertEqual(data["contact_email"], payload["contact_email"])

    # ========== 列表查询 ==========

    def test_list_company(self):
        """测试分页列表查询"""
        for i in range(15):
            self.client.post(
                "/api/company/entity/",
                data={"name": f"列表测试公司{i}", "status": "active"},
                format="json",
            )

        response = self.client.get("/api/company/entity/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["code"], 2000)
        self.assertIn("data", data)
        self.assertIn("total", data)
        self.assertGreaterEqual(data["total"], 15)

    def test_list_with_name_filter(self):
        """测试按公司全称过滤"""
        self.client.post(
            "/api/company/entity/",
            data={"name": "过滤目标公司", "status": "active"},
            format="json",
        )
        self.client.post(
            "/api/company/entity/",
            data={"name": "其他公司X", "status": "active"},
            format="json",
        )

        response = self.client.get(
            "/api/company/entity/", {"name": "过滤目标公司"}
        )
        data = response.json()
        self.assertEqual(data["total"], 1)
        self.assertEqual(data["data"][0]["name"], "过滤目标公司")

    def test_list_with_status_filter(self):
        """测试按状态过滤"""
        self.client.post(
            "/api/company/entity/",
            data={"name": "启用公司", "status": "active"},
            format="json",
        )
        self.client.post(
            "/api/company/entity/",
            data={"name": "停用公司", "status": "inactive"},
            format="json",
        )

        resp_active = self.client.get(
            "/api/company/entity/", {"status": "active"}
        )
        for item in resp_active.json()["data"]:
            self.assertEqual(item["status"], "active")

        resp_inactive = self.client.get(
            "/api/company/entity/", {"status": "inactive"}
        )
        for item in resp_inactive.json()["data"]:
            self.assertEqual(item["status"], "inactive")

    def test_list_with_search(self):
        """测试搜索功能"""
        self.client.post(
            "/api/company/entity/",
            data={"name": "搜索科技有限公司", "legal_person": "赵六", "status": "active"},
            format="json",
        )
        self.client.post(
            "/api/company/entity/",
            data={"name": "无关公司", "legal_person": "孙七", "status": "active"},
            format="json",
        )

        response = self.client.get(
            "/api/company/entity/", {"search": "赵六"}
        )
        data = response.json()
        self.assertEqual(data["total"], 1)
        self.assertEqual(data["data"][0]["legal_person"], "赵六")

    # ========== 详情 ==========

    def test_retrieve_company(self):
        """测试获取公司详情"""
        create_resp = self.client.post(
            "/api/company/entity/",
            data={"name": "详情测试公司", "status": "active", "short_name": "详情"},
            format="json",
        )
        pk = create_resp.json()["data"]["id"]

        response = self.client.get(f"/api/company/entity/{pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["code"], 2000)
        self.assertEqual(data["data"]["name"], "详情测试公司")
        self.assertEqual(data["data"]["short_name"], "详情")
        self.assertIn("parent_name", data["data"])

    def test_retrieve_nonexistent_returns_error(self):
        """获取不存在的公司应返回错误码 400"""
        response = self.client.get("/api/company/entity/99999/")
        self.assertNotEqual(response.json()["code"], 2000)

    # ========== 修改 ==========

    def test_update_company(self):
        """测试修改公司信息"""
        create_resp = self.client.post(
            "/api/company/entity/",
            data={"name": "原公司名称", "status": "active"},
            format="json",
        )
        pk = create_resp.json()["data"]["id"]

        response = self.client.put(
            f"/api/company/entity/{pk}/",
            data={"name": "新公司名称", "short_name": "新简称", "status": "inactive"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["code"], 2000)
        self.assertEqual(data["data"]["name"], "新公司名称")
        self.assertEqual(data["data"]["short_name"], "新简称")
        self.assertEqual(data["data"]["status"], "inactive")

    def test_update_company_name_to_existing_fails(self):
        """修改公司全称为已存在的名称应失败"""
        self.client.post(
            "/api/company/entity/",
            data={"name": "公司甲", "status": "active"},
            format="json",
        )
        create_b = self.client.post(
            "/api/company/entity/",
            data={"name": "公司乙", "status": "active"},
            format="json",
        )
        pk_b = create_b.json()["data"]["id"]

        response = self.client.put(
            f"/api/company/entity/{pk_b}/",
            data={"name": "公司甲", "status": "active"},
            format="json",
        )
        self.assertNotEqual(response.json()["code"], 2000)

    # ========== 删除 ==========

    def test_delete_company(self):
        """测试删除公司"""
        create_resp = self.client.post(
            "/api/company/entity/",
            data={"name": "待删除公司", "status": "active"},
            format="json",
        )
        pk = create_resp.json()["data"]["id"]

        response = self.client.delete(f"/api/company/entity/{pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["code"], 2000)

        # 确认已删除：列表中不再包含该公司
        list_resp = self.client.get("/api/company/entity/")
        names = [item["name"] for item in list_resp.json()["data"]]
        self.assertNotIn("待删除公司", names)

    def test_delete_with_parent(self):
        """有子公司的父级公司可以正常删除（SET_NULL 策略）"""
        parent_resp = self.client.post(
            "/api/company/entity/",
            data={"name": "待删父公司", "status": "active"},
            format="json",
        )
        parent_id = parent_resp.json()["data"]["id"]

        self.client.post(
            "/api/company/entity/",
            data={"name": "子公司在父删除后", "status": "active", "parent": parent_id},
            format="json",
        )

        # 删除父公司（on_delete=SET_NULL, db_constraint=False）
        response = self.client.delete(f"/api/company/entity/{parent_id}/")
        self.assertEqual(response.json()["code"], 2000)

    # ========== 批量删除 ==========

    def test_multiple_delete(self):
        """测试批量删除"""
        ids = []
        for i in range(3):
            resp = self.client.post(
                "/api/company/entity/",
                data={"name": f"批量删除测试{i}", "status": "active"},
                format="json",
            )
            ids.append(resp.json()["data"]["id"])

        response = self.client.delete(
            "/api/company/entity/multiple_delete/",
            data={"keys": ids},
            format="json",
        )
        self.assertEqual(response.json()["code"], 2000)

        # 确认全部已删除：列表中不再包含这些公司
        list_resp = self.client.get("/api/company/entity/")
        names = {item["name"] for item in list_resp.json()["data"]}
        for i in range(3):
            self.assertNotIn(f"批量删除测试{i}", names)

    # ========== parent_options ==========

    def test_parent_options_returns_active_companies(self):
        """parent_options 只返回启用状态的公司"""
        self.client.post(
            "/api/company/entity/",
            data={"name": "启用可选公司", "status": "active"},
            format="json",
        )
        self.client.post(
            "/api/company/entity/",
            data={"name": "停用不可选公司", "status": "inactive"},
            format="json",
        )

        response = self.client.get(
            "/api/company/entity/parent_options/"
        )
        data = response.json()
        self.assertEqual(data["code"], 2000)
        names = [item["name"] for item in data["data"]]
        self.assertIn("启用可选公司", names)
        self.assertNotIn("停用不可选公司", names)

    def test_parent_options_excludes_given_id(self):
        """parent_options 可排除指定ID（避免自身作为上级）"""
        resp = self.client.post(
            "/api/company/entity/",
            data={"name": "自身不应出现", "status": "active"},
            format="json",
        )
        pk = resp.json()["data"]["id"]

        response = self.client.get(
            "/api/company/entity/parent_options/", {"exclude_id": pk}
        )
        data = response.json()
        ids = [item["id"] for item in data["data"]]
        self.assertNotIn(pk, ids)

    # ========== tree ==========

    def test_tree_returns_hierarchical_structure(self):
        """tree 端点返回正确的树形结构"""
        root_resp = self.client.post(
            "/api/company/entity/",
            data={"name": "树根公司", "status": "active"},
            format="json",
        )
        root_id = root_resp.json()["data"]["id"]

        self.client.post(
            "/api/company/entity/",
            data={"name": "树子A", "status": "active", "parent": root_id},
            format="json",
        )
        self.client.post(
            "/api/company/entity/",
            data={"name": "树子B", "status": "active", "parent": root_id},
            format="json",
        )

        response = self.client.get("/api/company/entity/tree/")
        data = response.json()
        self.assertEqual(data["code"], 2000)

        roots = [n for n in data["data"] if n["name"] == "树根公司"]
        self.assertEqual(len(roots), 1)
        children = roots[0]["children"]
        self.assertEqual(len(children), 2)
        child_names = {c["name"] for c in children}
        self.assertEqual(child_names, {"树子A", "树子B"})

    def test_tree_with_status_filter(self):
        """tree 支持按状态过滤"""
        self.client.post(
            "/api/company/entity/",
            data={"name": "树根启用", "status": "active"},
            format="json",
        )

        response = self.client.get(
            "/api/company/entity/tree/", {"status": "inactive"}
        )
        data = response.json()
        for node in data["data"]:
            self.assertEqual(node["status"], "inactive")

    # ========== batch_set_status ==========

    def test_batch_set_status_active_to_inactive(self):
        """批量将启用改为停用"""
        ids = []
        for i in range(2):
            resp = self.client.post(
                "/api/company/entity/",
                data={"name": f"批量状态公司{i}", "status": "active"},
                format="json",
            )
            ids.append(resp.json()["data"]["id"])

        response = self.client.post(
            "/api/company/entity/batch_set_status/",
            data={"ids": ids, "status": "inactive"},
            format="json",
        )
        self.assertEqual(response.json()["code"], 2000)

        for pk in ids:
            detail = self.client.get(f"/api/company/entity/{pk}/")
            self.assertEqual(detail.json()["data"]["status"], "inactive")

    def test_batch_set_status_invalid_status(self):
        """传递无效状态值应返回错误"""
        resp = self.client.post(
            "/api/company/entity/",
            data={"name": "无效状态公司", "status": "active"},
            format="json",
        )
        pk = resp.json()["data"]["id"]

        response = self.client.post(
            "/api/company/entity/batch_set_status/",
            data={"ids": [pk], "status": "invalid_status"},
            format="json",
        )
        self.assertNotEqual(response.json()["code"], 2000)

    def test_batch_set_status_empty_ids(self):
        """未提供 ids 应返回错误"""
        response = self.client.post(
            "/api/company/entity/batch_set_status/",
            data={"ids": [], "status": "active"},
            format="json",
        )
        self.assertNotEqual(response.json()["code"], 2000)

    # ========== 排序 ==========

    def test_list_ordering_by_name(self):
        """测试按名称排序"""
        self.client.post(
            "/api/company/entity/",
            data={"name": "B公司", "status": "active"},
            format="json",
        )
        self.client.post(
            "/api/company/entity/",
            data={"name": "A公司", "status": "active"},
            format="json",
        )
        self.client.post(
            "/api/company/entity/",
            data={"name": "C公司", "status": "active"},
            format="json",
        )

        response = self.client.get(
            "/api/company/entity/", {"ordering": "name"}
        )
        data = response.json()
        names = [item["name"] for item in data["data"]]
        self.assertEqual(names[0], "A公司")

    # ========== parent_name 字段 ==========

    def test_list_includes_parent_name(self):
        """列表响应应包含 parent_name 字段"""
        parent_resp = self.client.post(
            "/api/company/entity/",
            data={"name": "父公司X", "status": "active"},
            format="json",
        )
        parent_id = parent_resp.json()["data"]["id"]

        self.client.post(
            "/api/company/entity/",
            data={"name": "子公司Y", "status": "active", "parent": parent_id},
            format="json",
        )

        response = self.client.get("/api/company/entity/")
        data = response.json()
        for item in data["data"]:
            self.assertIn("parent_name", item)
            if item["name"] == "子公司Y":
                self.assertEqual(item["parent_name"], "父公司X")
