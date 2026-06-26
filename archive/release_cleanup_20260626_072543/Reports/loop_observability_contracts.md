# Loop Observability Contracts - Phase 7C

This document specifies the telemetry log schemas, auditing parameters, and playback tracing contracts for loop executions in `bbc_aos`.

---

## 1. Tracing Parameters

Every iteration event logged to telemetry must include the following tracing block:

```json
{
  "trace_id": "f5b89a8c-12db-4fb9-a9de-9bc0bc503bc1",
  "replay_id": "402e9a5c-5b12-4fe0-be12-9de8e50b7bca",
  "iteration_id": "9bc0e5bc-a2de-4fb0-12de-8e50bc553d0e",
  "deterministic_hash": "a1b2c3d4e5f6..."
}
```

---

## 2. Telemetry Log Event Schema

Loop lifecycle transitions are appended to `telemetry.jsonl` under the following structured format:

```json
{
  "ts": "2026-06-24T17:50:00",
  "event": "LOOP_ITERATION",
  "session": "20260624_174000",
  "data": {
    "trace_id": "f5b89a8c-12db-4fb9-a9de-9bc0bc503bc1",
    "replay_id": "402e9a5c-5b12-4fe0-be12-9de8e50b7bca",
    "iteration_id": "9bc0e5bc-a2de-4fb0-12de-8e50bc553d0e",
    "iteration_index": 2,
    "from_state": "RUNNING",
    "to_state": "RETRYING",
    "deterministic_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "tokens_used": 1540,
    "time_elapsed_ms": 1250,
    "warning_code": "SYNTAX_CHECK_FAIL",
    "checkpoint_path": "state/20260624_174000_checkpoint_2.json"
  }
}
```

---

## 3. Auditing & Replay Protocol

To replay any execution run:
1. **Identify Session:** Locate the session ID and target `replay_id` in `telemetry.jsonl`.
2. **Collect Checkpoints:** Load the sequence of `LoopCheckpoint` files saved under `state/`.
3. **Execute Replay Suite:** Invoke the Loop Engine with the initial context. Ensure that at every step `iteration_index` = $N$:
   * Input parameters and file code match the state loaded from `checkpoint_N`.
   * The calculated `deterministic_hash` matches the recorded log hash byte-for-byte.
4. **Assert Outcome:** Verify that the final execution result matches the original output exactly.
