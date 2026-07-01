"""
云平台账号 — 序列化器
"""
from rest_framework import serializers

from dvadmin.cloud.models import CloudPlatform
from dvadmin.utils.serializers import CustomModelSerializer


def _mask_secret(value: str | None) -> str | None:
    """对密钥字段做脱敏展示。

    规则：仅保留前 4 位和后 4 位，中间以 ``****`` 替代；
    空值或过短值（<=8 字符）统一显示为 ``****``。

    :param value: 明文密钥（字段读取时已自动解密）
    :return: 脱敏后的字符串
    """
    if not value:
        return value
    if len(value) <= 8:
        return "****"
    return f"{value[:4]}****{value[-4:]}"


class CloudPlatformSerializer(CustomModelSerializer):
    """云平台账号 — 序列化器

    读写统一使用此类：
      - 写入（create/update）：接收明文密钥，由 EncryptedCharField 自动加密入库
      - 读取（list/retrieve）：通过 to_representation 对密钥字段脱敏展示
    明文仅在同步任务等内部逻辑中通过模型属性直接获取。
    """

    company_name = serializers.SerializerMethodField(read_only=True, help_text="归属主体公司名称")
    creator_name = serializers.CharField(source="creator.username", read_only=True, help_text="创建人")
    modifier_name = serializers.CharField(source="modifier.username", read_only=True, help_text="修改人")

    def get_company_name(self, instance: CloudPlatform) -> str | None:
        """获取归属主体公司名称"""
        if instance.company:
            return instance.company.name
        return None

    def to_representation(self, instance):
        """序列化输出时对密钥字段脱敏"""
        ret = super().to_representation(instance)
        ret["secret_id"] = _mask_secret(ret.get("secret_id"))
        ret["secret_key"] = _mask_secret(ret.get("secret_key"))
        return ret

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
