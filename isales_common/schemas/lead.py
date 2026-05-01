"""DTOs for lead.

Spec: retry-followup for status state machine and retry/follow-up scheduling.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from isales_common.enums import LeadStatus
from isales_common.schemas._base import AppModel, ORMModel


class LeadBase(AppModel):
    campaign_id: int
    name: str | None = None
    phone: str = Field(min_length=1, max_length=24)
    source: str | None = None
    custom_data: dict[str, Any] = Field(default_factory=dict)


class LeadCreate(LeadBase):
    pass


class LeadUpdate(AppModel):
    name: str | None = None
    phone: str | None = None
    source: str | None = None
    custom_data: dict[str, Any] | None = None
    status: LeadStatus | None = None
    next_call_at: datetime | None = None


class LeadRead(LeadBase, ORMModel):
    id: int
    status: LeadStatus
    retry_count: int
    follow_up_count: int
    next_call_at: datetime | None = None
    last_hangup_cause: str | None = None
    created_at: datetime
    updated_at: datetime
