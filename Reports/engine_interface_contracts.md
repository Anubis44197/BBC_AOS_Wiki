# Engine Interface Contracts

**Date:** 2026-06-24  
**Status:** Planning & Draft  

This document details state transitions, serialization schemas, and validation contracts enforced by the HMPU Governor and Engine.

---

## 1. Mathematical State Transitions

The Governor weight states transition deterministically during feedback and execution loops:

### A. Gradient Bend Degradation (nabla A)
When stability is compromised (i.e. validation warnings are triggered), diagonal weights degrade states:
$$\text{STABLE} \rightarrow \text{WEAK} \rightarrow \text{UNSTABLE} \rightarrow \text{NEG\_ZERO}$$

### B. Self-Healing Promotions (Omega Trigger)
Under the self-healing protocol:
* `NEG_ZERO` or `UNSTABLE` states are promoted to `WEAK` utilizing the `OmegaOperator`.
* If a weight's `heal_count` exceeds the `heal_limit` (session heal budget), it transitions permanently to `DEGENERATE`, causing an execution abort and registering a critical anomaly.

```
                  [Gradient Bend (Stability = False)]
      STABLE -----------------------------------------> WEAK
        ^                                                |
        | [Omega Healing]                                |
        +---------------- UNSTABLE <---------------------+
                                 |
                                 v
                              NEG_ZERO
                                 |
                                 v [Heal Budget Exhausted]
                            DEGENERATE (Abort)
```

---

## 2. Serialization Contracts

### A. Matrix Serialization Format (`hmpu_weights.json`)
The weights matrix is saved as a 3x3 list of serialized `BBCScalar` values:
```json
[
  [{"v": 0.0, "s": "STABLE", "m": {"origin": "math"}}, ...],
  [...],
  [...]
]
```
During deserialization, custom JSON object hooks (`bbc_hook`) must be loaded to restore standard `BBCScalar` types.

### B. Telemetry Schema
All events written to `.bbc/logs/telemetry.jsonl` must follow:
* `ts`: ISO 8601 UTC Timestamp (`%Y-%m-%dT%H:%M:%S`).
* `event`: Event type (`HEAL_APPROVED`, `DEGENERATE`, etc.).
* `session`: Active session ID string.
* `data`: Embedded dictionary containing context metrics.

---

## 3. Constraint Validation Protocol (CVP)

The CVP requires validation of outputs against the constitution:
* **Output Format:** Verifies dictionary key whitelists.
* **Forbidden Content:** Checks for banned phrases (e.g. "speculative", "commentary", "guess").
* **Max Tokens:** Restricts total character/token limits.
* **CVP Response Payload:**
  * `status`: `"error"`
  * `error_type`: `"CONSTRAINT_VIOLATION"`
  * `severity`: `"hard"` (aborts execution) or `"soft"` (discards output)
