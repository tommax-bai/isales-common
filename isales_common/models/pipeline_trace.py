"""pipeline_trace — per-turn detail of the dual-LLM pipeline.

Spec: transcript § pipeline_trace; ai-pipeline for stage semantics.

One row per (call_record_id, turn_id). Stored separately from
``call_record.transcript`` so debug detail does not pollute operator views.

pipeline-stream-and-referee: the three-layer role_candidates / judge_results /
polish_* field set is replaced by main_* (streaming reply) + referee_*
(side-band decision) + first_audio_ms (latency monitoring).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    PrimaryKeyConstraint,
    Text,
)
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

    # referee LLM (side-band enum decision, parallel to main TTS playback).
    referee_decision: Mapped[str | None] = mapped_column(Text, nullable=True)
    referee_goal_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    referee_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    referee_duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Latency monitoring: ms from PROCESSING entry to first PCM chunk played.
    first_audio_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Populated when the turn errored (main + fallback both failed, etc.).
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
