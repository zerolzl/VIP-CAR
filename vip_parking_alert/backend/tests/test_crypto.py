import pytest
from app.utils.crypto import CryptoUtil

SECRET_KEY = "test-secret-key-for-testing-only-32chars"

class TestCryptoUtil:
    def test_encrypt_decrypt(self):
        plaintext = "my_password_123"
        encrypted = CryptoUtil.encrypt(plaintext, SECRET_KEY)
        decrypted = CryptoUtil.decrypt(encrypted, SECRET_KEY)
        assert decrypted == plaintext

    def test_empty_string(self):
        encrypted = CryptoUtil.encrypt("", SECRET_KEY)
        decrypted = CryptoUtil.decrypt(encrypted, SECRET_KEY)
        assert decrypted == ""

    def test_wrong_key_fails(self):
        CryptoUtil.reset()
        encrypted = CryptoUtil.encrypt("secret", SECRET_KEY)
        CryptoUtil.reset()
        with pytest.raises(Exception):
            CryptoUtil.decrypt(encrypted, "wrong-key-different-key")

    def test_chinese_characters(self):
        plaintext = "中文密码测试"
        encrypted = CryptoUtil.encrypt(plaintext, SECRET_KEY)
        decrypted = CryptoUtil.decrypt(encrypted, SECRET_KEY)
        assert decrypted == plaintext

    def test_reset(self):
        CryptoUtil.reset()
        plaintext = "after_reset"
        encrypted = CryptoUtil.encrypt(plaintext, SECRET_KEY)
        assert CryptoUtil.decrypt(encrypted, SECRET_KEY) == plaintext
        CryptoUtil.reset()
