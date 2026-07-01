"""
资产管理 — 数据模型

覆盖五大核心资源实体：Project（项目）、Server（服务器）、IPAddress（IP）、
Domain（域名）、Port（端口），以及它们之间的多对多关联中间表和扩展关联表。
"""
from django.conf import settings
from django.db import models

from dvadmin.utils.models import CoreModel

table_prefix = "assets_"  # 数据库表前缀（App 级别）


# ============================================================
# 核心实体表
# ============================================================

class Project(CoreModel):
    """
    项目表

    运维项目的基本信息，作为资源关联拓扑的顶层入口。
    """
    is_soft_delete = True  # 启用 CoreModelManager 自动过滤已删除记录

    name = models.CharField(
        max_length=200, unique=True,
        verbose_name="项目名称", help_text="项目名称，唯一",
        db_comment="项目名称"
    )
    slug = models.SlugField(
        max_length=200,
        verbose_name="URL标识符", help_text="URL友好的标识符",
        db_comment="URL标识符"
    )
    description = models.TextField(
        null=True, blank=True,
        verbose_name="项目描述", help_text="项目描述",
        db_comment="项目描述"
    )
    status = models.CharField(
        max_length=20, default='running',
        choices=(
            ('running', '运行中'),
            ('offline', '已下线'),
            ('maintenance', '维护中'),
        ),
        verbose_name="状态", help_text="项目状态：运行中/已下线/维护中",
        db_comment="状态"
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='owned_projects', db_constraint=False,
        verbose_name="项目负责人", help_text="项目负责人",
        db_comment="项目负责人"
    )
    company = models.ForeignKey(
        'company.CompanyEntity', on_delete=models.SET_NULL, null=True, blank=True,
        db_constraint=False,
        verbose_name="归属主体公司", help_text="项目归属主体公司",
        db_comment="归属主体公司"
    )
    team = models.CharField(
        max_length=100, null=True, blank=True,
        verbose_name="所属团队/部门", help_text="所属团队或部门",
        db_comment="所属团队/部门"
    )
    is_deleted = models.BooleanField(
        default=False, db_index=True,
        verbose_name="软删除标记", help_text="软删除标记，默认False",
        db_comment="软删除标记"
    )

    class Meta:
        db_table = f"{table_prefix}project"
        verbose_name = "项目"
        verbose_name_plural = verbose_name
        ordering = ['-create_datetime']

    def __str__(self):
        return self.name


class Server(CoreModel):
    """
    服务器表

    服务器基本信息、规格、云平台归属、到期时间等。
    支持不同角色（应用服务器/反向代理/负载均衡/数据库等）。
    """
    is_soft_delete = True

    hostname = models.CharField(
        max_length=200,
        verbose_name="主机名", help_text="服务器主机名",
        db_comment="主机名"
    )
    os = models.CharField(
        max_length=100, null=True, blank=True,
        verbose_name="操作系统", help_text="操作系统，如CentOS 7.9 / Ubuntu 22.04",
        db_comment="操作系统"
    )
    cpu_cores = models.IntegerField(
        null=True, blank=True,
        verbose_name="CPU核数", help_text="CPU核数",
        db_comment="CPU核数"
    )
    memory_gb = models.FloatField(
        null=True, blank=True,
        verbose_name="内存(GB)", help_text="内存大小，单位GB",
        db_comment="内存(GB)"
    )
    disk_gb = models.FloatField(
        null=True, blank=True,
        verbose_name="磁盘(GB)", help_text="磁盘大小，单位GB",
        db_comment="磁盘(GB)"
    )
    cloud_platform = models.ForeignKey(
        'cloud.CloudPlatform', on_delete=models.SET_NULL, null=True, blank=True,
        db_constraint=False,
        verbose_name="所属云平台", help_text="所属云平台账号",
        db_comment="所属云平台"
    )
    company = models.ForeignKey(
        'company.CompanyEntity', on_delete=models.SET_NULL, null=True, blank=True,
        db_constraint=False,
        verbose_name="归属主体公司", help_text="归属主体公司（私有化部署场景）",
        db_comment="归属主体公司"
    )
    instance_id = models.CharField(
        max_length=200, null=True, blank=True,
        verbose_name="云实例ID", help_text="云平台实例ID，如ins-xxxx",
        db_comment="云实例ID"
    )
    ssh_port = models.IntegerField(
        default=22, null=True, blank=True,
        verbose_name="SSH端口", help_text="SSH端口，默认22",
        db_comment="SSH端口"
    )
    status = models.CharField(
        max_length=20, default='running',
        choices=(
            ('running', '运行中'),
            ('stopped', '已关机'),
            ('terminated', '已销毁'),
            ('maintenance', '维护中'),
        ),
        verbose_name="状态", help_text="服务器状态",
        db_comment="状态"
    )
    expire_date = models.DateField(
        null=True, blank=True,
        verbose_name="到期时间", help_text="包年包月实例到期时间",
        db_comment="到期时间"
    )
    remark = models.TextField(
        null=True, blank=True,
        verbose_name="备注", help_text="备注",
        db_comment="备注"
    )
    is_deleted = models.BooleanField(
        default=False, db_index=True,
        verbose_name="软删除标记", help_text="软删除标记",
        db_comment="软删除标记"
    )

    class Meta:
        db_table = f"{table_prefix}server"
        verbose_name = "服务器"
        verbose_name_plural = verbose_name
        ordering = ['-create_datetime']

    def __str__(self):
        return self.hostname


class IPAddress(CoreModel):
    """
    IP 地址表

    记录所有 IP 地址（公网/内网/弹性/VIP），与服务器关联。
    VIP 类型通过 server_vip 中间表关联多台服务器。
    """
    address = models.GenericIPAddressField(
        verbose_name="IP地址", help_text="IP地址",
        db_comment="IP地址"
    )
    ip_type = models.CharField(
        max_length=20, default='private',
        choices=(
            ('public', '公网IP'),
            ('private', '内网IP'),
            ('elastic', '弹性公网IP'),
            ('vip', '虚拟IP'),
        ),
        verbose_name="IP类型",
        help_text="public(公网) / private(内网) / elastic(弹性) / vip(虚拟IP)",
        db_comment="IP类型"
    )
    server = models.ForeignKey(
        Server, on_delete=models.SET_NULL, null=True, blank=True,
        db_constraint=False,
        verbose_name="归属服务器", help_text="归属服务器（vip类型可为NULL）",
        db_comment="归属服务器"
    )
    isp = models.CharField(
        max_length=50, null=True, blank=True,
        verbose_name="运营商", help_text="运营商：电信/联通/移动/BGP",
        db_comment="运营商"
    )
    remark = models.TextField(
        null=True, blank=True,
        verbose_name="备注", help_text="备注",
        db_comment="备注"
    )

    class Meta:
        db_table = f"{table_prefix}ip_address"
        verbose_name = "IP地址"
        verbose_name_plural = verbose_name
        ordering = ['-create_datetime']

    def __str__(self):
        return f"{self.address} ({self.get_ip_type_display()})"


class Domain(CoreModel):
    """
    域名表

    域名基本信息、注册商、备案状态、到期时间等。
    """
    is_soft_delete = True

    name = models.CharField(
        max_length=255, unique=True,
        verbose_name="域名", help_text="域名，如example.com，唯一",
        db_comment="域名"
    )
    registrar = models.ForeignKey(
        'cloud.Registrar', on_delete=models.SET_NULL, null=True, blank=True,
        db_constraint=False,
        verbose_name="注册商", help_text="域名注册商",
        db_comment="注册商"
    )
    company = models.ForeignKey(
        'company.CompanyEntity', on_delete=models.SET_NULL, null=True, blank=True,
        db_constraint=False,
        verbose_name="归属主体公司", help_text="域名归属主体公司",
        db_comment="归属主体公司"
    )
    register_date = models.DateField(
        null=True, blank=True,
        verbose_name="注册日期", help_text="域名注册日期",
        db_comment="注册日期"
    )
    expire_date = models.DateField(
        null=True, blank=True,
        verbose_name="到期日期", help_text="域名到期日期",
        db_comment="到期日期"
    )
    dns_provider = models.CharField(
        max_length=100, null=True, blank=True,
        verbose_name="DNS服务商", help_text="DNS服务商，如DNSPod/CloudFlare",
        db_comment="DNS服务商"
    )
    icp_status = models.CharField(
        max_length=20, default='unfiled',
        choices=(
            ('unfiled', '未备案'),
            ('filed', '已备案'),
            ('filing', '备案中'),
            ('cancelled', '备案注销'),
            ('exempt', '无需备案'),
        ),
        verbose_name="ICP状态", help_text="ICP备案状态",
        db_comment="ICP状态"
    )
    remark = models.TextField(
        null=True, blank=True,
        verbose_name="备注", help_text="备注",
        db_comment="备注"
    )
    is_deleted = models.BooleanField(
        default=False, db_index=True,
        verbose_name="软删除标记", help_text="软删除标记",
        db_comment="软删除标记"
    )

    class Meta:
        db_table = f"{table_prefix}domain"
        verbose_name = "域名"
        verbose_name_plural = verbose_name
        ordering = ['-create_datetime']

    def __str__(self):
        return self.name


class Port(CoreModel):
    """
    端口表

    记录服务器上的开放端口，包含协议、服务名称、绑定IP和关联项目。
    """
    number = models.IntegerField(
        verbose_name="端口号", help_text="端口号(1-65535)",
        db_comment="端口号"
    )
    protocol = models.CharField(
        max_length=10,
        choices=(('TCP', 'TCP'), ('UDP', 'UDP')),
        verbose_name="协议", help_text="TCP / UDP",
        db_comment="协议"
    )
    service_name = models.CharField(
        max_length=100, null=True, blank=True,
        verbose_name="服务名称", help_text="服务名称，如nginx/mysql/redis/ssh",
        db_comment="服务名称"
    )
    server = models.ForeignKey(
        Server, on_delete=models.CASCADE,
        db_constraint=False,
        verbose_name="所属服务器", help_text="所属服务器",
        db_comment="所属服务器"
    )
    ip = models.ForeignKey(
        IPAddress, on_delete=models.SET_NULL, null=True, blank=True,
        db_constraint=False,
        verbose_name="绑定IP", help_text="绑定的具体IP（为空表示监听所有IP）",
        db_comment="绑定IP"
    )
    project = models.ForeignKey(
        Project, on_delete=models.SET_NULL, null=True, blank=True,
        db_constraint=False,
        verbose_name="关联项目", help_text="关联项目",
        db_comment="关联项目"
    )
    remark = models.TextField(
        null=True, blank=True,
        verbose_name="备注", help_text="备注",
        db_comment="备注"
    )

    class Meta:
        db_table = f"{table_prefix}port"
        verbose_name = "端口"
        verbose_name_plural = verbose_name
        ordering = ['server', 'number']
        constraints = [
            models.UniqueConstraint(
                fields=['number', 'protocol', 'server', 'ip'],
                name='uq_port_number_protocol_server_ip'
            ),
        ]

    def __str__(self):
        return f"{self.number}/{self.protocol} ({self.service_name or '-'})"


# ============================================================
# 关联中间表
# ============================================================

class ProjectServer(CoreModel):
    """
    项目-服务器关联表

    记录项目与服务器的多对多部署关系，含服务器角色和环境标签。
    """
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE,
        db_constraint=False,
        verbose_name="项目", help_text="关联项目",
        db_comment="项目"
    )
    server = models.ForeignKey(
        Server, on_delete=models.CASCADE,
        db_constraint=False,
        verbose_name="服务器", help_text="关联服务器",
        db_comment="服务器"
    )
    role = models.CharField(
        max_length=20,
        choices=(
            ('app_server', '应用服务器'),
            ('reverse_proxy', '反向代理'),
            ('load_balancer', '负载均衡'),
            ('database', '数据库'),
            ('cache', '缓存'),
            ('message_queue', '消息队列'),
            ('static_files', '静态资源'),
        ),
        verbose_name="服务器角色", help_text="服务器在项目中的角色",
        db_comment="服务器角色"
    )
    environment = models.CharField(
        max_length=20, default='production',
        choices=(
            ('production', '生产环境'),
            ('staging', '预发布'),
            ('testing', '测试环境'),
            ('development', '开发环境'),
        ),
        verbose_name="环境标签", help_text="部署环境",
        db_comment="环境标签"
    )

    class Meta:
        db_table = f"{table_prefix}project_server"
        verbose_name = "项目-服务器关联"
        verbose_name_plural = verbose_name
        constraints = [
            models.UniqueConstraint(
                fields=['project', 'server', 'role'],
                name='uq_project_server_role'
            ),
        ]

    def __str__(self):
        return f"{self.project} ↔ {self.server} [{self.get_role_display()}]"


class DomainIP(CoreModel):
    """
    域名-IP 关联表

    记录 DNS 解析记录，包含记录类型、主机记录、解析线路等。
    """
    domain = models.ForeignKey(
        Domain, on_delete=models.CASCADE,
        db_constraint=False,
        verbose_name="域名", help_text="关联域名",
        db_comment="域名"
    )
    ip = models.ForeignKey(
        IPAddress, on_delete=models.CASCADE,
        db_constraint=False,
        verbose_name="目标IP", help_text="解析目标IP",
        db_comment="目标IP"
    )
    record_type = models.CharField(
        max_length=10, default='A',
        choices=(('A', 'A记录'), ('CNAME', 'CNAME记录')),
        verbose_name="记录类型", help_text="DNS记录类型",
        db_comment="记录类型"
    )
    host_record = models.CharField(
        max_length=100, null=True, blank=True,
        verbose_name="主机记录", help_text="主机记录，如 @ / www / api",
        db_comment="主机记录"
    )
    line = models.CharField(
        max_length=50, null=True, blank=True, default='默认',
        verbose_name="解析线路", help_text="解析线路，如默认/移动/联通",
        db_comment="解析线路"
    )
    ttl = models.IntegerField(
        null=True, blank=True,
        verbose_name="TTL(秒)", help_text="TTL值，单位秒",
        db_comment="TTL(秒)"
    )

    class Meta:
        db_table = f"{table_prefix}domain_ip"
        verbose_name = "域名-IP关联"
        verbose_name_plural = verbose_name
        constraints = [
            models.UniqueConstraint(
                fields=['domain', 'ip', 'record_type', 'host_record'],
                name='uq_domain_ip_record'
            ),
        ]

    def __str__(self):
        return f"{self.domain} → {self.ip} ({self.record_type})"


class ProjectDomain(CoreModel):
    """
    域名-项目关联表

    标记域名服务于哪个项目，支持一个域名关联多个项目。
    """
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE,
        db_constraint=False,
        verbose_name="项目", help_text="关联项目",
        db_comment="项目"
    )
    domain = models.ForeignKey(
        Domain, on_delete=models.CASCADE,
        db_constraint=False,
        verbose_name="域名", help_text="关联域名",
        db_comment="域名"
    )

    class Meta:
        db_table = f"{table_prefix}project_domain"
        verbose_name = "域名-项目关联"
        verbose_name_plural = verbose_name
        constraints = [
            models.UniqueConstraint(
                fields=['project', 'domain'],
                name='uq_project_domain'
            ),
        ]

    def __str__(self):
        return f"{self.domain} → {self.project}"


class ProjectPort(CoreModel):
    """
    端口-项目关联表

    标记端口所服务的具体项目。
    """
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE,
        db_constraint=False,
        verbose_name="项目", help_text="关联项目",
        db_comment="项目"
    )
    port = models.ForeignKey(
        Port, on_delete=models.CASCADE,
        db_constraint=False,
        verbose_name="端口", help_text="关联端口",
        db_comment="端口"
    )

    class Meta:
        db_table = f"{table_prefix}project_port"
        verbose_name = "端口-项目关联"
        verbose_name_plural = verbose_name
        constraints = [
            models.UniqueConstraint(
                fields=['project', 'port'],
                name='uq_project_port'
            ),
        ]

    def __str__(self):
        return f"{self.port} → {self.project}"


# ============================================================
# 扩展关联表
# ============================================================

class ServerVip(CoreModel):
    """
    服务器-VIP 关联表

    当 IP 类型为 vip 时，通过此中间表关联 VIP 与多台服务器节点。
    支持主备角色和优先级配置。
    """
    ip = models.ForeignKey(
        IPAddress, on_delete=models.CASCADE,
        db_constraint=False,
        verbose_name="VIP地址", help_text="VIP地址（ip_type必须为vip）",
        db_comment="VIP地址"
    )
    server = models.ForeignKey(
        Server, on_delete=models.CASCADE,
        db_constraint=False,
        verbose_name="服务器节点", help_text="挂载该VIP的服务器节点",
        db_comment="服务器节点"
    )
    role = models.CharField(
        max_length=20,
        choices=(
            ('master', '主节点'),
            ('backup', '备节点'),
            ('member', '集群成员'),
        ),
        verbose_name="节点角色", help_text="VIP节点角色：master/backup/member",
        db_comment="节点角色"
    )
    priority = models.IntegerField(
        null=True, blank=True,
        verbose_name="优先级", help_text="优先级（数值越大越优先，用于Master选举）",
        db_comment="优先级"
    )

    class Meta:
        db_table = f"{table_prefix}server_vip"
        verbose_name = "服务器-VIP关联"
        verbose_name_plural = verbose_name
        constraints = [
            models.UniqueConstraint(
                fields=['ip', 'server'],
                name='uq_server_vip'
            ),
        ]

    def __str__(self):
        return f"{self.ip} ↔ {self.server} [{self.get_role_display()}]"


class ServerProxyMapping(CoreModel):
    """
    服务器代理映射表

    记录 Nginx/HAProxy 等反向代理服务器与后端应用服务器的代理关系。
    这是解决"域名 → 代理服务器 → 后端服务器"关联链路的关键中间表。
    """
    proxy_server = models.ForeignKey(
        Server, on_delete=models.CASCADE, related_name='proxy_mappings_as_proxy',
        db_constraint=False,
        verbose_name="代理服务器", help_text="部署Nginx/HAProxy的服务器",
        db_comment="代理服务器"
    )
    backend_server = models.ForeignKey(
        Server, on_delete=models.CASCADE, related_name='proxy_mappings_as_backend',
        db_constraint=False,
        verbose_name="后端服务器", help_text="后端目标服务器",
        db_comment="后端服务器"
    )
    backend_port = models.ForeignKey(
        Port, on_delete=models.SET_NULL, null=True, blank=True,
        db_constraint=False,
        verbose_name="后端目标端口", help_text="后端目标端口（关联Port表）",
        db_comment="后端目标端口"
    )
    backend_port_number = models.IntegerField(
        null=True, blank=True,
        verbose_name="后端端口号", help_text="后端端口号（未在Port表中登记时使用）",
        db_comment="后端端口号"
    )
    proxy_port = models.IntegerField(
        null=True, blank=True,
        verbose_name="代理监听端口", help_text="代理服务器监听端口，如443/80",
        db_comment="代理监听端口"
    )
    server_name = models.CharField(
        max_length=255, null=True, blank=True,
        verbose_name="server_name", help_text="Nginx server_name指令值（域名）",
        db_comment="server_name"
    )
    proxy_path = models.CharField(
        max_length=500, null=True, blank=True, default='/',
        verbose_name="代理路径", help_text="代理路径，如/api/（默认/表示全部流量）",
        db_comment="代理路径"
    )
    protocol = models.CharField(
        max_length=10, default='http',
        choices=(('http', 'HTTP'), ('https', 'HTTPS'), ('tcp', 'TCP'), ('udp', 'UDP')),
        verbose_name="代理协议", help_text="代理协议：http/https/tcp/udp",
        db_comment="代理协议"
    )
    project = models.ForeignKey(
        Project, on_delete=models.SET_NULL, null=True, blank=True,
        db_constraint=False,
        verbose_name="关联项目", help_text="关联项目（便于追溯该代理规则服务于哪个项目）",
        db_comment="关联项目"
    )
    remark = models.TextField(
        null=True, blank=True,
        verbose_name="备注", help_text="备注（如对应的Nginx upstream名称）",
        db_comment="备注"
    )

    class Meta:
        db_table = f"{table_prefix}server_proxy_mapping"
        verbose_name = "服务器代理映射"
        verbose_name_plural = verbose_name
        constraints = [
            models.UniqueConstraint(
                fields=['proxy_server', 'backend_server', 'proxy_port', 'server_name', 'proxy_path'],
                name='uq_proxy_mapping'
            ),
        ]

    def __str__(self):
        return f"{self.proxy_server} → {self.backend_server}:{self.backend_port or self.backend_port_number}"


class ServiceDependency(CoreModel):
    """
    服务依赖表

    记录微服务架构中项目之间的调用依赖关系。
    前端项目通过内部域名调用后端项目 API 时，依赖此表描述调用拓扑。
    """
    from_project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='dependencies_as_caller',
        db_constraint=False,
        verbose_name="调用方项目", help_text="调用方项目（如前端项目G）",
        db_comment="调用方项目"
    )
    to_project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='dependencies_as_callee',
        db_constraint=False,
        verbose_name="被调用方项目", help_text="被调用方项目（如后端项目C）",
        db_comment="被调用方项目"
    )
    internal_domain = models.CharField(
        max_length=255,
        verbose_name="内部域名", help_text="内部域名，如api.project-c.internal",
        db_comment="内部域名"
    )
    protocol = models.CharField(
        max_length=10, default='http',
        choices=(('http', 'HTTP'), ('https', 'HTTPS'), ('grpc', 'gRPC'), ('tcp', 'TCP')),
        verbose_name="通信协议", help_text="通信协议：http/https/grpc/tcp",
        db_comment="通信协议"
    )
    target_port = models.IntegerField(
        verbose_name="目标端口", help_text="目标端口，如8080",
        db_comment="目标端口"
    )
    target_path = models.CharField(
        max_length=500, null=True, blank=True,
        verbose_name="API路径前缀", help_text="API路径前缀，如/api/v1/",
        db_comment="API路径前缀"
    )
    environment = models.CharField(
        max_length=20, default='production',
        choices=(
            ('production', '生产环境'),
            ('staging', '预发布'),
            ('testing', '测试环境'),
            ('development', '开发环境'),
        ),
        verbose_name="环境标签", help_text="部署环境",
        db_comment="环境标签"
    )
    remark = models.TextField(
        null=True, blank=True,
        verbose_name="备注", help_text="备注",
        db_comment="备注"
    )

    class Meta:
        db_table = f"{table_prefix}service_dependency"
        verbose_name = "服务依赖"
        verbose_name_plural = verbose_name
        constraints = [
            models.UniqueConstraint(
                fields=['from_project', 'to_project', 'internal_domain', 'environment'],
                name='uq_service_dependency'
            ),
        ]

    def __str__(self):
        return f"{self.from_project} → {self.to_project} ({self.internal_domain})"
