"""Symmetric encryption for at-rest secrets (e.g. SIM passwords, callback signing secrets).

Key is loaded from the ``ISALES_FERNET_KEY`` env var. v1 uses a single rotating key;
KMS integration is intentionally not abstracted (see design.md decision #2).
"""

from __future__ import annotations

import os

from cryptography.fernet import Fernet, InvalidToken

ENV_KEY = "ISALES_FERNET_KEY"


class CryptoConfigError(RuntimeError):
    """Raised when the Fernet key is missing or malformed."""


class CryptoError(ValueError):
    """Raised when decryption fails (wrong key, tampered ciphertext, etc.)."""


def _get_key() -> bytes:
    value = os.environ.get(ENV_KEY)
    if not value:
        raise CryptoConfigError(
            f"missing {ENV_KEY}; generate with: "
            "python -c 'from cryptography.fernet import Fernet; "
            "print(Fernet.generate_key().decode())'"
        )
    return value.encode("ascii")


def encrypt(plaintext: str) -> str:
    """Encrypt a UTF-8 string and return urlsafe base64 ciphertext."""
    token = Fernet(_get_key()).encrypt(plaintext.encode("utf-8"))
    return token.decode("ascii")


def decrypt(ciphertext: str) -> str:
    """Decrypt a token produced by :func:`encrypt` back to the original UTF-8 string."""
    try:
        plain = Fernet(_get_key()).decrypt(ciphertext.encode("ascii"))
    except InvalidToken as exc:
        raise CryptoError("invalid or tampered ciphertext") from exc
    return plain.decode("utf-8")
