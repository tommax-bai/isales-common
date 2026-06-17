"""add campaign.barge_in_fadeout_ms

Revision ID: f0a1b2c3d4e5
Revises: c4e6a8b0d2f3
Create Date: 2026-06-17 18:00:00.000000

Spec: openspec/changes/engine-barge-in-fade-out — capability
`interruption-detection`. Additive only:

- ``campaign.barge_in_fadeout_ms`` (Integer, NOT NULL, server_default "100") —
  on a barge-in the still-buffered AI voice is ramped down over this many ms
  instead of being hard-cut to silence (an amplitude step = audible click + a
  faster-than-human stop). ~100ms reads as a human trail-off; 15-30ms only
  declicks; 0 keeps the legacy hard cut. server_default backfills existing rows
  so the NOT NULL add is safe and in-flight calls are unaffected.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "f0a1b2c3d4e5"
down_revision: Union[str, Sequence[str], None] = "c4e6a8b0d2f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "campaign",
        sa.Column(
            "barge_in_fadeout_ms",
            sa.Integer(),
            nullable=False,
            server_default="100",
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("campaign", "barge_in_fadeout_ms")
