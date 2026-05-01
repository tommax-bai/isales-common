"""DTOs for callback_config / callback_log.

Spec: webhook-callback. ``signing_secret`` is sensitive; the Read DTO never
exposes it — generation/rotation goes through a dedicated API.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import Field

from isales_common.enums import CallbackStatus
from isales_common.schemas._base import AppModel, ORMModel
from isales_common.schemas.jsonb import CallbackTrigger, RetryPolicy

HttpMethod = Literal["POST", "PUT", "PATCH"]


class CallbackConfigBase(AppModel):
    campaign_id: int
    name: str = Field(min_length=1, max_length=128)
    trigger: CallbackTrigger
    url: str = Field(min_length=1, max_length=1024)
    method: HttpMethod = "POST"
    headers: dict[str, str] = Field(default_factory=dict)
    payload_template: str = Field(min_length=1)
    retry_policy: RetryPolicy
    timeout_seconds: int | None = Field(default=None, ge=1)
    enabled: bool = True


class CallbackConfigCreate(CallbackConfigBase):
    pass


class CallbackConfigUpdate(AppModel):
    name: str | None = None
    trigger: CallbackTrigger | None = None
    url: str | None = None
    method: HttpMethod | None = None
    headers: dict[str, str] | None = None
    payload_template: str | None = None
    retry_policy: RetryPolicy | None = None
    timeout_seconds: int | None = None
    enabled: bool | None = None


class CallbackConfigRead(CallbackConfigBase, ORMModel):
    id: int
    created_at: datetime
    updated_at: datetime


class CallbackLogRead(ORMModel):
    id: int
    callback_config_id: int
    call_record_id: int
    status: CallbackStatus
    request_body: str | None = None
    response_code: int | None = None
    response_body: str | None = None
    retry_count: int
    attempt_at: datetime | None = None
    next_retry_at: datetime | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class CallbackLogCreate(AppModel):
    callback_config_id: int
    call_record_id: int
    status: CallbackStatus = CallbackStatus.PENDING
    request_body: str | None = None
    response_code: int | None = None
    response_body: str | None = None
    retry_count: int = 0
    attempt_at: datetime | None = None
    next_retry_at: datetime | None = None
    error_message: str | None = None


CallbackPayloadContext = dict[str, Any]
"""Render-time context dict — `lead`, `call`, `call_summary`, `extracted` keys.

Validated only loosely here; the Jinja2 sandbox renders against this dict.
"""
