"""
云平台账号 — 序列化器
"""
from rest_framework import serializers

from dvadmin.cloud.models import CloudPlatform
from dvadmin.utils.serializers import CustomModelSerializer


class CloudPlatformSerializer(CustomModelSerializer):
    """云平台账号 — 列表/详情查询序列化器"""

    company_name = serializers.SerializerMethodField(read_only=True, help_text="归属主体公司名称")
    creator_name = serializers.CharField(source="creator.username", read_only=True, help_text="创建人")
    modifier_name = serializers.CharField(source="modifier.username", read_only=True, help_text="修改人")

    def get_company_name(self, instance: CloudPlatform) -> str | None:
        """获取归属主体公司名称"""
        if instance.company:
            return instance.company.name
        return None

    class Meta:
        model = CloudPlatform
        fields = "__all__"


class CloudPlatformImportSerializer(CustomModelSerializer):
    """云平台账号 — 导入序列化器"""

    class Meta:
        model = CloudPlatform
        fields = "__all__"


class CloudPlatformExportSerializer(CustomModelSerializer):
    """云平台账号 — 导出序列化器（不含密钥）"""

    company_name = serializers.SerializerMethodField(read_only=True, help_text="归属主体公司名称")

    def get_company_name(self, instance: CloudPlatform) -> str | None:
        if instance.company:
            return instance.company.name
        return None

    class Meta:
        model = CloudPlatform
        exclude = ("secret_id", "secret_key")
