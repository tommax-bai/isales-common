"""In-memory TTS mock for unit/integration tests."""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence

from isales_common.providers.tts import TTSProvider


class MockTTSProvider(TTSProvider):
    """Yields a fixed sequence of PCM byte chunks per ``synthesize_stream``.

    The mock records every call's ``(text, voice_id)`` so tests can assert
    what business code asked for, while keeping audio content trivial.
    """

    def __init__(
        self,
        scripted_chunks: Sequence[bytes] = (b"\x00\x00",),
    ) -> None:
        self._scripted = list(scripted_chunks)
        self.calls: list[tuple[str, str]] = []

    async def synthesize_stream(
        self,
        text: str,
        voice_id: str,
    ) -> AsyncIterator[bytes]:
        self.calls.append((text, voice_id))
        for chunk in self._scripted:
            yield chunk
