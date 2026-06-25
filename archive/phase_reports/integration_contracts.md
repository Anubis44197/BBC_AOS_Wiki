# Integration Contracts - Phase 9A

This document details the interface schemas, metadata parameters, and health status contracts for all subsystem interactions.

## 1. Tracing and Auditing Parameters

Every cross-subsystem transaction must include the following metadata envelope fields:

| Field | Type | Description |
| :--- | :--- | :--- |
| `trace_id` | `str` | Request tracking UUID to correlate logs across all runtimes. |
| `replay_id` | `str` | Replay transaction UUID to scope history playbacks. |
| `deterministic_hash` | `str` | SHA-256 fingerprint generated from inputs and states. |

### Schema Example:
```json
{
  "jsonrpc": "2.0",
  "method": "subsystem.action",
  "params": {
    "data": {},
    "metadata": {
      "trace_id": "tr_893b827e-8c70-4f9e-a0e2-b91c0154fbdf",
      "replay_id": "rp_5a60e0a5-f5b2-4d1a-be3b-2804b4c7ef39",
      "deterministic_hash": "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
    }
  },
  "id": 1
}
```

---

## 2. Health Status Contracts

Every subsystem registry or manager must implement the `get_health_status()` method.

```python
from typing import Dict, Any

def get_health_status(self) -> Dict[str, Any]:
    """
    Returns the current health status parameters of the subsystem.
    """
    pass
```

### Health Return Schema:
```json
{
  "subsystem": "memory | loop | agent | knowledge | core",
  "status": "OK | DEGRADED | UNHEALTHY",
  "is_frozen": true,
  "metrics": {
    "active_contexts": 0,
    "total_records": 128,
    "error_count": 0
  },
  "timestamp": "2026-06-24T18:35:00Z"
}
```

---

## 3. Exception Response Mapping

Errors returned by subsystems must map to JSON-RPC 2.0 error specifications:

| Code Range | Error Type | Subsystem |
| :--- | :--- | :--- |
| `-32000 to -32099` | Server Error (System) | Orchestrator / Broker |
| `-33000 to -33099` | Memory Error | Memory Layer |
| `-34000 to -34099` | Obsidian Sync / Safe Error | Obsidian Layer |
| `-35000 to -35099` | Loop Budget / State Error | Loop Engine |
| `-36000 to -36099` | Mathematical Stability Error | Deterministic Core |
| `-37000 to -37099` | Agent Dispatch / Safety Error | Agent Runtime |
