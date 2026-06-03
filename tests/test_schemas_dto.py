"""Unit tests for the DTO schemas (campaign / lead / call / callback / etc.).

Verifies field constraints, ORM <-> schema round-trip via from_attributes, and
JSONB nested validation propagation.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from isales_common.enums import (
    AgentStatus,
    CallbackStatus,
    CallStatus,
    ContinuousInterruptionStrategy,
    DeviceStatus,
    HandoffStatus,
    LeadStatus,
    PromptScopeType,
    RoleKind,
    SimCardStatus,
    TransferStatus,
    TransferTriggerType,
)
from isales_common.models import (
    Agent,
    CallbackConfig,
    CallbackLog,
    CallRecord,
    CallSummary,
    Campaign,
    Device,
    HandoffTask,
    Lead,
    PipelineTrace,
    PromptVersion,
    RoleConfig,
    SimCard,
    VoiceModel,
)
from isales_common.schemas.agent import AgentRead
from isales_common.schemas.call import (
    CallRecordRead,
    CallSummaryRead,
    PipelineTraceRead,
)
from isales_common.schemas.callback import (
    CallbackConfigCreate,
    CallbackConfigRead,
    CallbackLogRead,
)
from isales_common.schemas.campaign import CampaignCreate, CampaignRead, CampaignUpdate
from isales_common.schemas.device import (
    DeviceRead,
    DeviceSelectRequest,
    DeviceSelectResponse,
)
from isales_common.schemas.handoff import HandoffTaskRead
from isales_common.schemas.jsonb import (
    ExtractionField,
    RetryPolicy,
    TimeWindow,
)
from isales_common.schemas.lead import LeadCreate, LeadRead
from isales_common.schemas.prompt import PromptVersionRead
from isales_common.schemas.role_config import RoleConfigRead
from isales_common.schemas.sim_card import SimCardRead
from isales_common.schemas.voice_model import VoiceModelRead


def _now() -> datetime:
    return datetime(2026, 5, 1, 10, 0, 0, tzinfo=UTC)


def _campaign_kwargs() -> dict:
    return {
        "name": "test",
        "voice_id": None,
        "default_replies": ["啊", "嗯"],
        "concurrency": 2,
        "time_windows": [TimeWindow(days=["mon"], start="09:00", end="18:00")],
        "extraction_fields": [ExtractionField(name="age", type="number")],
        "max_silence_activations": 2,
        "silence_threshold_ms": 3000,
        "silence_phrases": [],
        "silence_hangup_phrase": None,
        "max_no_progress_seconds": None,
        "wrap_up_max_rounds": 3,
        "wrap_up_max_seconds": 60,
        "wrap_up_closing_phrases": [],
        "interruption_whitelist": [],
        "interruption_min_duration_ms": 400,
        "max_continuous_interruptions": 3,
        "continuous_interruption_strategy": ContinuousInterruptionStrategy.SHORT_REPLY,
        "transfer_keyword_enabled": False,
        "transfer_keywords": [],
        "transfer_intent_enabled": False,
        "transfer_intent_threshold": None,
        "transfer_round_enabled": False,
        "transfer_round_threshold": None,
        "transfer_llm_enabled": False,
        "transfer_llm_prompt_version_id": None,
        "transfer_phrases": [],
        "retry_intervals": [60, 240, 1440],
        "retry_max_count": 3,
        "follow_up_interval_days": None,
        "follow_up_max_count": 0,
        "do_not_call_keywords": ["不要打"],
        "do_not_call_llm_enabled": False,
        "do_not_call_llm_prompt_version_id": None,
        "respect_holidays": True,
    }


class TestCampaignSchemas:
    def test_create_valid(self):
        dto = CampaignCreate(**_campaign_kwargs())
        assert dto.concurrency == 2
        assert dto.time_windows[0].start == "09:00"

    def test_create_rejects_zero_concurrency(self):
        kw = _campaign_kwargs()
        kw["concurrency"] = 0
        with pytest.raises(ValidationError):
            CampaignCreate(**kw)

    def test_create_rejects_bad_time_window(self):
        kw = _campaign_kwargs()
        kw["time_windows"] = [{"days": ["mon"], "start": "9:00", "end": "18:00"}]
        with pytest.raises(ValidationError):
            CampaignCreate(**kw)

    def test_update_partial(self):
        u = CampaignUpdate(concurrency=5)
        assert u.concurrency == 5
        assert u.name is None

    def test_read_from_orm(self):
        orm = Campaign(
            id=42,
            name="orm",
            voice_id=None,
            default_replies=[],
            concurrency=1,
            time_windows=[{"days": ["mon"], "start": "09:00", "end": "18:00"}],
            extraction_fields=[],
            max_silence_activations=2,
            silence_threshold_ms=3000,
            silence_phrases=[],
            silence_hangup_phrase=None,
            max_no_progress_seconds=None,
            wrap_up_max_rounds=3,
            wrap_up_max_seconds=60,
            wrap_up_closing_phrases=[],
            interruption_whitelist=[],
            interruption_min_duration_ms=400,
            max_continuous_interruptions=3,
            continuous_interruption_strategy=ContinuousInterruptionStrategy.SHORT_REPLY,
            transfer_keyword_enabled=False,
            transfer_keywords=[],
            transfer_intent_enabled=False,
            transfer_intent_threshold=None,
            transfer_round_enabled=False,
            transfer_round_threshold=None,
            transfer_llm_enabled=False,
            transfer_llm_prompt_version_id=None,
            transfer_phrases=[],
            retry_intervals=[],
            retry_max_count=0,
            follow_up_interval_days=None,
            follow_up_max_count=0,
            do_not_call_keywords=[],
            do_not_call_llm_enabled=False,
            do_not_call_llm_prompt_version_id=None,
            respect_holidays=True,
            created_at=_now(),
            updated_at=_now(),
        )
        dto = CampaignRead.model_validate(orm)
        assert dto.id == 42
        assert dto.time_windows[0].start == "09:00"


class TestLeadSchemas:
    def test_create(self):
        dto = LeadCreate(campaign_id=1, phone="+8613800138000", custom_data={"vip": True})
        assert dto.custom_data["vip"] is True

    def test_read_from_orm(self):
        orm = Lead(
            id=1,
            campaign_id=1,
            name="张三",
            phone="+8613800138000",
            source="csv",
            custom_data={},
            status=LeadStatus.NEW,
            retry_count=0,
            follow_up_count=0,
            next_call_at=None,
            last_hangup_cause=None,
            created_at=_now(),
            updated_at=_now(),
        )
        dto = LeadRead.model_validate(orm)
        assert dto.status == LeadStatus.NEW


class TestCallSchemas:
    def test_call_record_read_with_transcript(self):
        orm = CallRecord(
            id=1,
            lead_id=1,
            campaign_id=1,
            caller_id="+8613800138000",
            status=CallStatus.END,
            started_at=_now(),
            ended_at=_now(),
            duration=60,
            transcript=[
                {"type": "greeting", "ts": 0, "text": "您好"},
                {"type": "hangup", "ts": 60000, "reason": "normal_clearing", "initiated_by": "ai"},
            ],
            recording_url=None,
            transfer_status=TransferStatus.NONE,
            transfer_reason=None,
            wrap_up_started_at=None,
            prompt_versions={"1": 11},
            created_at=_now(),
            updated_at=_now(),
        )
        dto = CallRecordRead.model_validate(orm)
        assert len(dto.transcript) == 2
        assert dto.transcript[0].type == "greeting"

    def test_call_record_rejects_bad_transcript_event(self):
        with pytest.raises(ValidationError):
            CallRecordRead.model_validate(
                {
                    "id": 1,
                    "lead_id": 1,
                    "campaign_id": 1,
                    "status": CallStatus.END,
                    "transcript": [{"type": "mystery", "ts": 0}],
                    "transfer_status": TransferStatus.NONE,
                    "prompt_versions": {},
                    "created_at": _now(),
                    "updated_at": _now(),
                }
            )

    def test_call_summary_read(self):
        orm = CallSummary(
            id=1,
            call_record_id=1,
            summary_text="ok",
            extracted_fields={"age": 30},
            goal_achieved=True,
            goal_type="appointment",
            created_at=_now(),
            updated_at=_now(),
        )
        dto = CallSummaryRead.model_validate(orm)
        assert dto.goal_achieved is True

    def test_pipeline_trace_read(self):
        orm = PipelineTrace(
            call_record_id=1,
            turn_id=0,
            ts_start=_now(),
            ts_end=_now(),
            user_input="hi",
            main_reply_text="您好，请问现在方便吗？",
            main_duration_ms=420,
            main_tokens_in=120,
            main_tokens_out=18,
            main_fallback_used=False,
            referee_decision="continue",
            referee_goal_type=None,
            referee_confidence=0.82,
            referee_duration_ms=310,
            first_audio_ms=480,
            error=None,
            created_at=_now(),
            updated_at=_now(),
        )
        dto = PipelineTraceRead.model_validate(orm)
        assert dto.main_reply_text == "您好，请问现在方便吗？"
        assert dto.referee_decision == "continue"
        assert dto.first_audio_ms == 480
        assert dto.main_fallback_used is False


class TestCallbackSchemas:
    def test_create_with_jsonlogic_trigger(self):
        dto = CallbackConfigCreate(
            campaign_id=1,
            name="appt-webhook",
            trigger={"==": [{"var": "goal_achieved"}, True]},
            url="https://example.com/hook",
            payload_template='{"x": 1}',
            retry_policy=RetryPolicy(intervals_seconds=[60, 300], max_attempts=2),
        )
        assert dto.method == "POST"
        assert dto.retry_policy.max_attempts == 2

    def test_method_whitelist(self):
        with pytest.raises(ValidationError):
            CallbackConfigCreate(
                campaign_id=1,
                name="x",
                trigger={"==": [1, 1]},
                url="https://e.com",
                method="DELETE",  # type: ignore[arg-type]
                payload_template="{}",
                retry_policy=RetryPolicy(intervals_seconds=[], max_attempts=1),
            )

    def test_config_read_from_orm(self):
        orm = CallbackConfig(
            id=1,
            campaign_id=1,
            name="x",
            trigger={"==": [1, 1]},
            url="https://e.com",
            method="POST",
            headers={},
            payload_template="{}",
            retry_policy={"intervals_seconds": [60], "max_attempts": 1},
            signing_secret=None,
            timeout_seconds=None,
            enabled=True,
            created_at=_now(),
            updated_at=_now(),
        )
        dto = CallbackConfigRead.model_validate(orm)
        assert dto.retry_policy.max_attempts == 1
        # signing_secret MUST NOT be exposed on the Read DTO
        assert "signing_secret" not in dto.model_dump()

    def test_log_read(self):
        orm = CallbackLog(
            id=1,
            callback_config_id=1,
            call_record_id=1,
            status=CallbackStatus.SUCCESS,
            response_code=200,
            retry_count=0,
            attempt_at=_now(),
            created_at=_now(),
            updated_at=_now(),
        )
        dto = CallbackLogRead.model_validate(orm)
        assert dto.status == CallbackStatus.SUCCESS


class TestMiscReadSchemas:
    def test_voice_model(self):
        orm = VoiceModel(
            id=1,
            name="v",
            provider="elevenlabs",
            voice_id="abc",
            sample_url=None,
            created_at=_now(),
            updated_at=_now(),
        )
        assert VoiceModelRead.model_validate(orm).provider == "elevenlabs"

    def test_role_config(self):
        orm = RoleConfig(
            id=1,
            campaign_id=1,
            kind=RoleKind.MAIN,
            model="gpt-4",
            current_prompt_version_id=None,
            temperature=0.7,
            top_p=1.0,
            ext_params={},
            enabled=True,
            created_at=_now(),
            updated_at=_now(),
        )
        assert RoleConfigRead.model_validate(orm).kind == RoleKind.MAIN

    def test_prompt(self):
        orm = PromptVersion(
            id=1,
            scope_type=PromptScopeType.MAIN,
            scope_id=1,
            content="hi",
            created_by="me",
            is_active=True,
            created_at=_now(),
            updated_at=_now(),
        )
        assert PromptVersionRead.model_validate(orm).is_active is True

    def test_device(self):
        ts = _now()
        orm = Device(
            id=1,
            name="dev1",
            usb_port="/dev/ttyUSB0",
            modem_model="EC25",
            imei="111",
            status=DeviceStatus.IDLE,
            last_seen_at=None,
            last_call_at=ts,
            created_at=_now(),
            updated_at=_now(),
        )
        read = DeviceRead.model_validate(orm)
        assert read.status == DeviceStatus.IDLE
        assert read.last_call_at == ts

    def test_device_select_round_trip(self):
        req = DeviceSelectRequest(campaign_id=42)
        assert DeviceSelectRequest.model_validate_json(req.model_dump_json()) == req
        with pytest.raises(ValidationError):
            DeviceSelectRequest(campaign_id=0)  # gt=0 enforced

        resp = DeviceSelectResponse(device_id=7, phone_number="+8613800138000")
        assert DeviceSelectResponse.model_validate_json(resp.model_dump_json()) == resp
        with pytest.raises(ValidationError):
            DeviceSelectResponse(device_id=7, phone_number="")

    def test_sim_card(self):
        orm = SimCard(
            id=1,
            iccid="89860000000",
            imsi=None,
            phone_number=None,
            carrier=None,
            plan=None,
            balance=Decimal("12.34"),
            signal_strength=20,
            status=SimCardStatus.ACTIVE,
            last_checked_at=None,
            created_at=_now(),
            updated_at=_now(),
        )
        dto = SimCardRead.model_validate(orm)
        assert dto.balance == Decimal("12.34")

    def test_agent(self):
        orm = Agent(
            id=1,
            name="agent1",
            login_user="a1",
            status=AgentStatus.ONLINE,
            created_at=_now(),
            updated_at=_now(),
        )
        assert AgentRead.model_validate(orm).status == AgentStatus.ONLINE

    def test_handoff(self):
        orm = HandoffTask(
            id=1,
            call_record_id=1,
            agent_id=None,
            trigger_type=TransferTriggerType.KEYWORD,
            trigger_detail="转人工",
            status=HandoffStatus.PENDING,
            picked_up_at=None,
            completed_at=None,
            created_at=_now(),
            updated_at=_now(),
        )
        dto = HandoffTaskRead.model_validate(orm)
        assert dto.trigger_type == TransferTriggerType.KEYWORD
