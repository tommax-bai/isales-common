"""ABCs for the cloud-edge gRPC control plane.

Spec: service-communication § Requirement: 云-边控制面 (cloud-edge gRPC
bidirectional streaming).

Concrete implementations live in isales-engine (server) and isales-telephony
(client); this module is a *contract*, not a runtime. It deliberately avoids
importing ``grpcio`` so downstream services can mock the entire transport
in unit tests.

Wire-format message classes (``Edge2Cloud`` / ``Cloud2Edge``) come from
:mod:`isales_common.proto.cloud_edge_pb2`. They are pure protobuf message
classes — pickling them requires only the ``protobuf`` runtime, not grpcio.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from isales_common.proto import cloud_edge_pb2 as pb

# =============================================================================
# Identity, errors, callback aliases
# =============================================================================


@dataclass(frozen=True)
class EdgeIdentity:
    """The identity an edge process presents after token verification.

    ``edge_device_id`` is the cloud-side primary key the engine uses to route
    Cloud2Edge frames. ``tenant_id`` is populated once C2 ``multi-tenant-
    roles-and-leads`` introduces multi-tenancy; in v1.0 it is always ``None``
    and routing is global.
    """

    edge_device_id: str
    tenant_id: str | None = None


class CloudEdgeError(Exception):
    """Base class for cloud-edge transport failures.

    Distinct from :class:`isales_common.providers._errors.ProviderError`
    because the cloud-edge control plane is not a vendor SaaS — it is our own
    gRPC service, with a different recovery story (auto-reconnect rather
    than provider fallback).
    """


class EdgeNotConnected(CloudEdgeError):
    """Raised when the cloud tries to push a message but no active stream
    exists for that edge_device_id.

    Callers SHOULD treat this as a transient condition for non-critical
    messages (e.g. config updates, RTC credential refresh) and a hard
    failure for dial commands (the scheduler retry path covers re-dial).
    """


class InvalidToken(CloudEdgeError):
    """Raised by :class:`TokenVerifier` for malformed, expired, or revoked
    Bearer tokens. The gRPC server MUST close the stream with
    ``UNAUTHENTICATED`` on this error.
    """


#: Server-side callback for inbound Edge2Cloud frames.
#: Receives the identity the stream is bound to plus the parsed envelope.
EdgeMessageCallback = Callable[[EdgeIdentity, pb.Edge2Cloud], Awaitable[None]]


#: Client-side callback for inbound Cloud2Edge frames.
CloudMessageCallback = Callable[[pb.Cloud2Edge], Awaitable[None]]


# =============================================================================
# Token verification
# =============================================================================


class TokenVerifier(ABC):
    """Verifies the Bearer token sent by an edge in gRPC initial metadata.

    v1.0 implementations may use a static HMAC-signed token (same secret as
    ``ISALES_JWT_SECRET`` but a different audience — see architecture spec
    "云-边 gRPC 控制面 使用独立 token"). C2 will swap in dynamic activation-
    code-derived tokens; the contract stays the same.
    """

    @abstractmethod
    async def verify(self, token: str) -> EdgeIdentity:
        """Validate ``token``; return the bound edge identity.

        Raises:
            InvalidToken: token is malformed, expired, or revoked.
        """
        raise NotImplementedError


# =============================================================================
# Server
# =============================================================================


class CloudEdgeServer(ABC):
    """Cloud-side gRPC server for the cloud-edge control plane.

    Hosted by isales-engine. One server instance fans out to many connected
    edges; ``send_to_edge`` is the only way for engine session code to push
    a Cloud2Edge frame (dial / cancel / config-update / rtc-credentials).

    Lifecycle::

        server = ConcreteCloudEdgeServer(token_verifier=...)
        server.on_edge_message(my_dispatcher)
        await server.start(listen_addr="[::]:50051")
        # ... run ...
        await server.stop()
    """

    @abstractmethod
    async def start(self, listen_addr: str) -> None:
        """Begin accepting gRPC connections on ``listen_addr``.

        ``listen_addr`` is in the grpcio format, e.g. ``"[::]:50051"`` or
        ``"unix:///tmp/cloud_edge.sock"``. TLS configuration is the
        concrete implementation's concern.
        """
        raise NotImplementedError

    @abstractmethod
    async def stop(self, grace_seconds: float = 5.0) -> None:
        """Drain pending RPCs, then close. Idempotent."""
        raise NotImplementedError

    @abstractmethod
    async def send_to_edge(
        self,
        edge_device_id: str,
        message: pb.Cloud2Edge,
    ) -> None:
        """Push ``message`` to the named edge.

        Raises:
            EdgeNotConnected: no active stream bound to that
                ``edge_device_id``. Callers MUST classify this as
                transient/critical themselves; the transport does not
                buffer Cloud2Edge frames (cloud-side state is the source
                of truth — see device-hardware "cloud → edge 命令丢失语义").
        """
        raise NotImplementedError

    @abstractmethod
    def on_edge_message(self, callback: EdgeMessageCallback) -> None:
        """Register the handler invoked once per inbound Edge2Cloud frame.

        MUST be called before :meth:`start`. Only one callback is supported;
        a second call replaces the first.
        """
        raise NotImplementedError


# =============================================================================
# Client
# =============================================================================


class CloudEdgeClient(ABC):
    """Edge-side gRPC client for the cloud-edge control plane.

    Hosted by isales-telephony. Maintains exactly one bidi stream to the
    cloud, with auto-reconnect using exponential backoff (initial 1s,
    capped at 30s, infinite retries — see service-communication
    Requirement § "断线重连与本地 buffer").

    Buffering policy:

    - ``CallEvent`` / ``HardwareAlert`` SHOULD be persisted to the edge's
      local SQLite buffer while disconnected and re-sent in order after
      reconnect.
    - ``Heartbeat`` MUST NOT be buffered (a stale heartbeat is meaningless).
    - ``DialAck`` SHOULD NOT be buffered (the cloud has already moved on if
      it didn't see the ACK; the scheduler's dial retry will produce a
      fresh DialCommand if needed).

    This ABC does not enforce the policy — that's the concrete client's
    responsibility — but :meth:`send` makes the buffering intent explicit
    via the ``critical`` flag.
    """

    @abstractmethod
    async def start(self, endpoint: str, token: str) -> None:
        """Connect to ``endpoint`` using ``token`` as Bearer auth.

        ``endpoint`` is the cloud-side gRPC URL, e.g.
        ``"isales.example.com:443"``. Returns once the initial connection
        is established; reconnect attempts continue in the background.
        """
        raise NotImplementedError

    @abstractmethod
    async def stop(self) -> None:
        """Cancel reconnection loop, close stream. Idempotent."""
        raise NotImplementedError

    @abstractmethod
    async def send(self, message: pb.Edge2Cloud, *, critical: bool = False) -> None:
        """Send ``message`` upstream.

        Args:
            message: parsed envelope.
            critical: when ``False`` (default), unsent frames during a
                disconnect MAY be buffered locally and re-sent on reconnect.
                When ``True``, the implementation MUST NOT buffer — if the
                stream is down the call raises :class:`EdgeNotConnected`.
                Use ``critical=True`` for ``Heartbeat`` and ``DialAck``.
        """
        raise NotImplementedError

    @abstractmethod
    def on_cloud_message(self, callback: CloudMessageCallback) -> None:
        """Register the handler invoked once per inbound Cloud2Edge frame.

        MUST be called before :meth:`start`. Only one callback is supported.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """``True`` when the bidi stream is currently established.

        Concrete implementations MAY also expose a richer state observable
        (e.g. for tray UX), but this property is the minimum contract.
        """
        raise NotImplementedError
