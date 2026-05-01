"""Shared Pydantic base classes used across DTO schemas.

- :class:`AppModel` is the parent for plain DTOs.
- :class:`ORMModel` adds ``from_attributes=True`` so ORM rows can be loaded via
  ``Model.model_validate(orm_obj)``.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class AppModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class ORMModel(AppModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        str_strip_whitespace=True,
        from_attributes=True,
    )
