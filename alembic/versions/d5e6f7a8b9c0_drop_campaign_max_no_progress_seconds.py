"""drop campaign.max_no_progress_seconds

Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
Create Date: 2026-06-10 09:30:00.000000

Spec: openspec/changes/silence-drop-no-progress-timeout — capability
`silence-activation` / `call-state-machine` / `data-model`.

Removes the standalone, seconds-based no-progress timer column. The
silence-timeout hangup is now solely the silence-max path
(`max_silence_activations` + `silence_threshold_ms` + `silence_hangup_phrase`
→ `silence_max_reached`); a parallel wall-clock `max_no_progress_seconds`
timer was redundant and misleading. The column was nullable and NULL in
production (the feature was never enabled), so the drop is non-destructive.
Downgrade re-adds the nullable column (values not recoverable — all were NULL).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "d5e6f7a8b9c0"
down_revision: Union[str, Sequence[str], None] = "c4d5e6f7a8b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop the redundant no-progress timer column."""
    op.drop_column("campaign", "max_no_progress_seconds")


def downgrade() -> None:
    """Re-add the nullable column (values not recoverable — were all NULL)."""
    op.add_column(
        "campaign",
        sa.Column("max_no_progress_seconds", sa.Integer(), nullable=True),
    )
