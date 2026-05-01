import pytest
from cryptography.fernet import Fernet

from isales_common.utils.crypto import (
    ENV_KEY,
    CryptoConfigError,
    CryptoError,
    decrypt,
    encrypt,
)


@pytest.fixture
def fernet_key(monkeypatch):
    key = Fernet.generate_key().decode()
    monkeypatch.setenv(ENV_KEY, key)
    return key


class TestEncryptDecrypt:
    def test_roundtrip_ascii(self, fernet_key):
        token = encrypt("hello")
        assert decrypt(token) == "hello"

    def test_roundtrip_unicode(self, fernet_key):
        plain = "你好，世界 🌏"
        assert decrypt(encrypt(plain)) == plain

    def test_roundtrip_empty(self, fernet_key):
        assert decrypt(encrypt("")) == ""

    def test_token_is_ascii(self, fernet_key):
        token = encrypt("hello")
        token.encode("ascii")  # must not raise

    def test_two_encryptions_differ(self, fernet_key):
        # Fernet includes a random IV so identical plaintexts encrypt to different tokens
        assert encrypt("same") != encrypt("same")


class TestKeyMissing:
    def test_encrypt_without_key_raises(self, monkeypatch):
        monkeypatch.delenv(ENV_KEY, raising=False)
        with pytest.raises(CryptoConfigError):
            encrypt("hello")

    def test_decrypt_without_key_raises(self, monkeypatch):
        monkeypatch.delenv(ENV_KEY, raising=False)
        with pytest.raises(CryptoConfigError):
            decrypt("anything")


class TestTampered:
    def test_tampered_ciphertext_raises(self, fernet_key):
        token = encrypt("hello")
        tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
        with pytest.raises(CryptoError):
            decrypt(tampered)

    def test_wrong_key_raises(self, monkeypatch):
        monkeypatch.setenv(ENV_KEY, Fernet.generate_key().decode())
        token = encrypt("hello")
        monkeypatch.setenv(ENV_KEY, Fernet.generate_key().decode())
        with pytest.raises(CryptoError):
            decrypt(token)
