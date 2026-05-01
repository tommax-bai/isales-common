"""Common base for all cross-service Redis messages.

Spec: message-contract § Requirement: 消息基类与版本字段, 序列化与可观测性.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import Field

from isales_common.schemas._base import AppModel


def _utc_now() -> datetime:
    return datetime.now(UTC)


class BaseMessage(AppModel):
    """Parent for every cross-service message body.

    Producers MUST construct via the concrete subclass, then serialise with
    ``.model_dump_json()``; consumers MUST validate the version before acting
    on the payload (see ``message-contract`` spec).
    """

    schema_version: int = 1
    message_id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=_utc_now)

    def __str__(self) -> str:
        return f"{type(self).__name__}(message_id={self.message_id})"
