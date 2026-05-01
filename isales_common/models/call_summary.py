"""call_summary — worker-produced summary + extracted fields per call.

Spec: data-model § call_summary; goal-achievement for goal_achieved / goal_type.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import BigInteger, Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from isales_common.models.base import Base, TimestampMixin


class CallSummary(Base, TimestampMixin):
    __tablename__ = "call_summary"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    call_record_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("call_record.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    summary_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_fields: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    goal_achieved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    goal_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
