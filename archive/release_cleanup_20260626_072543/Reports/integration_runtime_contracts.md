# Integration Runtime Contracts - Phase 9B

This document specifies the interface contracts, typing scopes, and schemas for all transactions in the End-to-End Integration Runtime.

## 1. Immutable Context Contract (`IntegrationContext`)

The `IntegrationContext` holds tracing metadata:

| Field | Type | Description |
| :--- | :--- | :--- |
| `trace_id` | `str` | Request tracing UUID. |
| `replay_id` | `str` | Replay matching UUID. |
| `deterministic_hash` | `str` | Payload SHA-256 fingerprint. |
| `payload` | `Dict[str, Any]` | JSON dictionary of context details. |
| `metadata` | `Dict[str, Any]` | Contextual tags. |

---

## 2. Immutable Result Contract (`IntegrationResult`)

The outcome of dispatches is wrapped in a structured result:

| Field | Type | Description |
| :--- | :--- | :--- |
| `success` | `bool` | True if the dispatch completed successfully. |
| `trace_id` | `str` | Request tracing UUID. |
| `replay_id` | `str` | Replay matching UUID. |
| `deterministic_hash` | `str` | Response payload SHA-256 fingerprint. |
| `data` | `Dict[str, Any]` | Response payload. |
| `error` | `Dict[str, Any]` | JSON error payload. |
| `metadata` | `Dict[str, Any]` | Tracking metadata. |

---

## 3. Telemetry and Exceptions Mapping

The `IntegrationOrchestrator` maps exceptions to standard JSON-RPC 2.0 error blocks:

* `IntegrationException` (-32000): General execution error.
* `IntegrationFrozenRegistryException` (-32001): Attempt to alter registered subsystems after startup freeze.
* `IntegrationValidationException` (-32002): Output schema or safety check validation failure.
* `IntegrationSyncException` (-32003): Synchronization or commit validation failure.
* `IntegrationLifecycleException` (-32004): Startup/Shutdown sequence ordering violation.
