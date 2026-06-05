"""DTOs for call_record / call_summary / pipeline_trace.

Spec: transcript for transcript event schema and pipeline_trace fields.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from isales_common.enums import CallStatus, TransferStatus
from isales_common.schemas._base import AppModel, ORMModel
from isales_common.schemas.jsonb import TranscriptEvent


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

    # post-call extractor (pipeline-stream-and-referee).
    extracted: dict[str, Any] | None = None
    extract_status: str | None = None
    extract_error: str | None = None

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

    # main streaming LLM.
    main_reply_text: str | None = None
    main_duration_ms: int | None = None
    main_tokens_in: int | None = None
    main_tokens_out: int | None = None
    main_fallback_used: bool = False

    # referee side-band LLMs (N parallel judges) + routing decision.
    referee_results: list[Any] = Field(default_factory=list)
    matched_rule: dict[str, Any] | None = None

    # restructure (re-voice) turn record.
    restructure_active: bool = False
    restructure_trigger: str | None = None
    restructure_source_text: str | None = None

    first_audio_ms: int | None = None
    error: str | None = None

    created_at: datetime
    updated_at: datetime
