.PHONY: proto proto-clean test lint format

# Regenerate protobuf / gRPC Python stubs from the .proto source.
# Outputs:
#   isales_common/proto/cloud_edge_pb2.py       — message classes
#   isales_common/proto/cloud_edge_pb2_grpc.py  — service stubs (client/server)
#   isales_common/proto/cloud_edge_pb2.pyi      — type stubs for mypy
#
# Run after editing any .proto file. The generated outputs ARE committed so
# downstream services (isales-engine, isales-telephony) don't need protoc.
proto:
	.venv/bin/python -m grpc_tools.protoc \
		-I isales_common/proto \
		--python_out=isales_common/proto \
		--grpc_python_out=isales_common/proto \
		--pyi_out=isales_common/proto \
		isales_common/proto/cloud_edge.proto
	# grpcio-tools emits bare `import cloud_edge_pb2` which only works if
	# `isales_common/proto/` is on sys.path. Rewrite to a package-relative
	# import so downstream services can `from isales_common.proto import ...`.
	sed -i.bak \
		-e 's/^import cloud_edge_pb2 as cloud__edge__pb2$$/from isales_common.proto import cloud_edge_pb2 as cloud__edge__pb2/' \
		isales_common/proto/cloud_edge_pb2_grpc.py
	rm isales_common/proto/cloud_edge_pb2_grpc.py.bak

proto-clean:
	rm -f isales_common/proto/*_pb2.py
	rm -f isales_common/proto/*_pb2.pyi
	rm -f isales_common/proto/*_pb2_grpc.py

test:
	.venv/bin/pytest

lint:
	.venv/bin/ruff check .
	.venv/bin/mypy isales_common

format:
	.venv/bin/ruff format .
