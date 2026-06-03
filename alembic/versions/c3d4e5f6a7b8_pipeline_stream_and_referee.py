"""pipeline stream and referee — dual-LLM architecture

Revision ID: c3d4e5f6a7b8
Revises: a908d5971908
Create Date: 2026-06-03 10:00:00.000000

Spec: openspec/changes/pipeline-stream-and-referee — capabilities
`data-model`, `ai-pipeline`, `transcript`.

BREAKING. The three-layer PK / judge / polish pipeline is replaced by the
dual-LLM architecture (main streaming + referee side-band + post-call
extractor). role_config.kind and prompt_version.scope_type are VARCHAR +
app-level validation (no PG enum type), so the kind swap is a plain DELETE of
the old rows — campaigns must be re-seeded with main/referee/extractor rows
post-upgrade (see change Migration Plan). v1 has no production data, so the
row deletion is acceptable; back up role_config / prompt_version first.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, Sequence[str], None] = "a908d5971908"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # --- role_config / prompt_version: drop the old {role, judge, polish} rows.
    # DELETE before any new kind is written so app validation never sees a stale
    # value. New main/referee/extractor rows are seeded manually post-upgrade.
    op.execute("DELETE FROM role_config WHERE kind IN ('role', 'judge', 'polish')")
    op.execute(
        "DELETE FROM prompt_version WHERE scope_type IN ('role', 'judge', 'polish')"
    )

    # --- pipeline_trace: drop the three-layer field set.
    for col in (
        "role_candidates",
        "judge_results",
        "polish_input",
        "polish_output",
        "polish_duration_ms",
        "polish_role_config_id",
        "polish_prompt_version_id",
        "final_selected_candidate_index",
    ):
        op.drop_column("pipeline_trace", col)

    # --- pipeline_trace: add the dual-LLM field set.
    op.add_column("pipeline_trace", sa.Column("main_reply_text", sa.Text(), nullable=True))
    op.add_column("pipeline_trace", sa.Column("main_duration_ms", sa.Integer(), nullable=True))
    op.add_column("pipeline_trace", sa.Column("main_tokens_in", sa.Integer(), nullable=True))
    op.add_column("pipeline_trace", sa.Column("main_tokens_out", sa.Integer(), nullable=True))
    op.add_column(
        "pipeline_trace",
        sa.Column(
            "main_fallback_used",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column("pipeline_trace", sa.Column("referee_decision", sa.Text(), nullable=True))
    op.add_column("pipeline_trace", sa.Column("referee_goal_type", sa.Text(), nullable=True))
    op.add_column("pipeline_trace", sa.Column("referee_confidence", sa.Float(), nullable=True))
    op.add_column("pipeline_trace", sa.Column("referee_duration_ms", sa.Integer(), nullable=True))
    op.add_column("pipeline_trace", sa.Column("first_audio_ms", sa.Integer(), nullable=True))
    op.add_column("pipeline_trace", sa.Column("error", sa.Text(), nullable=True))

    # --- call_record: post-call extractor columns.
    op.add_column("call_record", sa.Column("extracted", JSONB(), nullable=True))
    op.add_column("call_record", sa.Column("extract_status", sa.String(16), nullable=True))
    op.add_column("call_record", sa.Column("extract_error", sa.Text(), nullable=True))

    # --- campaign: filler opt-in flag (default off).
    op.add_column(
        "campaign",
        sa.Column(
            "filler_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    # --- data migration: carry historical extracted_fields to the new column so
    # past calls keep their CRM extraction without re-running the extractor.
    op.execute(
        """
        UPDATE call_record
        SET extracted = call_summary.extracted_fields,
            extract_status = 'done'
        FROM call_summary
        WHERE call_record.id = call_summary.call_record_id
          AND call_summary.extracted_fields IS NOT NULL
          AND call_summary.extracted_fields <> '{}'::jsonb
        """
    )


def downgrade() -> None:
    """Downgrade schema.

    Reverses the schema changes. Does NOT restore deleted role_config /
    prompt_version rows (v1 has no production data — restore from the manual
    pre-upgrade backup if needed).
    """
    op.drop_column("campaign", "filler_enabled")

    op.drop_column("call_record", "extract_error")
    op.drop_column("call_record", "extract_status")
    op.drop_column("call_record", "extracted")

    for col in (
        "error",
        "first_audio_ms",
        "referee_duration_ms",
        "referee_confidence",
        "referee_goal_type",
        "referee_decision",
        "main_fallback_used",
        "main_tokens_out",
        "main_tokens_in",
        "main_duration_ms",
        "main_reply_text",
    ):
        op.drop_column("pipeline_trace", col)

    op.add_column(
        "pipeline_trace",
        sa.Column("role_candidates", JSONB(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "pipeline_trace",
        sa.Column("judge_results", JSONB(), nullable=False, server_default="[]"),
    )
    op.add_column("pipeline_trace", sa.Column("polish_input", JSONB(), nullable=True))
    op.add_column("pipeline_trace", sa.Column("polish_output", sa.Text(), nullable=True))
    op.add_column("pipeline_trace", sa.Column("polish_duration_ms", sa.Integer(), nullable=True))
    op.add_column(
        "pipeline_trace",
        sa.Column(
            "polish_role_config_id",
            sa.BigInteger(),
            sa.ForeignKey("role_config.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "pipeline_trace",
        sa.Column(
            "polish_prompt_version_id",
            sa.BigInteger(),
            sa.ForeignKey("prompt_version.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "pipeline_trace",
        sa.Column("final_selected_candidate_index", sa.Integer(), nullable=True),
    )
