"""Unified error model for ASR / TTS / LLM providers.

Spec: provider-abc § Requirement: 统一错误模型. Real implementations MUST
wrap vendor-native exceptions into one of these types so the business layer
can react uniformly (e.g. fall back via ai-pipeline degradation paths).
"""

from __future__ import annotations


class ProviderError(Exception):
    """Base class for all provider-side failures.

    The ``provider`` field identifies the implementation (e.g. ``"openai"``);
    ``vendor_code`` carries the original error code if available, for logging.
    """

    def __init__(
        self,
        message: str,
        *,
        provider: str | None = None,
        vendor_code: str | None = None,
    ) -> None:
        super().__init__(message)
        self.provider = provider
        self.vendor_code = vendor_code


class ProviderTimeout(ProviderError):
    """Request exceeded the configured deadline."""


class ProviderRateLimited(ProviderError):
    """Vendor rejected the request due to quota / RPS limits (HTTP 429)."""

    def __init__(
        self,
        message: str,
        *,
        provider: str | None = None,
        vendor_code: str | None = None,
        retry_after_seconds: float | None = None,
    ) -> None:
        super().__init__(message, provider=provider, vendor_code=vendor_code)
        self.retry_after_seconds = retry_after_seconds


class ProviderInvalidRequest(ProviderError):
    """Malformed or rejected request (HTTP 4xx other than 429)."""


class ProviderServerError(ProviderError):
    """Vendor-side failure (HTTP 5xx or transport error)."""
