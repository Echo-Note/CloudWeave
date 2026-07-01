"""
Django 自定义加密字段

提供 ``EncryptedCharField``，继承自 ``CharField``，
在写入数据库时自动加密、读取时自动解密，业务代码无需感知。

设计要点：
  - ``from_db_value``：数据库读取时解密为明文，实例属性始终持有明文
  - ``get_prep_value``：写入数据库前加密为密文
  - ``to_python``：表单/序列化反序列化时透传明文
"""
from __future__ import annotations

from django.db import models

from dvadmin.utils.crypto import decrypt, encrypt


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

    def from_db_value(self, value, expression, connection):
        """数据库值 → Python 明文（查询时自动调用）。"""
        if value is None:
            return None
        return decrypt(value)

    def to_python(self, value):
        """表单/序列化值 → Python 明文（透传，写入时由 get_prep_value 加密）。"""
        return value

    def get_prep_value(self, value):
        """Python 值 → 数据库存储值。

        保存（save）及查询（filter）时会调用，自动加密明文。
        """
        if value is None:
            return None
        return encrypt(value)

    def value_to_string(self, obj) -> str:
        """序列化为字符串（如 dumpdata），存储密文。"""
        value = self.value_from_object(obj)
        prepared = self.get_prep_value(value)
        return prepared or ""
