"""add campaign.greeting

Revision ID: a908d5971908
Revises: b2c3d4e5f6a7
Create Date: 2026-05-29 16:00:00.000000

Spec: openspec/changes/campaign-fixed-greeting — capability `data-model`.
Additive only: new ``campaign.greeting`` column (Text, nullable). NULL
falls back to the LLM-generated greeting; non-NULL is played verbatim by
the engine (see ai-pipeline § "开场白不走管线" — fixed-template branch).

No data migration here; the one-time ``UPDATE campaign SET greeting = ...
WHERE id = 1`` is applied manually post-upgrade to preserve the existing
2026-05-29 experiment behavior (see openspec change ``Migration Plan``).

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "a908d5971908"
down_revision: Union[str, Sequence[str], None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "campaign",
        sa.Column("greeting", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("campaign", "greeting")
