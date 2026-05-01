"""agent — human seat for handoff.

Spec: data-model § agent; human-handoff for status semantics.
"""

from __future__ import annotations

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from isales_common.enums import AgentStatus
from isales_common.models.base import Base, TimestampMixin


class Agent(Base, TimestampMixin):
    __tablename__ = "agent"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    login_user: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    status: Mapped[AgentStatus] = mapped_column(
        String(16), nullable=False, default=AgentStatus.OFFLINE
    )
