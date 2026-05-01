"""callback_log — per-attempt record of webhook delivery.

Spec: data-model § callback_log; webhook-callback for retry semantics and
status state machine.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from isales_common.enums import CallbackStatus
from isales_common.models.base import Base, TimestampMixin


class CallbackLog(Base, TimestampMixin):
    __tablename__ = "callback_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    callback_config_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("callback_config.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    call_record_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("call_record.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    status: Mapped[CallbackStatus] = mapped_column(
        String(24), nullable=False, default=CallbackStatus.PENDING, index=True
    )
    request_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_code: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    response_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_retry_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
