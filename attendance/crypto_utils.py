# attendance/crypto_utils.py
import base64
import hashlib
from typing import Optional

from django.conf import settings


def _derive_fernet_key() -> bytes:
    """
    生成 Fernet 所需的 32-byte urlsafe base64 key。
    默认使用 settings.SECRET_KEY 派生；你也可以在 settings.py 配置：
        ATTENDANCE_TRUST_CODE_KEY = "your-extra-secret"
    """
    material = getattr(settings, "ATTENDANCE_TRUST_CODE_KEY", None) or settings.SECRET_KEY
    digest = hashlib.sha256(material.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def encrypt_trust_code(trust_code: str) -> str:
    """
    加密 trust_code，返回可落库的密文字符串。
    依赖 cryptography（Fernet）。如果环境没有安装 cryptography，会抛出 ImportError。
    """
    if trust_code is None:
        return ""
    trust_code = trust_code.strip()
    if not trust_code:
        return ""

    try:
        from cryptography.fernet import Fernet  # type: ignore
    except ImportError as e:
        raise ImportError(
            "缺少依赖 cryptography，无法安全加密 trust_code。请安装：pip install cryptography"
        ) from e

    f = Fernet(_derive_fernet_key())
    token = f.encrypt(trust_code.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_trust_code(cipher_text: Optional[str]) -> str:
    """
    解密落库密文，返回 trust_code 明文。
    """
    if not cipher_text:
        return ""

    try:
        from cryptography.fernet import Fernet  # type: ignore
    except ImportError as e:
        raise ImportError(
            "缺少依赖 cryptography，无法解密 trust_code。请安装：pip install cryptography"
        ) from e

    f = Fernet(_derive_fernet_key())
    plain = f.decrypt(cipher_text.encode("utf-8"))
    return plain.decode("utf-8")
