"""In-memory ASR mock for unit/integration tests.

Spec: provider-abc § Scenario "mock 用于本地与 CI".
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence

from isales_common.providers._models import ASRResult
from isales_common.providers.asr import ASRProvider


class MockASRProvider(ASRProvider):
    """Replays a scripted list of :class:`ASRResult` items.

    The mock drains the input ``audio_chunks`` so callers behave like they
    would against a real provider (the producer task completes), but the
    output is fully decoupled from the audio content.
    """

    def __init__(self, scripted_results: Sequence[ASRResult] = ()) -> None:
        self._scripted = list(scripted_results)
        self.received_chunks: list[bytes] = []

    async def stream_recognize(
        self,
        audio_chunks: AsyncIterator[bytes],
    ) -> AsyncIterator[ASRResult]:
        async for chunk in audio_chunks:
            self.received_chunks.append(chunk)
        for result in self._scripted:
            yield result
