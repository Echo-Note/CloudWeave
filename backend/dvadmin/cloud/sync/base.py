"""
云平台同步 — 抽象基类

定义各云厂商同步器的统一接口：
  - sync_servers(): 同步服务器（腾讯云/阿里云/华为云支持，美橙不支持）
  - sync_domains(): 同步域名（全部厂商支持）
  - sync_balance(): 同步余额（全部厂商支持）

子类按厂商 SDK 实现 _fetch_xxx 原始数据拉取，基类负责：
  1. 调用子类拉取方法
  2. 数据库 upsert（更新或创建）
  3. 记录同步结果与错误
  4. 写入 SyncLog
"""
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from django.db import transaction
from django.utils import timezone as dj_timezone

from dvadmin.assets.models import Domain, IPAddress, Server
from dvadmin.cloud.models import BalanceRecord, CloudPlatform, Registrar, SyncLog
from dvadmin.cloud.sync.schemas import (
    BalanceSyncData,
    DomainSyncData,
    ServerSyncData,
    SyncResult,
)


class BaseCloudSyncer(ABC):
    """
    云平台同步器抽象基类

    各厂商同步器继承此类，实现 _fetch_servers / _fetch_domains / _fetch_balance 方法。
    通过 SUPPORTED_RESOURCES 声明该厂商支持同步的资源类型。
    """

    # 该厂商支持的同步资源类型（子类覆盖）
    SUPPORTED_RESOURCES: set[str] = set()

    def __init__(self, cloud_platform: CloudPlatform):
        """
        初始化同步器

        :param cloud_platform: 云平台账号实例（含 API 凭证）
        """
        self.cloud_platform = cloud_platform
        self.platform_name = cloud_platform.name

    # ============================================================
    # 公共入口 — 同步引擎调用
    # ============================================================

    def sync_all(self, resources: Optional[list[str]] = None) -> dict[str, SyncResult]:
        """
        执行完整同步流程

        :param resources: 指定同步的资源类型列表，为空则同步该厂商支持的全部资源
        :return: {resource_type: SyncResult}
        """
        target_resources = set(resources or self.SUPPORTED_RESOURCES)
        # 仅同步该厂商支持的资源
        target_resources &= self.SUPPORTED_RESOURCES

        results: dict[str, SyncResult] = {}
        if "server" in target_resources:
            results["server"] = self._sync_servers_safe()
        if "domain" in target_resources:
            results["domain"] = self._sync_domains_safe()
        if "balance" in target_resources:
            results["balance"] = self._sync_balance_safe()
        return results

    # ============================================================
    # 服务器同步
    # ============================================================

    def _sync_servers_safe(self) -> SyncResult:
        """服务器同步（带异常捕获）"""
        result = SyncResult(resource_type="server")
        try:
            servers_data = self._fetch_servers()
        except NotImplementedError:
            return result
        except Exception as e:
            result.add_error("fetch_servers", str(e))
            return result

        for srv in servers_data:
            try:
                self._upsert_server(srv, result)
            except Exception as e:
                result.add_error(srv.hostname, str(e))
        return result

    @abstractmethod
    def _fetch_servers(self) -> list[ServerSyncData]:
        """
        从云平台拉取服务器列表（子类实现）

        腾讯云/阿里云/华为云必须实现，美橙等纯域名注册商 raise NotImplementedError。
        """
        raise NotImplementedError

    def _upsert_server(self, data: ServerSyncData, result: SyncResult) -> None:
        """服务器 upsert 到 assets.Server 表"""
        # 按 instance_id + cloud_platform 唯一定位
        if data.instance_id:
            server, created = Server.objects.select_for_update().get_or_create(
                cloud_platform=self.cloud_platform,
                instance_id=data.instance_id,
                defaults={
                    "hostname": data.hostname,
                    "os": data.os,
                    "cpu_cores": data.cpu_cores,
                    "memory_gb": data.memory_gb,
                    "disk_gb": data.disk_gb,
                    "status": data.status,
                    "expire_date": data.expire_date,
                    "remark": data.remark,
                },
            )
        else:
            # 无 instance_id 的按 hostname 匹配
            server, created = Server.objects.select_for_update().get_or_create(
                cloud_platform=self.cloud_platform,
                hostname=data.hostname,
                defaults={"status": data.status, "remark": data.remark},
            )

        if created:
            result.created += 1
        else:
            # 更新已有记录
            server.hostname = data.hostname
            server.os = data.os
            server.cpu_cores = data.cpu_cores
            server.memory_gb = data.memory_gb
            server.disk_gb = data.disk_gb
            server.status = data.status
            server.expire_date = data.expire_date
            if data.remark:
                server.remark = data.remark
            server.save()
            result.updated += 1

        # 同步 IP 地址
        self._sync_server_ips(server, data)

    def _sync_server_ips(self, server: Server, data: ServerSyncData) -> None:
        """同步服务器的内网/公网 IP"""
        for ip_addr in data.private_ips:
            IPAddress.objects.get_or_create(
                address=ip_addr,
                defaults={"ip_type": "private", "server": server},
            )
        for ip_addr in data.public_ips:
            IPAddress.objects.get_or_create(
                address=ip_addr,
                defaults={"ip_type": "public", "server": server},
            )

    # ============================================================
    # 域名同步
    # ============================================================

    def _sync_domains_safe(self) -> SyncResult:
        """域名同步（带异常捕获）"""
        result = SyncResult(resource_type="domain")
        try:
            domains_data = self._fetch_domains()
        except NotImplementedError:
            return result
        except Exception as e:
            result.add_error("fetch_domains", str(e))
            return result

        for dom in domains_data:
            try:
                self._upsert_domain(dom, result)
            except Exception as e:
                result.add_error(dom.name, str(e))
        return result

    @abstractmethod
    def _fetch_domains(self) -> list[DomainSyncData]:
        """从云平台/注册商拉取域名列表（子类实现）"""
        raise NotImplementedError

    def _upsert_domain(self, data: DomainSyncData, result: SyncResult) -> None:
        """域名 upsert 到 assets.Domain 表"""
        # 匹配或创建注册商
        registrar = None
        if data.registrar_name:
            registrar, _ = Registrar.objects.get_or_create(
                name=data.registrar_name,
                defaults={"cloud_platform": self.cloud_platform},
            )

        domain, created = Domain.objects.select_for_update().get_or_create(
            name=data.name,
            defaults={
                "registrar": registrar,
                "register_date": data.register_date,
                "expire_date": data.expire_date,
                "dns_provider": data.dns_provider,
                "remark": data.remark,
            },
        )

        if created:
            result.created += 1
        else:
            domain.registrar = registrar or domain.registrar
            domain.register_date = data.register_date or domain.register_date
            domain.expire_date = data.expire_date or domain.expire_date
            domain.dns_provider = data.dns_provider or domain.dns_provider
            if data.remark:
                domain.remark = data.remark
            domain.save()
            result.updated += 1

    # ============================================================
    # 余额同步
    # ============================================================

    def _sync_balance_safe(self) -> SyncResult:
        """余额同步（带异常捕获）"""
        result = SyncResult(resource_type="balance")
        try:
            balance_data = self._fetch_balance()
        except NotImplementedError:
            return result
        except Exception as e:
            result.add_error("fetch_balance", str(e))
            return result

        if balance_data:
            try:
                self._save_balance(balance_data)
                result.created += 1
            except Exception as e:
                result.add_error("save_balance", str(e))
        return result

    @abstractmethod
    def _fetch_balance(self) -> Optional[BalanceSyncData]:
        """从云平台拉取账户余额（子类实现）"""
        raise NotImplementedError

    def _save_balance(self, data: BalanceSyncData) -> BalanceRecord:
        """保存余额记录到 cloud.BalanceRecord 表"""
        return BalanceRecord.objects.create(
            cloud_platform=self.cloud_platform,
            cash_balance=data.cash_balance,
            voucher_balance=data.voucher_balance,
            credit_balance=data.credit_balance,
            frozen_amount=data.frozen_amount,
            total_balance=data.total_balance,
            currency=data.currency,
            recorded_at=data.recorded_at or dj_timezone.now(),
        )

    # ============================================================
    # 辅助方法
    # ============================================================

    @property
    def credentials(self) -> dict[str, str]:
        """获取 API 凭证明文。

        secret_id / secret_key 使用 EncryptedCharField，模型属性读取时已自动解密，
        此处直接返回明文供子类调用 SDK。
        """
        return {
            "secret_id": self.cloud_platform.secret_id or "",
            "secret_key": self.cloud_platform.secret_key or "",
        }
