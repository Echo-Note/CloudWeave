"""
主体公司管理 — 序列化器

提供 CompanyEntity 模型的序列化/反序列化支持，包括：
  - CompanyEntitySerializer：列表/详情查询
  - CompanyEntityImportSerializer：批量导入
  - CompanyEntityExportSerializer：批量导出
"""
from rest_framework import serializers

from dvadmin.company.models import CompanyEntity
from dvadmin.utils.serializers import CustomModelSerializer


class CompanyEntitySerializer(CustomModelSerializer):
    """主体公司 — 列表/详情查询序列化器"""

    parent_name = serializers.SerializerMethodField(
        read_only=True, help_text="上级主体名称"
    )

    def get_parent_name(self, instance: CompanyEntity) -> str | None:
        """获取上级主体名称"""
        if instance.parent:
            return instance.parent.name
        return None

    def to_representation(self, instance):
        """
        输出时将 business_license 相对路径转为可访问 URL

        私有对象存储下，default_storage.url() 会生成带签名的 presigned URL；
        本地存储下返回 /media/... 相对路径，由前端拼接后端地址。
        """
        ret = super().to_representation(instance)
        license_val = ret.get('business_license')
        if license_val and not license_val.startswith('http'):
            from django.core.files.storage import default_storage
            from urllib.parse import unquote
            # 数据库存的是 "media/files/..." 格式，S3Storage 的 key 是去掉 "media/" 前缀的部分
            key = license_val[6:] if license_val.startswith('media/') else license_val
            # 解码 percent-encoding，避免 default_storage.url() 二次编码导致签名失效
            key = unquote(key)
            try:
                ret['business_license'] = default_storage.url(key)
            except Exception:
                pass
        return ret

    class Meta:
        model = CompanyEntity
        fields = "__all__"


class CompanyEntityImportSerializer(CustomModelSerializer):
    """主体公司 — 导入序列化器"""

    class Meta:
        model = CompanyEntity
        fields = "__all__"


class CompanyEntityExportSerializer(CustomModelSerializer):
    """主体公司 — 导出序列化器"""

    parent_name = serializers.SerializerMethodField(
        read_only=True, help_text="上级主体名称"
    )

    def get_parent_name(self, instance: CompanyEntity) -> str | None:
        if instance.parent:
            return instance.parent.name
        return None

    class Meta:
        model = CompanyEntity
        exclude = ("description",)
