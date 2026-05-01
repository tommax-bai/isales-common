"""sim_card — SIM identity and balance, bound to devices via device_sim_binding.

Spec: data-model § sim_card; device-hardware for status semantics.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, Numeric, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from isales_common.enums import SimCardStatus
from isales_common.models.base import Base, TimestampMixin


class SimCard(Base, TimestampMixin):
    __tablename__ = "sim_card"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    iccid: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    imsi: Mapped[str | None] = mapped_column(String(32), nullable=True, unique=True)
    phone_number: Mapped[str | None] = mapped_column(String(24), nullable=True, index=True)
    carrier: Mapped[str | None] = mapped_column(String(32), nullable=True)
    plan: Mapped[str | None] = mapped_column(String(64), nullable=True)
    balance: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    signal_strength: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    status: Mapped[SimCardStatus] = mapped_column(
        String(16), nullable=False, default=SimCardStatus.ACTIVE
    )
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
