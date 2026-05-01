"""callback_config — webhook trigger + payload + retry config per campaign.

Spec: data-model § callback_config; webhook-callback for trigger DSL and rendering.

`signing_secret` is stored encrypted (see :mod:`isales_common.utils.crypto`); the
ORM column holds Fernet ciphertext, the application layer handles encrypt/decrypt.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from isales_common.models.base import Base, TimestampMixin


class CallbackConfig(Base, TimestampMixin):
    __tablename__ = "callback_config"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    campaign_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("campaign.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    trigger: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    url: Mapped[str] = mapped_column(String(1024), nullable=False)
    method: Mapped[str] = mapped_column(String(8), nullable=False, default="POST")
    headers: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    payload_template: Mapped[str] = mapped_column(Text, nullable=False)
    retry_policy: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    signing_secret: Mapped[str | None] = mapped_column(Text, nullable=True)
    timeout_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
