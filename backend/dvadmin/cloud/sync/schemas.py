"""
云平台同步 — 数据模式定义

定义各资源同步的标准化数据结构，各厂商同步器返回这些 dataclass，
由同步引擎统一写入数据库。与 assets 模型字段对齐。
"""
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Optional


@dataclass
class ServerSyncData:
    """服务器同步数据 — 对齐 assets.Server 模型字段"""

    hostname: str
    instance_id: Optional[str] = None
    os: Optional[str] = None
    cpu_cores: Optional[int] = None
    memory_gb: Optional[float] = None
    disk_gb: Optional[float] = None
    status: str = "running"  # running / stopped / terminated / maintenance
    expire_date: Optional[date] = None
    # 内网/公网 IP 列表（同步时一并写入 IPAddress 表）
    private_ips: list[str] = field(default_factory=list)
    public_ips: list[str] = field(default_factory=list)
    remark: Optional[str] = None


@dataclass
class DomainSyncData:
    """域名同步数据 — 对齐 assets.Domain 模型字段"""

    name: str
    registrar_name: Optional[str] = None  # 注册商名称，同步时自动匹配/创建 Registrar
    register_date: Optional[date] = None
    expire_date: Optional[date] = None
    dns_provider: Optional[str] = None
    remark: Optional[str] = None


@dataclass
class BalanceSyncData:
    """余额同步数据 — 对齐 cloud.BalanceRecord 模型字段"""

    total_balance: Decimal
    cash_balance: Optional[Decimal] = None
    voucher_balance: Optional[Decimal] = None
    credit_balance: Optional[Decimal] = None
    frozen_amount: Optional[Decimal] = None
    currency: str = "CNY"
    recorded_at: Optional[datetime] = None  # 为空则取当前时间


@dataclass
class SyncResult:
    """单个资源类型的同步结果"""

    resource_type: str  # server / domain / balance
    created: int = 0
    updated: int = 0
    terminated: int = 0
    errors: list[dict] = field(default_factory=list)

    @property
    def success_count(self) -> int:
        return self.created + self.updated

    def add_error(self, item: str, error: str) -> None:
        """记录单条错误"""
        self.errors.append({"item": item, "error": error})

    def merge(self, other: "SyncResult") -> None:
        """合并另一个同类型结果"""
        self.created += other.created
        self.updated += other.updated
        self.terminated += other.terminated
        self.errors.extend(other.errors)
