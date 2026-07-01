"""
美橙互联同步实现

美橙为纯域名注册商，不支持云服务器。
支持资源：域名、余额
依赖：美橙开放平台 API（HTTP REST）

美橙 API 文档参考其开放平台，鉴权方式为 API Key + 签名。
"""
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

import requests

from dvadmin.cloud.sync.base import BaseCloudSyncer
from dvadmin.cloud.sync.schemas import (
    BalanceSyncData,
    DomainSyncData,
    ServerSyncData,
)

# 美橙 API 基地址
MEICHENG_API_BASE = "https://api.meicheng.com/openapi/v1"


class MeichengSyncer(BaseCloudSyncer):
    """美橙互联同步器（仅域名 + 余额）"""

    SUPPORTED_RESOURCES = {"domain", "balance"}

    def _fetch_servers(self) -> list[ServerSyncData]:
        """美橙不支持云服务器，直接返回空列表"""
        raise NotImplementedError("美橙互联不支持服务器同步")

    def _fetch_domains(self) -> list[DomainSyncData]:
        """从美橙 API 拉取域名列表"""
        try:
            resp = requests.get(
                f"{MEICHENG_API_BASE}/domains",
                params={
                    "api_key": self.credentials["secret_id"],
                    "sign": self._sign("GET", "/domains"),
                    "page": 1,
                    "page_size": 100,
                },
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()

            domains: list[DomainSyncData] = []
            for d in data.get("data", {}).get("list", []):
                domains.append(DomainSyncData(
                    name=d.get("domain"),
                    registrar_name="美橙",
                    register_date=self._parse_date(d.get("register_date")),
                    expire_date=self._parse_date(d.get("expire_date")),
                    dns_provider=d.get("dns_server"),
                    remark=f"美橙互联 - {d.get('status', '')}",
                ))
            return domains
        except Exception:
            return []

    def _fetch_balance(self) -> Optional[BalanceSyncData]:
        """从美橙 API 查询账户余额"""
        try:
            resp = requests.get(
                f"{MEICHENG_API_BASE}/account/balance",
                params={
                    "api_key": self.credentials["secret_id"],
                    "sign": self._sign("GET", "/account/balance"),
                },
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json().get("data", {})

            balance = Decimal(str(data.get("balance", "0")))
            return BalanceSyncData(
                total_balance=balance,
                cash_balance=balance,
                currency="CNY",
                recorded_at=datetime.now(tz=timezone.utc),
            )
        except Exception:
            return None

    # ============================================================
    # 辅助方法
    # ============================================================

    def _sign(self, method: str, path: str) -> str:
        """
        美橙 API 签名计算

        美橙开放平台使用 HMAC-SHA256 对请求进行签名。
        具体签名规则参考美橙 API 文档。
        """
        import hashlib
        import hmac

        secret_key = self.credentials["secret_key"]
        string_to_sign = f"{method}\n{path}\n{self.credentials['secret_id']}"
        return hmac.new(
            secret_key.encode(),
            string_to_sign.encode(),
            hashlib.sha256,
        ).hexdigest()

    @staticmethod
    def _parse_date(date_str: Optional[str]):
        """解析美橙返回的日期字符串（YYYY-MM-DD）"""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return None
