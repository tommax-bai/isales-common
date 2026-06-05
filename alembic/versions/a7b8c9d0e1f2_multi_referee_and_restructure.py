"""multi referee + routing rules + restructure stream

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-06-05 16:00:00.000000

Spec: openspec/changes/engine-multi-referee-and-restructure — capabilities
`data-model` / `ai-pipeline` / `transcript`.

Upgrades the single-referee dual-LLM pipeline to N parallel referees + an
ordered routing-rule engine + an optional restructure (re-voice) stream:

- role_config.label: stable id routing rules bind to (referee/restructure rows).
- campaign.routing_rules / max_continuous_restructure / primary_referee_label.
- pipeline_trace: single referee_* columns → referee_results JSONB array +
  matched_rule + restructure_*.

Data migration (v1 has no real production data; row-level loss acceptable):
each existing campaign with a single referee row gets label="main_judge", the
campaign's primary_referee_label set to it, and an equivalent default
routing_rules set so behavior stays backward-compatible. The one narrowing is
goal_type: the old referee emitted it dynamically per turn; a static rule must
pin one, so the seed uses "appointment" (the common case). Admins re-author
routing_rules + referee prompts when adopting multi-referee.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a7b8c9d0e1f2"
down_revision: Union[str, Sequence[str], None] = "f6a7b8c9d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Equivalent default rules for an existing single referee. The old decision
# enum (continue/goal_achieved/customer_decline/transfer) is now the referee's
# `category`; continue needs no rule (no match → continue).
_DEFAULT_ROUTING_RULES = """[
  {"referee": "main_judge", "match": ["goal_achieved"],
   "action": {"type": "transition", "to": "goal_achieved", "goal_type": "appointment"}},
  {"referee": "main_judge", "match": ["transfer"],
   "action": {"type": "transition", "to": "transfer"}},
  {"referee": "main_judge", "match": ["customer_decline"],
   "action": {"type": "transition", "to": "customer_decline"}}
]"""


def upgrade() -> None:
    """Upgrade schema."""
    # --- role_config.label -------------------------------------------------
    op.add_column("role_config", sa.Column("label", sa.String(length=64), nullable=True))
    # Tag the existing single referee per campaign so default rules can bind.
    op.execute("UPDATE role_config SET label = 'main_judge' WHERE kind = 'referee' AND label IS NULL")
    # Unique per (campaign_id, label) among non-NULL labels (partial index).
    op.create_index(
        "uq_role_config_campaign_label",
        "role_config",
        ["campaign_id", "label"],
        unique=True,
        postgresql_where=sa.text("label IS NOT NULL"),
    )

    # --- campaign routing config ------------------------------------------
    op.add_column(
        "campaign",
        sa.Column("routing_rules", postgresql.JSONB(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "campaign",
        sa.Column("max_continuous_restructure", sa.Integer(), nullable=False, server_default="2"),
    )
    op.add_column(
        "campaign",
        sa.Column("primary_referee_label", sa.String(length=64), nullable=True),
    )
    # Seed equivalent default rules + primary referee for campaigns that had a
    # referee row (now labelled main_judge above).
    op.execute(
        "UPDATE campaign SET routing_rules = '"
        + _DEFAULT_ROUTING_RULES.replace("\n", " ")
        + "'::jsonb, primary_referee_label = 'main_judge' "
        "WHERE EXISTS (SELECT 1 FROM role_config rc "
        "WHERE rc.campaign_id = campaign.id AND rc.kind = 'referee')"
    )
    # Drop server_defaults — the ORM supplies them (default=list / default=2).
    op.alter_column("campaign", "routing_rules", server_default=None)
    op.alter_column("campaign", "max_continuous_restructure", server_default=None)

    # --- pipeline_trace: single referee_* → referee_results array ----------
    op.add_column(
        "pipeline_trace",
        sa.Column("referee_results", postgresql.JSONB(), nullable=False, server_default="[]"),
    )
    op.add_column("pipeline_trace", sa.Column("matched_rule", postgresql.JSONB(), nullable=True))
    op.add_column(
        "pipeline_trace",
        sa.Column("restructure_active", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("pipeline_trace", sa.Column("restructure_trigger", sa.String(length=32), nullable=True))
    op.add_column("pipeline_trace", sa.Column("restructure_source_text", sa.Text(), nullable=True))
    op.alter_column("pipeline_trace", "referee_results", server_default=None)
    op.alter_column("pipeline_trace", "restructure_active", server_default=None)
    # Old single-referee columns (v1 has no real trace data to preserve).
    op.drop_column("pipeline_trace", "referee_decision")
    op.drop_column("pipeline_trace", "referee_goal_type")
    op.drop_column("pipeline_trace", "referee_confidence")
    op.drop_column("pipeline_trace", "referee_duration_ms")


def downgrade() -> None:
    """Downgrade schema."""
    # pipeline_trace: restore single referee_* columns.
    op.add_column("pipeline_trace", sa.Column("referee_duration_ms", sa.Integer(), nullable=True))
    op.add_column("pipeline_trace", sa.Column("referee_confidence", sa.Float(), nullable=True))
    op.add_column("pipeline_trace", sa.Column("referee_goal_type", sa.Text(), nullable=True))
    op.add_column("pipeline_trace", sa.Column("referee_decision", sa.Text(), nullable=True))
    op.drop_column("pipeline_trace", "restructure_source_text")
    op.drop_column("pipeline_trace", "restructure_trigger")
    op.drop_column("pipeline_trace", "restructure_active")
    op.drop_column("pipeline_trace", "matched_rule")
    op.drop_column("pipeline_trace", "referee_results")

    # campaign routing config.
    op.drop_column("campaign", "primary_referee_label")
    op.drop_column("campaign", "max_continuous_restructure")
    op.drop_column("campaign", "routing_rules")

    # role_config.label.
    op.drop_index("uq_role_config_campaign_label", table_name="role_config")
    op.drop_column("role_config", "label")
