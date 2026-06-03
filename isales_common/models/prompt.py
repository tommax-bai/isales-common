"""prompt_version — versioned LLM prompt content for main/referee/extractor slots.

Spec: data-model § prompt_version; role-prompt for prompt assembly rules.

pipeline-stream-and-referee: ``scope_type`` allowed values are
``{main, referee, extractor}`` (was ``{role, judge, polish}``).
"""

from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from isales_common.enums import PromptScopeType
from isales_common.models.base import Base, TimestampMixin


class PromptVersion(Base, TimestampMixin):
    __tablename__ = "prompt_version"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    scope_type: Mapped[PromptScopeType] = mapped_column(String(16), nullable=False, index=True)
    # No FK: scope can be a role_config id, a campaign id (for transfer_llm /
    # do_not_call_llm), or a global default — resolved by scope_type at app layer.
    scope_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)

    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
