"""
云平台管理 — URL 路由
"""
from rest_framework import routers

from dvadmin.cloud.views import (
    BalanceRecordViewSet,
    CloudPlatformViewSet,
    RegistrarViewSet,
    SyncLogViewSet,
)

cloud_url = routers.SimpleRouter()
cloud_url.register(r"platform", CloudPlatformViewSet, basename="cloud_platform")
cloud_url.register(r"registrar", RegistrarViewSet, basename="cloud_registrar")
cloud_url.register(r"sync_log", SyncLogViewSet, basename="cloud_synclog")
cloud_url.register(r"balance", BalanceRecordViewSet, basename="cloud_balance")

urlpatterns = cloud_url.urls
