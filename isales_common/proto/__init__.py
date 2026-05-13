"""Protobuf / gRPC message definitions shared across services.

The wire format for the cloud-edge control plane.

Spec: service-communication § "云-边控制面 (cloud-edge gRPC bidirectional
streaming)".

Generated stubs live alongside the ``.proto`` source:

- ``cloud_edge.proto`` — authoritative schema; check this in.
- ``cloud_edge_pb2.py`` — message classes (Python).
- ``cloud_edge_pb2_grpc.py`` — service stubs (Python + grpcio).
- ``cloud_edge_pb2.pyi`` — type stubs for mypy.

Regenerate after editing the .proto::

    python -m grpc_tools.protoc -I isales_common/proto \\
        --python_out=isales_common/proto \\
        --grpc_python_out=isales_common/proto \\
        --pyi_out=isales_common/proto \\
        isales_common/proto/cloud_edge.proto

Or simply ``make proto`` from the repo root.

Versioning rule: the proto package carries a major version
(``isales.cloud_edge.v1``). Add new fields by number (proto3 semantics);
removing or renumbering existing fields MUST go through a v2 package, with
both v1 and v2 services running in parallel until edges have rolled forward.
"""
