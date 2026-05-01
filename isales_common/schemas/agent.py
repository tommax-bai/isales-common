"""DTOs for agent."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from isales_common.enums import AgentStatus
from isales_common.schemas._base import AppModel, ORMModel


class AgentBase(AppModel):
    name: str = Field(min_length=1, max_length=128)
    login_user: str = Field(min_length=1, max_length=64)


class AgentCreate(AgentBase):
    pass


class AgentUpdate(AppModel):
    name: str | None = None
    status: AgentStatus | None = None


class AgentRead(AgentBase, ORMModel):
    id: int
    status: AgentStatus
    created_at: datetime
    updated_at: datetime
