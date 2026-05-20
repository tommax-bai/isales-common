"""appointment — in-store visit booking.

Spec: data-model § appointment; appointment capability for lifecycle.

An ``appointment`` is created from the admin UI (typically from an interested
call record). It binds to a single ``lead`` and optionally references the
``call_record`` it was created from. Lead-status side-effects (``appointed``
on create, ``visited`` on complete) are managed at the API service layer
within the same DB transaction — see ``appointment`` spec § "Appointment 与
Lead 的状态联动".
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from isales_common.enums import AppointmentStatus
from isales_common.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from isales_common.models.call_record import CallRecord
    from isales_common.models.lead import Lead


class Appointment(Base, TimestampMixin):
    __tablename__ = "appointment"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    lead_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("lead.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_from_call_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("call_record.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    appointment_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    status: Mapped[AppointmentStatus] = mapped_column(
        String(16),
        nullable=False,
        default=AppointmentStatus.PENDING,
        index=True,
    )
    store_address: Mapped[str] = mapped_column(Text, nullable=False)
    directions: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    lead: Mapped["Lead"] = relationship("Lead", lazy="joined")
    created_from_call: Mapped["CallRecord | None"] = relationship(
        "CallRecord",
        lazy="joined",
    )
