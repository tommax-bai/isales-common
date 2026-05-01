"""engine → api pub/sub: real-time call event push.

Spec: service-communication § 通信通道矩阵 (engine→api row);
      message-contract § Scenario "v1 必有的消息类".

Pub/Sub semantics: occasional loss is acceptable (frontends reconcile via
DB); volume is high so payloads are kept compact.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import Field

from isales_common.enums import CallStatus, HangupCause
from isales_common.schemas.messages._base import BaseMessage


class _CallScopedEvent(BaseMessage):
    call_record_id: int


class StatusChanged(_CallScopedEvent):
    type: Literal["status_changed"] = "status_changed"
    status: CallStatus
    reason: str | None = None


class ASRPartial(_CallScopedEvent):
    type: Literal["asr_partial"] = "asr_partial"
    text: str
    timestamp_ms: int = Field(ge=0)


class ASRFinal(_CallScopedEvent):
    type: Literal["asr_final"] = "asr_final"
    text: str
    timestamp_ms: int = Field(ge=0)


class TranscriptAppended(_CallScopedEvent):
    """Notifies subscribers that a transcript event was persisted.

    The full event lives in ``call_record.transcript`` JSONB; this message
    carries only the ``ts`` and ``type`` so frontends can decide whether to
    refetch.
    """

    type: Literal["transcript_appended"] = "transcript_appended"
    event_type: str
    ts: int = Field(ge=0)


class CallStarted(_CallScopedEvent):
    type: Literal["call_started"] = "call_started"
    started_at: datetime


class CallEndedEvent(_CallScopedEvent):
    type: Literal["call_ended"] = "call_ended"
    hangup_cause: HangupCause
    ended_at: datetime


EngineEvent = Annotated[
    StatusChanged | ASRPartial | ASRFinal | TranscriptAppended | CallStarted | CallEndedEvent,
    Field(discriminator="type"),
]
