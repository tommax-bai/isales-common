"""pipeline_trace — per-turn detail of role / judge / polish pipeline.

Spec: transcript § pipeline_trace; ai-pipeline for stage semantics.

One row per (call_record_id, turn_id). Stored separately from
``call_record.transcript`` so debug detail does not pollute operator views.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    PrimaryKeyConstraint,
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
    role_candidates: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    judge_results: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)

    polish_input: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    polish_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    polish_duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    polish_role_config_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("role_config.id", ondelete="SET NULL"), nullable=True
    )
    polish_prompt_version_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("prompt_version.id", ondelete="SET NULL"), nullable=True
    )

    final_selected_candidate_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
