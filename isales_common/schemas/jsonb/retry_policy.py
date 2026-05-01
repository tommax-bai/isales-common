"""Schema for ``callback_config.retry_policy`` (JSONB).

Spec: webhook-callback § 重试策略.
"""

from __future__ import annotations

from pydantic import Field

from isales_common.schemas._base import AppModel


class RetryPolicy(AppModel):
    intervals_seconds: list[int] = Field(default_factory=list)
    max_attempts: int = Field(ge=1)
