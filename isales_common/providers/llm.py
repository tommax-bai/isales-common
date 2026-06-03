"""LLM provider abstract base class.

Spec: provider-abc § Requirement: LLM Provider chat 接口与 JSON Mode.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from isales_common.providers._models import LLMResponse, Message


class LLMProvider(ABC):
    """Chat-style LLM contract.

    ``json_mode`` is a first-class parameter on ``chat`` (referee + extractor
    need structured output). Implementations MUST enable the vendor's native
    JSON mode when available, or use system-prompt + post-validation as an
    equivalent fallback; they MUST NOT silently ignore the flag.

    ``chat_stream`` (pipeline-stream-and-referee) yields plain-text content
    deltas over SSE for the main streaming reply path. After the stream
    completes, implementations SHOULD populate ``last_call_tokens_in`` /
    ``last_call_tokens_out`` / ``last_call_finish_reason`` so the engine can
    record token usage on pipeline_trace without a second round trip.
    """

    #: Usage metadata from the most recent ``chat_stream`` call. None until the
    #: stream has been fully consumed (vendors emit usage only in the final
    #: SSE chunk); left None when the vendor does not report it.
    last_call_tokens_in: int | None = None
    last_call_tokens_out: int | None = None
    last_call_finish_reason: str | None = None

    @abstractmethod
    async def chat(
        self,
        messages: list[Message],
        *,
        json_mode: bool = False,
        temperature: float = 1.0,
        top_p: float = 1.0,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        raise NotImplementedError

    @abstractmethod
    def chat_stream(
        self,
        messages: list[Message],
        *,
        temperature: float = 1.0,
        top_p: float = 1.0,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]:
        """Stream content deltas (text chunks) over SSE.

        Returns an async iterator; each yielded ``str`` is one content delta.
        Defined as a regular method returning ``AsyncIterator[str]`` (not an
        ``async def``) so subclasses may implement it as an async generator
        while keeping the ABC signature abstract.
        """
        raise NotImplementedError
