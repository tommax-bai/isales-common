"""call_record — single call attempt with full transcript.

Spec: data-model § call_record; transcript for event schema; human-handoff for
transfer_status semantics; goal-achievement for wrap_up_started_at.

`transcript` JSONB array conforms to the transcript spec event-type enum.
`prompt_versions` JSONB snapshot pins which prompt_version_id was used per
role_config_id at call start, so the call is reproducible even after edits.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from isales_common.enums import CallStatus, TransferStatus
from isales_common.models.base import Base, TimestampMixin


class CallRecord(Base, TimestampMixin):
    __tablename__ = "call_record"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    lead_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("lead.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    campaign_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("campaign.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    caller_id: Mapped[str | None] = mapped_column(String(24), nullable=True)

    status: Mapped[CallStatus] = mapped_column(
        String(16), nullable=False, default=CallStatus.INIT, index=True
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration: Mapped[int | None] = mapped_column(Integer, nullable=True)

    transcript: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    recording_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    transfer_status: Mapped[TransferStatus] = mapped_column(
        String(24), nullable=False, default=TransferStatus.NONE
    )
    transfer_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    wrap_up_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Snapshot of {role_config_id: prompt_version_id} pinned at call start.
    # pipeline-stream-and-referee documents the JSONB shape as
    # {main_llm, referee_llm, extractor_llm, wrap_up_appended}; the DB column
    # stays free-form JSONB (no app-level schema enforcement).
    prompt_versions: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    # post-call extractor (pipeline-stream-and-referee): worker writes the
    # structured customer fields asynchronously after the call ends. Replaces
    # the engine-inline write into call_summary.extracted_fields.
    # extract_status: NULL (no extract queued) | 'pending' | 'done' | 'failed'.
    extracted: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    extract_status: Mapped[str | None] = mapped_column(String(16), nullable=True)
    extract_error: Mapped[str | None] = mapped_column(Text, nullable=True)
