# Changelog

All notable changes to `isales-common` are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project
adheres to [Semantic Versioning](https://semver.org/).

## [v0.5.0] — 2026-06-03

### Changed (BREAKING)

- **Pipeline three-layer → dual-LLM architecture** (change
  `pipeline-stream-and-referee`). The N-role PK + N×M judges + polish design is
  replaced by main (streaming text) + referee (side-band enum decision) +
  post-call extractor.
  - `RoleKind` / `PromptScopeType` enums: `{role, judge, polish}` →
    `{main, referee, extractor}`.
  - `pipeline_trace`: dropped `role_candidates / judge_results / polish_* /
    final_selected_candidate_index`; added `main_reply_text / main_duration_ms /
    main_tokens_in / main_tokens_out / main_fallback_used / referee_decision /
    referee_goal_type / referee_confidence / referee_duration_ms /
    first_audio_ms / error`.
  - Removed JSONB nested models `RoleCandidate / JudgeResult / PolishInput`
    (`isales_common.schemas.jsonb`).
  - `PipelineTraceRead` / `CallRecordRead` DTOs updated to match.

### Added

- `isales_common.schemas.pipeline` — `MainSpec / RefereeSpec / ExtractorSpec /
  PipelineConfig` (replaces the old engine-side dataclasses as the shared
  contract).
- `call_record.extracted / extract_status / extract_error` — post-call
  extractor output (worker-written, async).
- `campaign.filler_enabled` (default `false`) — filler opt-in flag.
- `LLMProvider.chat_stream(...) -> AsyncIterator[str]` abstract method plus
  `last_call_tokens_in / last_call_tokens_out / last_call_finish_reason`
  usage attributes, for the main streaming reply path.
- Alembic migration `c3d4e5f6a7b8_pipeline_stream_and_referee` (deletes old
  role_config / prompt_version rows; campaigns must be re-seeded).

## [v0.3.2] — 2026-05-22

### Added

- `isales_common.redis_keys` — shared Redis key-name constants for
  cross-service coordination. First entry: `SCHEDULER_ACTIVE_CAMPAIGNS_SET`
  (`scheduler:active-campaigns`), the SET that isales-scheduler maintains and
  isales-api reads to surface a campaign's start/stop state. Centralizes the
  literal so producer (scheduler) and consumer (api) can't drift.
  Change `web-admin-campaign-workflow`.

## [v0.3.1] — 2026-05-22

### Added

- `isales_common.schemas.filler` — `FillerSetCreate/Update/Read` +
  `FillerPhraseCreate/Update/Read` pydantic DTOs. The `filler_set` /
  `filler_phrase` SQLAlchemy models already existed; only the DTO layer
  was missing. Needed by isales-api's new filler admin CRUD endpoints
  (change `web-admin-campaign-workflow`).

## [v0.3.0] — 2026-05-19

### Added

- `appointment` SQLAlchemy model + alembic migration
  (`a1b2c3d4e5f6_add_appointment_table.py`) — additive table with FKs to
  `lead` (CASCADE on delete) and `call_record` (SET NULL on delete); status
  enum (pending / confirmed / completed / cancelled, default pending).
  Spec: `openspec/changes/web-admin-ui-redesign` capability `appointment`.
- `AppointmentCreate` / `AppointmentUpdate` / `AppointmentRead` /
  `AppointmentStatusAction` pydantic DTOs in
  `isales_common.schemas.appointment`.
- `LeadStatus.APPOINTED` / `VISITED` / `LOST` enum values. Column type is
  `String(24)`; no DDL needed.
- `AppointmentStatus` and `AppointmentAction` StrEnums.

## [v0.2.1] — 2026-05-13

### Fixed

- `proto.cloud_edge_pb2_grpc` now imports `cloud_edge_pb2` via the
  package-relative path (`from isales_common.proto import cloud_edge_pb2
  as cloud__edge__pb2`). The grpcio-tools default emits a bare
  `import cloud_edge_pb2`, which only resolves if `isales_common/proto/`
  itself is on `sys.path` — fine inside this repo but breaks downstream
  services importing the stub via the package path. The Makefile's
  `proto` target now post-processes the generated file with `sed` so
  future regenerations stay consistent.

[v0.2.1]: https://github.com/tommax-bai/isales-common/releases/tag/v0.2.1

## [v0.2.0] — 2026-05-13

### Added

- **Cloud-edge gRPC control plane** (`proto.cloud_edge`): authoritative
  `.proto` source plus committed Python / gRPC / `.pyi` stubs. One bidi
  `CloudEdge.Bidi` stream per edge process; `Edge2Cloud` and `Cloud2Edge`
  envelopes carry `Heartbeat` / `DialCommand` / `CancelCommand` /
  `CallEvent` / `HardwareAlert` / `RtcCredentials` / `ConfigUpdate` /
  `RemoteDiagnostic` / `DialAck`. `CallEvent` and `HardwareAlert` use
  nested `oneof kind` for typed event payloads. Package version pinned
  in the proto path (`isales.cloud_edge.v1`). Spec: arch-cloud-edge-split
  change, service-communication § "云-边控制面".
- **Transport ABCs** (`transport.cloud_edge`): `CloudEdgeServer` /
  `CloudEdgeClient` / `TokenVerifier` / `EdgeIdentity`, plus errors
  `CloudEdgeError` / `EdgeNotConnected` / `InvalidToken`. Pure contract —
  no `grpcio` import. Concrete server lives in isales-engine, concrete
  client in isales-telephony.
- **Transport test doubles** (`transport.testing`): `InMemoryCloudEdgeServer`
  / `InMemoryCloudEdgeClient` / `StaticTokenVerifier` for in-process
  dispatch tests; buffer-on-disconnect semantics match the production
  contract (`critical=True` rejects when disconnected; default buffers).
- **RTC session ABC** (`audio.rtc`): `RtcSession` plus `PcmFrame` / errors
  `RtcError` / `RtcNotJoined` / `RtcPushBackpressure`. Symmetric contract
  used by both the cloud engine and edge audio-bridge; awaits SDK drain
  on outbound backpressure. Spec: device-hardware § "audio-bridge 组件" /
  "云端 engine 的 ARTC SDK 接入".
- **RTC test doubles** (`audio.testing`): `InMemoryRtcSession` (loopback)
  and `linked_pair()` (cross-wired cloud ↔ edge) for end-to-end audio
  pipeline tests without real RTC.
- **`make proto` Makefile target**: regenerates pb2 / pb2_grpc / .pyi
  stubs in place via `grpc_tools.protoc`. Generated stubs are committed.
- **`protobuf>=5.0`** moved to runtime dependencies (proto message classes
  needed at import time). `grpcio-tools>=1.60` added to the `dev` extra.

### Notes

- proto field numbers ≤ 15 are reserved for hot-path payloads (1-byte
  tag); 16+ for cold metadata. Field renumbering / removal MUST go through
  a `v2` package — concurrent v1+v2 service stubs run in parallel until
  edges roll forward.
- `ruff` / `mypy` / `ruff format` are configured to skip generated
  `*_pb2*.py` files. Regenerate with `make proto`, never edit by hand.

[v0.2.0]: https://github.com/tommax-bai/isales-common/releases/tag/v0.2.0

## [v0.1.2] — 2026-05-06

### Added

- `Device.last_call_at` (nullable `DateTime(timezone=True)`) — the column the
  `/devices/select` algorithm orders by (NULLS FIRST). Alembic revision
  `580b817550c8_add_device_last_call_at`.
- `schemas.device.DeviceSelectRequest` (`campaign_id`) and `DeviceSelectResponse`
  (`device_id`, `phone_number`) — request/response DTOs for telephony-api's
  `/devices/select` endpoint, used by scheduler.
- `utils.jwt.verify_jwt(token, secret) -> dict` — HS256 verifier consumed by
  every service except isales-api (which signs). `InvalidJWT` raised for
  expired / mismatched-signature / malformed tokens. Adds `python-jose[cryptography]`
  dependency. Per the architecture spec, no signing helper is exposed here.

### Notes

- `DeviceUpdate` and `DeviceRead` gained `last_call_at` for symmetry with the
  new column.

## [v0.1.1] — 2026-05-01

### Fixed

- `isales_common.providers.testing` no longer imports `pytest` at module
  top, so downstream production services can use the in-memory mocks
  without taking on a `pytest` dependency. The pytest fixtures moved to
  `isales_common.providers.testing.fixtures`; downstream test suites can
  re-export them in their own `conftest.py`.
- `utils.phone.normalize` now wraps the `phonenumbers.format_number`
  result in `str()` to satisfy strict mypy (1.8) under the
  `phonenumbers.*` `ignore_missing_imports` override.

## [v0.1.0] — 2026-05-01

Initial release. Establishes the shared foundation for the seven-repo iSales
platform per the OpenSpec `init-isales-common` change.

### Added

- **Enums** (`isales_common.enums`): `CallStatus`, `RoleKind`, `LeadStatus`,
  `HangupCause`, `DeviceStatus`, `SimCardStatus`, `AgentStatus`,
  `HandoffStatus`, `CallbackStatus`, `GenerationStatus`,
  `TransferStatus`, `TransferTriggerType`, `PromptScopeType`,
  `ContinuousInterruptionStrategy`.
- **ORM models** (`isales_common.models`): all 19 tables defined in the
  `data-model` spec, sharing a single `Base` (DeclarativeBase) so alembic
  autogenerate can introspect the full schema.
- **DTO schemas** (`isales_common.schemas`): `Create` / `Update` / `Read`
  triplets for every resource; `from_attributes=True` for ORM ↔ schema
  round-trip.
- **JSONB schemas** (`isales_common.schemas.jsonb`): typed Pydantic models
  for every JSONB field — `TimeWindow`, `RetryPolicy`, `CallbackTrigger`,
  `ExtractionField`, `TranscriptEvent` (discriminated union),
  `PipelineTraceEntry` substructures.
- **Provider ABCs** (`isales_common.providers`): `ASRProvider`,
  `TTSProvider`, `LLMProvider` with async streaming / chat contracts
  (`provider-abc` spec); unified `ProviderError` hierarchy
  (`Timeout` / `RateLimited` / `InvalidRequest` / `ServerError`); in-memory
  mocks plus pytest fixtures under `isales_common.providers.testing`.
- **Cross-service message schemas** (`isales_common.schemas.messages`):
  `BaseMessage` envelope (`schema_version` / `message_id` / `created_at`);
  concrete classes `DialRequest`, `CallEnded`, `EngineControl`
  (discriminated union of `ManualHangup` / `TransferCommand`),
  `EngineEvent` (discriminated union of six event types),
  `CampaignControl` (discriminated union of `Start` / `Pause` / `Resume`).
  Helpers: `CURRENT_SCHEMA_VERSION`, `SUPPORTED_SCHEMA_VERSIONS`,
  `is_supported_version()`.
- **Utilities** (`isales_common.utils`): E.164 phone normalisation,
  Fernet-based crypto (key via `ISALES_FERNET_KEY`), async Redis client
  factory, PCM audio constants.
- **Alembic**: async-mode init, `env.py` reads `ISALES_DATABASE_URL`,
  initial revision `017c370560ce_initial_schema` creates all 19 tables;
  CI runs `upgrade → check → downgrade → upgrade` roundtrip.
- **Tooling**: `pyproject.toml` (hatchling); ruff + mypy strict + pytest +
  pre-commit; GitHub Actions CI with PostgreSQL 16 service container.

### Notes

- Three foreign keys with `use_alter=True`
  (`campaign.transfer_llm_prompt_version_id`,
  `campaign.do_not_call_llm_prompt_version_id`,
  `role_config.current_prompt_version_id`) are emitted as explicit
  `op.create_foreign_key` calls at the end of the upgrade and matching
  `op.drop_constraint` calls at the start of the downgrade — alembic
  autogenerate did not handle these inline.

[v0.1.2]: https://github.com/tommax-bai/isales-common/releases/tag/v0.1.2
[v0.1.1]: https://github.com/tommax-bai/isales-common/releases/tag/v0.1.1
[v0.1.0]: https://github.com/tommax-bai/isales-common/releases/tag/v0.1.0
