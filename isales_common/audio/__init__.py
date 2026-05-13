"""Audio transport abstractions shared by cloud and edge.

Two layers live here:

- :mod:`isales_common.utils.audio` (existing): format constants (sample
  rate enum, bytes-per-second helper). Pure data — no IO.
- :mod:`isales_common.audio.rtc` (this package's ``rtc`` module): the
  ABC for an Aliyun-RTC-style participant session that both subscribes
  to remote PCM and pushes outbound PCM.

Concrete implementations:

- isales-engine wraps the Linux ARTC SDK (server-side, in-cloud).
- isales-telephony wraps the platform-specific ARTC SDK (macOS / Windows).
- Tests use an in-memory ``InMemoryRtcSession`` that loops pushed PCM back
  as inbound frames so unit tests can exercise the multi-role PK pipeline
  without bringing up real RTC.

Spec: device-hardware § Requirement: audio-bridge 组件 / 云端 engine 的
ARTC SDK 接入. The ABC pins the contract; the spec pins the wire format.
"""

from __future__ import annotations

from isales_common.audio.rtc import (
    PcmFrame,
    RtcError,
    RtcNotJoined,
    RtcPushBackpressure,
    RtcSession,
)

__all__ = [
    "PcmFrame",
    "RtcError",
    "RtcNotJoined",
    "RtcPushBackpressure",
    "RtcSession",
]
