"""Smoke tests confirming enum values match spec wording."""

from isales_common.enums import (
    AgentStatus,
    CallbackStatus,
    CallStatus,
    ContinuousInterruptionStrategy,
    DeviceStatus,
    GenerationStatus,
    HandoffStatus,
    LeadStatus,
    PromptScopeType,
    RoleKind,
    SimCardStatus,
    TransferStatus,
    TransferTriggerType,
)


def test_call_status_values():
    # engine-tools-multidialogue-gating: collapsed 11 → 4 coarse lifecycle
    # labels. The fine in-call phases moved to engine-internal flags / transcript
    # events and are no longer CallStatus members.
    expected = {
        "init",
        "in_call",
        "transferring",
        "end",
    }
    assert {s.value for s in CallStatus} == expected


def test_role_kind_matches_prompt_scope():
    assert {k.value for k in RoleKind} == {p.value for p in PromptScopeType}


def test_transfer_trigger_types():
    assert {t.value for t in TransferTriggerType} == {"keyword", "intent", "round", "llm"}


def test_handoff_status_values():
    assert {s.value for s in HandoffStatus} == {"pending", "in_progress", "completed"}


def test_device_status_full_set():
    assert {s.value for s in DeviceStatus} == {
        "unknown",
        "detected",
        "registered",
        "idle",
        "dialing",
        "in_call",
        "offline",
        "flagged",
    }


def test_sim_card_status():
    assert {s.value for s in SimCardStatus} == {"active", "suspended", "arrears", "flagged"}


def test_agent_status():
    assert {s.value for s in AgentStatus} == {"online", "offline"}


def test_lead_status():
    assert {s.value for s in LeadStatus} == {
        "new",
        "queued",
        "calling",
        "retrying",
        "following_up",
        "completed",
        "failed",
        "follow_up_exhausted",
        "do_not_call",
        "transferred",
        # appointment lifecycle terminals added by web-admin-ui-redesign
        "appointed",
        "visited",
        "lost",
    }


def test_callback_status():
    assert {s.value for s in CallbackStatus} == {
        "pending",
        "success",
        "failed_render",
        "failed_http_4xx",
        "failed_http_5xx",
        "pending_retry",
        "exhausted",
    }


def test_generation_status():
    assert {s.value for s in GenerationStatus} == {"pending", "ready", "failed"}


def test_continuous_interruption_strategy():
    assert {s.value for s in ContinuousInterruptionStrategy} == {"short_reply", "listen_only"}


def test_transfer_status():
    assert {s.value for s in TransferStatus} == {"none", "marked_for_handoff"}


def test_str_enum_subclasses_str():
    # StrEnum members ARE strings — important for ORM VARCHAR storage
    assert isinstance(CallStatus.INIT, str)
    assert CallStatus.INIT == "init"
