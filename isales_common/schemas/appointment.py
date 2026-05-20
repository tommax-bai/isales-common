"""DTOs for appointment.

Spec: appointment for lifecycle and state-machine.

Status mutations MUST go through ``AppointmentStatusAction`` against the
``PATCH /api/appointments/{id}/status`` endpoint; ``AppointmentUpdate`` does
not expose ``status`` to prevent clients from bypassing the state machine.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from isales_common.enums import AppointmentAction, AppointmentStatus
from isales_common.schemas._base import AppModel, ORMModel


class AppointmentBase(AppModel):
    lead_id: int
    appointment_time: datetime
    store_address: str = Field(min_length=1)
    directions: str = Field(min_length=1)
    notes: str | None = None
    created_from_call_id: int | None = None


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentUpdate(AppModel):
    """Edit non-status fields. Status changes use AppointmentStatusAction."""

    appointment_time: datetime | None = None
    store_address: str | None = None
    directions: str | None = None
    notes: str | None = None


class AppointmentStatusAction(AppModel):
    action: AppointmentAction


class AppointmentRead(AppointmentBase, ORMModel):
    id: int
    status: AppointmentStatus
    created_at: datetime
    updated_at: datetime
    # Denormalized join fields for UI convenience — populated by API layer.
    lead_name: str | None = None
    lead_phone: str | None = None
