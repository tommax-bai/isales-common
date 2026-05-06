"""Unit tests for utils.jwt.verify_jwt — three paths: valid / expired / bad signature."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from jose import jwt as jose_jwt

from isales_common.utils.jwt import ALGORITHM, InvalidJWT, verify_jwt

SECRET = "test-secret-do-not-use-in-prod"


def _sign(claims: dict[str, object], secret: str = SECRET) -> str:
    return jose_jwt.encode(claims, secret, algorithm=ALGORITHM)


def _now_ts() -> int:
    return int(datetime.now(tz=UTC).timestamp())


class TestVerifyJWT:
    def test_valid_token_returns_claims(self) -> None:
        token = _sign({"sub": "admin", "exp": _now_ts() + 3600})
        claims = verify_jwt(token, SECRET)
        assert claims["sub"] == "admin"

    def test_expired_token_raises(self) -> None:
        token = _sign({"sub": "admin", "exp": _now_ts() - 60})
        with pytest.raises(InvalidJWT, match="expired"):
            verify_jwt(token, SECRET)

    def test_bad_signature_raises(self) -> None:
        token = _sign({"sub": "admin", "exp": _now_ts() + 3600}, secret="other")
        with pytest.raises(InvalidJWT):
            verify_jwt(token, SECRET)

    def test_malformed_token_raises(self) -> None:
        with pytest.raises(InvalidJWT):
            verify_jwt("not.a.jwt", SECRET)
