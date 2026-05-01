"""DTOs for handoff_task.

Spec: human-handoff for state machine and trigger types.
"""

from __future__ import annotations

from datetime import datetime

from isales_common.enums import HandoffStatus, TransferTriggerType
from isales_common.schemas._base import AppModel, ORMModel


class HandoffTaskCreate(AppModel):
    call_record_id: int
    trigger_type: TransferTriggerType
    trigger_detail: str | None = None


class HandoffTaskUpdate(AppModel):
    agent_id: int | None = None
    status: HandoffStatus | None = None
    picked_up_at: datetime | None = None
    completed_at: datetime | None = None


class HandoffTaskRead(ORMModel):
    id: int
    call_record_id: int
    agent_id: int | None = None
    trigger_type: TransferTriggerType
    trigger_detail: str | None = None
    status: HandoffStatus
    picked_up_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
