# Memory Runtime Contracts - Phase 8A

This document specifies the interface contracts, typing scopes, and schemas for all transactions in the Memory Layer.

## 1. Immutable Record Contract (`MemoryRecord`)

The `MemoryRecord` holds:

| Field | Type | Description |
| :--- | :--- | :--- |
| `memory_id` | `str` | Unique record key identifier. |
| `trace_id` | `str` | Request tracing UUID. |
| `replay_id` | `str` | Replay matching UUID. |
| `deterministic_hash` | `str` | Record payload SHA-256 fingerprint. |
| `version` | `int` | Version count index. |
| `created_at` | `str` | Timestamp of creation. |
| `originating_agent` | `str` | Identifier of agent who created the record. |
| `data` | `Dict[str, Any]` | JSON dictionary of payload details. |

---

## 2. Query and Result Contracts

* **`MemoryQuery` Fields:**
  * `layer`: Key of layer (`working`, `episodic`, etc.).
  * `filters`: Property filters dict.
  * `max_results`: Paging limit (default: 10).
  * `deterministic_sort`: Key ordering (`created_at_asc`).
* **`MemoryResult` Fields:**
  * `records`: Sorted List of `MemoryRecord` matching filters.
  * `audit_hash`: The hash computed for the corresponding audit log entry.
  * `metadata`: Contextual tags.

---

## 3. Telemetry and Exceptions Mapping

The `MemoryManager` maps exceptions to the standard JSON-RPC 2.0 error block:

* `MemoryException` (-33000): General execution error.
* `MemoryFrozenRegistryException` (-33001): Attempt to alter frozen configuration.
* `MemoryLifecycleException` (-33002): Invalid state transition.
* `MemoryPromotionException` (-33003): Invalid path or failed human authorization.
* `MemoryVisibilityException` (-33004): Actor role permission breach.
* `MemoryConflictException` (-33005): Duplicate write or collision detected.
