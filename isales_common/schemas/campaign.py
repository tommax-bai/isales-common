"""Pydantic DTOs for the campaign table.

Spec: data-model § campaign for the full column inventory; per-capability
specs for field semantics. Embedded JSONB columns are typed via
:mod:`isales_common.schemas.jsonb`.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from isales_common.enums import ContinuousInterruptionStrategy
from isales_common.schemas._base import AppModel, ORMModel
from isales_common.schemas.jsonb import ExtractionField, TimeWindow


class CampaignBase(AppModel):
    name: str = Field(min_length=1, max_length=255)
    voice_id: int | None = None

    default_replies: list[str] = Field(default_factory=list)
    concurrency: int = Field(ge=1)
    time_windows: list[TimeWindow] = Field(default_factory=list)
    extraction_fields: list[ExtractionField] = Field(default_factory=list)

    # silence-activation
    max_silence_activations: int = Field(ge=0)
    silence_threshold_ms: int = Field(ge=0)
    silence_phrases: list[str] = Field(default_factory=list)
    silence_hangup_phrase: str | None = None
    max_no_progress_seconds: int | None = None

    # wrap-up
    wrap_up_max_rounds: int = Field(ge=0)
    wrap_up_max_seconds: int = Field(ge=0)
    wrap_up_closing_phrases: list[str] = Field(default_factory=list)

    # greeting (fixed-template branch of ai-pipeline § "开场白不走管线"). NULL
    # falls back to the LLM-generated greeting path.
    greeting: str | None = None

    # filler opt-in (pipeline-stream-and-referee). Off by default — streaming
    # main link reaches first audio in ~500ms.
    filler_enabled: bool = False

    # interruption-detection
    interruption_whitelist: list[str] = Field(default_factory=list)
    interruption_min_duration_ms: int = Field(ge=0)
    max_continuous_interruptions: int = Field(ge=0)
    continuous_interruption_strategy: ContinuousInterruptionStrategy

    # human-handoff
    transfer_keyword_enabled: bool
    transfer_keywords: list[str] = Field(default_factory=list)
    transfer_intent_enabled: bool
    transfer_intent_threshold: float | None = None
    transfer_round_enabled: bool
    transfer_round_threshold: int | None = None
    transfer_llm_enabled: bool
    transfer_llm_prompt_version_id: int | None = None
    transfer_phrases: list[str] = Field(default_factory=list)

    # retry-followup
    retry_intervals: list[int] = Field(default_factory=list)
    retry_max_count: int = Field(ge=0)
    follow_up_interval_days: int | None = None
    follow_up_max_count: int = Field(ge=0)

    # do-not-call
    do_not_call_keywords: list[str] = Field(default_factory=list)
    do_not_call_llm_enabled: bool
    do_not_call_llm_prompt_version_id: int | None = None

    # time-window
    respect_holidays: bool


class CampaignCreate(CampaignBase):
    pass


class CampaignUpdate(AppModel):
    """All fields optional — patch semantics."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    voice_id: int | None = None
    default_replies: list[str] | None = None
    concurrency: int | None = Field(default=None, ge=1)
    time_windows: list[TimeWindow] | None = None
    extraction_fields: list[ExtractionField] | None = None
    max_silence_activations: int | None = None
    silence_threshold_ms: int | None = None
    silence_phrases: list[str] | None = None
    silence_hangup_phrase: str | None = None
    max_no_progress_seconds: int | None = None
    wrap_up_max_rounds: int | None = None
    wrap_up_max_seconds: int | None = None
    wrap_up_closing_phrases: list[str] | None = None
    greeting: str | None = None
    interruption_whitelist: list[str] | None = None
    interruption_min_duration_ms: int | None = None
    max_continuous_interruptions: int | None = None
    continuous_interruption_strategy: ContinuousInterruptionStrategy | None = None
    transfer_keyword_enabled: bool | None = None
    transfer_keywords: list[str] | None = None
    transfer_intent_enabled: bool | None = None
    transfer_intent_threshold: float | None = None
    transfer_round_enabled: bool | None = None
    transfer_round_threshold: int | None = None
    transfer_llm_enabled: bool | None = None
    transfer_llm_prompt_version_id: int | None = None
    transfer_phrases: list[str] | None = None
    retry_intervals: list[int] | None = None
    retry_max_count: int | None = None
    follow_up_interval_days: int | None = None
    follow_up_max_count: int | None = None
    do_not_call_keywords: list[str] | None = None
    do_not_call_llm_enabled: bool | None = None
    do_not_call_llm_prompt_version_id: int | None = None
    respect_holidays: bool | None = None


class CampaignRead(CampaignBase, ORMModel):
    id: int
    created_at: datetime
    updated_at: datetime
