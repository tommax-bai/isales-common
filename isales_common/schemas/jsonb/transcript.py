"""Schema for ``call_record.transcript`` JSONB array elements.

Spec: transcript § 通用事件结构 + 事件类型枚举.

Each event has common fields ``type`` (discriminator) and ``ts`` (ms relative
to call start), plus type-specific fields. Modeled as a Pydantic discriminated
union so consumers can ``model_validate`` arbitrary entries safely.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field

from isales_common.schemas._base import AppModel


class _BaseEvent(AppModel):
    ts: int = Field(ge=0)


class GreetingEvent(_BaseEvent):
    type: Literal["greeting"] = "greeting"
    text: str
    audio_duration_ms: int | None = None


class UserSpeechEvent(_BaseEvent):
    type: Literal["user_speech"] = "user_speech"
    text: str
    asr_confidence: float | None = None
    duration_ms: int | None = None


class AIReplyEvent(_BaseEvent):
    type: Literal["ai_reply"] = "ai_reply"
    text: str
    turn_id: int
    selected_role_config_id: int | None = None
    goal_achieved: bool = False
    goal_type: str | None = None
    extracted: dict[str, object] = Field(default_factory=dict)
    is_wrap_up: bool = False


class InterruptionEvent(_BaseEvent):
    type: Literal["interruption"] = "interruption"
    interrupted_event_id: int | None = None
    user_text_at_interruption: str | None = None


class FillerEvent(_BaseEvent):
    type: Literal["filler"] = "filler"
    text: str
    filler_phrase_id: int | None = None
    duration_ms: int | None = None


class DefaultReplyUsedEvent(_BaseEvent):
    type: Literal["default_reply_used"] = "default_reply_used"
    text: str
    reason: str | None = None


class SilenceActivationEvent(_BaseEvent):
    type: Literal["silence_activation"] = "silence_activation"
    text: str
    activation_index: int


class TransferInitiatedEvent(_BaseEvent):
    type: Literal["transfer_initiated"] = "transfer_initiated"
    trigger_type: str
    trigger_detail: str | None = None


class TransferMarkedEvent(_BaseEvent):
    type: Literal["transfer_marked"] = "transfer_marked"


class GoalAchievedEvent(_BaseEvent):
    type: Literal["goal_achieved"] = "goal_achieved"
    goal_type: str
    extracted: dict[str, object] = Field(default_factory=dict)


class WrapUpStartedEvent(_BaseEvent):
    type: Literal["wrap_up_started"] = "wrap_up_started"
    rounds_remaining: int
    seconds_remaining: int


class WrapUpCompletedEvent(_BaseEvent):
    type: Literal["wrap_up_completed"] = "wrap_up_completed"
    reason: Literal["max_rounds", "max_seconds"]


class HangupEvent(_BaseEvent):
    type: Literal["hangup"] = "hangup"
    reason: str
    initiated_by: Literal["user", "ai"]


class StateWarningEvent(_BaseEvent):
    """Advisory warning written when a state transition falls outside
    ``LEGAL_TRANSITIONS``. See call-state-machine spec § "非法 transition 改
    advisory 警告". Current event name written by the engine.
    """

    type: Literal["state_warning"] = "state_warning"
    attempted: str
    from_state: str
    to_state: str


class StateErrorEvent(_BaseEvent):
    """Historical event name (written by ``transition_to`` before the
    soften-guard change, on a real IllegalTransition). New calls no longer
    produce it, but historical DB rows may still contain it — consumers MUST
    be able to parse it (call-state-machine spec § "state_error 事件名迁移").
    """

    type: Literal["state_error"] = "state_error"
    attempted: str
    from_state: str
    to_state: str


TranscriptEvent = Annotated[
    GreetingEvent
    | UserSpeechEvent
    | AIReplyEvent
    | InterruptionEvent
    | FillerEvent
    | DefaultReplyUsedEvent
    | SilenceActivationEvent
    | TransferInitiatedEvent
    | TransferMarkedEvent
    | GoalAchievedEvent
    | WrapUpStartedEvent
    | WrapUpCompletedEvent
    | HangupEvent
    | StateWarningEvent
    | StateErrorEvent,
    Field(discriminator="type"),
]
