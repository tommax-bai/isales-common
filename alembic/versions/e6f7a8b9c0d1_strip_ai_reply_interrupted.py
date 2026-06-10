"""strip out-of-contract keys from call_record.transcript events

Revision ID: e6f7a8b9c0d1
Revises: d5e6f7a8b9c0
Create Date: 2026-06-10 14:40:00.000000

Spec: openspec/changes/fix-transcript-schema-drift — capability `transcript`.

isales-api's ``CallRecordRead`` validates the transcript with
``extra="forbid"``, so any stored event carrying a key outside its
``TranscriptEvent`` contract makes ``GET /calls`` 500 (the 外呼记录 list page
won't open). A full audit of the production transcript JSONB found two such
historical drifts:

1. ``ai_reply`` events carrying ``interrupted`` (a bool). The engine used to
   write it; it is consumed nowhere (worker/api/web) and the interruption is
   already recorded via the standalone ``interruption`` event + pipeline_trace.
   The engine stops writing it in this same change.

2. ``interruption`` events carrying ``rms`` / ``source`` / ``voice_active_ms``
   (raw VAD signal fields from an older engine build). The current engine
   writes only ``interrupted_event_id`` + ``user_text_at_interruption``
   (run_loop.py), so these are historical-only and consumed nowhere.

This data migration strips those keys from the affected event elements. It is
idempotent (the ``-`` operator is a no-op when the key is absent) and only
rewrites rows that actually contain a violating event. Array order is preserved
via WITH ORDINALITY.

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
    """Strip out-of-contract keys from ai_reply / interruption transcript events."""
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
                           WHEN elem->>'type' = 'interruption'
                           THEN elem - 'rms' - 'source' - 'voice_active_ms'
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
              WHERE (e->>'type' = 'ai_reply' AND e ? 'interrupted')
                 OR (e->>'type' = 'interruption'
                     AND (e ? 'rms' OR e ? 'source' OR e ? 'voice_active_ms'))
          );
        """
    )


def downgrade() -> None:
    """No-op: stripped ``interrupted`` values were write-only and unrecoverable."""
    pass
