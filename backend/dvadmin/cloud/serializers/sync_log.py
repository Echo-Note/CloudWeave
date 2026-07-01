"""
同步日志 — 序列化器（只读）
"""
from rest_framework import serializers

from dvadmin.cloud.models import SyncLog
from dvadmin.utils.serializers import CustomModelSerializer


class SyncLogSerializer(CustomModelSerializer):
    """同步日志 — 列表/详情查询序列化器（只读）"""

    cloud_platform_name = serializers.CharField(source="cloud_platform.name", read_only=True, help_text="云平台名称")
    creator_name = serializers.CharField(source="creator.username", read_only=True, help_text="创建人")

    class Meta:
        model = SyncLog
        fields = "__all__"
