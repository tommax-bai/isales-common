"""campaign.interruption_rules + drop primary_referee_label

Revision ID: c9d0e1f2a3b4
Revises: b8c9d0e1f2a3
Create Date: 2026-06-08 12:00:00.000000

Spec: openspec/changes/engine-interruption-rule-tree — capabilities
`interruption-detection` / `ai-pipeline`.

- campaign.interruption_rules (JSONB, nullable): composable barge-in rule tree
  (port of voxen core/interruption/). NULL → engine synthesizes a backward-compat
  default tree from interruption_whitelist + interruption_min_duration_ms, so
  existing campaigns keep current behavior with no data backfill (design D4).
- DROP campaign.primary_referee_label: its only functional consumer was the
  decider's low-confidence restructure fallback, which is removed by this change
  (dead branch — referees hardcode confidence=1.0). Removed across all repos
  (design D8). Downgrade re-adds the nullable column (no value restore).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "c9d0e1f2a3b4"
down_revision: Union[str, Sequence[str], None] = "b8c9d0e1f2a3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "campaign",
        sa.Column(
            "interruption_rules",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.drop_column("campaign", "primary_referee_label")


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column(
        "campaign",
        sa.Column("primary_referee_label", sa.String(length=64), nullable=True),
    )
    op.drop_column("campaign", "interruption_rules")
