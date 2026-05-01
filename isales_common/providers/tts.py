"""TTS provider abstract base class.

Spec: provider-abc § Requirement: TTS Provider 异步流式合成接口.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator


class TTSProvider(ABC):
    """Streaming text-to-speech contract.

    Implementations MUST yield raw PCM byte chunks (mono signed 16-bit LE,
    sample rate per :class:`isales_common.utils.audio.SampleRate`) so the
    modem-controller can stream them to the GSM voice channel without
    additional decoding.
    """

    @abstractmethod
    def synthesize_stream(
        self,
        text: str,
        voice_id: str,
    ) -> AsyncIterator[bytes]:
        """Synthesise ``text`` with the given ``voice_id``.

        ``voice_id`` is opaque to the ABC; it comes from the
        ``voice_model.voice_id`` column (data-model spec).
        """
        raise NotImplementedError
