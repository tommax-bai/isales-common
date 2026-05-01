"""Schema for ``campaign.extraction_fields`` (JSONB array element).

Spec: goal-achievement § Data Schema; field extraction is performed by the role
LLM, this struct only declares which fields the campaign expects to receive.
"""

from __future__ import annotations

from typing import Literal

from isales_common.schemas._base import AppModel

ExtractionFieldType = Literal["string", "number", "boolean", "datetime"]


class ExtractionField(AppModel):
    name: str
    type: ExtractionFieldType
    description: str | None = None
    required: bool = False
