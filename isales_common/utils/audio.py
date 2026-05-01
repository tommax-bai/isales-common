"""Audio format constants shared across modem-controller, engine, and worker.

Heavy processing (resampling, codec conversion) lives in the modem-controller;
this module only exposes constants and lightweight checks.
"""

from __future__ import annotations

from enum import IntEnum

# PCM signed 16-bit little-endian is the standard interchange format.
PCM_SAMPLE_WIDTH_BYTES = 2
PCM_CHANNELS = 1


class SampleRate(IntEnum):
    PSTN = 8000  # GSM voice channel native rate
    NARROW = 16000  # most ASR providers
    WIDE = 24000  # some TTS providers


def bytes_per_second(rate: SampleRate) -> int:
    return int(rate) * PCM_SAMPLE_WIDTH_BYTES * PCM_CHANNELS


def is_pcm_chunk_aligned(chunk: bytes) -> bool:
    """True if the byte length is a whole number of mono-16bit samples."""
    return len(chunk) % PCM_SAMPLE_WIDTH_BYTES == 0
