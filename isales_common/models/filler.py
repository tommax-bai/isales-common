"""filler_set + filler_phrase — pre-recorded conversational fillers.

Spec: data-model § filler_set / filler_phrase; filler for selection rules.
"""

from __future__ import annotations

from sqlalchemy import BigInteger, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from isales_common.enums import GenerationStatus
from isales_common.models.base import Base, TimestampMixin


class FillerSet(Base, TimestampMixin):
    __tablename__ = "filler_set"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    campaign_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("campaign.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class FillerPhrase(Base, TimestampMixin):
    __tablename__ = "filler_phrase"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    filler_set_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("filler_set.id", ondelete="CASCADE"), nullable=False, index=True
    )
    phrase: Mapped[str] = mapped_column(String(512), nullable=False)
    audio_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    generation_status: Mapped[GenerationStatus] = mapped_column(
        String(16), nullable=False, default=GenerationStatus.PENDING
    )
