"""Shared Redis key names for cross-service coordination.

When a Redis key is written by one service and read by another, the literal
string MUST live here — centralizing it prevents the producer and consumer
from drifting apart.
"""

from __future__ import annotations

#: Redis SET of currently-active (started) campaign ids.
#:
#: Written by ``isales-scheduler``'s control loop (``sadd`` / ``srem`` after
#: consuming the ``CampaignControl`` messages ``isales-api`` pushes). It is the
#: **source of truth** for a campaign's started/stopped state — the ``campaign``
#: table deliberately has no status column. Other services (e.g. ``isales-api``
#: surfacing a campaign's start/stop badge) MAY read this SET; they MUST NOT
#: write it.
SCHEDULER_ACTIVE_CAMPAIGNS_SET = "scheduler:active-campaigns"
