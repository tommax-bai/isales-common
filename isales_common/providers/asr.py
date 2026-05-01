"""ASR provider abstract base class.

Spec: provider-abc § Requirement: ASR Provider 异步流式接口.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from isales_common.providers._models import ASRResult


class ASRProvider(ABC):
    """Streaming speech-to-text contract.

    Implementations MUST consume an async iterator of PCM audio chunks and
    yield :class:`ASRResult` items including intermediate (``is_final=False``)
    results so interruption detection can react in real time.
    """

    @abstractmethod
    def stream_recognize(
        self,
        audio_chunks: AsyncIterator[bytes],
    ) -> AsyncIterator[ASRResult]:
        """Open a streaming recognition session.

        Returning an async iterator (rather than awaiting) lets callers drive
        the producer/consumer directly with ``async for``.
        """
        raise NotImplementedError
