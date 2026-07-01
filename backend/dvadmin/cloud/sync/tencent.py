"""
腾讯云同步实现

支持资源：服务器（CVM）、域名、余额
依赖 SDK：tencentcloud-sdk-python（可选，未安装时给出明确提示）

腾讯云 API 文档：
  - CVM DescribeInstances: 查询实例列表
  - Account DescribeAccountBalance: 查询账户余额
  - Domain DescribeDomainList: 查询域名列表
"""
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from dvadmin.cloud.sync.base import BaseCloudSyncer
from dvadmin.cloud.sync.schemas import (
    BalanceSyncData,
    DomainSyncData,
    ServerSyncData,
)


class TencentCloudSyncer(BaseCloudSyncer):
    """腾讯云同步器"""

    SUPPORTED_RESOURCES = {"server", "domain", "balance"}

    def _get_client(self, service: str, region: str = "ap-guangzhou"):
        """
        构造腾讯云 API 客户端

        :param service: 服务名，如 cvm / domain / billing
        :param region: 地域
        """
        try:
            from tencentcloud.common import credential
            from tencentcloud.common.profile.client_profile import ClientProfile
            from tencentcloud.common.profile.http_profile import HttpProfile
        except ImportError as e:
            raise ImportError(
                "腾讯云 SDK 未安装，请执行: pip install tencentcloud-sdk-python"
            ) from e

        cred = credential.Credential(
            self.credentials["secret_id"],
            self.credentials["secret_key"],
        )
        http_profile = HttpProfile()
        http_profile.endpoint = f"{service}.tencentcloudapi.com"
        client_profile = ClientProfile()
        client_profile.httpProfile = http_profile

        # 动态导入对应服务的 Client
        module = __import__(
            f"tencentcloud.{service}.v20170312",
            fromlist=[f"{service}_client"],
        )
        client_cls = getattr(module, f"{service.title()}Client")
        return client_cls(cred, region, client_profile)

    def _fetch_servers(self) -> list[ServerSyncData]:
        """从腾讯云 CVM 拉取服务器列表"""
        from tencentcloud.cvm.v20170312 import models as cvm_models

        regions = self.cloud_platform.sync_regions or ["ap-guangzhou"]
        all_servers: list[ServerSyncData] = []

        for region in regions:
            try:
                client = self._get_client("cvm", region)
                req = cvm_models.DescribeInstancesRequest()
                # 每页 100 条，循环拉取
                req.Limit = 100
                req.Offset = 0
                resp = client.DescribeInstances(req)

                for inst in resp.InstanceSet:
                    # 提取内网/公网 IP
                    private_ips = list(inst.PrivateIpAddresses or [])
                    public_ips = list(inst.PublicIpAddresses or [])

                    # 状态映射：腾讯云 → 本系统
                    status_map = {
                        "RUNNING": "running",
                        "STOPPED": "stopped",
                        "SHUTDOWN": "stopped",
                        "TERMINATING": "terminated",
                        "LAUNCH_FAILED": "terminated",
                    }
                    status = status_map.get(inst.InstanceState, "running")

                    # 到期时间（仅包年包月实例有）
                    expire_date = None
                    if hasattr(inst, "ExpiredTime") and inst.ExpiredTime:
                        expire_date = datetime.fromtimestamp(
                            inst.ExpiredTime, tz=timezone.utc
                        ).date()

                    all_servers.append(ServerSyncData(
                        hostname=inst.InstanceName or inst.InstanceId,
                        instance_id=inst.InstanceId,
                        os=inst.OsName if hasattr(inst, "OsName") else None,
                        cpu_cores=inst.CPU if hasattr(inst, "CPU") else None,
                        memory_gb=float(inst.Memory) / 1024 if hasattr(inst, "Memory") else None,
                        disk_gb=float(inst.SystemDisk.Size) if hasattr(inst, "SystemDisk") and inst.SystemDisk else None,
                        status=status,
                        expire_date=expire_date,
                        private_ips=private_ips,
                        public_ips=public_ips,
                        remark=f"腾讯云 {region} - {inst.InstanceType}",
                    ))
            except Exception:
                # 单地域失败不中断其他地域
                continue

        return all_servers

    def _fetch_domains(self) -> list[DomainSyncData]:
        """从腾讯云 Domain 服务拉取域名列表"""
        try:
            client = self._get_client("domain")
            from tencentcloud.domain.v20180308 import models as domain_models

            req = domain_models.DescribeDomainListRequest()
            req.Limit = 100
            req.Offset = 0
            resp = client.DescribeDomainList(req)

            domains: list[DomainSyncData] = []
            for d in resp.DomainList:
                domains.append(DomainSyncData(
                    name=d.Name,
                    registrar_name="腾讯云",
                    expire_date=datetime.fromtimestamp(
                        d.ExpirationDate, tz=timezone.utc
                    ).date() if d.ExpirationDate else None,
                    register_date=datetime.fromtimestamp(
                        d.CreationDate, tz=timezone.utc
                    ).date() if d.CreationDate else None,
                    dns_provider="DNSPod",
                ))
            return domains
        except ImportError:
            raise
        except Exception:
            return []

    def _fetch_balance(self) -> Optional[BalanceSyncData]:
        """从腾讯云 Billing 查询账户余额"""
        try:
            client = self._get_client("billing")
            from tencentcloud.billing.v20180709 import models as billing_models

            req = billing_models.DescribeAccountBalanceRequest()
            resp = client.DescribeAccountBalance(req)

            # 腾讯云返回余额单位为分，负数表示欠费
            balance_yuan = Decimal(str(resp.Balance)) / Decimal("100")

            return BalanceSyncData(
                total_balance=balance_yuan if balance_yuan > 0 else Decimal("0"),
                cash_balance=balance_yuan if balance_yuan > 0 else None,
                currency="CNY",
                recorded_at=datetime.now(tz=timezone.utc),
            )
        except ImportError:
            raise
        except Exception:
            return None
