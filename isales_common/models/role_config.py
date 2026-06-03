"""role_config — per-campaign LLM slot config (main / referee / extractor).

Spec: data-model § role_config; ai-pipeline + role-prompt for behavior.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import BigInteger, Boolean, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from isales_common.enums import RoleKind
from isales_common.models.base import Base, TimestampMixin


class RoleConfig(Base, TimestampMixin):
    __tablename__ = "role_config"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    campaign_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("campaign.id", ondelete="CASCADE"), nullable=False, index=True
    )
    kind: Mapped[RoleKind] = mapped_column(String(16), nullable=False, index=True)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    # Nullable until the first prompt_version is created for this slot.
    current_prompt_version_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("prompt_version.id", use_alter=True), nullable=True
    )
    temperature: Mapped[float] = mapped_column(Float, nullable=False, default=0.7)
    top_p: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    ext_params: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
