# CoderAgent API Contract Report
**Phase 11C — BBC-AOS Agent API Contracts**
**Status:** FROZEN
**Date:** 2026-06-24

---

## 1. Agent Metadata

| Property | Value |
|---|---|
| `AGENT_ID` | `coder_agent` |
| `AGENT_VERSION` | `1.0.0` |
| `SUPPORTED_ACTIONS` | `generate_diff`, `plan_modification`, `plan_refactor` |

---

## 2. Input Schema

```json
{
  "context": {
    "task": {
      "task_id": "string (required)",
      "description": "string (required)",
      "priority": "int (optional, 1-3)",
      "dependencies": ["string", "..."]
    },
    "packed_context": {
      "code_structure": [...],
      "_path_aliases": {...},
      "_shared_imports": [...],
      "metrics": {...}
    },
    "selected_files": ["string", "..."],
    "integration_log": "IntegrationAuditLog instance (optional)"
  },
  "metadata": {
    "trace_id": "string (required)",
    "replay_id": "string (required)"
  }
}
```

### Input Constraints

| Constraint | Limit |
|---|---|
| `selected_files` length | max 50 (truncated silently with warning) |
| `task.dependencies` length | max 5 (logged if exceeded) |
| `task_id` | non-empty string |
| `description` | non-empty string |
| `trace_id` | non-empty string |
| `replay_id` | non-empty string |

---

## 3. Output Schema (CodeDiff)

```json
{
  "modified_files": ["string", "..."],
  "added_files": ["string", "..."],
  "removed_files": ["string", "..."],
  "patch": "string (unified diff format)",
  "trace_id": "string",
  "replay_id": "string",
  "deterministic_hash": "string (SHA-256 hex, 64 chars)"
}
```

### Output Constraints

| Constraint | Limit |
|---|---|
| Total diff files (modified + added + removed) | max 20 |
| `deterministic_hash` | exactly 64 hex characters |
| `modified_files` | sorted, deduplicated list |
| `added_files` | sorted, deduplicated list |
| `removed_files` | always `[]` (removal not in current scope) |

---

## 4. Operation Types

| Operation | Keyword Triggers | Side Effects |
|---|---|---|
| `bugfix` | fix, bug, patch, error, repair | Only `modify` operations |
| `refactor` | refactor, restructure, clean, reorganize, migrate | Only `modify` operations |
| `feature` | feature, add, implement, extend, introduce | `modify` + `add` operations |
| `review` | review, audit, analyse, analyze, inspect, check | No modifications (read-only) |

---

## 5. Error Conditions

| Condition | Behaviour |
|---|---|
| Missing required input fields | `validate_input()` returns `False` |
| ValidationGateway failure | `IntegrationValidationException` raised |
| Empty blast radius | Empty diff returned (no error) |
| `selected_files` > 50 | Silently truncated to 50 + warning logged |
| `deterministic_hash` != 64 chars | `validate_output()` returns `False` |

---

## 6. Forbidden Operations

The `CoderAgent` MUST NOT:
- Access the repository filesystem directly.
- Write to `MemoryManager`.
- Communicate with other agents directly.
- Access the internet.
- Use any non-deterministic operations (random, time-based seeding, etc.).
- Modify files outside the provided blast radius (`selected_files`).

---

## 7. Audit Contract

Every `execute()` call emits exactly one `IntegrationAuditEvent`:

```json
{
  "event_id": "coder_{trace_id}",
  "event_type": "code_diff_generated",
  "trace_id": "...",
  "replay_id": "...",
  "deterministic_hash": "...",
  "details": {
    "task_id": "...",
    "operation": "bugfix|refactor|feature|review",
    "modified_count": 0,
    "added_count": 0,
    "removed_count": 0,
    "blast_radius_files": 0
  }
}
```
