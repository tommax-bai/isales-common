"""Cloud-edge protobuf serialization tests.

Spec: service-communication § Requirement: 云-边控制面 (cloud-edge gRPC
bidirectional streaming) — wire format round-trips.
"""

from __future__ import annotations

from google.protobuf.timestamp_pb2 import Timestamp

from isales_common.proto import cloud_edge_pb2 as pb


def test_dial_command_round_trip() -> None:
    msg = pb.Cloud2Edge(
        dial=pb.DialCommand(
            call_id="c-001",
            device_id=3,
            number="+8613800138000",
            caller_id="+8613900139000",
            rtc_channel="c-001",
            rtc_token="rtc-token-xxx",
            rtc_uid_edge="edge-c-001",
            rtc_uid_engine="engine-c-001",
        ),
    )

    wire = msg.SerializeToString()
    parsed = pb.Cloud2Edge.FromString(wire)

    assert parsed.WhichOneof("payload") == "dial"
    assert parsed.dial.call_id == "c-001"
    assert parsed.dial.device_id == 3
    assert parsed.dial.number == "+8613800138000"
    assert parsed.dial.rtc_uid_engine == "engine-c-001"


def test_call_event_oneof_remote_hangup() -> None:
    msg = pb.Edge2Cloud(
        call_event=pb.CallEvent(
            call_id="c-002",
            remote_hangup=pb.RemoteHangup(
                cause=pb.HANGUP_CAUSE_USER_BUSY,
                vendor_raw="BUSY",
            ),
        ),
    )

    wire = msg.SerializeToString()
    parsed = pb.Edge2Cloud.FromString(wire)

    assert parsed.WhichOneof("payload") == "call_event"
    assert parsed.call_event.WhichOneof("kind") == "remote_hangup"
    assert parsed.call_event.remote_hangup.cause == pb.HANGUP_CAUSE_USER_BUSY
    assert parsed.call_event.remote_hangup.vendor_raw == "BUSY"


def test_call_event_oneof_ringing_marker() -> None:
    # Empty-payload events still keep the oneof discriminator set, so the
    # cloud side can dispatch by WhichOneof('kind') alone.
    msg = pb.CallEvent(call_id="c-003", ringing=pb.Ringing())
    wire = msg.SerializeToString()
    parsed = pb.CallEvent.FromString(wire)
    assert parsed.WhichOneof("kind") == "ringing"


def test_hardware_alert_oneof() -> None:
    msg = pb.Edge2Cloud(
        hardware_alert=pb.HardwareAlert(
            device_id=7,
            audio_buffer_stalled=pb.AudioBufferStalled(
                direction="downstream",
                stalled_ms=250,
            ),
        ),
    )

    wire = msg.SerializeToString()
    parsed = pb.Edge2Cloud.FromString(wire)

    assert parsed.hardware_alert.WhichOneof("kind") == "audio_buffer_stalled"
    assert parsed.hardware_alert.audio_buffer_stalled.stalled_ms == 250


def test_heartbeat_with_device_health() -> None:
    ts = Timestamp()
    ts.seconds = 1_700_000_000
    msg = pb.Edge2Cloud(
        heartbeat=pb.Heartbeat(
            ts=ts,
            devices=[
                pb.DeviceHealth(
                    device_id=1,
                    status=pb.DEVICE_STATUS_IDLE,
                    signal_strength=22,
                    last_seen_at=ts,
                ),
                pb.DeviceHealth(
                    device_id=2,
                    status=pb.DEVICE_STATUS_OFFLINE,
                    signal_strength=-1,
                ),
            ],
        ),
    )

    wire = msg.SerializeToString()
    parsed = pb.Edge2Cloud.FromString(wire)

    assert parsed.heartbeat.ts.seconds == 1_700_000_000
    assert len(parsed.heartbeat.devices) == 2
    assert parsed.heartbeat.devices[0].status == pb.DEVICE_STATUS_IDLE
    assert parsed.heartbeat.devices[1].signal_strength == -1


def test_config_update_oneof_log_level() -> None:
    msg = pb.Cloud2Edge(
        config_update=pb.ConfigUpdate(
            log_level=pb.LogLevelUpdate(level="DEBUG"),
        ),
    )

    wire = msg.SerializeToString()
    parsed = pb.Cloud2Edge.FromString(wire)

    assert parsed.config_update.WhichOneof("change") == "log_level"
    assert parsed.config_update.log_level.level == "DEBUG"


def test_unset_oneof_serializes_compactly() -> None:
    # An envelope with no payload set is valid; consumers MUST check
    # WhichOneof and ignore otherwise.
    msg = pb.Cloud2Edge()
    wire = msg.SerializeToString()
    assert wire == b""
    parsed = pb.Cloud2Edge.FromString(wire)
    assert parsed.WhichOneof("payload") is None


def test_hangup_cause_enum_names_match_canonical_set() -> None:
    # Mirror the canonical set in device-hardware § "GSM hangup_cause 映射".
    canonical = {
        "HANGUP_CAUSE_UNSPECIFIED",
        "HANGUP_CAUSE_NO_ANSWER",
        "HANGUP_CAUSE_USER_BUSY",
        "HANGUP_CAUSE_NETWORK_OUT_OF_ORDER",
        "HANGUP_CAUSE_NORMAL_CLEARING",
        "HANGUP_CAUSE_CALL_REJECTED",
    }
    declared = {pb.HangupCause.Name(v) for v in pb.HangupCause.values()}
    assert declared == canonical
