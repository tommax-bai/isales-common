"""Cross-service Redis message schemas.

Spec: message-contract.

Producers MUST construct via the concrete class then ``.model_dump_json()``;
consumers MUST validate via the same class' ``.model_validate_json()`` and
gate on ``schema_version`` (see :func:`is_supported_version`).
"""

from __future__ import annotations

from isales_common.schemas.messages._base import BaseMessage
from isales_common.schemas.messages.call_lifecycle import CallEnded
from isales_common.schemas.messages.campaign_control import (
    CampaignControl,
    PauseCampaign,
    ResumeCampaign,
    StartCampaign,
)
from isales_common.schemas.messages.dial import (
    DialLeadInfo,
    DialRequest,
    HistorySummary,
    PromptVersionRef,
    PromptVersionsSnapshot,
)
from isales_common.schemas.messages.engine_control import (
    EngineControl,
    ManualHangup,
    TransferCommand,
)
from isales_common.schemas.messages.engine_event import (
    ASRFinal,
    ASRPartial,
    CallEndedEvent,
    CallStarted,
    EngineEvent,
    StatusChanged,
    TranscriptAppended,
)

#: The producer-side schema_version emitted by this build of isales-common.
#: Bump (and tag a new release) when a breaking change is introduced.
CURRENT_SCHEMA_VERSION = 1

#: Versions a consumer in this build accepts. Anything outside MUST go to a
#: dead-letter queue (see ``message-contract`` § Scenario "consumer 校验
#: schema_version").
SUPPORTED_SCHEMA_VERSIONS = frozenset({1})


def is_supported_version(schema_version: int) -> bool:
    return schema_version in SUPPORTED_SCHEMA_VERSIONS


__all__ = [
    "ASRFinal",
    "ASRPartial",
    "BaseMessage",
    "CURRENT_SCHEMA_VERSION",
    "CallEnded",
    "CallEndedEvent",
    "CallStarted",
    "CampaignControl",
    "DialLeadInfo",
    "DialRequest",
    "EngineControl",
    "EngineEvent",
    "HistorySummary",
    "ManualHangup",
    "PauseCampaign",
    "PromptVersionRef",
    "PromptVersionsSnapshot",
    "ResumeCampaign",
    "SUPPORTED_SCHEMA_VERSIONS",
    "StartCampaign",
    "StatusChanged",
    "TranscriptAppended",
    "TransferCommand",
    "is_supported_version",
]
