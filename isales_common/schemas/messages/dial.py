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


class RefereePromptVersionRef(PromptVersionRef):
    """A referee slot snapshot, tagged with its routing ``label`` so a call is
    reproducible even after the campaign's referees are re-seeded (id changes,
    label is stable — engine-multi-referee-and-restructure D1)."""

    label: str | None = None


class PersonaPromptVersionRef(PromptVersionRef):
    """A persona dialogue slot snapshot, tagged with its routing ``label``
    (engine-tools-multidialogue-gating). Mirrors ``RefereePromptVersionRef``;
    label is the stable id routing rules bind to via ``{type: route, to:...}``."""

    label: str | None = None


class PromptVersionsSnapshot(AppModel):
    """Mirrors ``call_record.prompt_versions`` JSONB shape (role-prompt spec).

    pipeline-stream-and-referee: dual-LLM slots — ``main_llm`` / ``referee_llm``
    / ``extractor_llm`` (was ``role_llms[]`` / ``judge_llm`` / ``polish_llm``).

    engine-multi-referee-and-restructure: single ``referee_llm`` → list
    ``referee_llms`` (one per configured referee); new optional ``restructure_llm``.
    """

    main_llm: PromptVersionRef | None = None
    referee_llms: list[RefereePromptVersionRef] = Field(default_factory=list)
    # engine-tools-multidialogue-gating: opt-in speculative dialogue personas.
    persona_llms: list[PersonaPromptVersionRef] = Field(default_factory=list)
    restructure_llm: PromptVersionRef | None = None
    extractor_llm: PromptVersionRef | None = None
    wrap_up_appended: bool = False


class DialRequest(BaseMessage):
    lead: DialLeadInfo
    history: list[HistorySummary] = Field(default_factory=list)
    prompt_versions: PromptVersionsSnapshot
    caller_id: str = Field(min_length=1, max_length=24)
    device_id: int
