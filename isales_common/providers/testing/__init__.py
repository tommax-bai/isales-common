"""In-memory provider mocks + pytest fixtures.

Spec: provider-abc § Requirement: Provider ABC 契约可被 mock 测试.

Usage in another repo's ``conftest.py``::

    from isales_common.providers.testing import (
        mock_asr_provider, mock_tts_provider, mock_llm_provider,
    )
"""

from __future__ import annotations

import pytest

from isales_common.providers.testing.asr import MockASRProvider
from isales_common.providers.testing.llm import MockLLMProvider, RecordedChatCall
from isales_common.providers.testing.tts import MockTTSProvider

__all__ = [
    "MockASRProvider",
    "MockLLMProvider",
    "MockTTSProvider",
    "RecordedChatCall",
    "mock_asr_provider",
    "mock_llm_provider",
    "mock_tts_provider",
]


@pytest.fixture
def mock_asr_provider() -> MockASRProvider:
    return MockASRProvider()


@pytest.fixture
def mock_tts_provider() -> MockTTSProvider:
    return MockTTSProvider()


@pytest.fixture
def mock_llm_provider() -> MockLLMProvider:
    return MockLLMProvider()
