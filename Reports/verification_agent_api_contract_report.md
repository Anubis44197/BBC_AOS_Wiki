# VerificationAgent API Contract Report - Phase 11E

This report documents the JSON-RPC input parameters, output schemas, and integration contracts for the production `VerificationAgent`.

---

## 1. Input Contract Schema

The `VerificationAgent` expects parameters formatted inside standard `context` and `metadata` envelopes:

### Parameter Schema (JSON)

```json
{
  "context": {
    "task": {
      "task_id": "string (mandatory)",
      "description": "string (mandatory)",
      "dependencies": "array of strings (optional)"
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
    "validation_plan": {
      "trace_id": "string (mandatory)",
      "replay_id": "string (mandatory)",
      "deterministic_hash": "string (mandatory)",
      "validation_tasks": [
        {
          "task_id": "string (mandatory)",
          "test_type": "string (mandatory)",
          "target_file": "string (mandatory)",
          "description": "string (mandatory)",
          "priority": "integer (mandatory)",
          "dependencies": "array of strings (mandatory)"
        }
      ],
      "risk_level": "string (mandatory)",
      "coverage_targets": "object (mandatory)"
    },
    "packed_context": {
      "selected_files": "array of strings (mandatory)",
      "dependencies": "array of strings (optional)",
      "packed_context": "object (optional)"
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

The output is serialized as a plain dictionary:

### Result Schema (JSON)

```json
{
  "trace_id": "string",
  "replay_id": "string",
  "deterministic_hash": "string (64 hex characters representing SHA-256 fingerprint)",
  "verdict": "string (APPROVED | REJECTED)",
  "violations": "array of strings",
  "risk_level": "string (LOW | MEDIUM | HIGH | CRITICAL)",
  "validation_summary": {
    "files_checked": "integer",
    "tasks_checked": "integer",
    "violations_count": "integer",
    "risk_level": "string"
  }
}
```

---

## 3. Structural Limits and Rules

* **Blast Radius Containment:** Any modified, added, or removed file in `code_diff` must strictly exist in `packed_context["selected_files"]`.
* **Validation Tasks Ordering:** Tasks list in `validation_plan` must be sorted by `priority` first and then `task_id`.
* **Dependency Depth Limit:** The maximum depth of the task dependency tree in `validation_plan` must not exceed 5. No cyclic dependencies are allowed.
* **Hash Verification:** All deterministic hashes must be exactly 64 hexadecimal characters representing valid SHA-256 digests.
