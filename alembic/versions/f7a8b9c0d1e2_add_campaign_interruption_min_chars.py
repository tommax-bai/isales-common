"""add campaign.interruption_min_chars

Revision ID: f7a8b9c0d1e2
Revises: e6f7a8b9c0d1
Create Date: 2026-06-10 16:00:00.000000

Spec: openspec/changes/interruption-min-chars-and-mode-toggle — capability
`data-model` § campaign.interruption_min_chars / `interruption-detection`.
Additive only: new ``campaign.interruption_min_chars`` column (Integer, NOT
NULL, server_default 2). Promotes the engine's historical hardcoded
``default_rule(min_text_length=2)`` to a Campaign-level field; only read when
``interruption_rules`` is NULL (non-advanced mode). server_default backfills
existing rows so the NOT NULL add is safe and null-rule barge-in behavior is
byte-for-byte unchanged (length>=2).

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "f7a8b9c0d1e2"
down_revision: Union[str, Sequence[str], None] = "e6f7a8b9c0d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "campaign",
        sa.Column(
            "interruption_min_chars",
            sa.Integer(),
            nullable=False,
            server_default="2",
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("campaign", "interruption_min_chars")
