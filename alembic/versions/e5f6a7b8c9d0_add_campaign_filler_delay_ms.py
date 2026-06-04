"""add campaign.filler_delay_ms

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-06-04 13:00:00.000000

Spec: openspec/changes/tts-cache-and-gated-filler — capability `data-model` § B.
Additive only: new ``campaign.filler_delay_ms`` column (Integer, nullable).
NULL falls back to the engine default (600ms) for the filler time-gate: a
filler is played only when the main reply's first audio hasn't started within
this window.

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, Sequence[str], None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "campaign",
        sa.Column("filler_delay_ms", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("campaign", "filler_delay_ms")
