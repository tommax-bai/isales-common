"""add appointment table

Revision ID: a1b2c3d4e5f6
Revises: 580b817550c8
Create Date: 2026-05-19 12:00:00.000000

Spec: openspec/changes/web-admin-ui-redesign — capability `appointment`.
Additive only: new ``appointment`` table with FKs to ``lead`` (CASCADE)
and ``call_record`` (SET NULL). No data migration; safe to apply on
populated cloud DB. The new ``lead.status`` enum values ``appointed`` /
``visited`` ride on the existing ``String(24)`` column without DDL.

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "580b817550c8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "appointment",
        sa.Column(
            "id",
            sa.BigInteger(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column("lead_id", sa.BigInteger(), nullable=False),
        sa.Column("created_from_call_id", sa.BigInteger(), nullable=True),
        sa.Column(
            "appointment_time",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=16),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("store_address", sa.Text(), nullable=False),
        sa.Column("directions", sa.Text(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["lead_id"],
            ["lead.id"],
            ondelete="CASCADE",
            name=op.f("fk_appointment_lead_id_lead"),
        ),
        sa.ForeignKeyConstraint(
            ["created_from_call_id"],
            ["call_record.id"],
            ondelete="SET NULL",
            name=op.f("fk_appointment_created_from_call_id_call_record"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_appointment")),
    )
    op.create_index(
        op.f("ix_appointment_lead_id"),
        "appointment",
        ["lead_id"],
    )
    op.create_index(
        op.f("ix_appointment_created_from_call_id"),
        "appointment",
        ["created_from_call_id"],
    )
    op.create_index(
        op.f("ix_appointment_appointment_time"),
        "appointment",
        ["appointment_time"],
    )
    op.create_index(
        op.f("ix_appointment_status"),
        "appointment",
        ["status"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_appointment_status"), table_name="appointment")
    op.drop_index(
        op.f("ix_appointment_appointment_time"),
        table_name="appointment",
    )
    op.drop_index(
        op.f("ix_appointment_created_from_call_id"),
        table_name="appointment",
    )
    op.drop_index(op.f("ix_appointment_lead_id"), table_name="appointment")
    op.drop_table("appointment")
