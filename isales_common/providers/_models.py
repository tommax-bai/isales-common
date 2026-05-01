"""Input/output models shared by ASR / TTS / LLM provider ABCs.

Spec refs:
- provider-abc § ASR Provider 异步流式接口 (ASRResult fields)
- provider-abc § LLM Provider chat 接口与 JSON Mode (Message, LLMResponse)
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from isales_common.schemas._base import AppModel

MessageRole = Literal["system", "user", "assistant"]
FinishReason = Literal["stop", "length", "content_filter", "tool_calls", "error"]


class ASRResult(AppModel):
    """One incremental output from a streaming ASR session.

    ``is_final=False`` results MUST be emitted continuously to drive
    interruption-detection (provider-abc § Scenario "中间结果驱动打断检测").
    """

    text: str
    is_final: bool
    timestamp_ms: int = Field(ge=0)


class Message(AppModel):
    """One turn in an LLM chat history."""

    role: MessageRole
    content: str


class LLMResponse(AppModel):
    """Result of a single ``LLMProvider.chat`` call."""

    content: str
    tokens_in: int = Field(ge=0)
    tokens_out: int = Field(ge=0)
    finish_reason: FinishReason
    latency_ms: int = Field(ge=0)
