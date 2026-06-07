"""Schema for ``campaign.tools`` values (JSONB map: alias → tool config).

Spec: data-model § "campaign.tools 工具配置 schema"; ai-pipeline § "挂断 / 转人工
lazy tool route". engine-tools-multidialogue-gating.

A tool is a lazy route referenced by a routing rule ``{type: tool, tool: <alias>}``.
Two kinds, discriminated by ``type``:

- ``hangup``: AI proactively ends the call (cause=referee_hangup), optionally
  playing a single ``closing_phrase`` first; the dialogue reply is suppressed.
- ``transfer``: hand off to a human. Carries NO phrase field — the connecting
  phrase reuses the single source ``campaign.transfer_phrases`` via the existing
  ``_perform_handoff`` (human-handoff spec); MUST NOT introduce a second source.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field

from isales_common.schemas._base import AppModel


class HangupToolConfig(AppModel):
    """Proactive hangup tool."""

    type: Literal["hangup"] = "hangup"
    # Single sentence TTS-played before hangup; empty/None → hang up immediately
    # (no extra dialogue turn).
    closing_phrase: str | None = Field(default=None, max_length=512)
    # When True the closing_phrase may interrupt an in-flight reply; default False
    # (gating lands before audio so hangup naturally replaces the buffered reply).
    interrupt: bool = False


class TransferToolConfig(AppModel):
    """Transfer-to-human tool. No phrase field (single-source transfer_phrases)."""

    type: Literal["transfer"] = "transfer"


#: Discriminated by ``type`` — robust as a ``dict[str, ToolConfig]`` value type.
ToolConfig = Annotated[HangupToolConfig | TransferToolConfig, Field(discriminator="type")]
