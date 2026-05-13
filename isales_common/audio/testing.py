"""In-memory implementation of :class:`RtcSession` for tests.

Loopback semantics: PCM passed to :meth:`push_audio` appears as inbound
:class:`PcmFrame` on the same session (with ``sender_uid`` set to whatever
peer-uid the session was configured with). This lets downstream tests
exercise the cloud / edge audio_pipe logic without bringing up real RTC.

For tests that need the *two-participant* setup (cloud session A pushes,
edge session B receives), use :func:`linked_pair` which returns two
sessions cross-wired so A's push lands as B's inbound and vice versa.

Not intended for production.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Self

from isales_common.audio.rtc import (
    PcmFrame,
    RtcNotJoined,
    RtcSession,
)


class InMemoryRtcSession(RtcSession):
    """One side of a loopback RTC session.

    Args:
        peer_uid: the ``sender_uid`` value attached to inbound frames. In
            real RTC this comes from the remote participant; in the in-memory
            loopback the test configures it explicitly so subscriber filters
            still exercise the right code path.
        loopback: when ``True``, frames pushed via :meth:`push_audio` are
            immediately appended to this session's own inbound queue with
            ``sender_uid=peer_uid``. When ``False``, inbound frames come
            only from :meth:`_inject` calls (used by :func:`linked_pair`).
    """

    def __init__(self, *, peer_uid: str = "peer", loopback: bool = True) -> None:
        self._peer_uid = peer_uid
        self._loopback = loopback
        self._joined = False
        self._send_sample_rate = 16000
        self._send_channels = 1
        # Bounded queue exerts mild backpressure on push_audio in tests.
        self._inbound: asyncio.Queue[PcmFrame | None] = asyncio.Queue(maxsize=256)

    async def join(
        self,
        channel: str,
        token: str,
        uid: str,
        *,
        send_sample_rate: int = 16000,
        send_channels: int = 1,
    ) -> None:
        self._joined = True
        self._send_sample_rate = send_sample_rate
        self._send_channels = send_channels

    async def leave(self) -> None:
        if not self._joined:
            return
        self._joined = False
        # Sentinel terminates any in-flight async-for over audio_frames.
        await self._inbound.put(None)

    @property
    def is_joined(self) -> bool:
        return self._joined

    async def audio_frames(self) -> AsyncIterator[PcmFrame]:
        if not self._joined:
            raise RtcNotJoined("audio_frames() called before join()")
        while True:
            frame = await self._inbound.get()
            if frame is None:
                return
            yield frame

    async def push_audio(self, pcm: bytes, *, timestamp_ms: int) -> None:
        if not self._joined:
            raise RtcNotJoined("push_audio() called before join()")
        if not self._loopback:
            return
        await self._inbound.put(
            PcmFrame(
                sender_uid=self._peer_uid,
                pcm=pcm,
                sample_rate=self._send_sample_rate,
                channels=self._send_channels,
                timestamp_ms=timestamp_ms,
            ),
        )

    # ----- helpers (not part of the ABC) -----

    async def _inject(self, frame: PcmFrame) -> None:
        """Manually push a frame to the inbound queue. Used by
        :func:`linked_pair` to cross-wire two sessions."""
        if not self._joined:
            raise RtcNotJoined("_inject() called before join()")
        await self._inbound.put(frame)


def linked_pair(
    *,
    a_uid: str,
    b_uid: str,
    sample_rate: int = 16000,
) -> tuple[InMemoryRtcSession, InMemoryRtcSession]:
    """Build two cross-wired :class:`InMemoryRtcSession` instances.

    What A pushes lands as B's inbound with ``sender_uid=a_uid``, and vice
    versa. Useful for end-to-end tests of cloud ↔ edge audio path.

    Both sessions are returned in the "not joined" state — call
    :meth:`RtcSession.join` on each before exchanging audio.
    """
    a = _LinkedHalf(peer_uid=b_uid)
    b = _LinkedHalf(peer_uid=a_uid)
    a._linked = b
    b._linked = a
    a._self_uid = a_uid
    b._self_uid = b_uid
    a._send_sample_rate = sample_rate
    b._send_sample_rate = sample_rate
    return a, b


class _LinkedHalf(InMemoryRtcSession):
    """One half of a cross-wired pair. Push lands on the other half's
    inbound queue (not its own)."""

    _linked: _LinkedHalf | None
    _self_uid: str

    def __init__(self, *, peer_uid: str) -> None:
        super().__init__(peer_uid=peer_uid, loopback=False)
        self._linked = None
        self._self_uid = ""

    async def push_audio(self, pcm: bytes, *, timestamp_ms: int) -> None:
        if not self._joined:
            raise RtcNotJoined("push_audio() called before join()")
        if self._linked is None or not self._linked._joined:
            return  # peer hasn't joined yet — drop silently (same as RTC)
        await self._linked._inbound.put(
            PcmFrame(
                sender_uid=self._self_uid,
                pcm=pcm,
                sample_rate=self._send_sample_rate,
                channels=self._send_channels,
                timestamp_ms=timestamp_ms,
            ),
        )


# Re-export the Self alias the type-checker pulled in.
_ = Self


__all__ = ["InMemoryRtcSession", "linked_pair"]
