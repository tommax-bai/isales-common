"""In-memory provider mocks usable from any context.

Spec: provider-abc § Requirement: Provider ABC 契约可被 mock 测试.

The mocks have no test-runner dependency so production code (e.g. running a
local dev profile against fixed responses) can import them too. pytest
fixtures live in :mod:`isales_common.providers.testing.fixtures` to keep
``pytest`` strictly optional at import time.
"""

from __future__ import annotations

from isales_common.providers.testing.asr import MockASRProvider
from isales_common.providers.testing.llm import MockLLMProvider, RecordedChatCall
from isales_common.providers.testing.tts import MockTTSProvider

__all__ = [
    "MockASRProvider",
    "MockLLMProvider",
    "MockTTSProvider",
    "RecordedChatCall",
]
