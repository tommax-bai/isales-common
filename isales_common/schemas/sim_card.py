"""DTOs for sim_card."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import Field

from isales_common.enums import SimCardStatus
from isales_common.schemas._base import AppModel, ORMModel


class SimCardBase(AppModel):
    iccid: str = Field(min_length=1, max_length=32)
    imsi: str | None = None
    phone_number: str | None = None
    carrier: str | None = None
    plan: str | None = None
    balance: Decimal | None = None
    signal_strength: int | None = Field(default=None, ge=0, le=31)


class SimCardCreate(SimCardBase):
    pass


class SimCardUpdate(AppModel):
    imsi: str | None = None
    phone_number: str | None = None
    carrier: str | None = None
    plan: str | None = None
    balance: Decimal | None = None
    signal_strength: int | None = Field(default=None, ge=0, le=31)
    status: SimCardStatus | None = None
    last_checked_at: datetime | None = None


class SimCardRead(SimCardBase, ORMModel):
    id: int
    status: SimCardStatus
    last_checked_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
