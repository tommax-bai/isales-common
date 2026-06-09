"""DTOs for filler_phrase.

Spec: filler for selection rules. A campaign owns a single flat pool of filler
phrases (no ``filler_set`` grouping layer post-``filler-single-pool``).
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
    campaign_id: int


class FillerPhraseUpdate(AppModel):
    phrase: str | None = None
    audio_url: str | None = None
    generation_status: GenerationStatus | None = None


class FillerPhraseRead(FillerPhraseBase, ORMModel):
    id: int
    campaign_id: int
    generation_status: GenerationStatus
    created_at: datetime
    updated_at: datetime
