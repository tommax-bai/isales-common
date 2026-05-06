"""DTOs for device."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from isales_common.enums import DeviceStatus
from isales_common.schemas._base import AppModel, ORMModel


class DeviceBase(AppModel):
    name: str = Field(min_length=1, max_length=128)
    usb_port: str | None = None
    modem_model: str | None = None
    imei: str | None = None


class DeviceCreate(DeviceBase):
    pass


class DeviceUpdate(AppModel):
    name: str | None = None
    usb_port: str | None = None
    modem_model: str | None = None
    imei: str | None = None
    status: DeviceStatus | None = None
    last_seen_at: datetime | None = None
    last_call_at: datetime | None = None


class DeviceRead(DeviceBase, ORMModel):
    id: int
    status: DeviceStatus
    last_seen_at: datetime | None = None
    last_call_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class DeviceSelectRequest(AppModel):
    """Scheduler → telephony-api: request an idle device for a campaign.

    Spec: device-hardware § /devices/select; clarify-stage2-boundaries.
    """

    campaign_id: int = Field(gt=0)


class DeviceSelectResponse(AppModel):
    """telephony-api → scheduler: the chosen device + its active SIM phone number."""

    device_id: int = Field(gt=0)
    phone_number: str = Field(min_length=1, max_length=32)
