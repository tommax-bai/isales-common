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
from isales_common.schemas.jsonb import (
    ExtractionField,
    InterruptionRule,
    RoutingRule,
    TimeWindow,
    ToolConfig,
)


class CampaignBase(AppModel):
    name: str = Field(min_length=1, max_length=255)
    voice_id: str | None = Field(default=None, max_length=128)

    default_replies: list[str] = Field(default_factory=list)
    concurrency: int = Field(ge=1)
    time_windows: list[TimeWindow] = Field(default_factory=list)
    extraction_fields: list[ExtractionField] = Field(default_factory=list)

    # multi-referee routing (engine-multi-referee-and-restructure D3/D4/D5).
    routing_rules: list[RoutingRule] = Field(default_factory=list)
    max_continuous_restructure: int = Field(default=2, ge=0)
    # auto_restructure_on_interrupt (engine-auto-restructure-on-interrupt): when ON,
    # a barge-in-interrupted turn with no explicit routing-rule match resumes the
    # cut-off line (restructure) instead of replying. Off by default.
    auto_restructure_on_interrupt: bool = False

    # gating + multi-persona (engine-tools-multidialogue-gating). tools: alias →
    # hangup/transfer config; persona_fanout_cap: total speculative routes incl
    # main, clamp [1,3]; referee_timeout_ms: gating timeout; referee_fail_open_route:
    # route released on gate timeout/invalid/low-confidence.
    tools: dict[str, ToolConfig] = Field(default_factory=dict)
    persona_fanout_cap: int = Field(default=1, ge=1, le=3)
    referee_timeout_ms: int = Field(default=600, gt=0)
    referee_fail_open_route: str = Field(default="main", min_length=1, max_length=64)

    # silence-activation
    max_silence_activations: int = Field(ge=0)
    silence_threshold_ms: int = Field(ge=0)
    silence_phrases: list[str] = Field(default_factory=list)
    silence_hangup_phrase: str | None = None

    # wrap-up
    wrap_up_max_rounds: int = Field(ge=0)
    wrap_up_max_seconds: int = Field(ge=0)
    wrap_up_closing_phrases: list[str] = Field(default_factory=list)
    # engine-wrap-up-silence-hangup: WRAPPING_UP-phase user-silence hangup window.
    wrap_up_silence_hangup_ms: int = Field(default=6000, ge=0)
    # engine-wrap-up-bypass-referee: opt-in wrap-up done-detection referee.
    wrap_up_referee_enabled: bool = False

    # greeting (fixed-template branch of ai-pipeline § "开场白不走管线"). NULL
    # falls back to the LLM-generated greeting path.
    greeting: str | None = None

    # filler opt-in (pipeline-stream-and-referee). Off by default — streaming
    # main link reaches first audio in ~500ms.
    filler_enabled: bool = False

    # filler time-gate (tts-cache-and-gated-filler). NULL → engine default
    # 600ms. Only play a filler when first audio hasn't started within this.
    filler_delay_ms: int | None = None

    # filler phrases — flat per-campaign pool (filler-campaign-column), edited as
    # a semicolon-separated input like interruption_whitelist.
    filler_phrases: list[str] = Field(default_factory=list)

    # asr endpoint silence threshold (pipeline-latency-tail § A). NULL → engine
    # default 400ms.
    asr_eos_silence_ms: int | None = None

    # ambient background mix (engine-ambient-background-mix). ambient_audio: a
    # background-noise asset identifier; NULL/empty → off (outbound unchanged).
    # ambient_gain: linear mix level for the background relative to TTS
    # (0.1 ≈ -20dB), kept low to limit echo back into the caller's mic/ASR.
    ambient_audio: str | None = Field(default=None, max_length=128)
    ambient_gain: float = Field(default=0.1, ge=0.0, le=1.0)

    # interruption-detection
    # interruption_rules: composable barge-in rule tree (engine-interruption-rule-
    # tree). NULL → engine synthesizes a backward-compat default tree from
    # interruption_whitelist + interruption_min_duration_ms (legacy columns,
    # removal tracked for a followup once campaigns migrate to explicit trees).
    interruption_rules: InterruptionRule | None = None
    interruption_whitelist: list[str] = Field(default_factory=list)
    interruption_min_duration_ms: int = Field(ge=0)
    # min rune count for the NULL-rule default tree's length leaf; default 2 keeps
    # legacy behavior byte-for-byte. Only read by engine when interruption_rules is NULL.
    interruption_min_chars: int = Field(default=2, ge=1)
    max_continuous_interruptions: int = Field(ge=0)
    continuous_interruption_strategy: ContinuousInterruptionStrategy
    # barge-in fade-out window in ms (engine-barge-in-fade-out). On a barge-in
    # the still-buffered AI voice is ramped down over this window instead of
    # hard-cut to silence. ~100ms = human trail-off; 15-30ms only declicks; 0 =
    # legacy hard cut.
    barge_in_fadeout_ms: int = Field(default=100, ge=0)

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

    # time-window
    respect_holidays: bool


class CampaignCreate(CampaignBase):
    pass


class CampaignUpdate(AppModel):
    """All fields optional — patch semantics."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    voice_id: str | None = Field(default=None, max_length=128)
    default_replies: list[str] | None = None
    concurrency: int | None = Field(default=None, ge=1)
    time_windows: list[TimeWindow] | None = None
    extraction_fields: list[ExtractionField] | None = None
    routing_rules: list[RoutingRule] | None = None
    max_continuous_restructure: int | None = Field(default=None, ge=0)
    auto_restructure_on_interrupt: bool | None = None
    tools: dict[str, ToolConfig] | None = None
    persona_fanout_cap: int | None = Field(default=None, ge=1, le=3)
    referee_timeout_ms: int | None = Field(default=None, gt=0)
    referee_fail_open_route: str | None = Field(default=None, min_length=1, max_length=64)
    max_silence_activations: int | None = None
    silence_threshold_ms: int | None = None
    silence_phrases: list[str] | None = None
    silence_hangup_phrase: str | None = None
    asr_eos_silence_ms: int | None = None
    ambient_audio: str | None = Field(default=None, max_length=128)
    ambient_gain: float | None = Field(default=None, ge=0.0, le=1.0)
    filler_delay_ms: int | None = None
    filler_phrases: list[str] | None = None
    wrap_up_max_rounds: int | None = None
    wrap_up_max_seconds: int | None = None
    wrap_up_closing_phrases: list[str] | None = None
    wrap_up_silence_hangup_ms: int | None = None
    wrap_up_referee_enabled: bool | None = None
    greeting: str | None = None
    interruption_rules: InterruptionRule | None = None
    interruption_whitelist: list[str] | None = None
    interruption_min_duration_ms: int | None = None
    interruption_min_chars: int | None = Field(default=None, ge=1)
    max_continuous_interruptions: int | None = None
    continuous_interruption_strategy: ContinuousInterruptionStrategy | None = None
    barge_in_fadeout_ms: int | None = Field(default=None, ge=0)
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
    respect_holidays: bool | None = None


class CampaignRead(CampaignBase, ORMModel):
    id: int
    created_at: datetime
    updated_at: datetime
