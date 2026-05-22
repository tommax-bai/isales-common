"""DTOs for filler_set + filler_phrase.

Spec: filler for selection rules.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from isales_common.enums import GenerationStatus
from isales_common.schemas._base import AppModel, ORMModel


class FillerPhraseBase(AppModel):
    phrase: str = Field(min_length=1, max_length=512)
    audio_url: str | None = None


class FillerPhraseCreate(FillerPhraseBase):
    filler_set_id: int


class FillerPhraseUpdate(AppModel):
    phrase: str | None = None
    audio_url: str | None = None
    generation_status: GenerationStatus | None = None


class FillerPhraseRead(FillerPhraseBase, ORMModel):
    id: int
    filler_set_id: int
    generation_status: GenerationStatus
    created_at: datetime
    updated_at: datetime


class FillerSetBase(AppModel):
    campaign_id: int
    name: str = Field(min_length=1, max_length=128)
    sort_order: int = 0


class FillerSetCreate(FillerSetBase):
    pass


class FillerSetUpdate(AppModel):
    name: str | None = None
    sort_order: int | None = None


class FillerSetRead(FillerSetBase, ORMModel):
    id: int
    created_at: datetime
    updated_at: datetime
