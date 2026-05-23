"""DTOs for provider_credential.

Spec: provider-credential capability.

Read shape 不携带明文 / cipher，仅暴露 masked 预览 + 审计 meta。
Upsert 接收明文，由 API 层加密 + upsert 行；Upsert response 仍走 Read
shape（masked），不回显明文。
"""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from isales_common.schemas._base import AppModel, ORMModel


class ProviderCredentialUpsert(AppModel):
    """POST /api/provider-credentials body。

    服务端按 ``(provider_id, field_name)`` upsert；plaintext_value 加密
    后写入 cipher_text 列。
    """

    provider_id: str = Field(min_length=1, max_length=32)
    field_name: str = Field(min_length=1, max_length=32)
    plaintext_value: str = Field(min_length=1)


class ProviderCredentialRead(ORMModel):
    """GET 响应。masked_value 由 API 层填充 — 不在 ORM 列里。"""

    id: int
    provider_id: str
    field_name: str
    masked_value: str
    updated_by: str | None
    updated_at: datetime
