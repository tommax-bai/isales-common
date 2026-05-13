"""Cloud-edge transport ABC + in-memory implementation tests.

Spec: service-communication § Requirement: 云-边控制面 (cloud-edge gRPC
bidirectional streaming).
"""

from __future__ import annotations

import asyncio

import pytest

from isales_common.proto import cloud_edge_pb2 as pb
from isales_common.transport.cloud_edge import (
    CloudEdgeClient,
    CloudEdgeServer,
    EdgeIdentity,
    EdgeNotConnected,
    InvalidToken,
)
from isales_common.transport.testing import (
    InMemoryCloudEdgeClient,
    InMemoryCloudEdgeServer,
    StaticTokenVerifier,
)

# --------------------------------------------------------------------------
# ABC conformance — the in-memory pair satisfies the contract types.
# --------------------------------------------------------------------------


def test_inmemory_server_implements_abc() -> None:
    server = InMemoryCloudEdgeServer(
        token_verifier=StaticTokenVerifier(token="t", edge_device_id="e1"),
    )
    assert isinstance(server, CloudEdgeServer)


def test_inmemory_client_implements_abc() -> None:
    server = InMemoryCloudEdgeServer(
        token_verifier=StaticTokenVerifier(token="t", edge_device_id="e1"),
    )
    client = InMemoryCloudEdgeClient(server=server)
    assert isinstance(client, CloudEdgeClient)


# --------------------------------------------------------------------------
# Token verification
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_static_verifier_accepts_valid_token() -> None:
    v = StaticTokenVerifier(token="secret", edge_device_id="edge-7")
    identity = await v.verify("secret")
    assert identity == EdgeIdentity(edge_device_id="edge-7")


@pytest.mark.asyncio
async def test_static_verifier_rejects_wrong_token() -> None:
    v = StaticTokenVerifier(token="secret", edge_device_id="edge-7")
    with pytest.raises(InvalidToken):
        await v.verify("guess")


# --------------------------------------------------------------------------
# End-to-end dispatch via in-memory pair
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_edge_to_cloud_callback_dispatches_envelope() -> None:
    server = InMemoryCloudEdgeServer(
        token_verifier=StaticTokenVerifier(token="t", edge_device_id="e1"),
    )
    received: list[tuple[EdgeIdentity, pb.Edge2Cloud]] = []

    async def handler(identity: EdgeIdentity, msg: pb.Edge2Cloud) -> None:
        received.append((identity, msg))

    server.on_edge_message(handler)
    await server.start("memory")

    client = InMemoryCloudEdgeClient(server=server)
    await client.start("memory", "t")

    await client.send(
        pb.Edge2Cloud(
            call_event=pb.CallEvent(call_id="c-1", connected=pb.Connected()),
        ),
    )

    assert len(received) == 1
    identity, msg = received[0]
    assert identity.edge_device_id == "e1"
    assert msg.call_event.WhichOneof("kind") == "connected"

    await client.stop()
    await server.stop()


@pytest.mark.asyncio
async def test_cloud_to_edge_callback_dispatches_envelope() -> None:
    server = InMemoryCloudEdgeServer(
        token_verifier=StaticTokenVerifier(token="t", edge_device_id="e1"),
    )
    await server.start("memory")

    client = InMemoryCloudEdgeClient(server=server)
    received: list[pb.Cloud2Edge] = []

    async def handler(msg: pb.Cloud2Edge) -> None:
        received.append(msg)

    client.on_cloud_message(handler)
    await client.start("memory", "t")

    await server.send_to_edge(
        "e1",
        pb.Cloud2Edge(cancel=pb.CancelCommand(call_id="c-1", reason="user-hangup")),
    )

    assert len(received) == 1
    assert received[0].cancel.call_id == "c-1"

    await client.stop()
    await server.stop()


@pytest.mark.asyncio
async def test_send_to_unconnected_edge_raises() -> None:
    server = InMemoryCloudEdgeServer(
        token_verifier=StaticTokenVerifier(token="t", edge_device_id="e1"),
    )
    await server.start("memory")

    with pytest.raises(EdgeNotConnected):
        await server.send_to_edge(
            "no-such-edge",
            pb.Cloud2Edge(heartbeat=pb.Heartbeat()),
        )

    await server.stop()


@pytest.mark.asyncio
async def test_critical_send_while_disconnected_raises() -> None:
    server = InMemoryCloudEdgeServer(
        token_verifier=StaticTokenVerifier(token="t", edge_device_id="e1"),
    )
    await server.start("memory")
    client = InMemoryCloudEdgeClient(server=server)
    # client.start() not called → not connected.

    with pytest.raises(EdgeNotConnected):
        await client.send(
            pb.Edge2Cloud(heartbeat=pb.Heartbeat()),
            critical=True,
        )

    await server.stop()


@pytest.mark.asyncio
async def test_non_critical_send_while_disconnected_buffers_until_start() -> None:
    server = InMemoryCloudEdgeServer(
        token_verifier=StaticTokenVerifier(token="t", edge_device_id="e1"),
    )
    received: list[pb.Edge2Cloud] = []

    async def handler(_identity: EdgeIdentity, msg: pb.Edge2Cloud) -> None:
        received.append(msg)

    server.on_edge_message(handler)
    await server.start("memory")

    client = InMemoryCloudEdgeClient(server=server)
    # Queue two events before starting; should buffer.
    await client.send(
        pb.Edge2Cloud(call_event=pb.CallEvent(call_id="c-1", ringing=pb.Ringing())),
    )
    await client.send(
        pb.Edge2Cloud(call_event=pb.CallEvent(call_id="c-1", connected=pb.Connected())),
    )

    assert received == []  # nothing delivered yet

    await client.start("memory", "t")
    # Yield once so any flush task can run; in this impl flush is inline,
    # but other ABC implementations may flush via a background task.
    await asyncio.sleep(0)

    assert [m.call_event.WhichOneof("kind") for m in received] == ["ringing", "connected"]

    await client.stop()
    await server.stop()


@pytest.mark.asyncio
async def test_is_connected_tracks_lifecycle() -> None:
    server = InMemoryCloudEdgeServer(
        token_verifier=StaticTokenVerifier(token="t", edge_device_id="e1"),
    )
    await server.start("memory")
    client = InMemoryCloudEdgeClient(server=server)

    assert client.is_connected is False
    await client.start("memory", "t")
    assert client.is_connected is True
    await client.stop()
    assert client.is_connected is False

    await server.stop()


@pytest.mark.asyncio
async def test_invalid_token_blocks_start() -> None:
    server = InMemoryCloudEdgeServer(
        token_verifier=StaticTokenVerifier(token="right", edge_device_id="e1"),
    )
    await server.start("memory")

    client = InMemoryCloudEdgeClient(server=server)
    with pytest.raises(InvalidToken):
        await client.start("memory", "wrong")
    assert client.is_connected is False

    await server.stop()
