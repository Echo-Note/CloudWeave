"""
域名注册商 — 序列化器
"""
from rest_framework import serializers

from dvadmin.cloud.models import Registrar
from dvadmin.utils.serializers import CustomModelSerializer


class RegistrarSerializer(CustomModelSerializer):
    """域名注册商 — 列表/详情查询序列化器"""

    company_name = serializers.SerializerMethodField(read_only=True, help_text="归属主体公司名称")
    cloud_platform_name = serializers.SerializerMethodField(read_only=True, help_text="关联云平台名称")
    creator_name = serializers.CharField(source="creator.username", read_only=True, help_text="创建人")
    modifier_name = serializers.CharField(source="modifier.username", read_only=True, help_text="修改人")

    def get_company_name(self, instance: Registrar) -> str | None:
        """获取归属主体公司名称"""
        if instance.company:
            return instance.company.name
        return None

    def get_cloud_platform_name(self, instance: Registrar) -> str | None:
        """获取关联云平台名称"""
        if instance.cloud_platform:
            return instance.cloud_platform.name
        return None

    class Meta:
        model = Registrar
        fields = "__all__"


class RegistrarImportSerializer(CustomModelSerializer):
    """域名注册商 — 导入序列化器"""

    class Meta:
        model = Registrar
        fields = "__all__"


class RegistrarExportSerializer(CustomModelSerializer):
    """域名注册商 — 导出序列化器"""

    company_name = serializers.SerializerMethodField(read_only=True, help_text="归属主体公司名称")
    cloud_platform_name = serializers.SerializerMethodField(read_only=True, help_text="关联云平台名称")

    def get_company_name(self, instance: Registrar) -> str | None:
        if instance.company:
            return instance.company.name
        return None

    def get_cloud_platform_name(self, instance: Registrar) -> str | None:
        if instance.cloud_platform:
            return instance.cloud_platform.name
        return None

    class Meta:
        model = Registrar
        fields = "__all__"
