"""Pipeline LLM-slot specs for the dual-LLM architecture.

pipeline-stream-and-referee: replaces the old ``RoleSpec / JudgeSpec /
PolishSpec / PipelineConfig`` three-layer dataclasses. The pipeline now has
exactly three slots:

- ``main``     — streaming text reply (``chat_stream``), drives TTS directly.
- ``referee``  — side-band enum decision (``chat`` json_mode), parallel to TTS.
- ``extractor``— post-call structured extraction, run offline by the worker.

These are the shared data contract. Per-call rendering inputs (lead info,
default replies, follow-up count) live in the engine's runtime layer, not here.
"""

from __future__ import annotations

from pydantic import Field

from isales_common.schemas._base import AppModel
from isales_common.schemas.jsonb import RoutingRule, ToolConfig


class _SlotSpec(AppModel):
    """Common shape of an LLM slot: which prompt_version + model params to use."""

    role_config_id: int
    prompt_version_id: int
    system_prompt: str
    model: str = "mock"
    temperature: float = 1.0
    top_p: float = 1.0


class MainSpec(_SlotSpec):
    """Main streaming LLM slot (plain-text reply, no JSON)."""


class RefereeSpec(_SlotSpec):
    """A single referee side-band LLM slot (category-decision JSON).

    engine-multi-referee-and-restructure: ``label`` is the stable id routing
    rules bind to. The referee's category enum semantics live in its prompt;
    the engine never hardcodes them.
    """

    label: str


class RestructureSpec(_SlotSpec):
    """Restructure / rewrite LLM slot — re-voices InterruptText (D4)."""

    label: str


class PersonaSpec(_SlotSpec):
    """An opt-in speculative dialogue persona slot (engine-tools-multidialogue-
    gating). ``label`` is the stable id routing rules bind to via
    ``{type: route, to: <label>}``. Runs eagerly in parallel with main; the
    referee gate selects one and cancels the rest.
    """

    label: str


class ExtractorSpec(_SlotSpec):
    """Post-call extractor LLM slot (structured-fields JSON)."""


class PipelineConfig(AppModel):
    """The resolved LLM slots + routing config for one call.

    engine-multi-referee-and-restructure: single ``referee`` → ``referees``
    list; new optional ``restructure`` slot; routing rules + restructure caps
    carried through from the campaign.

    ``short_reply_active`` carries the continuous-interruption protection flag
    through to main-prompt assembly (unchanged semantics from the old config).
    """

    main: MainSpec
    referees: list[RefereeSpec] = Field(default_factory=list)
    restructure: RestructureSpec | None = None
    extractor: ExtractorSpec
    routing_rules: list[RoutingRule] = Field(default_factory=list)
    max_continuous_restructure: int = 2
    primary_referee_label: str | None = None
    short_reply_active: bool = False

    # gating + multi-persona (engine-tools-multidialogue-gating). personas: opt-in
    # speculative dialogue slots run in parallel with main; the gate selects one.
    # tools: alias → hangup/transfer config referenced by routing rules.
    # persona_fanout_cap: total speculative routes incl main, clamp [1,3].
    personas: list[PersonaSpec] = Field(default_factory=list)
    tools: dict[str, ToolConfig] = Field(default_factory=dict)
    persona_fanout_cap: int = 1
    referee_timeout_ms: int = 600
    referee_fail_open_route: str = "main"
