"""RtcSession ABC + in-memory implementation tests.

Spec: device-hardware § Requirement: audio-bridge 组件 /
      云端 engine 的 ARTC SDK 接入.
"""

from __future__ import annotations

import asyncio

import pytest

from isales_common.audio.rtc import PcmFrame, RtcNotJoined, RtcSession
from isales_common.audio.testing import InMemoryRtcSession, linked_pair


def _silence(ms: int, *, sample_rate: int = 16000) -> bytes:
    """Generate ``ms`` of silence at the given rate (mono 16-bit)."""
    nsamples = sample_rate * ms // 1000
    return b"\x00\x00" * nsamples


# --------------------------------------------------------------------------
# ABC conformance
# --------------------------------------------------------------------------


def test_inmemory_implements_abc() -> None:
    sess = InMemoryRtcSession(peer_uid="peer")
    assert isinstance(sess, RtcSession)


# --------------------------------------------------------------------------
# Lifecycle
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_push_before_join_raises() -> None:
    sess = InMemoryRtcSession()
    with pytest.raises(RtcNotJoined):
        await sess.push_audio(_silence(20), timestamp_ms=0)


@pytest.mark.asyncio
async def test_audio_frames_before_join_raises() -> None:
    sess = InMemoryRtcSession()
    with pytest.raises(RtcNotJoined):
        async for _ in sess.audio_frames():
            pass


@pytest.mark.asyncio
async def test_join_leave_idempotent() -> None:
    sess = InMemoryRtcSession()
    await sess.join("ch", "tok", "uid")
    assert sess.is_joined is True
    await sess.leave()
    assert sess.is_joined is False
    # Second leave is a no-op.
    await sess.leave()


# --------------------------------------------------------------------------
# Single-session loopback
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_loopback_session_yields_pushed_pcm_as_inbound() -> None:
    sess = InMemoryRtcSession(peer_uid="peer-A", loopback=True)
    await sess.join("ch", "tok", "uid-self", send_sample_rate=24000)

    expected = _silence(20, sample_rate=24000)
    await sess.push_audio(expected, timestamp_ms=100)

    iterator = sess.audio_frames()
    frame = await asyncio.wait_for(anext(iterator), timeout=1.0)
    assert isinstance(frame, PcmFrame)
    assert frame.sender_uid == "peer-A"
    assert frame.pcm == expected
    assert frame.sample_rate == 24000
    assert frame.timestamp_ms == 100

    await sess.leave()


@pytest.mark.asyncio
async def test_leave_terminates_audio_frames_iterator() -> None:
    sess = InMemoryRtcSession(peer_uid="peer", loopback=False)
    await sess.join("ch", "tok", "uid")

    iterator = sess.audio_frames()

    async def consumer() -> int:
        n = 0
        async for _ in iterator:
            n += 1
        return n

    task = asyncio.create_task(consumer())
    await asyncio.sleep(0.01)  # let consumer block on the queue
    await sess.leave()
    n = await asyncio.wait_for(task, timeout=1.0)
    assert n == 0


# --------------------------------------------------------------------------
# Linked pair (cloud ↔ edge)
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_linked_pair_cross_wires_audio() -> None:
    cloud, edge = linked_pair(a_uid="engine-c1", b_uid="edge-c1")

    await cloud.join("c1", "tok-cloud", "engine-c1")
    await edge.join("c1", "tok-edge", "edge-c1")

    # Edge pushes upstream PCM (8k modem -> resampled to 16k by audio-bridge
    # in real code; here we just send 16k directly).
    await edge.push_audio(_silence(20), timestamp_ms=1)

    cloud_iter = cloud.audio_frames()
    frame_at_cloud = await asyncio.wait_for(anext(cloud_iter), timeout=1.0)
    assert frame_at_cloud.sender_uid == "edge-c1"
    assert frame_at_cloud.timestamp_ms == 1

    # Cloud pushes TTS PCM downstream.
    tts_chunk = b"\x12\x34" * 320  # 20ms at 16k mono
    await cloud.push_audio(tts_chunk, timestamp_ms=2)

    edge_iter = edge.audio_frames()
    frame_at_edge = await asyncio.wait_for(anext(edge_iter), timeout=1.0)
    assert frame_at_edge.sender_uid == "engine-c1"
    assert frame_at_edge.pcm == tts_chunk

    await cloud.leave()
    await edge.leave()


@pytest.mark.asyncio
async def test_linked_pair_push_before_peer_joins_drops_silently() -> None:
    cloud, edge = linked_pair(a_uid="engine", b_uid="edge")
    await cloud.join("ch", "tok", "engine")
    # edge has NOT joined yet — cloud's push should drop (mimicking RTC's
    # "no subscriber" behaviour) rather than raising.
    await cloud.push_audio(_silence(20), timestamp_ms=0)

    await edge.join("ch", "tok", "edge")
    # edge's inbound queue should be empty: the earlier push was dropped.
    # Now push again and we should see only the new frame.
    await cloud.push_audio(b"\xaa\xbb" * 320, timestamp_ms=10)

    edge_iter = edge.audio_frames()
    frame = await asyncio.wait_for(anext(edge_iter), timeout=1.0)
    assert frame.pcm == b"\xaa\xbb" * 320
    assert frame.timestamp_ms == 10

    await cloud.leave()
    await edge.leave()
