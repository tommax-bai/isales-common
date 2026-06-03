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

from isales_common.schemas._base import AppModel


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
    """Referee side-band LLM slot (enum decision JSON)."""


class ExtractorSpec(_SlotSpec):
    """Post-call extractor LLM slot (structured-fields JSON)."""


class PipelineConfig(AppModel):
    """The three resolved LLM slots for one call.

    ``short_reply_active`` carries the continuous-interruption protection flag
    through to main-prompt assembly (unchanged semantics from the old config).
    """

    main: MainSpec
    referee: RefereeSpec
    extractor: ExtractorSpec
    short_reply_active: bool = False
