"""Unit tests for isales_common.credentials (CredentialStore + mask).

DB-backed from_db() 留给 isales-api / isales-engine 集成测试。这里仅覆盖
进程内行为 (mask / get / has / fields / providers / row_count) 以及
encrypt/decrypt 包装的 round-trip。
"""
from __future__ import annotations

import pytest
from cryptography.fernet import Fernet

from isales_common.credentials import CredentialStore, mask
from isales_common.utils.crypto import ENV_KEY


@pytest.fixture
def fernet_key(monkeypatch):
    monkeypatch.setenv(ENV_KEY, Fernet.generate_key().decode())


class TestMask:
    def test_short_string_full_mask(self):
        assert mask("abc") == "*" * 8
        assert mask("1234567") == "*" * 8  # 7 chars - 边界 < 8

    def test_exactly_8_chars_keeps_first_and_last_4(self):
        assert mask("abcd1234") == "abcd" + "*" * 8 + "1234"

    def test_long_string(self):
        assert mask("sk-1234567890abcdef") == "sk-1" + "*" * 8 + "cdef"

    def test_empty_string(self):
        assert mask("") == "*" * 8

    def test_none(self):
        assert mask(None) == "*" * 8

    def test_unicode(self):
        # 中文字 4 + 8 + 4 字符规则不变
        assert mask("中文测试abcdefgh") == "中文测试" + "*" * 8 + "efgh"


class TestStoreInMemory:
    def test_empty_store(self):
        s = CredentialStore()
        assert s.get("volcengine", "app_key") is None
        assert s.has("volcengine") is False
        assert list(s.providers()) == []
        assert s.row_count() == 0

    def test_populated_store(self):
        s = CredentialStore(
            {
                "volcengine": {"app_key": "vc-key", "app_token": "vc-tok"},
                "dashscope": {"api_key": "sk-test"},
            }
        )
        assert s.get("volcengine", "app_key") == "vc-key"
        assert s.get("volcengine", "app_token") == "vc-tok"
        assert s.get("dashscope", "api_key") == "sk-test"
        assert s.get("dashscope", "missing") is None
        assert s.get("unknown_provider", "any") is None
        assert s.has("volcengine") is True
        assert s.has("unknown_provider") is False
        assert set(s.providers()) == {"volcengine", "dashscope"}
        assert set(s.fields("volcengine")) == {"app_key", "app_token"}
        assert s.row_count() == 3


class TestEncryptDecryptWrapping:
    def test_static_round_trip(self, fernet_key):
        cipher = CredentialStore.encrypt("plaintext")
        assert CredentialStore.decrypt(cipher) == "plaintext"

    def test_static_mask(self, fernet_key):
        assert CredentialStore.mask("sk-1234567890ab") == "sk-1" + "*" * 8 + "90ab"
