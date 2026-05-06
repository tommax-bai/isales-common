"""add device.last_call_at

Revision ID: 580b817550c8
Revises: 017c370560ce
Create Date: 2026-05-06 10:34:59.447045

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '580b817550c8'
down_revision: Union[str, Sequence[str], None] = '017c370560ce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'device',
        sa.Column('last_call_at', sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('device', 'last_call_at')
