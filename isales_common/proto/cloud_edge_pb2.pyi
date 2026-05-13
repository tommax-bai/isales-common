import datetime

from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class DeviceStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    DEVICE_STATUS_UNSPECIFIED: _ClassVar[DeviceStatus]
    DEVICE_STATUS_UNKNOWN: _ClassVar[DeviceStatus]
    DEVICE_STATUS_DETECTED: _ClassVar[DeviceStatus]
    DEVICE_STATUS_REGISTERED: _ClassVar[DeviceStatus]
    DEVICE_STATUS_IDLE: _ClassVar[DeviceStatus]
    DEVICE_STATUS_DIALING: _ClassVar[DeviceStatus]
    DEVICE_STATUS_IN_CALL: _ClassVar[DeviceStatus]
    DEVICE_STATUS_OFFLINE: _ClassVar[DeviceStatus]
    DEVICE_STATUS_FLAGGED: _ClassVar[DeviceStatus]
    DEVICE_STATUS_ERROR: _ClassVar[DeviceStatus]

class HangupCause(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    HANGUP_CAUSE_UNSPECIFIED: _ClassVar[HangupCause]
    HANGUP_CAUSE_NO_ANSWER: _ClassVar[HangupCause]
    HANGUP_CAUSE_USER_BUSY: _ClassVar[HangupCause]
    HANGUP_CAUSE_NETWORK_OUT_OF_ORDER: _ClassVar[HangupCause]
    HANGUP_CAUSE_NORMAL_CLEARING: _ClassVar[HangupCause]
    HANGUP_CAUSE_CALL_REJECTED: _ClassVar[HangupCause]
DEVICE_STATUS_UNSPECIFIED: DeviceStatus
DEVICE_STATUS_UNKNOWN: DeviceStatus
DEVICE_STATUS_DETECTED: DeviceStatus
DEVICE_STATUS_REGISTERED: DeviceStatus
DEVICE_STATUS_IDLE: DeviceStatus
DEVICE_STATUS_DIALING: DeviceStatus
DEVICE_STATUS_IN_CALL: DeviceStatus
DEVICE_STATUS_OFFLINE: DeviceStatus
DEVICE_STATUS_FLAGGED: DeviceStatus
DEVICE_STATUS_ERROR: DeviceStatus
HANGUP_CAUSE_UNSPECIFIED: HangupCause
HANGUP_CAUSE_NO_ANSWER: HangupCause
HANGUP_CAUSE_USER_BUSY: HangupCause
HANGUP_CAUSE_NETWORK_OUT_OF_ORDER: HangupCause
HANGUP_CAUSE_NORMAL_CLEARING: HangupCause
HANGUP_CAUSE_CALL_REJECTED: HangupCause

class Edge2Cloud(_message.Message):
    __slots__ = ("heartbeat", "dial_ack", "call_event", "hardware_alert")
    HEARTBEAT_FIELD_NUMBER: _ClassVar[int]
    DIAL_ACK_FIELD_NUMBER: _ClassVar[int]
    CALL_EVENT_FIELD_NUMBER: _ClassVar[int]
    HARDWARE_ALERT_FIELD_NUMBER: _ClassVar[int]
    heartbeat: Heartbeat
    dial_ack: DialAck
    call_event: CallEvent
    hardware_alert: HardwareAlert
    def __init__(self, heartbeat: _Optional[_Union[Heartbeat, _Mapping]] = ..., dial_ack: _Optional[_Union[DialAck, _Mapping]] = ..., call_event: _Optional[_Union[CallEvent, _Mapping]] = ..., hardware_alert: _Optional[_Union[HardwareAlert, _Mapping]] = ...) -> None: ...

class Cloud2Edge(_message.Message):
    __slots__ = ("heartbeat", "dial", "cancel", "rtc_credentials", "config_update", "remote_diag")
    HEARTBEAT_FIELD_NUMBER: _ClassVar[int]
    DIAL_FIELD_NUMBER: _ClassVar[int]
    CANCEL_FIELD_NUMBER: _ClassVar[int]
    RTC_CREDENTIALS_FIELD_NUMBER: _ClassVar[int]
    CONFIG_UPDATE_FIELD_NUMBER: _ClassVar[int]
    REMOTE_DIAG_FIELD_NUMBER: _ClassVar[int]
    heartbeat: Heartbeat
    dial: DialCommand
    cancel: CancelCommand
    rtc_credentials: RtcCredentials
    config_update: ConfigUpdate
    remote_diag: RemoteDiagnostic
    def __init__(self, heartbeat: _Optional[_Union[Heartbeat, _Mapping]] = ..., dial: _Optional[_Union[DialCommand, _Mapping]] = ..., cancel: _Optional[_Union[CancelCommand, _Mapping]] = ..., rtc_credentials: _Optional[_Union[RtcCredentials, _Mapping]] = ..., config_update: _Optional[_Union[ConfigUpdate, _Mapping]] = ..., remote_diag: _Optional[_Union[RemoteDiagnostic, _Mapping]] = ...) -> None: ...

class Heartbeat(_message.Message):
    __slots__ = ("ts", "devices")
    TS_FIELD_NUMBER: _ClassVar[int]
    DEVICES_FIELD_NUMBER: _ClassVar[int]
    ts: _timestamp_pb2.Timestamp
    devices: _containers.RepeatedCompositeFieldContainer[DeviceHealth]
    def __init__(self, ts: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., devices: _Optional[_Iterable[_Union[DeviceHealth, _Mapping]]] = ...) -> None: ...

class DeviceHealth(_message.Message):
    __slots__ = ("device_id", "status", "signal_strength", "last_seen_at")
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    SIGNAL_STRENGTH_FIELD_NUMBER: _ClassVar[int]
    LAST_SEEN_AT_FIELD_NUMBER: _ClassVar[int]
    device_id: int
    status: DeviceStatus
    signal_strength: int
    last_seen_at: _timestamp_pb2.Timestamp
    def __init__(self, device_id: _Optional[int] = ..., status: _Optional[_Union[DeviceStatus, str]] = ..., signal_strength: _Optional[int] = ..., last_seen_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class DialCommand(_message.Message):
    __slots__ = ("call_id", "device_id", "number", "caller_id", "rtc_channel", "rtc_token", "rtc_uid_edge", "rtc_uid_engine")
    CALL_ID_FIELD_NUMBER: _ClassVar[int]
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    NUMBER_FIELD_NUMBER: _ClassVar[int]
    CALLER_ID_FIELD_NUMBER: _ClassVar[int]
    RTC_CHANNEL_FIELD_NUMBER: _ClassVar[int]
    RTC_TOKEN_FIELD_NUMBER: _ClassVar[int]
    RTC_UID_EDGE_FIELD_NUMBER: _ClassVar[int]
    RTC_UID_ENGINE_FIELD_NUMBER: _ClassVar[int]
    call_id: str
    device_id: int
    number: str
    caller_id: str
    rtc_channel: str
    rtc_token: str
    rtc_uid_edge: str
    rtc_uid_engine: str
    def __init__(self, call_id: _Optional[str] = ..., device_id: _Optional[int] = ..., number: _Optional[str] = ..., caller_id: _Optional[str] = ..., rtc_channel: _Optional[str] = ..., rtc_token: _Optional[str] = ..., rtc_uid_edge: _Optional[str] = ..., rtc_uid_engine: _Optional[str] = ...) -> None: ...

class DialAck(_message.Message):
    __slots__ = ("call_id", "accepted", "reason", "ts")
    CALL_ID_FIELD_NUMBER: _ClassVar[int]
    ACCEPTED_FIELD_NUMBER: _ClassVar[int]
    REASON_FIELD_NUMBER: _ClassVar[int]
    TS_FIELD_NUMBER: _ClassVar[int]
    call_id: str
    accepted: bool
    reason: str
    ts: _timestamp_pb2.Timestamp
    def __init__(self, call_id: _Optional[str] = ..., accepted: bool = ..., reason: _Optional[str] = ..., ts: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class CancelCommand(_message.Message):
    __slots__ = ("call_id", "reason", "ts")
    CALL_ID_FIELD_NUMBER: _ClassVar[int]
    REASON_FIELD_NUMBER: _ClassVar[int]
    TS_FIELD_NUMBER: _ClassVar[int]
    call_id: str
    reason: str
    ts: _timestamp_pb2.Timestamp
    def __init__(self, call_id: _Optional[str] = ..., reason: _Optional[str] = ..., ts: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class RtcCredentials(_message.Message):
    __slots__ = ("call_id", "rtc_token", "expires_at")
    CALL_ID_FIELD_NUMBER: _ClassVar[int]
    RTC_TOKEN_FIELD_NUMBER: _ClassVar[int]
    EXPIRES_AT_FIELD_NUMBER: _ClassVar[int]
    call_id: str
    rtc_token: str
    expires_at: _timestamp_pb2.Timestamp
    def __init__(self, call_id: _Optional[str] = ..., rtc_token: _Optional[str] = ..., expires_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class ConfigUpdate(_message.Message):
    __slots__ = ("log_level", "heartbeat_interval")
    LOG_LEVEL_FIELD_NUMBER: _ClassVar[int]
    HEARTBEAT_INTERVAL_FIELD_NUMBER: _ClassVar[int]
    log_level: LogLevelUpdate
    heartbeat_interval: HeartbeatIntervalUpdate
    def __init__(self, log_level: _Optional[_Union[LogLevelUpdate, _Mapping]] = ..., heartbeat_interval: _Optional[_Union[HeartbeatIntervalUpdate, _Mapping]] = ...) -> None: ...

class LogLevelUpdate(_message.Message):
    __slots__ = ("level",)
    LEVEL_FIELD_NUMBER: _ClassVar[int]
    level: str
    def __init__(self, level: _Optional[str] = ...) -> None: ...

class HeartbeatIntervalUpdate(_message.Message):
    __slots__ = ("interval_seconds",)
    INTERVAL_SECONDS_FIELD_NUMBER: _ClassVar[int]
    interval_seconds: int
    def __init__(self, interval_seconds: _Optional[int] = ...) -> None: ...

class RemoteDiagnostic(_message.Message):
    __slots__ = ("request_id", "upload_url", "expires_at")
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    UPLOAD_URL_FIELD_NUMBER: _ClassVar[int]
    EXPIRES_AT_FIELD_NUMBER: _ClassVar[int]
    request_id: str
    upload_url: str
    expires_at: _timestamp_pb2.Timestamp
    def __init__(self, request_id: _Optional[str] = ..., upload_url: _Optional[str] = ..., expires_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class CallEvent(_message.Message):
    __slots__ = ("call_id", "ts", "ringing", "connected", "remote_hangup", "device_error", "user_speaking_started", "user_speaking_stopped")
    CALL_ID_FIELD_NUMBER: _ClassVar[int]
    TS_FIELD_NUMBER: _ClassVar[int]
    RINGING_FIELD_NUMBER: _ClassVar[int]
    CONNECTED_FIELD_NUMBER: _ClassVar[int]
    REMOTE_HANGUP_FIELD_NUMBER: _ClassVar[int]
    DEVICE_ERROR_FIELD_NUMBER: _ClassVar[int]
    USER_SPEAKING_STARTED_FIELD_NUMBER: _ClassVar[int]
    USER_SPEAKING_STOPPED_FIELD_NUMBER: _ClassVar[int]
    call_id: str
    ts: _timestamp_pb2.Timestamp
    ringing: Ringing
    connected: Connected
    remote_hangup: RemoteHangup
    device_error: DeviceError
    user_speaking_started: UserSpeakingStarted
    user_speaking_stopped: UserSpeakingStopped
    def __init__(self, call_id: _Optional[str] = ..., ts: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., ringing: _Optional[_Union[Ringing, _Mapping]] = ..., connected: _Optional[_Union[Connected, _Mapping]] = ..., remote_hangup: _Optional[_Union[RemoteHangup, _Mapping]] = ..., device_error: _Optional[_Union[DeviceError, _Mapping]] = ..., user_speaking_started: _Optional[_Union[UserSpeakingStarted, _Mapping]] = ..., user_speaking_stopped: _Optional[_Union[UserSpeakingStopped, _Mapping]] = ...) -> None: ...

class Ringing(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class Connected(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class RemoteHangup(_message.Message):
    __slots__ = ("cause", "vendor_raw")
    CAUSE_FIELD_NUMBER: _ClassVar[int]
    VENDOR_RAW_FIELD_NUMBER: _ClassVar[int]
    cause: HangupCause
    vendor_raw: str
    def __init__(self, cause: _Optional[_Union[HangupCause, str]] = ..., vendor_raw: _Optional[str] = ...) -> None: ...

class DeviceError(_message.Message):
    __slots__ = ("device_id", "code", "detail")
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    CODE_FIELD_NUMBER: _ClassVar[int]
    DETAIL_FIELD_NUMBER: _ClassVar[int]
    device_id: int
    code: str
    detail: str
    def __init__(self, device_id: _Optional[int] = ..., code: _Optional[str] = ..., detail: _Optional[str] = ...) -> None: ...

class UserSpeakingStarted(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class UserSpeakingStopped(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class HardwareAlert(_message.Message):
    __slots__ = ("ts", "device_id", "signal_lost", "sim_arrears", "modem_init_failed", "audio_buffer_stalled", "sim_changed")
    TS_FIELD_NUMBER: _ClassVar[int]
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    SIGNAL_LOST_FIELD_NUMBER: _ClassVar[int]
    SIM_ARREARS_FIELD_NUMBER: _ClassVar[int]
    MODEM_INIT_FAILED_FIELD_NUMBER: _ClassVar[int]
    AUDIO_BUFFER_STALLED_FIELD_NUMBER: _ClassVar[int]
    SIM_CHANGED_FIELD_NUMBER: _ClassVar[int]
    ts: _timestamp_pb2.Timestamp
    device_id: int
    signal_lost: SignalLost
    sim_arrears: SimArrears
    modem_init_failed: ModemInitFailed
    audio_buffer_stalled: AudioBufferStalled
    sim_changed: SimChanged
    def __init__(self, ts: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., device_id: _Optional[int] = ..., signal_lost: _Optional[_Union[SignalLost, _Mapping]] = ..., sim_arrears: _Optional[_Union[SimArrears, _Mapping]] = ..., modem_init_failed: _Optional[_Union[ModemInitFailed, _Mapping]] = ..., audio_buffer_stalled: _Optional[_Union[AudioBufferStalled, _Mapping]] = ..., sim_changed: _Optional[_Union[SimChanged, _Mapping]] = ...) -> None: ...

class SignalLost(_message.Message):
    __slots__ = ("last_signal_strength",)
    LAST_SIGNAL_STRENGTH_FIELD_NUMBER: _ClassVar[int]
    last_signal_strength: int
    def __init__(self, last_signal_strength: _Optional[int] = ...) -> None: ...

class SimArrears(_message.Message):
    __slots__ = ("balance_text",)
    BALANCE_TEXT_FIELD_NUMBER: _ClassVar[int]
    balance_text: str
    def __init__(self, balance_text: _Optional[str] = ...) -> None: ...

class ModemInitFailed(_message.Message):
    __slots__ = ("stage", "detail")
    STAGE_FIELD_NUMBER: _ClassVar[int]
    DETAIL_FIELD_NUMBER: _ClassVar[int]
    stage: str
    detail: str
    def __init__(self, stage: _Optional[str] = ..., detail: _Optional[str] = ...) -> None: ...

class AudioBufferStalled(_message.Message):
    __slots__ = ("direction", "stalled_ms")
    DIRECTION_FIELD_NUMBER: _ClassVar[int]
    STALLED_MS_FIELD_NUMBER: _ClassVar[int]
    direction: str
    stalled_ms: int
    def __init__(self, direction: _Optional[str] = ..., stalled_ms: _Optional[int] = ...) -> None: ...

class SimChanged(_message.Message):
    __slots__ = ("new_iccid",)
    NEW_ICCID_FIELD_NUMBER: _ClassVar[int]
    new_iccid: str
    def __init__(self, new_iccid: _Optional[str] = ...) -> None: ...
