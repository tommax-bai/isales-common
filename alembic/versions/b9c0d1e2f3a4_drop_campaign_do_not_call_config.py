"""drop dead campaign do-not-call config (keywords / llm_enabled / llm_prompt_version_id)

Revision ID: b9c0d1e2f3a4
Revises: a8b9c0d1e2f3
Create Date: 2026-06-12 12:00:00.000000

Spec: openspec/changes/remove-do-not-call-campaign-config — capabilities
`data-model` § campaign 全表清单 / `retry-followup` § "勿打"识别. Destructive:
drops the three campaign-level do-not-call config columns
``do_not_call_keywords`` / ``do_not_call_llm_enabled`` /
``do_not_call_llm_prompt_version_id`` and the FK
``fk_campaign_do_not_call_llm_prompt_version_id_prompt_version``. These were
never read by engine/scheduler/worker at runtime (the keyword arm had no ASR
matcher, the independent-LLM-judge arm was deferred in impl-engine and never
built, and the prompt-version id could not reach the engine — PromptVersionsSnapshot
has no slot for it). The ``do_not_call`` lead-status outcome stays live via the
generic routing-rule ``goal_type='do_not_call'`` / ``do_not_call_marked`` marker
path, which does not touch these columns. Column data is discarded (never consumed).
Downgrade re-adds the columns + FK with their original definitions.

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "b9c0d1e2f3a4"
down_revision: Union[str, Sequence[str], None] = "a8b9c0d1e2f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint(
        op.f("fk_campaign_do_not_call_llm_prompt_version_id_prompt_version"),
        "campaign",
        type_="foreignkey",
    )
    op.drop_column("campaign", "do_not_call_llm_prompt_version_id")
    op.drop_column("campaign", "do_not_call_llm_enabled")
    op.drop_column("campaign", "do_not_call_keywords")


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column(
        "campaign",
        sa.Column(
            "do_not_call_keywords",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column(
        "campaign",
        sa.Column(
            "do_not_call_llm_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "campaign",
        sa.Column(
            "do_not_call_llm_prompt_version_id",
            sa.BigInteger(),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        op.f("fk_campaign_do_not_call_llm_prompt_version_id_prompt_version"),
        "campaign",
        "prompt_version",
        ["do_not_call_llm_prompt_version_id"],
        ["id"],
    )
