"""JWT verification helper shared by isales-api (signs) and other services (verify only).

Per the architecture spec, isales-common MUST NOT expose a signing function; only
isales-api signs JWTs. Other services pull this verify helper to validate tokens
issued by isales-api. Secret is read by the caller from ``ISALES_JWT_SECRET`` —
this module never touches the environment.
"""

from __future__ import annotations

from typing import Any, cast

from jose import ExpiredSignatureError, JWTError, jwt

ALGORITHM = "HS256"


class InvalidJWT(Exception):
    """Raised when a token is malformed, expired, or fails signature check."""


def verify_jwt(token: str, secret: str) -> dict[str, Any]:
    """Verify an HS256 JWT and return its claims.

    :raises InvalidJWT: signature mismatch, expired token, malformed payload.
    """
    try:
        return cast(dict[str, Any], jwt.decode(token, secret, algorithms=[ALGORITHM]))
    except ExpiredSignatureError as exc:
        raise InvalidJWT("token expired") from exc
    except JWTError as exc:
        raise InvalidJWT(str(exc)) from exc
