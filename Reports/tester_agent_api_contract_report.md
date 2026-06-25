# TesterAgent API Contract Report - Phase 11D

This report documents the JSON-RPC input parameters, output schemas, and integration contracts for the production `TesterAgent`.

---

## 1. Input Contract Schema

The `TesterAgent` expects parameters formatted inside standard `context` and `metadata` envelopes:

### Parameter Schema (JSON)

```json
{
  "context": {
    "task": {
      "task_id": "string (mandatory)",
      "description": "string (mandatory)",
      "priority": "integer (optional)",
      "dependencies": "array of strings (optional, depth <= 5)"
    },
    "code_diff": {
      "modified_files": "array of strings (mandatory)",
      "added_files": "array of strings (mandatory)",
      "removed_files": "array of strings (mandatory)",
      "patch": "string (mandatory)",
      "trace_id": "string (mandatory)",
      "replay_id": "string (mandatory)",
      "deterministic_hash": "string (mandatory)"
    },
    "integration_log": "IntegrationAuditLog instance (optional)"
  },
  "metadata": {
    "trace_id": "string (mandatory)",
    "replay_id": "string (mandatory)"
  }
}
```

---

## 2. Output Contract Schema

The output is serialized as a plain dictionary conforming to the standard `ValidationPlan` contract:

### Result Schema (JSON)

```json
{
  "trace_id": "string",
  "replay_id": "string",
  "deterministic_hash": "string (64 hex characters representing SHA-256 fingerprint)",
  "validation_tasks": [
    {
      "task_id": "string",
      "test_type": "string (syntax | unit | integration | regression | replay)",
      "target_file": "string",
      "description": "string",
      "priority": "integer (1 to 5)",
      "dependencies": "array of strings (depth <= 5)"
    }
  ],
  "risk_level": "string (LOW | MEDIUM | HIGH | CRITICAL)",
  "coverage_targets": {
    "syntax": "boolean",
    "unit": "boolean",
    "integration": "boolean",
    "regression": "boolean",
    "replay": "boolean"
  }
}
```

---

## 3. Structural Limits

* **Max Tasks:** `len(validation_tasks) <= 50`.
* **Max Dependencies:** `len(dependencies) <= 5` for any generated task.
* **Hash Validation:** `deterministic_hash` must be exactly 64 hex characters.
* **Risk Levels:** Must strictly map to: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.
* **Coverage Keys:** Must strictly include: `syntax`, `unit`, `integration`, `regression`, `replay`.
