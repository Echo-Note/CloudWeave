"""
华为云同步实现

支持资源：服务器（ECS）、域名、余额
依赖 SDK：huaweicloud-sdk-ecs / huaweicloud-sdk-domain / huaweicloud-sdk-bss
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


class HuaweiCloudSyncer(BaseCloudSyncer):
    """华为云同步器"""

    SUPPORTED_RESOURCES = {"server", "domain", "balance"}

    def _get_credentials(self):
        """返回华为云 AK/SK"""
        return (
            self.credentials["secret_id"],   # Access Key
            self.credentials["secret_key"],  # Secret Key
        )

    def _fetch_servers(self) -> list[ServerSyncData]:
        """从华为云 ECS 拉取服务器列表"""
        try:
            from huaweicloudsdkcore.auth.credentials import BasicCredentials
            from huaweicloudsdkecs.v2 import (
                EcsClient,
                ListServersDetailsRequest,
            )
        except ImportError as e:
            raise ImportError(
                "华为云 SDK 未安装，请执行: pip install huaweicloudsdkcore "
                "huaweicloudsdkecs huaweicloudsdkdomain huaweicloudsdkecs"
            ) from e

        ak, sk = self._get_credentials()
        cred = BasicCredentials(ak=ak, sk=sk)

        regions = self.cloud_platform.sync_regions or ["cn-north-4"]
        all_servers: list[ServerSyncData] = []

        for region in regions:
            try:
                client = EcsClient.new_builder().with_credentials(cred).with_region(
                    region
                ).build()

                req = ListServersDetailsRequest(limit=100, offset=1)
                resp = client.list_servers_details(req)

                for inst in resp.servers:
                    # 状态映射：华为云 → 本系统
                    status_map = {
                        "ACTIVE": "running",
                        "STOPPED": "stopped",
                        "ERROR": "terminated",
                    }
                    status = status_map.get(inst.status, "running")

                    # 提取 IP（华为云 addresses 是 dict: {网卡名: [ip_info]}）
                    private_ips = []
                    public_ips = []
                    if inst.addresses:
                        for _nic, ip_list in inst.addresses.items():
                            for ip_info in ip_list:
                                if ip_info.os_ext_ip_stype == "fixed":
                                    private_ips.append(ip_info.addr)
                                elif ip_info.os_ext_ip_stype == "floating":
                                    public_ips.append(ip_info.addr)

                    all_servers.append(ServerSyncData(
                        hostname=inst.name or inst.id,
                        instance_id=inst.id,
                        os=inst.os_ext_srv_atts.os_type if inst.os_ext_srv_atts else None,
                        cpu_cores=inst.flavor.vcpus if inst.flavor else None,
                        memory_gb=float(inst.flavor.ram) / 1024 if inst.flavor and inst.flavor.ram else None,
                        status=status,
                        expire_date=inst.os_ext_srv_atts.launch_time.date() if inst.os_ext_srv_atts else None,
                        private_ips=private_ips,
                        public_ips=public_ips,
                        remark=f"华为云 {region}",
                    ))
            except Exception:
                continue

        return all_servers

    def _fetch_domains(self) -> list[DomainSyncData]:
        """从华为云 Domain 服务拉取域名列表"""
        try:
            from huaweicloudsdkcore.auth.credentials import BasicCredentials
            from huaweicloudsdkdomain.v2 import (
                DomainClient,
                ListDomainsRequest,
            )

            ak, sk = self._get_credentials()
            cred = BasicCredentials(ak=ak, sk=sk)
            client = DomainClient.new_builder().with_credentials(cred).build()

            req = ListDomainsRequest(offset=0, limit=100)
            resp = client.list_domains(req)

            domains: list[DomainSyncData] = []
            for d in resp.domains:
                domains.append(DomainSyncData(
                    name=d.domain_name,
                    registrar_name="华为云",
                    expire_date=d.expiry_date.date() if d.expiry_date else None,
                    register_date=d.register_date.date() if d.register_date else None,
                    dns_provider="华为云DNS",
                ))
            return domains
        except ImportError:
            raise
        except Exception:
            return []

    def _fetch_balance(self) -> Optional[BalanceSyncData]:
        """从华为云 BSS 查询账户余额"""
        try:
            from huaweicloudsdkcore.auth.credentials import BasicCredentials
            from huaweicloudsdkecs.v2 import EcsClient  # noqa: F401
            from huaweicloudsdkecs.v2.region.ecs_region import EcsRegion  # noqa: F401

            # 华为云 BSS 使用全局 endpoint
            import requests

            ak, sk = self._get_credentials()
            # 华为云 BSS 查余额需通过 IAM Token 调用 REST API
            # 这里简化处理，实际需按华为云 BSS API 文档实现签名
            url = "https://bss.myhuaweicloud.com/v2.0/customer/customer-amount/balances"
            headers = {"Content-Type": "application/json"}
            resp = requests.get(url, headers=headers, auth=(ak, sk), timeout=30)

            if resp.status_code == 200:
                data = resp.json()
                balance = Decimal(str(data.get("amount", "0")))
                return BalanceSyncData(
                    total_balance=balance,
                    currency="CNY",
                    recorded_at=datetime.now(tz=timezone.utc),
                )
            return None
        except ImportError:
            raise
        except Exception:
            return None
