"""strip ai_reply.interrupted from call_record.transcript

Revision ID: e6f7a8b9c0d1
Revises: d5e6f7a8b9c0
Create Date: 2026-06-10 14:40:00.000000

Spec: openspec/changes/fix-transcript-schema-drift — capability `transcript`.

The engine previously wrote an unregistered ``interrupted`` boolean onto
``ai_reply`` transcript events. That field is not part of the transcript event
contract (transcript spec § 事件类型枚举) and is consumed nowhere
(worker/api/web). isales-api's ``CallRecordRead`` validates the transcript with
``extra="forbid"``, so any stored ``ai_reply`` carrying ``interrupted`` makes
``GET /calls`` 500 (the 外呼记录 list page won't open).

This data migration strips the ``interrupted`` key from every ``ai_reply``
element in ``call_record.transcript``. It is idempotent (elements without the
key are untouched) and only rewrites rows that actually contain an ``ai_reply``
element with ``interrupted``. Array order is preserved via WITH ORDINALITY.

The engine stops writing the field in the same change, so no new rows acquire
it after deploy.

Downgrade is a no-op: the stripped values were write-only and are not
recoverable (and were never read by anything).
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "e6f7a8b9c0d1"
down_revision: Union[str, Sequence[str], None] = "d5e6f7a8b9c0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Strip ``interrupted`` key from all ai_reply transcript events."""
    op.execute(
        """
        UPDATE call_record AS cr
        SET transcript = sub.new_transcript
        FROM (
            SELECT c.id,
                   jsonb_agg(
                       CASE
                           WHEN elem->>'type' = 'ai_reply'
                           THEN elem - 'interrupted'
                           ELSE elem
                       END
                       ORDER BY ord
                   ) AS new_transcript
            FROM call_record AS c,
                 LATERAL jsonb_array_elements(c.transcript)
                         WITH ORDINALITY AS t(elem, ord)
            WHERE jsonb_typeof(c.transcript) = 'array'
            GROUP BY c.id
        ) AS sub
        WHERE cr.id = sub.id
          AND EXISTS (
              SELECT 1
              FROM jsonb_array_elements(cr.transcript) AS e
              WHERE e->>'type' = 'ai_reply'
                AND e ? 'interrupted'
          );
        """
    )


def downgrade() -> None:
    """No-op: stripped ``interrupted`` values were write-only and unrecoverable."""
    pass
