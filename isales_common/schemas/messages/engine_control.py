"""api → engine pub/sub: real-time control commands.

Spec: service-communication § 通信通道矩阵 (api→engine row);
      message-contract § Scenario "v1 必有的消息类".

Discriminated union so consumers can ``model_validate`` an arbitrary control
message and dispatch on ``type`` without try/except chains.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field

from isales_common.schemas.messages._base import BaseMessage


class ManualHangup(BaseMessage):
    type: Literal["manual_hangup"] = "manual_hangup"
    call_record_id: int
    operator: str | None = None  # who clicked the button (audit only)


class TransferCommand(BaseMessage):
    type: Literal["transfer"] = "transfer"
    call_record_id: int
    agent_id: int


EngineControl = Annotated[
    ManualHangup | TransferCommand,
    Field(discriminator="type"),
]
