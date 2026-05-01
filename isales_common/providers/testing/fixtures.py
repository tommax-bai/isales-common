"""pytest fixtures for the provider mocks.

Importing this module requires ``pytest`` to be installed (it is in the
``[dev]`` extra of isales-common). Downstream test suites typically wire up
the fixtures by re-exporting them in their own ``conftest.py``::

    # conftest.py
    from isales_common.providers.testing.fixtures import (
        mock_asr_provider,
        mock_llm_provider,
        mock_tts_provider,
    )
"""

from __future__ import annotations

import pytest

from isales_common.providers.testing.asr import MockASRProvider
from isales_common.providers.testing.llm import MockLLMProvider
from isales_common.providers.testing.tts import MockTTSProvider

__all__ = [
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
