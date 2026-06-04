"""add campaign.asr_eos_silence_ms

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-06-04 10:00:00.000000

Spec: openspec/changes/pipeline-latency-tail — capability `data-model` § A.
Additive only: new ``campaign.asr_eos_silence_ms`` column (Integer, nullable).
NULL falls back to the engine default (400ms) for the ASR EOS stable-silence
window; a smaller value opens the AI's turn faster but risks clipping a
hesitating caller's pause as "done" (see asr_volcengine partial_stable_s).

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "campaign",
        sa.Column("asr_eos_silence_ms", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("campaign", "asr_eos_silence_ms")
