"""add pipeline_trace.main_first_token_ms / main_first_sentence_ms

Revision ID: d1e2f3a4b5c6
Revises: c0d1e2f3a4b5
Create Date: 2026-06-15 11:00:00.000000

Spec: openspec/changes/engine-turn-latency-and-tts-guard — capability
`data-model` § "pipeline_trace 首 token / 首句延迟列".
Additive only: two nullable Integer columns on ``pipeline_trace`` carrying the
main LLM's first-token (TTFT) and first-sentence latencies (ms from generation
start), computed in MainStreamResult but previously discarded at turn end. With
main_duration_ms + first_audio_ms they decompose one turn's "LLM received →
user playback" per node. Nullable: historic rows + fallback / no-token turns
stay NULL. downgrade drops both.

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "d1e2f3a4b5c6"
down_revision: Union[str, Sequence[str], None] = "c0d1e2f3a4b5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "pipeline_trace",
        sa.Column("main_first_token_ms", sa.Integer(), nullable=True),
    )
    op.add_column(
        "pipeline_trace",
        sa.Column("main_first_sentence_ms", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("pipeline_trace", "main_first_sentence_ms")
    op.drop_column("pipeline_trace", "main_first_token_ms")
