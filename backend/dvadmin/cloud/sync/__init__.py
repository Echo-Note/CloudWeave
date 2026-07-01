"""
云平台同步模块

按厂商实现各云平台的资产同步：
  - base.py: 抽象基类 BaseCloudSyncer
  - schemas.py: 数据模式（ServerSyncData / DomainSyncData / BalanceSyncData / SyncResult）
  - engine.py: 同步引擎 SyncEngine（工厂 + 日志写入）
  - tencent.py: 腾讯云（服务器 + 域名 + 余额）
  - aliyun.py: 阿里云（服务器 + 域名 + 余额）
  - huawei.py: 华为云（服务器 + 域名 + 余额）
  - meicheng.py: 美橙互联（仅域名 + 余额，不支持服务器）

使用方式：
    from dvadmin.cloud.sync.engine import SyncEngine
    engine = SyncEngine(cloud_platform)
    engine.run(trigger="manual")
"""
from dvadmin.cloud.sync.base import BaseCloudSyncer
from dvadmin.cloud.sync.engine import SyncEngine, get_syncer
from dvadmin.cloud.sync.schemas import (
    BalanceSyncData,
    DomainSyncData,
    ServerSyncData,
    SyncResult,
)

__all__ = [
    "BaseCloudSyncer",
    "SyncEngine",
    "get_syncer",
    "ServerSyncData",
    "DomainSyncData",
    "BalanceSyncData",
    "SyncResult",
]
