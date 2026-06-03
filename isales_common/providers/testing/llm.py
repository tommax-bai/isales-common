"""In-memory LLM mock for unit/integration tests."""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass

from isales_common.providers._models import LLMResponse, Message
from isales_common.providers.llm import LLMProvider


@dataclass
class RecordedChatCall:
    messages: list[Message]
    json_mode: bool
    temperature: float
    top_p: float
    max_tokens: int | None


class MockLLMProvider(LLMProvider):
    """Returns scripted :class:`LLMResponse` objects in order.

    When ``responses`` is exhausted the mock keeps yielding the last entry,
    so simple tests can supply a single response.
    """

    def __init__(
        self,
        responses: list[LLMResponse] | None = None,
    ) -> None:
        self._responses = list(responses) if responses else [_default_response()]
        self.calls: list[RecordedChatCall] = []

    async def chat(
        self,
        messages: list[Message],
        *,
        json_mode: bool = False,
        temperature: float = 1.0,
        top_p: float = 1.0,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        self.calls.append(
            RecordedChatCall(
                messages=list(messages),
                json_mode=json_mode,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
            )
        )
        if len(self._responses) > 1:
            return self._responses.pop(0)
        return self._responses[0]

    async def chat_stream(
        self,
        messages: list[Message],
        *,
        temperature: float = 1.0,
        top_p: float = 1.0,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]:
        """Yield the next scripted response's content one character at a time."""
        self.calls.append(
            RecordedChatCall(
                messages=list(messages),
                json_mode=False,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
            )
        )
        resp = self._responses.pop(0) if len(self._responses) > 1 else self._responses[0]
        for ch in resp.content:
            yield ch
        self.last_call_tokens_in = resp.tokens_in
        self.last_call_tokens_out = resp.tokens_out
        self.last_call_finish_reason = resp.finish_reason


def _default_response() -> LLMResponse:
    return LLMResponse(
        content="ok",
        tokens_in=0,
        tokens_out=1,
        finish_reason="stop",
        latency_ms=0,
    )
