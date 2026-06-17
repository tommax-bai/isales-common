"""campaign — top-level configuration entity.

Spec: data-model § campaign (full column list); cross-references many capability
specs (interruption-detection, silence-activation, retry-followup, time-window,
goal-achievement, filler, role-prompt, webhook-callback, transcript).
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import BigInteger, Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from isales_common.enums import ContinuousInterruptionStrategy
from isales_common.models.base import Base, TimestampMixin


class Campaign(Base, TimestampMixin):
    __tablename__ = "campaign"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    # voice_id holds the vendor speaker string directly (e.g.
    # "zh_female_xiaohe_uranus_bigtts"), typed by the admin in the campaign
    # form. Was a BigInteger FK to voice_model.id; switched to a plain string
    # (campaign-greeting-tts-preview § 4C) so voices need not be catalogued in
    # the DB — the engine passes it straight to the TTS provider as the
    # speaker, and the web 试听 sends it verbatim. NULL → TTS default speaker.
    voice_id: Mapped[str | None] = mapped_column(String(128), nullable=True)

    default_replies: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    concurrency: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    time_windows: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    extraction_fields: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)

    # silence-activation
    max_silence_activations: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    silence_threshold_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=3000)
    silence_phrases: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    silence_hangup_phrase: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # multi-referee routing (engine-multi-referee-and-restructure D3). Ordered
    # list of rules, each {referee: <label>, match: [<category>...], action: {...}}.
    # decider walks the list and the first matching rule wins. No match → continue.
    # Stored as a JSONB column (not a separate table) — same pattern as
    # default_replies; element shape validated by schemas.jsonb.RoutingRule. The
    # trigger to migrate to a real table (cross-campaign rule templates / per-rule
    # audit) is documented in design.md D3.
    routing_rules: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    # restructure (engine-multi-referee-and-restructure D4/D5). Cap on consecutive
    # restructure turns before falling back to default_replies / continuous-
    # interruption handling, so the AI doesn't sound like it's on repeat.
    max_continuous_restructure: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    # auto_restructure_on_interrupt (engine-auto-restructure-on-interrupt). When ON,
    # the decider's no-explicit-rule-match fallback on a barge-in-interrupted turn
    # (session.interrupt_remaining_text set) becomes restructure(interrupt_remaining)
    # instead of continue — i.e. resume the cut-off line when no routing rule vetoed.
    # referee + explicit rules stay the veto (first-match-wins). Off by default →
    # behavior unchanged. See ai-pipeline § 被打断自动重组开关.
    auto_restructure_on_interrupt: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    # gating + multi-persona (engine-tools-multidialogue-gating). tools: alias →
    # {type: hangup|transfer, ...} discriminated union (schemas.jsonb.tool_config);
    # referenced by routing_rules {type: tool, tool: <alias>}. persona_fanout_cap:
    # total speculative dialogue routes per turn INCLUDING main, clamped [1,3];
    # 1 = main only, no speculation (opt-in default off). referee_timeout_ms:
    # pre-reply gating timeout. referee_fail_open_route: route released on gate
    # timeout/invalid/low-confidence (default "main", already eager-buffered).
    tools: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    persona_fanout_cap: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    referee_timeout_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=600)
    referee_fail_open_route: Mapped[str] = mapped_column(
        String(64), nullable=False, default="main"
    )

    # wrap-up (goal-achievement)
    wrap_up_max_rounds: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    wrap_up_max_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    wrap_up_closing_phrases: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    # engine-wrap-up-silence-hangup: WRAPPING_UP-phase user-silence hangup. After
    # the farewell, if the customer stays silent this long the engine hangs up
    # directly (NO "你好，还在么？" reactivation — that ladder is main-phase only).
    # Deliberately longer than silence_threshold_ms (3000) to give the customer
    # thinking time after the goodbye; the wrap_up counters remain the hard cap.
    wrap_up_silence_hangup_ms: Mapped[int] = mapped_column(
        Integer, nullable=False, default=6000
    )
    # engine-wrap-up-bypass-referee: opt-in. When true, a bypass (non-gating,
    # parallel) wrap-up referee classifies the customer's post-farewell reply;
    # if it has no substantive new question the engine hangs up early instead of
    # dragging on to the counter cap. Default off → wrap-up unchanged (Slice-1
    # silence hangup + counters only). Built-in prompt/categories live in engine.
    wrap_up_referee_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    # greeting (ai-pipeline § "开场白不走管线" — fixed-template branch).
    # NULL → load_runtime_config sets fixed_greeting=None → generate_greeting
    # falls back to the LLM path; non-NULL → engine plays the literal text via
    # TTS, no LLM call.
    greeting: Mapped[str | None] = mapped_column(Text, nullable=True)

    # filler (pipeline-stream-and-referee): streaming main link reaches first
    # audio in ~500ms so filler is off by default. Opt-in for campaigns running
    # a slow main model. Removal trigger: pipeline-remove-filler (3 months
    # post-archive with no campaign enabling this).
    filler_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # filler time-gate (tts-cache-and-gated-filler). NULL → engine default
    # 600ms: only play a filler when the main reply's first audio hasn't
    # started within this window (mask a slow LLM TTFT without polluting fast
    # turns).
    filler_delay_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # filler phrases — a flat per-campaign pool stored as a JSONB list[str]
    # (filler-campaign-column), same pattern as silence_phrases /
    # interruption_whitelist. Replaces the old filler_phrase table; the engine
    # picks one at random without repeating within a call.
    filler_phrases: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)

    # asr endpoint silence threshold (pipeline-latency-tail § A). NULL →
    # load_runtime_config uses the system default (400ms) for the ASR EOS
    # stable-silence window; lower = faster open but more likely to clip a
    # hesitating caller's pause as "done".
    asr_eos_silence_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # ambient background mix (engine-ambient-background-mix). ambient_audio holds
    # a preprocessed background-noise asset identifier (basename under the
    # engine's ambient asset dir); NULL/empty → no background, the engine's
    # outbound path stays the existing pull-driven direct-push (byte-identical to
    # before this change). Non-empty → engine runs a continuous outbound mixing
    # pump that loops the asset under the TTS so the customer hears a persistent
    # room tone even between sentences. ambient_gain is the linear mix level for
    # the background relative to TTS (0.1 ≈ -20dB); low by default to limit echo
    # leaking back into the customer's mic / ASR. Default off via NULL asset.
    ambient_audio: Mapped[str | None] = mapped_column(String(128), nullable=True)
    ambient_gain: Mapped[float] = mapped_column(
        Float, nullable=False, server_default="0.1", default=0.1
    )

    # interruption-detection
    # interruption_rules: composable barge-in rule tree (engine-interruption-rule-
    # tree, port of voxen core/interruption/). NULL → engine synthesizes a
    # backward-compat default tree from interruption_whitelist +
    # interruption_min_duration_ms (legacy columns; removal tracked for a followup
    # once campaigns migrate to explicit trees). Element shape validated by
    # schemas.jsonb.InterruptionRule.
    interruption_rules: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    interruption_whitelist: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    interruption_min_duration_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=400)
    # min rune count for the NULL-rule default tree's length leaf (promoted from
    # the engine's historical hardcoded default_rule(min_text_length=2); only read
    # when interruption_rules is NULL). server_default backfills existing rows.
    interruption_min_chars: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="2", default=2
    )
    max_continuous_interruptions: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    # barge-in fade-out window (engine-barge-in-fade-out). After a barge-in the
    # engine no longer hard-cuts the AI's voice to silence (an amplitude step at
    # a frame boundary = audible click + a faster-than-human stop). Instead the
    # still-buffered TTS is ramped down over this many ms so the voice trails off
    # naturally. ~100ms reads as a human trail-off; 15-30ms only declicks; 0
    # keeps the legacy hard cut. server_default backfills existing rows.
    barge_in_fadeout_ms: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="100", default=100
    )
    continuous_interruption_strategy: Mapped[ContinuousInterruptionStrategy] = mapped_column(
        String(16), nullable=False, default=ContinuousInterruptionStrategy.SHORT_REPLY
    )

    # human-handoff (4 trigger types)
    transfer_keyword_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    transfer_keywords: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    transfer_intent_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    transfer_intent_threshold: Mapped[float | None] = mapped_column(Float, nullable=True)
    transfer_round_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    transfer_round_threshold: Mapped[int | None] = mapped_column(Integer, nullable=True)
    transfer_llm_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    transfer_llm_prompt_version_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("prompt_version.id", use_alter=True), nullable=True
    )
    transfer_phrases: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)

    # retry-followup
    retry_intervals: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    retry_max_count: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    follow_up_interval_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    follow_up_max_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # time-window
    respect_holidays: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
