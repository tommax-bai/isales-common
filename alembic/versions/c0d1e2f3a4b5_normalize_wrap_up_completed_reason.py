"""normalize call_record.transcript wrap_up_completed.reason to spec vocabulary

Revision ID: c0d1e2f3a4b5
Revises: b9c0d1e2f3a4
Create Date: 2026-06-12 16:10:00.000000

Spec: capability ``transcript`` — ``wrap_up_completed`` event carries
``reason`` constrained to ``Literal["max_rounds", "max_seconds"]`` (transcript
spec § event table). The engine's wrap-up evaluator
(``isales_engine.wrapup.manager.evaluate_wrap_up``) historically emitted its
INTERNAL control vocabulary ``"rounds_exhausted"`` / ``"seconds_exhausted"``
straight into the persisted event, so any call that completed wrap-up stored an
out-of-contract ``reason``. ``isales-api``'s ``CallRecordRead`` validates the
transcript with ``extra="forbid"`` + the ``reason`` Literal, so a single such
row makes ``GET /calls`` 500 (the 外呼记录 list page won't open).

A full audit of the production transcript JSONB (186 rows / 1248 events) found
exactly one drift signature: ``wrap_up_completed.reason='rounds_exhausted'``
(call 173). This data migration rewrites the stored value to the spec
vocabulary for BOTH sibling values the engine could produce:

    rounds_exhausted  -> max_rounds
    seconds_exhausted -> max_seconds

The engine is fixed in the same change to emit the spec vocabulary directly, so
no new rows with the old vocabulary are produced after deploy. The rewrite is
idempotent (already-correct values fall through the ELSE), preserves array
order via WITH ORDINALITY, and only touches rows that actually contain a
violating event.

Downgrade is a no-op: ``max_rounds`` / ``max_seconds`` is the canonical spec
value; reverting would re-introduce out-of-contract data AND would corrupt the
correct rows the fixed engine writes post-deploy.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "c0d1e2f3a4b5"
down_revision: Union[str, Sequence[str], None] = "b9c0d1e2f3a4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Rewrite wrap_up_completed.reason to the spec Literal vocabulary."""
    op.execute(
        """
        UPDATE call_record AS cr
        SET transcript = sub.new_transcript
        FROM (
            SELECT c.id,
                   jsonb_agg(
                       CASE
                           WHEN elem->>'type' = 'wrap_up_completed'
                                AND elem->>'reason' = 'rounds_exhausted'
                           THEN jsonb_set(elem, '{reason}', '"max_rounds"'::jsonb)
                           WHEN elem->>'type' = 'wrap_up_completed'
                                AND elem->>'reason' = 'seconds_exhausted'
                           THEN jsonb_set(elem, '{reason}', '"max_seconds"'::jsonb)
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
              WHERE e->>'type' = 'wrap_up_completed'
                AND e->>'reason' IN ('rounds_exhausted', 'seconds_exhausted')
          );
        """
    )


def downgrade() -> None:
    """No-op: max_rounds/max_seconds is canonical; reverting would re-break data."""
    pass
