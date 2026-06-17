"""add campaign.wrap_up_referee_enabled

Revision ID: c4e6a8b0d2f3
Revises: b3d5f7a9c1e2
Create Date: 2026-06-17 16:00:00.000000

Spec: openspec/changes/engine-wrap-up-bypass-referee — capability
`ai-pipeline` / `goal-achievement`. Additive only:

- ``campaign.wrap_up_referee_enabled`` (Boolean, NOT NULL, server_default false)
  — opt-in. When true, a bypass (non-gating, parallel) wrap-up referee classifies
  the customer's post-farewell reply; no substantive new question → early hangup.
  Default false → wrap-up behavior unchanged. server_default backfills existing
  rows so the NOT NULL add is safe and in-flight calls are unaffected.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "c4e6a8b0d2f3"
down_revision: Union[str, Sequence[str], None] = "b3d5f7a9c1e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "campaign",
        sa.Column(
            "wrap_up_referee_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("campaign", "wrap_up_referee_enabled")
