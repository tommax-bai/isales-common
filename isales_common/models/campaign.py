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
    max_no_progress_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

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
    # Which referee (by label) is the "primary" judge used for the low-confidence
    # restructure fallback (D5 case c). NULL → no low-confidence restructure.
    primary_referee_label: Mapped[str | None] = mapped_column(String(64), nullable=True)

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

    # asr endpoint silence threshold (pipeline-latency-tail § A). NULL →
    # load_runtime_config uses the system default (400ms) for the ASR EOS
    # stable-silence window; lower = faster open but more likely to clip a
    # hesitating caller's pause as "done".
    asr_eos_silence_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # interruption-detection
    interruption_whitelist: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    interruption_min_duration_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=400)
    max_continuous_interruptions: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
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

    # do-not-call (under retry-followup)
    do_not_call_keywords: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    do_not_call_llm_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    do_not_call_llm_prompt_version_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("prompt_version.id", use_alter=True), nullable=True
    )

    # time-window
    respect_holidays: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
