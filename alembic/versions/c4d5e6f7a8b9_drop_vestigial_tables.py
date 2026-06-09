"""drop vestigial tables: appointment, voice_model, handoff_task

Revision ID: c4d5e6f7a8b9
Revises: b2f3a4c5d6e7
Create Date: 2026-06-09 17:00:00.000000

Spec: openspec/changes/admin-prune-vestigial-features — capability `data-model`
(removes the `appointment` capability, modifies `human-handoff`).

Drops three write-never / no-runtime-consumer tables whose admin features are
being removed end-to-end:
- `appointment`  — manual-only booking ledger; no engine/scheduler/worker
                   producer or consumer (created in a1b2c3d4e5f6).
- `voice_model`  — TTS voice catalog; engine reads free-text campaign.voice_id
                   instead, and the FK was severed in f6a7b8c9d0e1 (orphan table).
- `handoff_task` — transfer-to-human queue; never written (engine marks the
                   lead TRANSFERRED + hangs up, no row insert ever happened).

All three were created in the genesis migration 017c370560ce; this drops them at
head. v1.0 has no production data, so the drop is safe. ``downgrade()`` re-creates
the tables structurally (DDL copied verbatim from their create migrations); it
deliberately does NOT re-add the severed campaign->voice_model FK (campaign.voice_id
is String now, per f6a7b8c9d0e1).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "c4d5e6f7a8b9"
down_revision: Union[str, Sequence[str], None] = "b2f3a4c5d6e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop appointment, handoff_task, voice_model (+ their indexes)."""
    # appointment — child FKs to lead (CASCADE) + call_record (SET NULL)
    op.drop_index(op.f("ix_appointment_status"), table_name="appointment")
    op.drop_index(op.f("ix_appointment_appointment_time"), table_name="appointment")
    op.drop_index(
        op.f("ix_appointment_created_from_call_id"), table_name="appointment"
    )
    op.drop_index(op.f("ix_appointment_lead_id"), table_name="appointment")
    op.drop_table("appointment")

    # handoff_task — child FKs to agent (SET NULL) + call_record (RESTRICT)
    op.drop_index(op.f("ix_handoff_task_status"), table_name="handoff_task")
    op.drop_index(op.f("ix_handoff_task_call_record_id"), table_name="handoff_task")
    op.drop_index(op.f("ix_handoff_task_agent_id"), table_name="handoff_task")
    op.drop_table("handoff_task")

    # voice_model — no FK, PK only
    op.drop_table("voice_model")


def downgrade() -> None:
    """Re-create the three tables structurally (DDL from their create migrations).

    Does NOT restore the campaign->voice_model FK (severed in f6a7b8c9d0e1; the
    campaign.voice_id column is String(128) now).
    """
    # voice_model (from 017c370560ce)
    op.create_table(
        "voice_model",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("voice_id", sa.String(length=128), nullable=False),
        sa.Column("sample_url", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_voice_model")),
    )

    # handoff_task (from 017c370560ce)
    op.create_table(
        "handoff_task",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("call_record_id", sa.BigInteger(), nullable=False),
        sa.Column("agent_id", sa.BigInteger(), nullable=True),
        sa.Column("trigger_type", sa.String(length=16), nullable=False),
        sa.Column("trigger_detail", sa.String(length=512), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("picked_up_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["agent_id"],
            ["agent.id"],
            name=op.f("fk_handoff_task_agent_id_agent"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["call_record_id"],
            ["call_record.id"],
            name=op.f("fk_handoff_task_call_record_id_call_record"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_handoff_task")),
    )
    op.create_index(
        op.f("ix_handoff_task_agent_id"), "handoff_task", ["agent_id"], unique=False
    )
    op.create_index(
        op.f("ix_handoff_task_call_record_id"),
        "handoff_task",
        ["call_record_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_handoff_task_status"), "handoff_task", ["status"], unique=False
    )

    # appointment (from a1b2c3d4e5f6)
    op.create_table(
        "appointment",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("lead_id", sa.BigInteger(), nullable=False),
        sa.Column("created_from_call_id", sa.BigInteger(), nullable=True),
        sa.Column("appointment_time", sa.DateTime(timezone=True), nullable=False),
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
    op.create_index(op.f("ix_appointment_lead_id"), "appointment", ["lead_id"])
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
    op.create_index(op.f("ix_appointment_status"), "appointment", ["status"])
