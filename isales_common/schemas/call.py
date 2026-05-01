"""DTOs for call_record / call_summary / pipeline_trace.

Spec: transcript for transcript event schema and pipeline_trace fields.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from isales_common.enums import CallStatus, TransferStatus
from isales_common.schemas._base import AppModel, ORMModel
from isales_common.schemas.jsonb import (
    JudgeResult,
    PolishInput,
    RoleCandidate,
    TranscriptEvent,
)


class CallRecordRead(ORMModel):
    id: int
    lead_id: int
    campaign_id: int
    caller_id: str | None = None

    status: CallStatus
    started_at: datetime | None = None
    ended_at: datetime | None = None
    duration: int | None = None

    transcript: list[TranscriptEvent] = Field(default_factory=list)
    recording_url: str | None = None

    transfer_status: TransferStatus
    transfer_reason: str | None = None
    wrap_up_started_at: datetime | None = None

    prompt_versions: dict[str, Any] = Field(default_factory=dict)

    created_at: datetime
    updated_at: datetime


class CallSummaryRead(ORMModel):
    id: int
    call_record_id: int
    summary_text: str | None = None
    extracted_fields: dict[str, Any] = Field(default_factory=dict)
    goal_achieved: bool
    goal_type: str | None = None
    created_at: datetime
    updated_at: datetime


class CallSummaryCreate(AppModel):
    call_record_id: int
    summary_text: str | None = None
    extracted_fields: dict[str, Any] = Field(default_factory=dict)
    goal_achieved: bool = False
    goal_type: str | None = None


class PipelineTraceRead(ORMModel):
    call_record_id: int
    turn_id: int
    ts_start: datetime
    ts_end: datetime | None = None
    user_input: str | None = None
    role_candidates: list[RoleCandidate] = Field(default_factory=list)
    judge_results: list[JudgeResult] = Field(default_factory=list)
    polish_input: PolishInput | None = None
    polish_output: str | None = None
    polish_duration_ms: int | None = None
    polish_role_config_id: int | None = None
    polish_prompt_version_id: int | None = None
    final_selected_candidate_index: int | None = None
    created_at: datetime
    updated_at: datetime
