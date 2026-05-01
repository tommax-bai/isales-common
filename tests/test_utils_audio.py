from isales_common.utils.audio import (
    PCM_CHANNELS,
    PCM_SAMPLE_WIDTH_BYTES,
    SampleRate,
    bytes_per_second,
    is_pcm_chunk_aligned,
)


def test_pcm_constants():
    assert PCM_SAMPLE_WIDTH_BYTES == 2
    assert PCM_CHANNELS == 1


def test_sample_rates():
    assert SampleRate.PSTN == 8000
    assert SampleRate.NARROW == 16000
    assert SampleRate.WIDE == 24000


def test_bytes_per_second():
    assert bytes_per_second(SampleRate.PSTN) == 16_000
    assert bytes_per_second(SampleRate.NARROW) == 32_000
    assert bytes_per_second(SampleRate.WIDE) == 48_000


def test_chunk_alignment():
    assert is_pcm_chunk_aligned(b"\x00\x00") is True
    assert is_pcm_chunk_aligned(b"\x00\x00\x00\x00") is True
    assert is_pcm_chunk_aligned(b"") is True
    assert is_pcm_chunk_aligned(b"\x00") is False
    assert is_pcm_chunk_aligned(b"\x00\x00\x00") is False
