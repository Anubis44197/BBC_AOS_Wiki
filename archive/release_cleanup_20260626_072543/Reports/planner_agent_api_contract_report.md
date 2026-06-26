# PlannerAgent API Contract Report - Phase 11A

This document specifies the input parameters and output schemas required for calling the `PlannerAgent`.

## 1. Input Parameter Schema

A call to `PlannerAgent.execute()` must conform to the following schema:

```json
{
  "context": {
    "goal": "string",
    "goal_id": "string"
  },
  "metadata": {
    "trace_id": "string",
    "replay_id": "string"
  }
}
```

* **goal:** The high-level user goal to decompose.
* **goal_id:** Unique goal identifier.
* **trace_id:** Tracing UUID.
* **replay_id:** Replay transaction UUID.

---

## 2. Output Schema

The output dictionary returned must conform to the following schema:

```json
{
  "goal_id": "string",
  "tasks": [
    {
      "task_id": "string",
      "description": "string",
      "priority": "integer (1, 2, or 3)",
      "dependencies": "array of strings"
    }
  ],
  "trace_id": "string",
  "replay_id": "string",
  "deterministic_hash": "string (SHA-256 digest)"
}
```

* **tasks:** Ordered list of tasks, capped at 20.
* **dependencies:** Pre-requisite task IDs, guaranteeing a maximum depth of 5.
* **deterministic_hash:** SHA-256 fingerprint generated from the `goal_id` and the sorted `tasks` JSON string.
