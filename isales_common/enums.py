"""Global string enums shared across services. v1 stores as VARCHAR + app-level validation."""

from enum import StrEnum


class CallStatus(StrEnum):
    INIT = "init"
    GREETING = "greeting"
    LISTENING = "listening"
    SPEAKING = "speaking"
    INTERRUPTED = "interrupted"
    FILLER = "filler"
    PROCESSING = "processing"
    WRAPPING_UP = "wrapping_up"
    ACTIVATING = "activating"
    TRANSFERRING = "transferring"
    END = "end"


class RoleKind(StrEnum):
    ROLE = "role"
    JUDGE = "judge"
    POLISH = "polish"


class PromptScopeType(StrEnum):
    ROLE = "role"
    JUDGE = "judge"
    POLISH = "polish"


class TransferStatus(StrEnum):
    NONE = "none"
    MARKED_FOR_HANDOFF = "marked_for_handoff"


class TransferTriggerType(StrEnum):
    KEYWORD = "keyword"
    INTENT = "intent"
    ROUND = "round"
    LLM = "llm"


class HandoffStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class DeviceStatus(StrEnum):
    UNKNOWN = "unknown"
    DETECTED = "detected"
    REGISTERED = "registered"
    IDLE = "idle"
    DIALING = "dialing"
    IN_CALL = "in_call"
    OFFLINE = "offline"
    FLAGGED = "flagged"


class SimCardStatus(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ARREARS = "arrears"
    FLAGGED = "flagged"


class AgentStatus(StrEnum):
    ONLINE = "online"
    OFFLINE = "offline"


class LeadStatus(StrEnum):
    NEW = "new"
    QUEUED = "queued"
    CALLING = "calling"
    RETRYING = "retrying"
    FOLLOWING_UP = "following_up"
    COMPLETED = "completed"
    FAILED = "failed"
    FOLLOW_UP_EXHAUSTED = "follow_up_exhausted"
    DO_NOT_CALL = "do_not_call"
    TRANSFERRED = "transferred"


class CallbackStatus(StrEnum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED_RENDER = "failed_render"
    FAILED_HTTP_4XX = "failed_http_4xx"
    FAILED_HTTP_5XX = "failed_http_5xx"
    PENDING_RETRY = "pending_retry"
    EXHAUSTED = "exhausted"


class GenerationStatus(StrEnum):
    PENDING = "pending"
    READY = "ready"
    FAILED = "failed"


class ContinuousInterruptionStrategy(StrEnum):
    SHORT_REPLY = "short_reply"
    LISTEN_ONLY = "listen_only"


class HangupCause(StrEnum):
    """Unified hangup reason recorded on call end.

    GSM-side causes come from ``device-hardware`` spec; application-side
    causes come from ``call-state-machine`` spec. ``retry-followup`` spec
    classifies these into retry / follow-up / do-not-call buckets.
    """

    # GSM-side
    NO_ANSWER = "no_answer"
    USER_BUSY = "user_busy"
    NETWORK_OUT_OF_ORDER = "network_out_of_order"
    TEMPORARY_FAILURE = "temporary_failure"
    NORMAL_CLEARING = "normal_clearing"
    CALL_REJECTED = "call_rejected"
    # Application-side
    USER_HANGUP = "user_hangup"
    WRAP_UP_COMPLETED = "wrap_up_completed"
    SILENCE_MAX_REACHED = "silence_max_reached"
    MARKED_FOR_HANDOFF = "marked_for_handoff"
    NO_PROGRESS_TIMEOUT = "no_progress_timeout"
    MANUAL_HANGUP = "manual_hangup"
