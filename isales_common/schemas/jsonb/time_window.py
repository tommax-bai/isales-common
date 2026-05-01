"""Schema for ``campaign.time_windows`` (JSONB array element).

Spec: time-window § Campaign 级多窗口配置.
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import Field, field_validator

from isales_common.schemas._base import AppModel

WeekDay = Literal["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
_HHMM_RE = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")


class TimeWindow(AppModel):
    days: list[WeekDay] = Field(min_length=1)
    start: str
    end: str

    @field_validator("start", "end")
    @classmethod
    def _validate_hhmm(cls, v: str) -> str:
        if not _HHMM_RE.match(v):
            raise ValueError("must be HH:MM in 24-hour clock")
        return v
