"""engine → worker queue: "this call ended, please post-process".

Spec: service-communication § 通信通道矩阵 (engine→worker row);
      message-contract § Scenario "v1 必有的消息类".
"""

from __future__ import annotations

from datetime import datetime

from isales_common.enums import HangupCause
from isales_common.schemas.messages._base import BaseMessage


class CallEnded(BaseMessage):
    call_record_id: int
    hangup_cause: HangupCause
    ended_at: datetime
