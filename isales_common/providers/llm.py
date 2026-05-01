"""LLM provider abstract base class.

Spec: provider-abc § Requirement: LLM Provider chat 接口与 JSON Mode.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from isales_common.providers._models import LLMResponse, Message


class LLMProvider(ABC):
    """Chat-style LLM contract.

    ``json_mode`` is a first-class parameter (ai-pipeline spec requires
    structured output for role / judge / polish LLMs). Implementations MUST
    enable the vendor's native JSON mode when available, or use system-prompt
    + post-validation as an equivalent fallback; they MUST NOT silently ignore
    the flag.
    """

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
