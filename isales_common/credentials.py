"""provider_credential 装载 / 解密 + 掩码 + DB 批量缓存。

Spec: provider-credential capability.

包装 :mod:`isales_common.utils.crypto` 的 encrypt/decrypt，加 batch load
from DB + in-memory cache + UI mask helper。设计原则:

1. 进程启动期 ``CredentialStore.from_db(session)`` 一次性查全表 + 解密 +
   缓存到内存 dict ``{provider_id: {field_name: plaintext}}``。
2. 运行期 ``store.get(provider_id, field_name)`` O(1) 内存查询。
3. UI 暴露走 ``store.mask(plaintext)`` —— 永不回明文。
4. v1.0 不实装 live reload；UI 改 key 后必须 ``systemctl restart`` 服务。
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

from sqlalchemy import select

from isales_common.utils.crypto import CryptoError, decrypt, encrypt

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


MASK_FILL = "*" * 8


def mask(plaintext: str | None) -> str:
    """返回 UI 安全的掩码 — 前 4 + 8 个 * + 后 4 字符。

    长度 < 8 的字符串整体掩码为 ``********``，不暴露真实长度。
    None / 空串返回 ``********``。
    """
    if not plaintext or len(plaintext) < 8:
        return MASK_FILL
    return f"{plaintext[:4]}{MASK_FILL}{plaintext[-4:]}"


class CredentialStore:
    """provider 凭据的进程内只读缓存。

    通过 :meth:`from_db` 批量装载；不可变。要刷新需重新调 ``from_db``
    （v1.0 仅在 startup 调一次）。
    """

    def __init__(self, data: dict[str, dict[str, str]] | None = None) -> None:
        self._data: dict[str, dict[str, str]] = data or {}

    @classmethod
    async def from_db(cls, session: AsyncSession) -> CredentialStore:
        """从 ``provider_credential`` 表批量装载 + 解密。

        Fernet 解密失败 / 主密钥缺失会抛 ``CryptoError`` 或
        ``CryptoConfigError``；调用方决定 hard-fail 还是 fallback。
        """
        from isales_common.models.provider_credential import ProviderCredential

        rows = (await session.execute(select(ProviderCredential))).scalars().all()
        data: dict[str, dict[str, str]] = {}
        for row in rows:
            plaintext = decrypt(row.cipher_text)
            data.setdefault(row.provider_id, {})[row.field_name] = plaintext
        return cls(data)

    def get(self, provider_id: str, field_name: str) -> str | None:
        """O(1) 查询。缺失返回 None。"""
        return self._data.get(provider_id, {}).get(field_name)

    def has(self, provider_id: str) -> bool:
        return provider_id in self._data

    def fields(self, provider_id: str) -> Iterable[str]:
        return self._data.get(provider_id, {}).keys()

    def providers(self) -> Iterable[str]:
        return self._data.keys()

    def row_count(self) -> int:
        """总行数 — 用于 startup log ``credentials_loaded count=N``。"""
        return sum(len(fields) for fields in self._data.values())

    @staticmethod
    def encrypt(plaintext: str) -> str:
        """字段加密。透传到 utils.crypto.encrypt；返回 urlsafe base64 str。"""
        return encrypt(plaintext)

    @staticmethod
    def decrypt(ciphertext: str) -> str:
        """字段解密。透传到 utils.crypto.decrypt；解密失败抛 CryptoError。"""
        return decrypt(ciphertext)

    @staticmethod
    def mask(plaintext: str | None) -> str:
        return mask(plaintext)


__all__ = ["CredentialStore", "CryptoError", "mask"]
