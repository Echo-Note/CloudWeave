"""
阿里云同步实现

支持资源：服务器（ECS）、域名、余额
依赖 SDK：alibabacloud-ecs20140526 / alibabacloud-domain20180129 / alibabacloud-bssopenapi20171214
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


class AliyunSyncer(BaseCloudSyncer):
    """阿里云同步器"""

    SUPPORTED_RESOURCES = {"server", "domain", "balance"}

    def _get_credential(self):
        """构造阿里云凭证"""
        try:
            from alibabacloud_tea_openapi import models as open_api_models
        except ImportError as e:
            raise ImportError(
                "阿里云 SDK 未安装，请执行: pip install alibabacloud-ecs20140526 "
                "alibabacloud-domain20180129 alibabacloud-bssopenapi20171214"
            ) from e

        config = open_api_models.Config(
            access_key_id=self.credentials["secret_id"],
            access_key_secret=self.credentials["secret_key"],
        )
        return config

    def _fetch_servers(self) -> list[ServerSyncData]:
        """从阿里云 ECS 拉取服务器列表"""
        from alibabacloud_ecs20140526.client import Client as EcsClient
        from alibabacloud_ecs20140526 import models as ecs_models
        from alibabacloud_tea_openapi import models as open_api_models

        regions = self.cloud_platform.sync_regions or ["cn-hangzhou"]
        all_servers: list[ServerSyncData] = []

        for region in regions:
            try:
                config = self._get_credential()
                config.endpoint = f"ecs.{region}.aliyuncs.com"
                client = EcsClient(config)

                req = ecs_models.DescribeInstancesRequest(
                    region_id=region,
                    page_size=100,
                    page_number=1,
                )
                resp = client.describe_instances(req)

                for inst in resp.body.instances.instance:
                    # 状态映射：阿里云 → 本系统
                    status_map = {
                        "Running": "running",
                        "Stopped": "stopped",
                        "Starting": "running",
                        "Stopping": "stopped",
                        "Deleted": "terminated",
                    }
                    status = status_map.get(inst.status, "running")

                    # 提取 IP
                    private_ips = []
                    public_ips = []
                    if inst.vpc_attributes and inst.vpc_attributes.private_ip_address:
                        private_ips = inst.vpc_attributes.private_ip_address.ip_address or []
                    if inst.vpc_attributes and inst.vpc_attributes.nat_ip_address:
                        public_ips = [inst.vpc_attributes.nat_ip_address]
                    if inst.public_ip_address:
                        public_ips = inst.public_ip_address.ip_address or []

                    all_servers.append(ServerSyncData(
                        hostname=inst.instance_name or inst.instance_id,
                        instance_id=inst.instance_id,
                        os=inst.os_name,
                        cpu_cores=inst.cpu,
                        memory_gb=float(inst.memory) / 1024 if inst.memory else None,
                        status=status,
                        expire_date=inst.expired_time.date() if inst.expired_time else None,
                        private_ips=private_ips,
                        public_ips=public_ips,
                        remark=f"阿里云 {region} - {inst.instance_type}",
                    ))
            except Exception:
                continue

        return all_servers

    def _fetch_domains(self) -> list[DomainSyncData]:
        """从阿里云 Domain 服务拉取域名列表"""
        try:
            from alibabacloud_domain20180129.client import Client as DomainClient
            from alibabacloud_domain20180129 import models as domain_models

            config = self._get_credential()
            config.endpoint = "domain.aliyuncs.com"
            client = DomainClient(config)

            req = domain_models.QueryDomainListRequest(
                page_num=1,
                page_size=100,
            )
            resp = client.query_domain_list(req)

            domains: list[DomainSyncData] = []
            for d in resp.body.data:
                domains.append(DomainSyncData(
                    name=d.domain_name,
                    registrar_name="阿里云",
                    expire_date=d.expiration_date.date() if d.expiration_date else None,
                    register_date=d.registration_date.date() if d.registration_date else None,
                    dns_provider="阿里云DNS",
                ))
            return domains
        except ImportError:
            raise
        except Exception:
            return []

    def _fetch_balance(self) -> Optional[BalanceSyncData]:
        """从阿里云 BSS（费用中心）查询账户余额"""
        try:
            from alibabacloud_bssopenapi20171214.client import Client as BssClient
            from alibabacloud_bssopenapi20171214 import models as bss_models

            config = self._get_credential()
            config.endpoint = "business.aliyuncs.com"
            client = BssClient(config)

            req = bss_models.QueryAccountBalanceRequest()
            resp = client.query_account_balance(req)

            data = resp.body.data
            # 阿里云 available_amount 为可用余额（字符串）
            total = Decimal(data.available_amount) if data.available_amount else Decimal("0")
            cash = Decimal(data.available_cash_amount) if data.available_cash_amount else None

            return BalanceSyncData(
                total_balance=total,
                cash_balance=cash,
                currency="CNY",
                recorded_at=datetime.now(tz=timezone.utc),
            )
        except ImportError:
            raise
        except Exception:
            return None
