"""filler_phrase — pre-recorded conversational fillers, per campaign.

Spec: data-model § filler_phrase; filler for selection rules. A campaign owns a
single flat pool of filler phrases (the ``filler_set`` grouping layer was
removed in ``filler-single-pool``); the engine picks one at random without
repeating within a call.
"""

from __future__ import annotations

from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from isales_common.enums import GenerationStatus
from isales_common.models.base import Base, TimestampMixin


class FillerPhrase(Base, TimestampMixin):
    __tablename__ = "filler_phrase"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    campaign_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("campaign.id", ondelete="CASCADE"), nullable=False, index=True
    )
    phrase: Mapped[str] = mapped_column(String(512), nullable=False)
    audio_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    generation_status: Mapped[GenerationStatus] = mapped_column(
        String(16), nullable=False, default=GenerationStatus.PENDING
    )
