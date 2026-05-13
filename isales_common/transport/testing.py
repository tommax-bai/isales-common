"""In-memory implementations of cloud-edge transport ABCs for tests.

Lets downstream test suites exercise the dispatch contract end-to-end
without bringing up grpcio. Cloud-side test pushes Cloud2Edge frames,
edge-side test sees them via its registered callback; vice versa.

Not intended for production. The transport guarantees this implementation
provides:

- Single client connected at a time (only one edge_device_id per server).
- Synchronous in-process delivery — no network, no buffering.
- No reconnect logic — the client either ``start()`` succeeds against an
  attached server or raises.
"""

from __future__ import annotations

import asyncio
from contextlib import suppress

from isales_common.proto import cloud_edge_pb2 as pb
from isales_common.transport.cloud_edge import (
    CloudEdgeClient,
    CloudEdgeServer,
    CloudMessageCallback,
    EdgeIdentity,
    EdgeMessageCallback,
    EdgeNotConnected,
    InvalidToken,
    TokenVerifier,
)


class StaticTokenVerifier(TokenVerifier):
    """Verifier that accepts a single hard-coded ``token`` and binds it to
    a single ``edge_device_id``. Anything else raises :class:`InvalidToken`.
    """

    def __init__(self, *, token: str, edge_device_id: str) -> None:
        self._token = token
        self._edge_device_id = edge_device_id

    async def verify(self, token: str) -> EdgeIdentity:
        if token != self._token:
            raise InvalidToken(f"unexpected token: {token!r}")
        return EdgeIdentity(edge_device_id=self._edge_device_id)


class InMemoryCloudEdgeServer(CloudEdgeServer):
    """Server impl that exposes itself as an in-process "endpoint" for the
    matching :class:`InMemoryCloudEdgeClient` to attach to.

    Usage::

        server = InMemoryCloudEdgeServer(
            token_verifier=StaticTokenVerifier(token="t", edge_device_id="edge-1"),
        )
        server.on_edge_message(my_dispatcher)
        await server.start(listen_addr="memory")

        client = InMemoryCloudEdgeClient(server=server)
        client.on_cloud_message(my_handler)
        await client.start(endpoint="memory", token="t")
    """

    def __init__(self, *, token_verifier: TokenVerifier) -> None:
        self._verifier = token_verifier
        self._edge_callback: EdgeMessageCallback | None = None
        # edge_device_id -> attached client
        self._clients: dict[str, InMemoryCloudEdgeClient] = {}
        self._running = False

    async def start(self, listen_addr: str) -> None:
        self._running = True

    async def stop(self, grace_seconds: float = 5.0) -> None:
        # Tear down attached clients first so their pending tasks don't
        # outlive the server. Concrete grpcio impl gets this for free via
        # server.stop(grace) cancelling RPCs.
        for client in list(self._clients.values()):
            with suppress(Exception):
                await client.stop()
        self._clients.clear()
        self._running = False

    async def send_to_edge(
        self,
        edge_device_id: str,
        message: pb.Cloud2Edge,
    ) -> None:
        client = self._clients.get(edge_device_id)
        if client is None:
            raise EdgeNotConnected(edge_device_id)
        await client._deliver(message)

    def on_edge_message(self, callback: EdgeMessageCallback) -> None:
        self._edge_callback = callback

    # ----- in-memory wiring (not part of the ABC) -----

    async def _attach(self, client: InMemoryCloudEdgeClient, token: str) -> EdgeIdentity:
        if not self._running:
            raise RuntimeError("server not started")
        identity = await self._verifier.verify(token)
        self._clients[identity.edge_device_id] = client
        return identity

    def _detach(self, edge_device_id: str) -> None:
        self._clients.pop(edge_device_id, None)

    async def _receive_from_edge(self, identity: EdgeIdentity, message: pb.Edge2Cloud) -> None:
        if self._edge_callback is None:
            return
        await self._edge_callback(identity, message)


class InMemoryCloudEdgeClient(CloudEdgeClient):
    """Client impl that attaches directly to an :class:`InMemoryCloudEdgeServer`
    via ``endpoint="memory"`` (sentinel). Useful for unit tests; not for
    production.
    """

    def __init__(self, *, server: InMemoryCloudEdgeServer) -> None:
        self._server = server
        self._cloud_callback: CloudMessageCallback | None = None
        self._identity: EdgeIdentity | None = None
        self._connected = False
        # Frames queued while disconnected when critical=False.
        self._buffer: list[pb.Edge2Cloud] = []

    async def start(self, endpoint: str, token: str) -> None:
        self._identity = await self._server._attach(self, token)
        self._connected = True
        # Flush any frames buffered before start (testing convenience).
        pending, self._buffer = self._buffer, []
        for msg in pending:
            await self._server._receive_from_edge(self._identity, msg)

    async def stop(self) -> None:
        if self._identity is not None:
            self._server._detach(self._identity.edge_device_id)
        self._connected = False
        self._identity = None

    async def send(self, message: pb.Edge2Cloud, *, critical: bool = False) -> None:
        if not self._connected:
            if critical:
                raise EdgeNotConnected("client not connected")
            self._buffer.append(message)
            return
        assert self._identity is not None  # narrows for type-checker
        await self._server._receive_from_edge(self._identity, message)

    def on_cloud_message(self, callback: CloudMessageCallback) -> None:
        self._cloud_callback = callback

    @property
    def is_connected(self) -> bool:
        return self._connected

    # ----- in-memory wiring (not part of the ABC) -----

    async def _deliver(self, message: pb.Cloud2Edge) -> None:
        if self._cloud_callback is None:
            return
        await self._cloud_callback(message)


__all__ = [
    "InMemoryCloudEdgeClient",
    "InMemoryCloudEdgeServer",
    "StaticTokenVerifier",
]


# Silence "unused" warnings if test runner imports asyncio for fixtures.
_ = asyncio
