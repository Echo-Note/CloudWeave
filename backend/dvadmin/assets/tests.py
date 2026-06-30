"""
资产管理 — 模型测试

覆盖 5 个核心实体和 7 张关联中间表。
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from dvadmin.company.models import CompanyEntity
from dvadmin.cloud.models import CloudPlatform, Registrar
from dvadmin.assets.models import (
    Project, Server, IPAddress, Domain, Port,
    ProjectServer, DomainIP, ProjectDomain, ProjectPort,
    ServerVip, ServerProxyMapping, ServiceDependency,
)

User = get_user_model()


class ProjectModelTest(TestCase):
    """项目模型测试"""

    def setUp(self):
        self.user = User.objects.create(username="admin", is_active=True)

    def test_create_project(self):
        """测试创建项目"""
        project = Project.objects.create(
            name="电商平台", slug="ecommerce", owner=self.user, team="平台组"
        )
        self.assertEqual(project.name, "电商平台")
        self.assertEqual(project.status, "running")
        self.assertIsNotNone(project.create_datetime)

    def test_name_unique_constraint(self):
        """测试项目名称唯一约束"""
        Project.objects.create(name="唯一项目", slug="unique", owner=self.user)
        with self.assertRaises(Exception):
            Project.objects.create(name="唯一项目", slug="unique2", owner=self.user)

    def test_default_status(self):
        """测试默认状态为 running"""
        project = Project.objects.create(name="新项目", slug="new", owner=self.user)
        self.assertEqual(project.status, "running")

    def test_soft_delete(self):
        """测试软删除"""
        project = Project.objects.create(name="待删除项目", slug="del", owner=self.user)
        self.assertFalse(project.is_deleted)
        project.is_deleted = True
        project.save()
        # CoreModelManager 自动过滤 is_deleted=True
        self.assertEqual(Project.objects.filter(name="待删除项目").count(), 0)
        self.assertEqual(Project.all_objects.filter(name="待删除项目").count(), 1)

    def test_str_method(self):
        """测试 __str__ 方法"""
        project = Project.objects.create(name="测试项目", slug="test", owner=self.user)
        self.assertEqual(str(project), "测试项目")


class ServerModelTest(TestCase):
    """服务器模型测试"""

    def test_create_server(self):
        """测试创建服务器"""
        server = Server.objects.create(
            hostname="web-server-01", os="Ubuntu 22.04", cpu_cores=4, memory_gb=16.0
        )
        self.assertEqual(server.hostname, "web-server-01")
        self.assertEqual(server.status, "running")
        self.assertEqual(server.ssh_port, 22)

    def test_default_ssh_port(self):
        """测试默认 SSH 端口"""
        server = Server.objects.create(hostname="test-server")
        self.assertEqual(server.ssh_port, 22)

    def test_soft_delete(self):
        """测试软删除"""
        server = Server.objects.create(hostname="deleted-server")
        server.is_deleted = True
        server.save()
        self.assertEqual(Server.objects.filter(hostname="deleted-server").count(), 0)


class IPAddressModelTest(TestCase):
    """IP 地址模型测试"""

    def test_create_ip(self):
        """测试创建 IP"""
        ip = IPAddress.objects.create(address="192.168.1.1", ip_type="private")
        self.assertEqual(ip.address, "192.168.1.1")
        self.assertEqual(ip.ip_type, "private")

    def test_default_ip_type(self):
        """测试默认 IP 类型"""
        ip = IPAddress.objects.create(address="10.0.0.1")
        self.assertEqual(ip.ip_type, "private")

    def test_vip_without_server(self):
        """测试 VIP 类型可以不关联服务器"""
        ip = IPAddress.objects.create(address="10.0.0.100", ip_type="vip")
        self.assertIsNone(ip.server)
        self.assertEqual(ip.ip_type, "vip")

    def test_str_method(self):
        """测试 __str__ 方法"""
        ip = IPAddress.objects.create(address="8.8.8.8", ip_type="public")
        self.assertIn("8.8.8.8", str(ip))
        self.assertIn("公网IP", str(ip))


class DomainModelTest(TestCase):
    """域名模型测试"""

    def test_create_domain(self):
        """测试创建域名"""
        domain = Domain.objects.create(name="example.com")
        self.assertEqual(domain.name, "example.com")
        self.assertEqual(domain.icp_status, "unfiled")

    def test_domain_name_unique(self):
        """测试域名唯一约束"""
        Domain.objects.create(name="unique.com")
        with self.assertRaises(Exception):
            Domain.objects.create(name="unique.com")

    def test_soft_delete(self):
        """测试软删除"""
        domain = Domain.objects.create(name="deleted.com")
        domain.is_deleted = True
        domain.save()
        self.assertEqual(Domain.objects.filter(name="deleted.com").count(), 0)


class PortModelTest(TestCase):
    """端口模型测试"""

    def setUp(self):
        self.server = Server.objects.create(hostname="test-server")

    def test_create_port(self):
        """测试创建端口"""
        port = Port.objects.create(
            number=443, protocol="TCP", service_name="nginx", server=self.server
        )
        self.assertEqual(port.number, 443)
        self.assertEqual(port.protocol, "TCP")

    def test_unique_constraint(self):
        """测试 (number, protocol, server, ip) 唯一约束"""
        ip = IPAddress.objects.create(address="10.0.0.1")
        Port.objects.create(number=8080, protocol="TCP", server=self.server, ip=ip)
        with self.assertRaises(Exception):
            Port.objects.create(number=8080, protocol="TCP", server=self.server, ip=ip)

    def test_str_method(self):
        """测试 __str__ 方法"""
        port = Port.objects.create(
            number=3306, protocol="TCP", service_name="mysql", server=self.server
        )
        self.assertIn("3306", str(port))
        self.assertIn("mysql", str(port))


# ============================================================
# 关联中间表测试
# ============================================================

class ProjectServerModelTest(TestCase):
    """项目-服务器关联测试"""

    def setUp(self):
        self.user = User.objects.create(username="admin", is_active=True)
        self.project = Project.objects.create(name="测试项目", slug="test", owner=self.user)
        self.server = Server.objects.create(hostname="test-server")

    def test_create_association(self):
        """测试创建项目-服务器关联"""
        ps = ProjectServer.objects.create(
            project=self.project, server=self.server, role="app_server", environment="production"
        )
        self.assertEqual(ps.role, "app_server")
        self.assertEqual(ps.environment, "production")

    def test_default_environment(self):
        """测试默认环境为生产"""
        ps = ProjectServer.objects.create(
            project=self.project, server=self.server, role="database"
        )
        self.assertEqual(ps.environment, "production")

    def test_unique_constraint(self):
        """测试 (project, server, role) 唯一约束"""
        ProjectServer.objects.create(project=self.project, server=self.server, role="app_server")
        with self.assertRaises(Exception):
            ProjectServer.objects.create(project=self.project, server=self.server, role="app_server")


class DomainIPModelTest(TestCase):
    """域名-IP 关联测试"""

    def setUp(self):
        self.domain = Domain.objects.create(name="example.com")
        self.ip = IPAddress.objects.create(address="1.2.3.4")

    def test_create_domain_ip(self):
        """测试创建域名-IP 关联"""
        di = DomainIP.objects.create(domain=self.domain, ip=self.ip, record_type="A")
        self.assertEqual(di.record_type, "A")
        self.assertEqual(di.domain, self.domain)

    def test_unique_constraint(self):
        """测试 (domain, ip, record_type, host_record) 唯一约束"""
        DomainIP.objects.create(domain=self.domain, ip=self.ip, record_type="A", host_record="@")
        with self.assertRaises(Exception):
            DomainIP.objects.create(domain=self.domain, ip=self.ip, record_type="A", host_record="@")


class ServerVipModelTest(TestCase):
    """服务器-VIP 关联测试"""

    def setUp(self):
        self.server_a = Server.objects.create(hostname="server-a")
        self.server_b = Server.objects.create(hostname="server-b")
        self.vip = IPAddress.objects.create(address="10.0.0.100", ip_type="vip")

    def test_create_vip_association(self):
        """测试创建 VIP 关联"""
        sv = ServerVip.objects.create(ip=self.vip, server=self.server_a, role="master")
        self.assertEqual(sv.role, "master")

    def test_unique_constraint(self):
        """测试 (ip, server) 唯一约束"""
        ServerVip.objects.create(ip=self.vip, server=self.server_a, role="master")
        with self.assertRaises(Exception):
            ServerVip.objects.create(ip=self.vip, server=self.server_a, role="backup")


class ServerProxyMappingModelTest(TestCase):
    """代理映射模型测试"""

    def setUp(self):
        self.proxy = Server.objects.create(hostname="proxy-server")
        self.backend = Server.objects.create(hostname="backend-server")

    def test_create_proxy_mapping(self):
        """测试创建代理映射"""
        mapping = ServerProxyMapping.objects.create(
            proxy_server=self.proxy, backend_server=self.backend,
            proxy_port=443, server_name="api.example.com", proxy_path="/",
            protocol="https",
        )
        self.assertEqual(mapping.protocol, "https")
        self.assertEqual(mapping.server_name, "api.example.com")

    def test_default_proxy_path(self):
        """测试默认代理路径"""
        mapping = ServerProxyMapping.objects.create(
            proxy_server=self.proxy, backend_server=self.backend,
            protocol="http",
        )
        self.assertEqual(mapping.proxy_path, "/")


class ServiceDependencyModelTest(TestCase):
    """服务依赖模型测试"""

    def setUp(self):
        self.user = User.objects.create(username="admin", is_active=True)
        self.project_a = Project.objects.create(name="前端项目", slug="frontend", owner=self.user)
        self.project_b = Project.objects.create(name="后端API", slug="backend", owner=self.user)

    def test_create_dependency(self):
        """测试创建服务依赖"""
        dep = ServiceDependency.objects.create(
            from_project=self.project_a, to_project=self.project_b,
            internal_domain="api.backend.internal", protocol="http",
            target_port=8080, environment="production",
        )
        self.assertEqual(dep.target_port, 8080)
        self.assertEqual(dep.internal_domain, "api.backend.internal")

    def test_unique_constraint(self):
        """测试唯一约束"""
        ServiceDependency.objects.create(
            from_project=self.project_a, to_project=self.project_b,
            internal_domain="api.backend.internal", protocol="http",
            target_port=8080, environment="production",
        )
        with self.assertRaises(Exception):
            ServiceDependency.objects.create(
                from_project=self.project_a, to_project=self.project_b,
                internal_domain="api.backend.internal", protocol="http",
                target_port=8080, environment="production",
            )
