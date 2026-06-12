"""add campaign.auto_restructure_on_interrupt

Revision ID: a8b9c0d1e2f3
Revises: f7a8b9c0d1e2
Create Date: 2026-06-12 09:00:00.000000

Spec: openspec/changes/engine-auto-restructure-on-interrupt — capability
`data-model` § campaign.auto_restructure_on_interrupt / ai-pipeline §
被打断自动重组开关. Additive only: new ``campaign.auto_restructure_on_interrupt``
column (Boolean, NOT NULL, server_default false). When ON, the engine's decider
turns its no-explicit-rule-match fallback on a barge-in-interrupted turn
(``session.interrupt_remaining_text`` set) into restructure(interrupt_remaining)
instead of continue. server_default false backfills existing rows so the NOT NULL
add is safe and existing campaigns keep today's behavior (off).

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "a8b9c0d1e2f3"
down_revision: Union[str, Sequence[str], None] = "f7a8b9c0d1e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "campaign",
        sa.Column(
            "auto_restructure_on_interrupt",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("campaign", "auto_restructure_on_interrupt")
