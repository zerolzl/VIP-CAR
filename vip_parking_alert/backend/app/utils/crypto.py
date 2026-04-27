import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
import logging

logger = logging.getLogger(__name__)


class CryptoUtil:
    """基于Fernet的加解密工具，使用PBKDF2从SECRET_KEY派生密钥"""
    _fernet: Fernet | None = None

    @classmethod
    def _get_fernet(cls, secret_key: str) -> Fernet:
        if cls._fernet is not None:
            return cls._fernet
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"vip_parking_salt_v1",
            iterations=480000,
        )
        derived_key = base64.urlsafe_b64encode(kdf.derive(secret_key.encode("utf-8")))
        cls._fernet = Fernet(derived_key)
        return cls._fernet

    @classmethod
    def encrypt(cls, plaintext: str, secret_key: str) -> str:
        fernet = cls._get_fernet(secret_key)
        return fernet.encrypt(plaintext.encode("utf-8")).decode("utf-8")

    @classmethod
    def decrypt(cls, ciphertext: str, secret_key: str) -> str:
        fernet = cls._get_fernet(secret_key)
        return fernet.decrypt(ciphertext.encode("utf-8")).decode("utf-8")

    @classmethod
    def reset(cls):
        cls._fernet = None
