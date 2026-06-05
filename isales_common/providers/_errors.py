"""Unified error model for ASR / TTS / LLM providers + HTTP error mapping.

Spec: provider-abc § Requirement: 统一错误模型. Real implementations MUST
wrap vendor-native exceptions into one of these types so the business layer
can react uniformly (e.g. fall back via ai-pipeline degradation paths).

The ``map_http_error`` / ``map_transport_error`` helpers live here (rather
than in a single consuming service) because the volcengine TTS provider is
shared across isales-engine and isales-api (campaign-greeting-tts-preview §
决策 1 — 跨服务共用实现下沉 common). ``isales_engine.providers._errors``
re-exports these for engine-local ASR / LLM providers.
"""

from __future__ import annotations

from typing import Any

import httpx


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


# ---- HTTP / transport → ProviderError mapping -----------------------------
#
# Real provider implementations call ``map_http_error(...)`` after every
# ``httpx.Response`` to convert vendor-native errors into one of:
#   * ProviderRateLimited     — HTTP 429
#   * ProviderServerError     — HTTP 5xx + transport / WebSocket close
#   * ProviderTimeout         — caller-level timeout (raised by caller)
#   * ProviderInvalidRequest  — HTTP 4xx (non-429) + JSON / contract errors


def map_http_error(
    response: httpx.Response,
    *,
    provider: str,
    vendor_code: str | None = None,
) -> ProviderError:
    """Return a ProviderError subclass for a non-2xx ``httpx.Response``.

    Caller is responsible for raising the returned exception. Always returns
    a concrete instance — never returns ``None`` even on 2xx (use only on
    error responses; spec contract is "ProviderError on every non-success").
    """

    status = response.status_code
    body_snippet = _safe_body_snippet(response)
    code = vendor_code or _peek_vendor_code(response)

    if status == 429:
        retry_after = _parse_retry_after(response)
        return ProviderRateLimited(
            f"{provider} 429: {body_snippet}",
            provider=provider,
            vendor_code=code,
            retry_after_seconds=retry_after,
        )
    if 500 <= status < 600:
        return ProviderServerError(
            f"{provider} {status}: {body_snippet}",
            provider=provider,
            vendor_code=code,
        )
    if 400 <= status < 500:
        return ProviderInvalidRequest(
            f"{provider} {status}: {body_snippet}",
            provider=provider,
            vendor_code=code,
        )

    # 2xx / 3xx is not an error — caller misuse.
    return ProviderInvalidRequest(
        f"{provider} unexpected status {status}: {body_snippet}",
        provider=provider,
        vendor_code=code,
    )


def map_transport_error(
    exc: BaseException, *, provider: str
) -> ProviderError:
    """Translate a non-HTTP transport exception into a ProviderError."""

    if isinstance(exc, httpx.TimeoutException):
        return ProviderTimeout(f"{provider} timeout: {exc}", provider=provider)
    # ConnectError, ReadError, RemoteProtocolError, NetworkError — anything that
    # the vendor server didn't actually respond cleanly to.
    return ProviderServerError(f"{provider} transport error: {exc}", provider=provider)


def as_provider_invalid_response(
    message: str, *, provider: str, vendor_code: str | None = None
) -> ProviderInvalidRequest:
    """Helper for "response was 200 but body doesn't match contract"."""

    return ProviderInvalidRequest(message, provider=provider, vendor_code=vendor_code)


# ---- helpers --------------------------------------------------------------


def _safe_body_snippet(response: httpx.Response, *, limit: int = 200) -> str:
    try:
        text = response.text
    except Exception:  # noqa: BLE001
        return "<unreadable body>"
    return text[:limit].replace("\n", " ")


def _peek_vendor_code(response: httpx.Response) -> str | None:
    try:
        data: Any = response.json()
    except Exception:  # noqa: BLE001
        return None
    if isinstance(data, dict):
        # Common shapes across vendors.
        for key in ("code", "error_code", "errorCode"):
            v = data.get(key)
            if isinstance(v, (str, int)):
                return str(v)
        err = data.get("error")
        if isinstance(err, dict):
            for key in ("code", "type"):
                v = err.get(key)
                if isinstance(v, str):
                    return v
    return None


def _parse_retry_after(response: httpx.Response) -> float | None:
    raw = response.headers.get("Retry-After")
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None
