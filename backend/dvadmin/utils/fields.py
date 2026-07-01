"""
Django 自定义加密字段

提供 ``EncryptedCharField``，继承自 ``CharField``，
在写入数据库时自动加密、读取时自动解密，业务代码无需感知。

设计要点：
  - ``from_db_value``：数据库读取时解密为明文，实例属性始终持有明文
  - ``pre_save``：写入数据库前加密为密文
  - 历史明文兼容：解密时若发现无 ``enc:v1:`` 前缀，原样返回，支持平滑迁移
  - ``to_python``：表单/序列化反序列化时透传，避免对明文重复处理
"""
from __future__ import annotations

from django.db import models

from dvadmin.utils.crypto import decrypt, encrypt, is_encrypted


class EncryptedCharField(models.CharField):
    """透明加解密的 CharField。

    用法与普通 CharField 一致，数据库中存储 AES-256-GCM 密文。

    示例::

        secret_key = EncryptedCharField(
            max_length=1000, null=True, blank=True,
            verbose_name="SecretKey", help_text="API 密钥（加密存储）",
        )

    注意：``max_length`` 应考虑密文膨胀（密文长度约为明文的 2 倍 + 固定开销）。
    """

    description = "AES-256-GCM 加密 CharField"

    def from_db_value(self, value, expression, connection):
        """数据库值 → Python 明文（查询时自动调用）。"""
        if value is None:
            return None
        return decrypt(value)

    def to_python(self, value):
        """表单/序列化值 → Python 明文。

        若传入的是密文（带前缀）则解密，否则视为明文原样返回。
        """
        if value is None:
            return None
        if isinstance(value, str) and is_encrypted(value):
            return decrypt(value)
        return value

    def get_prep_value(self, value):
        """Python 值 → 数据库存储值。

        保存（save）及查询（filter）时会调用，自动加密明文。
        """
        if value is None:
            return None
        # 明文加密；已是密文则不重复加密
        return encrypt(value)

    def value_to_string(self, obj):
        """序列化为字符串（如 dumpdata），存储密文。"""
        value = self.value_from_object(obj)
        return self.get_prep_value(value)

    def deconstruct(self):
        """序列化字段定义（makemigrations 用），保持与 CharField 一致。"""
        name, path, args, kwargs = super().deconstruct()
        return name, path, args, kwargs
