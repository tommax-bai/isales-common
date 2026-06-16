"""Tests for VolcengineTTSProvider over the V3 SSE protocol + the shared
``build_volcengine_tts`` constructor.

Moved here from isales-engine (campaign-greeting-tts-preview § 决策 1) when
the provider was shared into isales-common for engine + api. Uses
``httpx.MockTransport`` injected into the provider's persistent client to
verify SSE framing, ProviderError mapping, and the pipeline-latency-tail § C
connection-reuse + ``aclose()`` behavior.
"""

from __future__ import annotations

import base64
import json
from typing import Any

import httpx
import pytest

from isales_common.credentials import CredentialStore
from isales_common.providers._errors import (
    ProviderInvalidRequest,
    ProviderRateLimited,
    ProviderServerError,
)
from isales_common.providers.tts_volcengine import (
    VolcengineTTSProvider,
    build_volcengine_tts,
)


def _sse(*frames: tuple[str, dict[str, Any]]) -> bytes:
    """Build a V3 SSE byte body from (event_id, data_obj) pairs."""
    parts: list[str] = []
    for event_id, data_obj in frames:
        parts.append(f"event: {event_id}")
        parts.append(f"data: {json.dumps(data_obj)}")
        parts.append("")  # blank line = frame terminator
    return ("\n".join(parts) + "\n").encode("utf-8")


def _audio_frame(pcm: bytes) -> tuple[str, dict[str, Any]]:
    return ("352", {"code": 0, "message": "", "data": base64.b64encode(pcm).decode()})


_FINISH = ("152", {"code": 20000000, "message": "OK", "data": None})


def _provider_with(handler: Any) -> VolcengineTTSProvider:
    """Construct a provider, then swap its persistent client for one backed
    by the given MockTransport — mirrors how the real provider reuses a
    single ``self._client`` across sentences."""
    provider = VolcengineTTSProvider(api_key="key-uuid")
    transport = httpx.MockTransport(handler)
    provider._client = httpx.AsyncClient(transport=transport, timeout=5.0)
    return provider


# ---- happy path -----------------------------------------------------------


async def test_streaming_yields_pcm_chunks() -> None:
    pcm_chunks = [b"\x01\x02" * 80, b"\x03\x04" * 80, b"\x05\x06" * 80]

    def handler(request: httpx.Request) -> httpx.Response:
        body = _sse(*[_audio_frame(c) for c in pcm_chunks], _FINISH)
        return httpx.Response(200, content=body)

    provider = _provider_with(handler)
    received = [c async for c in provider.synthesize_stream("hello", "BV001")]
    assert b"".join(received) == b"".join(pcm_chunks)


async def test_request_payload_shape() -> None:
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen.update(json.loads(request.content))
        return httpx.Response(200, content=_sse(_audio_frame(b"\x00\x00"), _FINISH))

    provider = _provider_with(handler)
    [c async for c in provider.synthesize_stream("您好", "zh_female_test_uranus_bigtts")]

    assert seen["req_params"]["text"] == "您好"
    assert seen["req_params"]["speaker"] == "zh_female_test_uranus_bigtts"
    assert seen["req_params"]["audio_params"]["format"] == "pcm"
    # 情绪波动强度默认 2 (降 vendor 默认 ~4)，注入 audio_params
    assert seen["req_params"]["audio_params"]["emotion_scale"] == 2


# ---- resource_id routing by speaker family --------------------------------


async def test_standard_voice_uses_tts_resource_id() -> None:
    """A 预置/standard speaker (no ``S_`` prefix) goes to the seed-tts SKU."""
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["resource"] = request.headers["X-Api-Resource-Id"]
        return httpx.Response(200, content=_sse(_audio_frame(b"\x00\x00"), _FINISH))

    provider = _provider_with(handler)
    [c async for c in provider.synthesize_stream("您好", "zh_female_xiaohe_uranus_bigtts")]
    assert seen["resource"] == "seed-tts-2.0"


async def test_cloned_voice_routes_to_icl_resource() -> None:
    """A 声音复刻 speaker (``S_`` prefix) is routed to the seed-icl SKU even
    though the standard resource_id stays seed-tts-2.0."""
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["resource"] = request.headers["X-Api-Resource-Id"]
        return httpx.Response(200, content=_sse(_audio_frame(b"\x00\x00"), _FINISH))

    provider = _provider_with(handler)
    [c async for c in provider.synthesize_stream("您好", "S_Are7Mp342")]
    assert seen["resource"] == "seed-icl-2.0"


async def test_cloned_voice_omits_emotion_scale() -> None:
    """复刻音色 (``S_``) MUST NOT carry emotion_scale — that knob is tuned to
    flatten the standard 多情感 voice and would over-suppress the clone.
    Standard voices still carry it."""
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen.update(json.loads(request.content))
        return httpx.Response(200, content=_sse(_audio_frame(b"\x00\x00"), _FINISH))

    provider = _provider_with(handler)
    [c async for c in provider.synthesize_stream("您好", "S_Are7Mp342")]
    assert "emotion_scale" not in seen["req_params"]["audio_params"]
    assert seen["req_params"]["audio_params"]["format"] == "pcm"


# ---- error mapping --------------------------------------------------------


async def test_429_raises_rate_limited() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, json={"error": "throttled"})

    provider = _provider_with(handler)
    with pytest.raises(ProviderRateLimited):
        async for _ in provider.synthesize_stream("x", "v"):
            pass


async def test_5xx_raises_server_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"error": "vendor down"})

    provider = _provider_with(handler)
    with pytest.raises(ProviderServerError):
        async for _ in provider.synthesize_stream("x", "v"):
            pass


async def test_4xx_raises_invalid_request() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"error": "bad voice"})

    provider = _provider_with(handler)
    with pytest.raises(ProviderInvalidRequest):
        async for _ in provider.synthesize_stream("x", "v"):
            pass


async def test_session_failed_event_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body = _sse(("153", {"code": 40000001, "message": "bad speaker", "data": None}))
        return httpx.Response(200, content=body)

    provider = _provider_with(handler)
    with pytest.raises(ProviderInvalidRequest):
        async for _ in provider.synthesize_stream("x", "v"):
            pass


# ---- connection reuse (pipeline-latency-tail § C) -------------------------


async def test_reuses_same_client_across_sentences() -> None:
    """Consecutive synthesize_stream calls MUST go through the same
    persistent client (no per-sentence client rebuild)."""
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(200, content=_sse(_audio_frame(b"\x10\x11"), _FINISH))

    provider = _provider_with(handler)
    client_before = provider._client
    for sentence in ("第一句", "第二句", "第三句"):
        async for _ in provider.synthesize_stream(sentence, "v"):
            pass

    assert calls["n"] == 3
    # Same client object reused for every sentence — not rebuilt per call.
    assert provider._client is client_before
    assert provider._client.is_closed is False


async def test_aclose_releases_client() -> None:
    provider = VolcengineTTSProvider(api_key="key-uuid")
    assert provider._client.is_closed is False
    await provider.aclose()
    assert provider._client.is_closed is True


# ---- build_volcengine_tts (shared constructor) ----------------------------


# 凭据读自 volcengine_speech (split-model-and-speech-provider-config: 火山方舟
# Ark LLM 与豆包语音两条产品线两套密钥, build_volcengine_tts 只读语音 id)。
def test_build_new_console_api_key() -> None:
    store = CredentialStore({"volcengine_speech": {"api_key": "uuid-key"}})
    provider = build_volcengine_tts(store)
    assert isinstance(provider, VolcengineTTSProvider)
    assert provider._api_key == "uuid-key"


def test_build_legacy_app_key_token() -> None:
    store = CredentialStore(
        {"volcengine_speech": {"app_key": "k", "app_token": "t"}}
    )
    provider = build_volcengine_tts(store)
    assert isinstance(provider, VolcengineTTSProvider)
    assert provider._app_id == "k"
    assert provider._access_key == "t"


def test_build_missing_credentials_raises_invalid_request() -> None:
    """No credentials configured → ProviderInvalidRequest (so callers can
    surface a 4xx, not a 500)."""
    with pytest.raises(ProviderInvalidRequest, match="not configured"):
        build_volcengine_tts(CredentialStore())


def test_build_ignores_volcengine_llm_credentials() -> None:
    """volcengine (Ark LLM) 的 api_key 是 ark key, 绝不能被语音 TTS 读到 —— 只
    配 volcengine 没配 volcengine_speech 时, TTS 应报 not configured。"""
    store = CredentialStore({"volcengine": {"api_key": "ark-llm-key"}})
    with pytest.raises(ProviderInvalidRequest, match="not configured"):
        build_volcengine_tts(store)


def test_build_resource_id_override() -> None:
    store = CredentialStore(
        {"volcengine_speech": {"api_key": "k", "tts_resource_id": "seed-icl-2.0"}}
    )
    provider = build_volcengine_tts(store)
    assert provider._resource_id == "seed-icl-2.0"
