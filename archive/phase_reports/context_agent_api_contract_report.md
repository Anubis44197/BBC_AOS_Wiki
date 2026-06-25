# ContextAgent API Contract Report - Phase 11B

This document specifies the input parameters and output schemas required for calling the `ContextAgent`.

## 1. Input Parameter Schema

A call to `ContextAgent.execute()` must conform to the following schema:

```json
{
  "context": {
    "task": {
      "task_id": "string",
      "description": "string",
      "priority": "integer",
      "dependencies": "array of strings"
    },
    "task_profile": "string (optional: bugfix, feature, refactor, review)",
    "target_file": "string (optional)",
    "target_symbol": "string (optional)",
    "memory_manager": "MemoryManager (optional)",
    "integration_log": "IntegrationAuditLog (optional)"
  },
  "metadata": {
    "trace_id": "string",
    "replay_id": "string"
  }
}
```

* **task:** The target task dictionary produced by PlannerAgent.
* **task_profile:** Optional task compilation profile mapping to compiler budgets.
* **target_file / target_symbol:** Optional specific resolution targets. If omitted, they are extracted from the task description.

---

## 2. Output Schema

The output dictionary returned must conform to the following schema:

```json
{
  "trace_id": "string",
  "replay_id": "string",
  "deterministic_hash": "string (SHA-256 digest)",
  "task_id": "string",
  "selected_files": "array of strings",
  "dependencies": "array of strings",
  "packed_context": "object (lossless packed context dictionary)"
}
```

* **selected_files:** Extracted subset list of file paths, capped at 50.
* **dependencies:** Propagated task dependencies from input task, capped at depth 5.
* **packed_context:** The semantic-packed and compressed code context containing compiled symbol details, aliased path prefixes, and deduplicated shared imports.
* **deterministic_hash:** SHA-256 fingerprint generated from the `task_id`, `trace_id`, and sorted `packed_context` JSON string.
