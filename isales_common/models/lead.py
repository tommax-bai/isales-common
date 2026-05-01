"""lead — call target with retry / follow-up state.

Spec: data-model § lead; retry-followup for status state machine and
retry/follow-up scheduling.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from isales_common.enums import LeadStatus
from isales_common.models.base import Base, TimestampMixin


class Lead(Base, TimestampMixin):
    __tablename__ = "lead"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    campaign_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("campaign.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    phone: Mapped[str] = mapped_column(String(24), nullable=False, index=True)
    source: Mapped[str | None] = mapped_column(String(64), nullable=True)
    custom_data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    status: Mapped[LeadStatus] = mapped_column(
        String(24), nullable=False, default=LeadStatus.NEW, index=True
    )
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    follow_up_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    next_call_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    last_hangup_cause: Mapped[str | None] = mapped_column(String(64), nullable=True)
