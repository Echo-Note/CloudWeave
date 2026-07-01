"""
云平台管理 — 视图包

按模型拆分子模块，统一聚合导出，外部引用路径不变：
    from dvadmin.cloud.views import CloudPlatformViewSet
"""
from dvadmin.cloud.views.balance_record import BalanceRecordViewSet
from dvadmin.cloud.views.cloud_platform import CloudPlatformViewSet
from dvadmin.cloud.views.registrar import RegistrarViewSet
from dvadmin.cloud.views.sync_log import SyncLogViewSet

__all__ = [
    "CloudPlatformViewSet",
    "RegistrarViewSet",
    "SyncLogViewSet",
    "BalanceRecordViewSet",
]
