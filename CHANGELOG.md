# Changelog

All notable changes to `isales-common` are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project
adheres to [Semantic Versioning](https://semver.org/).

## [v0.8.21] — 2026-06-17

### Added

- **`campaign.wrap_up_silence_hangup_ms` 字段**（change
  `engine-wrap-up-silence-hangup`）。收尾（WRAPPING_UP）期客户静默主动挂断的时长
  阈值，Integer NOT NULL server_default 6000。alembic 迁移 `b3d5f7a9c1e2`
  ADD COLUMN（server_default 回填存量行，NOT NULL 安全；对在途通话无影响）。
  收尾期客户静默达此时长 → engine 直接主动挂断，**跳过**「你好，还在么？」重新
  激活阶梯（该阶梯仍为通话中段专用）。刻意配置为长于 `silence_threshold_ms`
  （3000），给客户告别后留思考时间；`wrap_up_max_rounds` / `wrap_up_max_seconds`
  计数器仍为硬上限兜底。

## [v0.8.6] — 2026-06-10

### Removed (BREAKING)

- **`campaign.max_no_progress_seconds` 字段下线**（change
  `silence-drop-no-progress-timeout`）。删除模型列 + `CampaignBase` /
  `CampaignUpdate` schema 字段，alembic 迁移 `d5e6f7a8b9c0` DROP COLUMN
  `campaign.max_no_progress_seconds`（nullable、生产恒 NULL，drop 非破坏）。
  独立的秒级「无进展超时」计时器与「沉默超限挂断」（`max_silence_activations`
  + `silence_threshold_ms` + `silence_hangup_phrase` → `silence_max_reached`）
  重复且误导，统一收口到沉默超限一条路径。`HangupCause.NO_PROGRESS_TIMEOUT`
  枚举**保留**（仍是 engine / worker 内部异常兜底 cause + 历史行）。

## [v0.8.5] — 2026-06-09

### Removed (BREAKING)

- **预约 / 音色目录 / 转人工任务 三个 vestigial 功能整体下线**（change
  `admin-prune-vestigial-features`）。删除 ORM 模型 `Appointment` / `VoiceModel`
  / `HandoffTask`、对应 schemas，枚举 `AppointmentStatus` / `AppointmentAction`
  / `HandoffStatus`，以及 `LeadStatus.APPOINTED` / `LeadStatus.VISITED`
  （`LeadStatus.LOST` 保留）。alembic 迁移 `c4d5e6f7a8b9` DROP 三张表
  `appointment` / `voice_model` / `handoff_task`（均为 write-never / 无运行时
  消费方；v1.0 无生产数据，drop 安全）。`downgrade()` 结构性重建三表。
- **`TransferMarkedEvent.handoff_task_id` 死字段移除**：转人工不再写
  `handoff_task` 记录，该恒为 0 的字段随表删除。引擎转人工检测（标记
  `transfer_status=marked_for_handoff` + 挂断）与 worker `lead.status=transferred`
  信号保持不变；`TransferTriggerType` 枚举保留（转人工触发词汇规范定义）。

## [v0.5.2] — 2026-06-04

### Added

- **`campaign.filler_delay_ms`** (Integer, nullable) — per-campaign filler
  time-gate in ms (change `tts-cache-and-gated-filler` § B). NULL falls back
  to the engine default (600ms): a filler is played only when the main
  reply's first audio hasn't started within this window. Added to `Campaign`
  model, `CampaignBase` / `CampaignUpdate` schemas, and alembic migration
  `e5f6a7b8c9d0` (additive column).

## [v0.5.1] — 2026-06-04

### Added

- **`campaign.asr_eos_silence_ms`** (Integer, nullable) — per-campaign ASR EOS
  stable-silence threshold in ms (change `pipeline-latency-tail` § A). NULL
  falls back to the engine default (400ms). Added to `Campaign` model,
  `CampaignBase` / `CampaignUpdate` schemas, and alembic migration
  `d4e5f6a7b8c9` (additive column, no data migration).

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
  - `PromptVersionsSnapshot` (dial message): `role_llms[] / judge_llm /
    polish_llm` → `main_llm / referee_llm / extractor_llm` (the
    `call_record.prompt_versions` snapshot shape; produced by isales-scheduler,
    consumed by isales-engine).

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
- `isales_common.redis_keys.EXTRACT_QUEUE` (`isales:extract`) — engine→worker
  post-call extraction queue.

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
