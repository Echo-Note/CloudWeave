"""
余额记录 — 序列化器（只读）
"""
from rest_framework import serializers

from dvadmin.cloud.models import BalanceRecord
from dvadmin.utils.serializers import CustomModelSerializer


class BalanceRecordSerializer(CustomModelSerializer):
    """余额记录 — 列表/详情查询序列化器（只读）"""

    cloud_platform_name = serializers.CharField(source="cloud_platform.name", read_only=True, help_text="云平台名称")
    creator_name = serializers.CharField(source="creator.username", read_only=True, help_text="创建人")

    class Meta:
        model = BalanceRecord
        fields = "__all__"
