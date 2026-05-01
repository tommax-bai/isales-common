"""holiday — calendar dates honored by time-window.

Spec: data-model § holiday; time-window for usage.
"""

from __future__ import annotations

from datetime import date as date_type

from sqlalchemy import BigInteger, Date, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from isales_common.models.base import Base, TimestampMixin


class Holiday(Base, TimestampMixin):
    __tablename__ = "holiday"
    __table_args__ = (UniqueConstraint("date", "region", name="holiday_date_region"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    date: Mapped[date_type] = mapped_column(Date, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    region: Mapped[str] = mapped_column(String(32), nullable=False, default="CN")
