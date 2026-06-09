"""Global string enums shared across services. v1 stores as VARCHAR + app-level validation."""

from enum import StrEnum


class CallStatus(StrEnum):
    """Coarse, externally-observed call lifecycle (engine-tools-multidialogue-gating).

    Collapsed from the old 11-value FSM-as-controller set to 4 lifecycle labels.
    The fine-grained in-call phases (greeting / listening / processing / speaking /
    interrupted / filler / wrapping_up / activating) are NO LONGER call states —
    they are engine-internal event/role concerns and live in transcript events,
    not here. ``in_call`` covers the whole conversation; only a human-handoff
    (``transferring``) and the lifecycle bookends (``init`` / ``end``) are
    distinct. Stored as VARCHAR (call_record.status String(16)) — no PG enum, so
    the collapse needs no DB migration; pre-collapse rows holding removed values
    are acceptable orphans (v1 has no production data).
    """

    INIT = "init"
    IN_CALL = "in_call"
    TRANSFERRING = "transferring"
    END = "end"


# pipeline-stream-and-referee: three-layer PK/judge/polish replaced by the
# voxen-style dual-LLM architecture. main = streaming text reply, referee =
# gating enum decision, extractor = post-call structured extraction.
# engine-multi-referee-and-restructure: referee may now be configured N rows
# per campaign (each with its own prompt + enum semantics); restructure is a
# new optional slot that re-voices the last reply / barge-in remainder.
# engine-tools-multidialogue-gating: persona is an opt-in speculative dialogue
# role (label required, unique per campaign) for eager multi-dialogue gating.
class RoleKind(StrEnum):
    MAIN = "main"
    REFEREE = "referee"
    EXTRACTOR = "extractor"
    RESTRUCTURE = "restructure"
    PERSONA = "persona"


class PromptScopeType(StrEnum):
    MAIN = "main"
    REFEREE = "referee"
    EXTRACTOR = "extractor"
    RESTRUCTURE = "restructure"
    PERSONA = "persona"


class TransferStatus(StrEnum):
    NONE = "none"
    MARKED_FOR_HANDOFF = "marked_for_handoff"


class TransferTriggerType(StrEnum):
    KEYWORD = "keyword"
    INTENT = "intent"
    ROUND = "round"
    LLM = "llm"


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
    # 已流失：运营人员在 leads view 手动标注的终态。Column is String(24)。
    LOST = "lost"


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
    # silence-drop-no-progress-timeout: the config-driven
    # ``campaign.max_no_progress_seconds`` timer that produced this cause was
    # removed (silence-timeout hangup is now solely the silence-max path →
    # ``silence_max_reached``). This member is RETAINED because it remains the
    # engine ``run_session`` / worker ``session_runner`` internal-error fallback
    # cause and classifies under retry-followup; historical call_record rows may
    # also carry it. It is no longer a config-driven business hangup reason.
    NO_PROGRESS_TIMEOUT = "no_progress_timeout"
    MANUAL_HANGUP = "manual_hangup"
    # engine-tools-multidialogue-gating: AI proactively hangs up via a referee
    # gating verdict selecting tool:hangup. retry-followup classifies this into
    # the no-auto-redial bucket.
    REFEREE_HANGUP = "referee_hangup"
