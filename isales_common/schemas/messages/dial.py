"""scheduler → engine queue: "dial this lead".

Spec: service-communication § 通信通道矩阵 (scheduler→engine row);
      message-contract § Scenario "v1 必有的消息类".

Snapshots all data the engine needs to start a call without further DB reads:
lead context, prior-call summaries, prompt versions in effect at dispatch
time, and the chosen device / caller_id.
"""

from __future__ import annotations

from typing import Any

from pydantic import Field

from isales_common.schemas._base import AppModel
from isales_common.schemas.messages._base import BaseMessage


class DialLeadInfo(AppModel):
    lead_id: int
    campaign_id: int
    phone: str = Field(min_length=1, max_length=24)
    name: str | None = None
    custom_data: dict[str, Any] = Field(default_factory=dict)


class HistorySummary(AppModel):
    """One prior-call summary surfaced to the engine for context.

    The schema is intentionally minimal — full transcript / summary text
    lives in PostgreSQL; this is what the LLM gets at greeting time.
    """

    call_record_id: int
    summary: str
    ended_at: str  # ISO-8601 to keep payload diff-friendly


class PromptVersionRef(AppModel):
    role_config_id: int
    prompt_version_id: int


class PromptVersionsSnapshot(AppModel):
    """Mirrors ``call_record.prompt_versions`` JSONB shape (role-prompt spec)."""

    role_llms: list[PromptVersionRef] = Field(default_factory=list)
    judge_llm: PromptVersionRef | None = None
    polish_llm: PromptVersionRef | None = None
    wrap_up_appended: bool = False


class DialRequest(BaseMessage):
    lead: DialLeadInfo
    history: list[HistorySummary] = Field(default_factory=list)
    prompt_versions: PromptVersionsSnapshot
    caller_id: str = Field(min_length=1, max_length=24)
    device_id: int
