"""DTOs for voice_model."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from isales_common.schemas._base import AppModel, ORMModel


class VoiceModelBase(AppModel):
    name: str = Field(min_length=1, max_length=128)
    provider: str = Field(min_length=1, max_length=64)
    voice_id: str = Field(min_length=1, max_length=128)
    sample_url: str | None = None


class VoiceModelCreate(VoiceModelBase):
    pass


class VoiceModelUpdate(AppModel):
    name: str | None = None
    provider: str | None = None
    voice_id: str | None = None
    sample_url: str | None = None


class VoiceModelRead(VoiceModelBase, ORMModel):
    id: int
    created_at: datetime
    updated_at: datetime
