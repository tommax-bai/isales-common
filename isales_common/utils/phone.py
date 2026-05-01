"""E.164 phone normalization and validation."""

from __future__ import annotations

import phonenumbers
from phonenumbers import NumberParseException


class PhoneError(ValueError):
    """Raised when a phone string cannot be parsed or validated."""


def normalize(raw: str, default_region: str = "CN") -> str:
    """Parse a raw phone string and return E.164 form (e.g. ``+8613800001234``).

    `default_region` is a CLDR region code used when the input lacks a country prefix.
    """
    if not raw or not raw.strip():
        raise PhoneError("phone is empty")
    try:
        parsed = phonenumbers.parse(raw, default_region)
    except NumberParseException as exc:
        raise PhoneError(f"unparseable phone: {raw!r}") from exc
    if not phonenumbers.is_valid_number(parsed):
        raise PhoneError(f"invalid phone: {raw!r}")
    return str(phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164))


def is_valid(raw: str, default_region: str = "CN") -> bool:
    try:
        normalize(raw, default_region)
    except PhoneError:
        return False
    return True
