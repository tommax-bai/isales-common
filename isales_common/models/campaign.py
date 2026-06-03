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
    voice_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("voice_model.id"), nullable=True
    )

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
