"""Cross-service message schema tests.

Spec: message-contract § round-trip serialization, schema_version handling.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import TypeAdapter, ValidationError

from isales_common.enums import CallStatus, HangupCause
from isales_common.schemas.messages import (
    CURRENT_SCHEMA_VERSION,
    SUPPORTED_SCHEMA_VERSIONS,
    ASRFinal,
    ASRPartial,
    BaseMessage,
    CallEnded,
    CallEndedEvent,
    CallStarted,
    CampaignControl,
    DialLeadInfo,
    DialRequest,
    EngineControl,
    EngineEvent,
    HistorySummary,
    ManualHangup,
    PauseCampaign,
    PromptVersionRef,
    PromptVersionsSnapshot,
    ResumeCampaign,
    StartCampaign,
    StatusChanged,
    TranscriptAppended,
    TransferCommand,
    is_supported_version,
)

# ---- BaseMessage defaults -------------------------------------------------


def test_base_message_autofills_envelope():
    msg = StartCampaign(campaign_id=42)
    assert msg.schema_version == 1
    assert msg.message_id is not None
    assert msg.created_at.tzinfo is not None
    assert "StartCampaign(message_id=" in str(msg)


def test_distinct_message_ids():
    a = StartCampaign(campaign_id=1)
    b = StartCampaign(campaign_id=1)
    assert a.message_id != b.message_id


# ---- DialRequest round-trip ----------------------------------------------


def _sample_dial_request() -> DialRequest:
    return DialRequest(
        lead=DialLeadInfo(
            lead_id=10,
            campaign_id=2,
            phone="+8613800000000",
            name="alice",
            custom_data={"city": "shanghai"},
        ),
        history=[
            HistorySummary(
                call_record_id=99,
                summary="user requested callback",
                ended_at="2026-04-30T08:30:00+00:00",
            ),
        ],
        prompt_versions=PromptVersionsSnapshot(
            main_llm=PromptVersionRef(role_config_id=1, prompt_version_id=5),
            referee_llm=PromptVersionRef(role_config_id=2, prompt_version_id=7),
            extractor_llm=PromptVersionRef(role_config_id=3, prompt_version_id=9),
            wrap_up_appended=False,
        ),
        caller_id="+8675500000000",
        device_id=4,
    )


def test_dial_request_round_trip():
    msg = _sample_dial_request()
    raw = msg.model_dump_json()
    restored = DialRequest.model_validate_json(raw)
    assert restored == msg


# ---- CallEnded round-trip ------------------------------------------------


def test_call_ended_round_trip():
    msg = CallEnded(
        call_record_id=123,
        hangup_cause=HangupCause.NORMAL_CLEARING,
        ended_at=datetime(2026, 5, 1, 10, 0, tzinfo=UTC),
    )
    restored = CallEnded.model_validate_json(msg.model_dump_json())
    assert restored == msg
    assert restored.hangup_cause is HangupCause.NORMAL_CLEARING


# ---- Discriminated unions ------------------------------------------------


def test_engine_control_discriminator():
    adapter = TypeAdapter(EngineControl)

    hangup = ManualHangup(call_record_id=7, operator="ops-1")
    transfer = TransferCommand(call_record_id=7, agent_id=3)

    for original in (hangup, transfer):
        payload = original.model_dump_json()
        restored = adapter.validate_json(payload)
        assert restored == original


def test_engine_control_unknown_type_rejected():
    adapter = TypeAdapter(EngineControl)
    bad = json.dumps(
        {
            "schema_version": 1,
            "message_id": str(uuid4()),
            "created_at": "2026-05-01T10:00:00+00:00",
            "type": "nonsense",
            "call_record_id": 1,
        }
    )
    with pytest.raises(ValidationError):
        adapter.validate_json(bad)


def test_engine_event_round_trip_all_subtypes():
    adapter = TypeAdapter(EngineEvent)
    base = {"call_record_id": 100}
    subs: list[BaseMessage] = [
        StatusChanged(**base, status=CallStatus.LISTENING),
        ASRPartial(**base, text="he", timestamp_ms=100),
        ASRFinal(**base, text="hello", timestamp_ms=400),
        TranscriptAppended(**base, event_type="user_speech", ts=400),
        CallStarted(**base, started_at=datetime(2026, 5, 1, 10, 0, tzinfo=UTC)),
        CallEndedEvent(
            **base,
            hangup_cause=HangupCause.USER_HANGUP,
            ended_at=datetime(2026, 5, 1, 10, 5, tzinfo=UTC),
        ),
    ]
    for original in subs:
        restored = adapter.validate_json(original.model_dump_json())
        assert restored == original


def test_campaign_control_round_trip():
    adapter = TypeAdapter(CampaignControl)
    for original in (
        StartCampaign(campaign_id=1),
        PauseCampaign(campaign_id=2),
        ResumeCampaign(campaign_id=3),
    ):
        restored = adapter.validate_json(original.model_dump_json())
        assert restored == original


# ---- schema_version dead-letter handling ---------------------------------


def test_supported_versions_includes_current():
    assert CURRENT_SCHEMA_VERSION in SUPPORTED_SCHEMA_VERSIONS


def test_is_supported_version_helper():
    assert is_supported_version(CURRENT_SCHEMA_VERSION)
    assert not is_supported_version(999)
    assert not is_supported_version(0)


def test_consumer_can_detect_unsupported_version():
    """Producer/consumer drift simulation.

    Producer sends a future schema_version; consumer parses the envelope
    fields, sees the version is unsupported, and routes to dead-letter.
    """
    msg = StartCampaign(campaign_id=1)
    raw = json.loads(msg.model_dump_json())
    raw["schema_version"] = 999  # tamper

    parsed = StartCampaign.model_validate(raw)
    # Pydantic itself does not gate on the int value — the consumer must:
    assert not is_supported_version(parsed.schema_version)
