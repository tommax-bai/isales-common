"""Transport abstractions shared across services.

Two transports live here:

- **cloud-edge** (this package's ``cloud_edge`` module): the long-lived gRPC
  bidi stream between the cloud-side engine and each edge process. ABCs only —
  concrete server / client implementations live in isales-engine and
  isales-telephony respectively. Lets unit tests inject a mock without
  bringing up grpcio.

The wire format for both ends lives in :mod:`isales_common.proto`.
"""

from __future__ import annotations

from isales_common.transport.cloud_edge import (
    CloudEdgeClient,
    CloudEdgeError,
    CloudEdgeServer,
    CloudMessageCallback,
    EdgeIdentity,
    EdgeMessageCallback,
    EdgeNotConnected,
    InvalidToken,
    TokenVerifier,
)

__all__ = [
    "CloudEdgeClient",
    "CloudEdgeError",
    "CloudEdgeServer",
    "CloudMessageCallback",
    "EdgeIdentity",
    "EdgeMessageCallback",
    "EdgeNotConnected",
    "InvalidToken",
    "TokenVerifier",
]
