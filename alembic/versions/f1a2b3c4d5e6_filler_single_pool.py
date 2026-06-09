"""collapse filler_set into campaign (filler_phrase.campaign_id)

Revision ID: f1a2b3c4d5e6
Revises: c9d0e1f2a3b4
Create Date: 2026-06-09 16:00:00.000000

Spec: openspec/changes/filler-single-pool — capability `filler` / `data-model`.

Breaking: removes the `filler_set` grouping layer. `filler_phrase` now hangs off
`campaign` directly (`filler_phrase.campaign_id`). All phrases of a campaign's
former sets merge into one flat per-campaign pool — the set boundaries are NOT
preserved (the filler spec already forbade sets carrying any semantics, so the
merge loses no business meaning). Downgrade re-creates one default set per
campaign as a structural fallback; the original multi-set grouping is not
recoverable.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = "c9d0e1f2a3b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema — hang filler_phrase off campaign, drop filler_set."""
    # 1. add campaign_id (nullable first, to backfill from the owning set).
    op.add_column(
        "filler_phrase",
        sa.Column("campaign_id", sa.BigInteger(), nullable=True),
    )
    # 2. backfill: each phrase inherits its set's campaign.
    op.execute(
        """
        UPDATE filler_phrase fp
        SET campaign_id = fs.campaign_id
        FROM filler_set fs
        WHERE fp.filler_set_id = fs.id
        """
    )
    # 3. drop any orphan phrases whose set vanished (defensive; the FK forbids it).
    op.execute("DELETE FROM filler_phrase WHERE campaign_id IS NULL")
    # 4. enforce NOT NULL + index + FK to campaign.
    op.alter_column(
        "filler_phrase", "campaign_id", existing_type=sa.BigInteger(), nullable=False
    )
    op.create_index(
        op.f("ix_filler_phrase_campaign_id"),
        "filler_phrase",
        ["campaign_id"],
        unique=False,
    )
    op.create_foreign_key(
        op.f("fk_filler_phrase_campaign_id_campaign"),
        "filler_phrase",
        "campaign",
        ["campaign_id"],
        ["id"],
        ondelete="CASCADE",
    )
    # 5. drop the old set linkage. Postgres drops filler_set_id's FK + index with
    #    the column, after which nothing references filler_set → drop the table.
    op.drop_column("filler_phrase", "filler_set_id")
    op.drop_table("filler_set")


def downgrade() -> None:
    """Downgrade — structural rollback only.

    The original multi-set grouping is NOT recoverable: re-create filler_set, give
    every campaign that has phrases one default set, and re-point its phrases there.
    """
    op.create_table(
        "filler_set",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("campaign_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
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
            name=op.f("fk_filler_set_campaign_id_campaign"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_filler_set")),
    )
    op.create_index(
        op.f("ix_filler_set_campaign_id"), "filler_set", ["campaign_id"], unique=False
    )
    # one default set per campaign that currently owns phrases.
    op.execute(
        """
        INSERT INTO filler_set (campaign_id, name, sort_order)
        SELECT DISTINCT campaign_id, '默认垫词组', 0 FROM filler_phrase
        """
    )
    op.add_column(
        "filler_phrase",
        sa.Column("filler_set_id", sa.BigInteger(), nullable=True),
    )
    op.execute(
        """
        UPDATE filler_phrase fp
        SET filler_set_id = fs.id
        FROM filler_set fs
        WHERE fs.campaign_id = fp.campaign_id
        """
    )
    op.alter_column(
        "filler_phrase", "filler_set_id", existing_type=sa.BigInteger(), nullable=False
    )
    op.create_index(
        op.f("ix_filler_phrase_filler_set_id"),
        "filler_phrase",
        ["filler_set_id"],
        unique=False,
    )
    op.create_foreign_key(
        op.f("fk_filler_phrase_filler_set_id_filler_set"),
        "filler_phrase",
        "filler_set",
        ["filler_set_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_constraint(
        op.f("fk_filler_phrase_campaign_id_campaign"),
        "filler_phrase",
        type_="foreignkey",
    )
    op.drop_index(op.f("ix_filler_phrase_campaign_id"), table_name="filler_phrase")
    op.drop_column("filler_phrase", "campaign_id")
