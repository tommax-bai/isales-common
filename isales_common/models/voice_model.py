"""voice_model — TTS voice catalog (referenced by campaign.voice_id).

Spec: data-model § voice_model.
"""

from __future__ import annotations

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from isales_common.models.base import Base, TimestampMixin


class VoiceModel(Base, TimestampMixin):
    __tablename__ = "voice_model"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    voice_id: Mapped[str] = mapped_column(String(128), nullable=False)
    sample_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
