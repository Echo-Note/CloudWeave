"""
同步日志 — API 视图（只读）
"""
from dvadmin.cloud.models import SyncLog
from dvadmin.cloud.serializers.sync_log import SyncLogSerializer
from dvadmin.utils.viewset import CustomModelViewSet


class SyncLogViewSet(CustomModelViewSet):
    """
    同步日志（只读）

    list:  查询同步日志列表（支持分页、过滤）
    retrieve:  查看同步日志详情
    """

    queryset = SyncLog.objects.all()
    serializer_class = SyncLogSerializer
    filter_fields = ["cloud_platform", "sync_type", "trigger", "status"]
    search_fields = ["cloud_platform__name"]
    ordering_fields = "__all__"
    # 只读：禁用增删改
    http_method_names = ["get", "head", "options"]
