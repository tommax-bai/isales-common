"""provider_credential — admin-managed encrypted credential rows.

Spec: data-model § provider_credential; provider-credential capability.

每行一个 ``(provider_id, field_name)`` 字段，cipher_text 存 Fernet
urlsafe base64 cipher (由 :mod:`isales_common.utils.crypto` /
:class:`isales_common.credentials.CredentialStore` 加解密)。``updated_by``
存 JWT ``sub`` claim (项目无独立 user 表，故不设 FK)。
"""

from __future__ import annotations

from sqlalchemy import BigInteger, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from isales_common.models.base import Base, TimestampMixin


class ProviderCredential(Base, TimestampMixin):
    __tablename__ = "provider_credential"
    __table_args__ = (
        UniqueConstraint(
            "provider_id", "field_name", name="uq_provider_credential_provider_field"
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    provider_id: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
    )
    field_name: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )
    cipher_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    updated_by: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )
