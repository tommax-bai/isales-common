"""DTOs for prompt_version.

Spec: role-prompt for prompt assembly rules.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from isales_common.enums import PromptScopeType
from isales_common.schemas._base import AppModel, ORMModel


class PromptVersionBase(AppModel):
    scope_type: PromptScopeType
    scope_id: int
    content: str = Field(min_length=1)
    created_by: str | None = None
    is_active: bool = False


class PromptVersionCreate(PromptVersionBase):
    pass


class PromptVersionUpdate(AppModel):
    content: str | None = None
    is_active: bool | None = None


class PromptVersionRead(PromptVersionBase, ORMModel):
    id: int
    created_at: datetime
    updated_at: datetime
