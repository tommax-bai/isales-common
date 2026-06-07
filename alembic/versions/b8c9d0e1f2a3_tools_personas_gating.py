"""tools + personas + pre-reply gating columns

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-06-07 10:00:00.000000

Spec: openspec/changes/engine-tools-multidialogue-gating — capabilities
`data-model` / `ai-pipeline` / `transcript`.

Purely additive (v1 has no down-migration dependency; rollback leaves the new
columns harmless):

- campaign.tools (JSONB map alias→tool config), persona_fanout_cap (total
  speculative dialogue routes incl main, default 1), referee_timeout_ms
  (pre-reply gating timeout, default 600), referee_fail_open_route (default
  "main").
- pipeline_trace.selected_route_id / selected_route_kind / persona_candidates
  (gating route selection trace; all nullable).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "b8c9d0e1f2a3"
down_revision: Union[str, Sequence[str], None] = "a7b8c9d0e1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema (additive)."""
    # --- campaign: gating + multi-persona ----------------------------------
    op.add_column(
        "campaign",
        sa.Column(
            "tools",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.add_column(
        "campaign",
        sa.Column(
            "persona_fanout_cap", sa.Integer(), nullable=False, server_default="1"
        ),
    )
    op.add_column(
        "campaign",
        sa.Column(
            "referee_timeout_ms", sa.Integer(), nullable=False, server_default="600"
        ),
    )
    op.add_column(
        "campaign",
        sa.Column(
            "referee_fail_open_route",
            sa.String(length=64),
            nullable=False,
            server_default="main",
        ),
    )

    # --- pipeline_trace: gating route selection ----------------------------
    op.add_column(
        "pipeline_trace",
        sa.Column("selected_route_id", sa.String(length=96), nullable=True),
    )
    op.add_column(
        "pipeline_trace",
        sa.Column("selected_route_kind", sa.String(length=16), nullable=True),
    )
    op.add_column(
        "pipeline_trace",
        sa.Column(
            "persona_candidates",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("pipeline_trace", "persona_candidates")
    op.drop_column("pipeline_trace", "selected_route_kind")
    op.drop_column("pipeline_trace", "selected_route_id")
    op.drop_column("campaign", "referee_fail_open_route")
    op.drop_column("campaign", "referee_timeout_ms")
    op.drop_column("campaign", "persona_fanout_cap")
    op.drop_column("campaign", "tools")
