"""handoff_task — work item dispatched to a human agent.

Spec: data-model § handoff_task; human-handoff for state machine and trigger
types.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from isales_common.enums import HandoffStatus, TransferTriggerType
from isales_common.models.base import Base, TimestampMixin


class HandoffTask(Base, TimestampMixin):
    __tablename__ = "handoff_task"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    call_record_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("call_record.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    agent_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("agent.id", ondelete="SET NULL"), nullable=True, index=True
    )
    trigger_type: Mapped[TransferTriggerType] = mapped_column(String(16), nullable=False)
    trigger_detail: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[HandoffStatus] = mapped_column(
        String(16), nullable=False, default=HandoffStatus.PENDING, index=True
    )
    picked_up_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
