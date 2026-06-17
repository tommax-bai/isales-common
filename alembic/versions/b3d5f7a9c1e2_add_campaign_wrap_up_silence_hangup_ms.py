"""add campaign.wrap_up_silence_hangup_ms

Revision ID: b3d5f7a9c1e2
Revises: a2c4e6b8d0f2
Create Date: 2026-06-17 11:30:00.000000

Spec: openspec/changes/engine-wrap-up-silence-hangup — capability
`goal-achievement` § "收尾期间的特殊情况处理". Additive only:

- ``campaign.wrap_up_silence_hangup_ms`` (Integer, NOT NULL, server_default
  6000) — WRAPPING_UP-phase user-silence hangup window. After the farewell, if
  the customer stays silent this long the engine hangs up directly, skipping the
  "你好，还在么？" reactivation ladder (which stays main-phase only). Deliberately
  longer than silence_threshold_ms (3000) to give thinking time after goodbye;
  wrap_up counters remain the hard cap. server_default backfills existing rows so
  the NOT NULL add is safe and in-flight calls are unaffected.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "b3d5f7a9c1e2"
down_revision: Union[str, Sequence[str], None] = "a2c4e6b8d0f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "campaign",
        sa.Column(
            "wrap_up_silence_hangup_ms",
            sa.Integer(),
            nullable=False,
            server_default="6000",
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("campaign", "wrap_up_silence_hangup_ms")
