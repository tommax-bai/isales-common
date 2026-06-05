"""campaign.voice_id: BigInteger FK → vendor speaker string

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-06-05 14:30:00.000000

Spec: openspec/changes/campaign-greeting-tts-preview § 4C — capability
`data-model`. Voices are no longer catalogued in the DB; the admin types the
vendor speaker string (e.g. "zh_female_xiaohe_uranus_bigtts") directly into
the campaign form. ``campaign.voice_id`` switches from a BigInteger FK to
``voice_model.id`` into a plain ``String(128)`` holding the speaker string.

The FK is dropped and existing int values are nulled on conversion — the
engine never consumed ``campaign.voice_id`` before § 4B (always synthesized
with "default"), so no campaign has a meaningful voice to preserve.

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, Sequence[str], None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop the FK to voice_model. Name follows the project naming_convention
    # (base.py: fk_%(table)s_%(col)s_%(reftable)s).
    op.execute(
        "ALTER TABLE campaign DROP CONSTRAINT IF EXISTS "
        "fk_campaign_voice_id_voice_model"
    )
    op.alter_column(
        "campaign",
        "voice_id",
        existing_type=sa.BigInteger(),
        type_=sa.String(length=128),
        existing_nullable=True,
        postgresql_using="NULL",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        "campaign",
        "voice_id",
        existing_type=sa.String(length=128),
        type_=sa.BigInteger(),
        existing_nullable=True,
        postgresql_using="NULL",
    )
    op.create_foreign_key(
        "fk_campaign_voice_id_voice_model",
        "campaign",
        "voice_model",
        ["voice_id"],
        ["id"],
    )
