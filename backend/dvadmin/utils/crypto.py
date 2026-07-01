"""
敏感数据加解密工具

使用 AES-256-GCM（带认证的对称加密）对敏感字段进行加解密，
保证数据库中只存储密文，业务代码通过 EncryptedCharField 透明读取明文。

密文存储格式：``enc:v1:<base64(nonce + ciphertext + tag)>``
  - ``enc:v1:`` 前缀用于区分密文与历史明文，便于平滑迁移
  - base64 内容包含 12 字节随机 nonce、密文、16 字节 GCM tag

密钥来源（优先级从高到低）：
  1. 环境变量 ``CLOUDWEAVE_AES_KEY``
  2. Django settings 中的 ``CLOUDWEAVE_AES_KEY``
  3. 开发环境回退密钥（仅 DEBUG 模式，生产必须配置正式密钥）

安全说明：
  - GCM 模式自带完整性校验，密文被篡改时解密会抛出 InvalidTag
  - 每次加密使用随机 nonce，相同明文产生不同密文
  - 密钥长度固定 32 字节（256 位），由 ``_derive_key`` 从任意长度口令派生
"""
from __future__ import annotations

import base64
import hashlib
import os

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ImportError as _exc:  # pragma: no cover
    raise ImportError(
        "加密模块依赖 cryptography 库，请执行 `uv add cryptography` 或 "
        "`pip install cryptography` 安装。"
    ) from _exc

# 密文前缀，用于区分密文与历史明文
_CIPHER_PREFIX = "enc:v1:"
# GCM nonce 长度（字节）
_NONCE_LENGTH = 12
# AES-256 密钥长度（字节）
_KEY_LENGTH = 32
# 开发环境回退密钥（仅 DEBUG=True 时使用，生产环境必须配置 CLOUDWEAVE_AES_KEY）
_DEV_FALLBACK_KEY = b"CloudWeave-DEV-ONLY-KEY-DO-NOT-USE-IN-PROD!!"


def _derive_key(raw: str | bytes) -> bytes:
    """从任意长度的口令派生固定 32 字节 AES 密钥（SHA-256）。

    :param raw: 原始密钥字符串或字节
    :return: 32 字节密钥
    """
    if isinstance(raw, str):
        raw = raw.encode("utf-8")
    return hashlib.sha256(raw).digest()


def _get_key() -> bytes:
    """获取当前生效的 AES 密钥。

    优先级：环境变量 > Django settings > 开发回退密钥（仅 DEBUG）。

    :return: 32 字节密钥
    :raises ImproperlyConfigured: 生产环境未配置密钥时抛出
    """
    raw = os.environ.get("CLOUDWEAVE_AES_KEY") or getattr(settings, "CLOUDWEAVE_AES_KEY", None)
    if raw:
        return _derive_key(raw)
    # 未配置密钥
    if getattr(settings, "DEBUG", False):
        return _derive_key(_DEV_FALLBACK_KEY)
    raise ImproperlyConfigured(
        "生产环境必须配置 CLOUDWEAVE_AES_KEY（环境变量或 settings.CLOUDWEAVE_AES_KEY），"
        "建议使用 32 位以上随机字符串。"
    )


def encrypt(plaintext: str) -> str:
    """加密明文，返回带前缀的密文字符串。

    :param plaintext: 待加密明文
    :return: ``enc:v1:<base64>`` 格式密文
    """
    if not plaintext:
        return plaintext
    # 兼容：已是密文则不重复加密
    if plaintext.startswith(_CIPHER_PREFIX):
        return plaintext
    key = _get_key()
    nonce = os.urandom(_NONCE_LENGTH)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    blob = nonce + ciphertext  # nonce + (ciphertext||tag)
    encoded = base64.urlsafe_b64encode(blob).decode("ascii")
    return f"{_CIPHER_PREFIX}{encoded}"


def decrypt(ciphertext: str) -> str:
    """解密密文，返回明文。

    对于无 ``enc:v1:`` 前缀的历史明文，直接原样返回以兼容旧数据。

    :param ciphertext: 密文或历史明文
    :return: 明文
    :raises ValueError: 密文格式损坏或被篡改时抛出
    """
    if not ciphertext:
        return ciphertext
    # 无前缀视为历史明文，原样返回（兼容迁移前数据）
    if not ciphertext.startswith(_CIPHER_PREFIX):
        return ciphertext
    encoded = ciphertext[len(_CIPHER_PREFIX):]
    try:
        blob = base64.urlsafe_b64decode(encoded)
    except Exception as e:
        raise ValueError("密文 base64 解码失败，数据可能已损坏") from e
    if len(blob) < _NONCE_LENGTH:
        raise ValueError("密文长度异常，数据可能已损坏")
    nonce = blob[:_NONCE_LENGTH]
    ct = blob[_NONCE_LENGTH:]
    key = _get_key()
    aesgcm = AESGCM(key)
    try:
        plaintext = aesgcm.decrypt(nonce, ct, None)
    except Exception as e:
        raise ValueError("密文解密失败，密钥可能已变更或数据被篡改") from e
    return plaintext.decode("utf-8")


def is_encrypted(value: str) -> bool:
    """判断字符串是否为加密后的密文格式。

    :param value: 待判断字符串
    :return: 是否为密文
    """
    return bool(value) and value.startswith(_CIPHER_PREFIX)
