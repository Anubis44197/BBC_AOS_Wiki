# Loop Runtime Contracts - Phase 7D

This document specifies the interface contracts, schemas, and typing models for all data exchange and state structures within the `bbc_aos` Loop Engine.

## 1. Immutable Input Contract (`LoopContext`)

The `LoopContext` is frozen at creation. It holds the tracking parameters:

| Field | Type | Description |
| :--- | :--- | :--- |
| `trace_id` | `str` | Unique trace UUID propagated from parent orchestrator request. |
| `replay_id` | `str` | Unique identifier used for deterministic test suite matching. |
| `task_id` | `str` | Task identifier being processed within the loop. |
| `params` | `Dict[str, Any]` | JSON parameter payload containing step-specific configuration. |
| `metadata` | `Dict[str, Any]` | General execution logs and contextual tags. |

---

## 2. Outcome Result Contract (`LoopResult`)

The `LoopResult` holds execution completion details:

| Field | Type | Description |
| :--- | :--- | :--- |
| `trace_id` | `str` | Trace identifier. |
| `replay_id` | `str` | Replay identifier. |
| `deterministic_hash` | `str` | Final iteration state SHA-256 fingerprint. |
| `checkpoint_id` | `Optional[str]` | The identifier of the last saved state checkpoint. |
| `execution_time_ms` | `float` | Duration in milliseconds. |
| `final_state` | `str` | Terminal state machine state (`COMPLETED`, `FAILED`, `TERMINATED`). |
| `success` | `bool` | True if the loop concluded without budget or validation breach. |
| `data` | `Dict[str, Any]` | Dictionary of compiled outputs. |
| `error_details` | `Optional[Dict]` | Error trace and RPC-compatible message structures if failed. |

---

## 3. Serialization Contract (`LoopCheckpoint`)

The checkpoint format supports backward recovery and replay matching:

```json
{
  "checkpoint_id": "cp_iter_1",
  "trace_id": "893c5c99-0d1a-4d92-a1de-50cbfa192be4",
  "replay_id": "402e9a5c-5b12-4fe0-be12-9de8e50b7bca",
  "deterministic_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "iteration_id": "iter_1",
  "parent_checkpoint_id": "cp_iter_0",
  "state_data": {},
  "workspace_diff": {}
}
```

---

## 4. Structured Exceptions Mapping

All internal exceptions map to unique JSON-RPC 2.0 error codes:

* `LoopException` (-32000): General loop error.
* `LoopBudgetExceededException` (-32001): Budget bounds (iterations, time, tokens) exceeded.
* `LoopSafetyViolationException` (-32002): sandbox or direct caller restriction violation.
* `LoopFrozenRegistryException` (-32003): Registry modification after startup frozen.
* `LoopStateMachineException` (-32004): Invalid transition attempt.
* `LoopCheckpointException` (-32005): Failed to save or deserialize checkpoint state.
