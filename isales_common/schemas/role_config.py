"""DTOs for role_config."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from isales_common.enums import RoleKind
from isales_common.schemas._base import AppModel, ORMModel


class RoleConfigBase(AppModel):
    campaign_id: int
    kind: RoleKind
    model: str = Field(min_length=1, max_length=128)
    current_prompt_version_id: int | None = None
    temperature: float = Field(ge=0.0, le=2.0)
    top_p: float = Field(ge=0.0, le=1.0)
    ext_params: dict[str, Any] = Field(default_factory=dict)
    enabled: bool


class RoleConfigCreate(RoleConfigBase):
    pass


class RoleConfigUpdate(AppModel):
    kind: RoleKind | None = None
    model: str | None = None
    current_prompt_version_id: int | None = None
    temperature: float | None = None
    top_p: float | None = None
    ext_params: dict[str, Any] | None = None
    enabled: bool | None = None


class RoleConfigRead(RoleConfigBase, ORMModel):
    id: int
    created_at: datetime
    updated_at: datetime
