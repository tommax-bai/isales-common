# Changelog

All notable changes to `isales-common` are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project
adheres to [Semantic Versioning](https://semver.org/).

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
