"""add campaign.ambient_audio / ambient_gain

Revision ID: a2c4e6b8d0f2
Revises: d1e2f3a4b5c6
Create Date: 2026-06-16 16:00:00.000000

Spec: openspec/changes/engine-ambient-background-mix — capability `data-model`
§ campaign.ambient_audio / ambient_gain. Additive only:

- ``campaign.ambient_audio`` (String(128), NULL) — background-noise asset id;
  NULL/empty → off, outbound audio path stays the existing pull-driven
  direct-push (byte-identical to before this change).
- ``campaign.ambient_gain`` (Float, NOT NULL, server_default 0.1) — linear mix
  level for the background relative to TTS (0.1 ≈ -20dB). server_default
  backfills existing rows so the NOT NULL add is safe; with ambient_audio NULL
  the value is inert.

Existing campaigns get ambient_audio NULL → background mixing OFF, behavior
unchanged.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "a2c4e6b8d0f2"
down_revision: Union[str, Sequence[str], None] = "d1e2f3a4b5c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "campaign",
        sa.Column("ambient_audio", sa.String(length=128), nullable=True),
    )
    op.add_column(
        "campaign",
        sa.Column(
            "ambient_gain",
            sa.Float(),
            nullable=False,
            server_default="0.1",
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("campaign", "ambient_gain")
    op.drop_column("campaign", "ambient_audio")
