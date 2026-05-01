"""Contract tests for provider ABCs and their in-memory mocks.

Spec: provider-abc § Scenario "实现类必须继承 ABC", "mock 用于本地与 CI".
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest

from isales_common.providers import (
    ASRProvider,
    ASRResult,
    LLMProvider,
    LLMResponse,
    Message,
    ProviderError,
    ProviderInvalidRequest,
    ProviderRateLimited,
    ProviderServerError,
    ProviderTimeout,
    TTSProvider,
)
from isales_common.providers.testing import (
    MockASRProvider,
    MockLLMProvider,
    MockTTSProvider,
)

# ---- ABC abstractness -----------------------------------------------------


def test_abc_cannot_be_instantiated_directly():
    with pytest.raises(TypeError):
        ASRProvider()  # type: ignore[abstract]
    with pytest.raises(TypeError):
        TTSProvider()  # type: ignore[abstract]
    with pytest.raises(TypeError):
        LLMProvider()  # type: ignore[abstract]


def test_subclass_missing_method_cannot_instantiate():
    class IncompleteASR(ASRProvider):
        pass

    class IncompleteTTS(TTSProvider):
        pass

    class IncompleteLLM(LLMProvider):
        pass

    with pytest.raises(TypeError):
        IncompleteASR()  # type: ignore[abstract]
    with pytest.raises(TypeError):
        IncompleteTTS()  # type: ignore[abstract]
    with pytest.raises(TypeError):
        IncompleteLLM()  # type: ignore[abstract]


def test_mocks_satisfy_abc():
    assert isinstance(MockASRProvider(), ASRProvider)
    assert isinstance(MockTTSProvider(), TTSProvider)
    assert isinstance(MockLLMProvider(), LLMProvider)


# ---- Mock behavior --------------------------------------------------------


async def _aiter(items: list[bytes]) -> AsyncIterator[bytes]:
    for item in items:
        yield item


@pytest.mark.asyncio
async def test_mock_asr_streams_scripted_results():
    scripted = [
        ASRResult(text="he", is_final=False, timestamp_ms=100),
        ASRResult(text="hello", is_final=True, timestamp_ms=400),
    ]
    asr = MockASRProvider(scripted)
    audio = _aiter([b"\x00\x00", b"\x01\x01"])

    out = [r async for r in asr.stream_recognize(audio)]

    assert out == scripted
    assert asr.received_chunks == [b"\x00\x00", b"\x01\x01"]


@pytest.mark.asyncio
async def test_mock_tts_records_calls_and_yields_chunks():
    tts = MockTTSProvider(scripted_chunks=[b"\xaa\xaa", b"\xbb\xbb"])

    chunks = [c async for c in tts.synthesize_stream("hi", "voice-1")]

    assert chunks == [b"\xaa\xaa", b"\xbb\xbb"]
    assert tts.calls == [("hi", "voice-1")]


@pytest.mark.asyncio
async def test_mock_llm_returns_scripted_and_records_calls():
    r1 = LLMResponse(
        content='{"a":1}',
        tokens_in=1,
        tokens_out=2,
        finish_reason="stop",
        latency_ms=10,
    )
    r2 = LLMResponse(
        content="bye",
        tokens_in=3,
        tokens_out=4,
        finish_reason="stop",
        latency_ms=20,
    )
    llm = MockLLMProvider(responses=[r1, r2])

    got1 = await llm.chat(
        [Message(role="user", content="hi")],
        json_mode=True,
        temperature=0.2,
        top_p=0.9,
        max_tokens=100,
    )
    got2 = await llm.chat([Message(role="user", content="bye")])
    got3 = await llm.chat([Message(role="user", content="again")])

    assert got1 == r1
    assert got2 == r2
    assert got3 == r2  # last response is sticky once exhausted

    assert len(llm.calls) == 3
    assert llm.calls[0].json_mode is True
    assert llm.calls[0].temperature == 0.2
    assert llm.calls[0].top_p == 0.9
    assert llm.calls[0].max_tokens == 100
    assert llm.calls[1].json_mode is False  # default


# ---- Error hierarchy ------------------------------------------------------


def test_error_hierarchy():
    for cls in (
        ProviderTimeout,
        ProviderRateLimited,
        ProviderInvalidRequest,
        ProviderServerError,
    ):
        assert issubclass(cls, ProviderError)


def test_error_carries_metadata():
    err = ProviderRateLimited(
        "slow down",
        provider="openai",
        vendor_code="429",
        retry_after_seconds=2.5,
    )
    assert err.provider == "openai"
    assert err.vendor_code == "429"
    assert err.retry_after_seconds == 2.5
    assert str(err) == "slow down"
