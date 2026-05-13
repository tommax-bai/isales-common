"""Aliyun-RTC-style session ABC.

Spec: device-hardware § Requirement: audio-bridge 组件;
      device-hardware § Requirement: 云端 engine 的 ARTC SDK 接入;
      service-communication § Requirement: 云-边媒体面 (阿里 RTC PaaS).

A single :class:`RtcSession` participant in one RTC channel both:

1. Subscribes to inbound PCM from remote uids (``audio_frames`` async iterator).
2. Pushes outbound PCM (``push_audio``).

Cloud and edge are SYMMETRIC participants — both implement / use this same
ABC. They just point ``uid_remote_filter`` at each other:

- Cloud engine joins as ``"engine-{call_id}"``, subscribes filtering on
  ``"edge-{call_id}"``.
- Edge audio-bridge joins as ``"edge-{call_id}"``, subscribes filtering on
  ``"engine-{call_id}"``.

Both push raw PCM 16-bit / mono. Sample rate negotiated at ``join`` time;
the SDK does internal resampling if it differs from RTC channel format.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass

# =============================================================================
# Data types
# =============================================================================


@dataclass(frozen=True)
class PcmFrame:
    """One inbound audio frame from a remote participant.

    ``sender_uid`` lets multi-uid channels route frames; callers SHOULD ignore
    frames whose sender is not the expected peer (defence in depth — see
    Decision 2 in arch-cloud-edge-split design, "AudioFormatPcmBeforMixing"
    subscription with uid filtering).

    ``timestamp_ms`` is the SDK-supplied capture timestamp at the sender,
    useful for jitter buffer logic in the engine; not load-bearing for
    correctness.
    """

    sender_uid: str
    pcm: bytes
    sample_rate: int = 16000
    channels: int = 1
    timestamp_ms: int = 0


# =============================================================================
# Errors
# =============================================================================


class RtcError(Exception):
    """Base class for RTC media-plane failures.

    Distinct from :class:`isales_common.providers._errors.ProviderError` —
    RTC failures recover via SDK-internal ICE renegotiation, not via
    provider fallback. If recovery exceeds the SDK's internal timeout,
    the session signals end-of-call (callers SHOULD hang up the modem).
    """


class RtcNotJoined(RtcError):
    """Raised when :meth:`RtcSession.push_audio` or
    :meth:`RtcSession.audio_frames` is called before :meth:`RtcSession.join`
    completes, or after :meth:`RtcSession.leave` returns.
    """


class RtcPushBackpressure(RtcError):
    """Raised when the SDK's outbound buffer is full and the caller did not
    pause pushing.

    The right response is to drain (await an SDK ``OnPushAudioFrameBufferFull``
    drained signal) before retrying. Concrete implementations MAY also expose
    this as a non-exceptional signal — see ``RtcSession.outbound_drain()``.
    """


# =============================================================================
# Session ABC
# =============================================================================


class RtcSession(ABC):
    """One participant in one RTC channel.

    Lifecycle::

        sess = ConcreteRtcSession(...)
        await sess.join(channel="call-123", token="...", uid="engine-call-123")

        # Inbound PCM:
        async for frame in sess.audio_frames():
            if frame.sender_uid == "edge-call-123":
                feed_to_asr(frame.pcm)

        # Outbound PCM (typically a separate task):
        async for tts_chunk in tts_stream:
            await sess.push_audio(tts_chunk, timestamp_ms=now_ms())

        await sess.leave()
    """

    # ----- lifecycle -----

    @abstractmethod
    async def join(
        self,
        channel: str,
        token: str,
        uid: str,
        *,
        send_sample_rate: int = 16000,
        send_channels: int = 1,
    ) -> None:
        """Join the named RTC channel as ``uid``.

        Args:
            channel: RTC channel id; for iSales calls this equals the
                ``call_id`` from :class:`DialCommand`.
            token: short-lived RTC token signed with the AppKey. Cloud-side
                callers generate it themselves; edge-side callers receive it
                via :class:`Cloud2Edge.DialCommand`.
            uid: this participant's RTC user id.
            send_sample_rate: rate of PCM passed to :meth:`push_audio`.
                The SDK may resample internally if RTC channel uses a
                different rate.
            send_channels: 1 (mono) is the iSales default.

        Returns once the SDK reports the channel is joined. Raises
        :class:`RtcError` on auth / network failure.
        """
        raise NotImplementedError

    @abstractmethod
    async def leave(self) -> None:
        """Leave the channel; release SDK resources.

        Idempotent. After :meth:`leave`, further :meth:`push_audio` calls
        raise :class:`RtcNotJoined` and any active :meth:`audio_frames`
        iterator terminates.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def is_joined(self) -> bool:
        """``True`` between a successful :meth:`join` and :meth:`leave`."""
        raise NotImplementedError

    # ----- inbound PCM -----

    @abstractmethod
    def audio_frames(self) -> AsyncIterator[PcmFrame]:
        """Async iterator over inbound PCM frames.

        Yields one :class:`PcmFrame` per SDK ``OnSubscribeAudioFrame``
        callback (per-uid before-mixing format — see service-communication
        spec § "入站 PCM 订阅"). The iterator does NOT filter by sender_uid;
        callers filter explicitly (see module docstring example).

        Iterator terminates when :meth:`leave` is called or the channel
        is lost beyond SDK-internal recovery.

        Single-consumer: only one ``async for`` may be active at a time on
        a given session. Concrete implementations MAY raise if a second
        iterator is requested.
        """
        raise NotImplementedError

    # ----- outbound PCM -----

    @abstractmethod
    async def push_audio(self, pcm: bytes, *, timestamp_ms: int) -> None:
        """Push outbound PCM into the channel.

        ``pcm`` is signed 16-bit little-endian mono at ``send_sample_rate``
        from :meth:`join`. Chunk size is the caller's choice — typical
        values are 20 ms (640 bytes at 16 kHz) for streaming TTS, but the
        SDK absorbs variable chunk sizes via its internal buffer.

        Backpressure handling: if the SDK's outbound buffer fills, this
        coroutine awaits the SDK's drain signal before returning rather
        than raising. Callers therefore get natural backpressure simply
        by awaiting ``push_audio`` — no explicit drain-poll loop needed.
        Implementations that cannot await drain SHOULD raise
        :class:`RtcPushBackpressure` so callers can stall TTS chunk pull.

        Raises :class:`RtcNotJoined` if called before :meth:`join` or after
        :meth:`leave`.
        """
        raise NotImplementedError
