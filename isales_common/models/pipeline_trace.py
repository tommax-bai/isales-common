"""pipeline_trace — per-turn detail of the dual-LLM pipeline.

Spec: transcript § pipeline_trace; ai-pipeline for stage semantics.

One row per (call_record_id, turn_id). Stored separately from
``call_record.transcript`` so debug detail does not pollute operator views.

pipeline-stream-and-referee: the three-layer role_candidates / judge_results /
polish_* field set is replaced by main_* (streaming reply) + referee_*
(side-band decision) + first_audio_ms (latency monitoring).

engine-multi-referee-and-restructure: the single referee_* fields are replaced
by ``referee_results`` (JSONB array, one element per referee) + ``matched_rule``
(the routing rule that won) + restructure_* (which re-voice turn, if any).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    PrimaryKeyConstraint,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from isales_common.models.base import Base, TimestampMixin


class PipelineTrace(Base, TimestampMixin):
    __tablename__ = "pipeline_trace"
    __table_args__ = (PrimaryKeyConstraint("call_record_id", "turn_id"),)

    call_record_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("call_record.id", ondelete="CASCADE"), nullable=False
    )
    turn_id: Mapped[int] = mapped_column(Integer, nullable=False)

    ts_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ts_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user_input: Mapped[str | None] = mapped_column(Text, nullable=True)

    # main LLM (streaming text reply, aggregated from sentence splitter output).
    main_reply_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    main_duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    main_tokens_in: Mapped[int | None] = mapped_column(Integer, nullable=True)
    main_tokens_out: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # True when chat_stream failed mid-turn and the non-streaming chat() one-shot
    # fallback was used (pipeline-remove-streaming-fallback removal trigger).
    main_fallback_used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # referee LLMs (N side-band judges run in parallel to main TTS playback).
    # Each element: {label, category, confidence, duration_ms}; category carries
    # the referee prompt's enum value or a fail-open marker
    # ("timeout"/"invalid"/"low_confidence").
    referee_results: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    # The routing rule the decider matched this turn ({referee, match, action}),
    # or NULL when no rule matched (→ continue).
    matched_rule: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    # restructure turn record (engine-multi-referee-and-restructure).
    restructure_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # one of "last_reply" / "interrupt_remaining" / "low_confidence".
    restructure_trigger: Mapped[str | None] = mapped_column(String(32), nullable=True)
    restructure_source_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Latency monitoring: ms from PROCESSING entry to first PCM chunk played.
    first_audio_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Populated when the turn errored (main + fallback both failed, etc.).
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
