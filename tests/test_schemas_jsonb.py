"""Unit tests for the JSONB nested schemas."""

from __future__ import annotations

import pytest
from pydantic import TypeAdapter, ValidationError

from isales_common.schemas.jsonb import (
    AIReplyEvent,
    ExtractionField,
    GreetingEvent,
    HangupEvent,
    RetryPolicy,
    TimeWindow,
    TranscriptEvent,
    UserSpeechEvent,
)


class TestTimeWindow:
    def test_valid(self):
        w = TimeWindow(days=["mon", "tue"], start="09:00", end="18:30")
        assert w.start == "09:00"

    def test_bad_time_format(self):
        with pytest.raises(ValidationError):
            TimeWindow(days=["mon"], start="9:00", end="18:00")

    def test_24_hour_boundary(self):
        with pytest.raises(ValidationError):
            TimeWindow(days=["mon"], start="24:00", end="25:00")

    def test_empty_days(self):
        with pytest.raises(ValidationError):
            TimeWindow(days=[], start="09:00", end="18:00")

    def test_invalid_day(self):
        with pytest.raises(ValidationError):
            TimeWindow(days=["funday"], start="09:00", end="18:00")


class TestRetryPolicy:
    def test_valid(self):
        p = RetryPolicy(intervals_seconds=[60, 300, 1800], max_attempts=3)
        assert p.max_attempts == 3

    def test_max_attempts_must_be_positive(self):
        with pytest.raises(ValidationError):
            RetryPolicy(intervals_seconds=[60], max_attempts=0)


class TestExtractionField:
    def test_valid(self):
        f = ExtractionField(name="appointment_time", type="datetime", required=True)
        assert f.required is True

    def test_invalid_type(self):
        with pytest.raises(ValidationError):
            ExtractionField(name="x", type="json")  # type: ignore[arg-type]


class TestTranscriptEventDiscriminatedUnion:
    adapter = TypeAdapter(TranscriptEvent)

    def test_greeting(self):
        ev = self.adapter.validate_python(
            {"type": "greeting", "ts": 0, "text": "hi", "audio_duration_ms": 1200}
        )
        assert isinstance(ev, GreetingEvent)

    def test_user_speech(self):
        ev = self.adapter.validate_python(
            {"type": "user_speech", "ts": 1500, "text": "hello", "asr_confidence": 0.95}
        )
        assert isinstance(ev, UserSpeechEvent)

    def test_ai_reply_with_extracted(self):
        ev = self.adapter.validate_python(
            {
                "type": "ai_reply",
                "ts": 2000,
                "text": "ok",
                "turn_id": 1,
                "goal_achieved": True,
                "goal_type": "appointment",
                "extracted": {"appointment_time": "2026-05-08T14:00"},
            }
        )
        assert isinstance(ev, AIReplyEvent)
        assert ev.extracted["appointment_time"] == "2026-05-08T14:00"

    def test_hangup(self):
        ev = self.adapter.validate_python(
            {"type": "hangup", "ts": 30000, "reason": "normal_clearing", "initiated_by": "ai"}
        )
        assert isinstance(ev, HangupEvent)

    def test_unknown_type_rejected(self):
        with pytest.raises(ValidationError):
            self.adapter.validate_python({"type": "mystery", "ts": 0})

    def test_negative_ts_rejected(self):
        with pytest.raises(ValidationError):
            self.adapter.validate_python({"type": "greeting", "ts": -1, "text": "x"})

    def test_round_trip(self):
        events = [
            {"type": "greeting", "ts": 0, "text": "hi"},
            {"type": "user_speech", "ts": 1500, "text": "hello"},
            {"type": "ai_reply", "ts": 2000, "text": "ok", "turn_id": 1},
            {"type": "hangup", "ts": 30000, "reason": "normal_clearing", "initiated_by": "user"},
        ]
        adapter = TypeAdapter(list[TranscriptEvent])
        parsed = adapter.validate_python(events)
        dumped = adapter.dump_python(parsed)
        assert dumped[0]["type"] == "greeting"
        assert dumped[3]["initiated_by"] == "user"
