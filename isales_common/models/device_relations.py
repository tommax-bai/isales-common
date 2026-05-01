"""device_sim_binding + campaign_device — device association tables.

Spec: data-model § device_sim_binding / campaign_device; device-hardware for usage.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from isales_common.models.base import Base, TimestampMixin, utc_now


class DeviceSimBinding(Base, TimestampMixin):
    __tablename__ = "device_sim_binding"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    device_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("device.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sim_card_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("sim_card.id", ondelete="CASCADE"), nullable=False, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    bind_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    unbind_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class CampaignDevice(Base, TimestampMixin):
    __tablename__ = "campaign_device"
    __table_args__ = (UniqueConstraint("campaign_id", "device_id", name="campaign_device_pair"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    campaign_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("campaign.id", ondelete="CASCADE"), nullable=False, index=True
    )
    device_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("device.id", ondelete="CASCADE"), nullable=False, index=True
    )
