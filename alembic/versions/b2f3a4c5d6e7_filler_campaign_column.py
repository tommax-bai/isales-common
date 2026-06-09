"""collapse filler_phrase table into campaign.filler_phrases

Revision ID: b2f3a4c5d6e7
Revises: f1a2b3c4d5e6
Create Date: 2026-06-09 16:30:00.000000

Spec: openspec/changes/filler-campaign-column — capability `filler` / `data-model`.

Collapses the `filler_phrase` table into a `campaign.filler_phrases` JSONB
list[str] column (same pattern as silence_phrases / interruption_whitelist).
Each campaign's phrases (ordered by id) become a string array; the per-phrase
`audio_url` / `generation_status` (stage-6 OSS pre-render fields, dormant in
v1.0) are dropped. Downgrade re-creates the table from the array as a structural
fallback — audio_url NULL, generation_status 'pending' (not recoverable).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "b2f3a4c5d6e7"
down_revision: Union[str, Sequence[str], None] = "f1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade — campaign.filler_phrases column, drop filler_phrase table."""
    # add NOT NULL column to an existing table: needs a temporary server_default.
    op.add_column(
        "campaign",
        sa.Column(
            "filler_phrases",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    # migrate: each campaign's phrases (ordered by id) -> string array.
    op.execute(
        """
        UPDATE campaign c
        SET filler_phrases = COALESCE(
            (SELECT jsonb_agg(fp.phrase ORDER BY fp.id)
             FROM filler_phrase fp WHERE fp.campaign_id = c.id),
            '[]'::jsonb
        )
        """
    )
    op.drop_table("filler_phrase")
    # drop the server_default — the app supplies the value (model default=list,
    # matching silence_phrases / interruption_whitelist which carry no DB default).
    op.alter_column("campaign", "filler_phrases", server_default=None)


def downgrade() -> None:
    """Downgrade — re-create filler_phrase from the array (lossy).

    audio_url / generation_status are NOT recoverable (they were dropped).
    """
    op.create_table(
        "filler_phrase",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("campaign_id", sa.BigInteger(), nullable=False),
        sa.Column("phrase", sa.String(length=512), nullable=False),
        sa.Column("audio_url", sa.String(length=512), nullable=True),
        sa.Column(
            "generation_status",
            sa.String(length=16),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["campaign_id"],
            ["campaign.id"],
            name=op.f("fk_filler_phrase_campaign_id_campaign"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_filler_phrase")),
    )
    op.create_index(
        op.f("ix_filler_phrase_campaign_id"),
        "filler_phrase",
        ["campaign_id"],
        unique=False,
    )
    # expand each campaign's array back into rows.
    op.execute(
        """
        INSERT INTO filler_phrase (campaign_id, phrase)
        SELECT c.id, elem.value
        FROM campaign c,
             LATERAL jsonb_array_elements_text(c.filler_phrases) AS elem(value)
        WHERE jsonb_typeof(c.filler_phrases) = 'array'
        """
    )
    op.drop_column("campaign", "filler_phrases")
