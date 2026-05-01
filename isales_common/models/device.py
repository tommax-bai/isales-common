"""device — physical USB GSM modem registered on the host.

Spec: data-model § device; device-hardware for status state machine.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from isales_common.enums import DeviceStatus
from isales_common.models.base import Base, TimestampMixin


class Device(Base, TimestampMixin):
    __tablename__ = "device"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    usb_port: Mapped[str | None] = mapped_column(String(128), nullable=True)
    modem_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    imei: Mapped[str | None] = mapped_column(String(32), nullable=True, unique=True, index=True)
    status: Mapped[DeviceStatus] = mapped_column(
        String(16), nullable=False, default=DeviceStatus.UNKNOWN, index=True
    )
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
