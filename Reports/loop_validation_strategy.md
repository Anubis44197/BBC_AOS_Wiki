# Loop Validation Strategy - Phase 7C

This document defines the validation strategy, testing protocols, and verification checkpoints for the `bbc_aos` Loop Engine.

---

## 1. Validation Checks

Every execution loop iteration must pass through three verification checks before committing state transactions:

```
[Iteration Step] ──> [Syntax & AST Check] ──> [Hallucination Scan] ──> [Budget Audit] ──> [Commit Checkpoint]
```

1. **Syntax & AST Check:** Proposed patches are compiled using `ast.parse()`. If syntactically invalid, the step is rejected, and a retry is triggered.
2. **Hallucination Scan:** The `VerificationAgent` checks proposed code edits against the workspace symbol graph. If it references unknown external APIs, execution is halted.
3. **Budget Audit:** The `LoopSupervisor` verifies that the active run remains within iteration, token, time, and safety budgets.
4. **Checkpoint Commit:** Once verified, the state is persisted as a `LoopCheckpoint` on disk before execution moves to the next step.

---

## 2. Checkpoint Recovery Verification

To guarantee that loop executions are fully auditable and replayable:
* **Checkpoints State Matching:** Checkpoints saved to disk contain the serialized `LoopContext`, active metrics, and file diff state.
* **Deterministic Replay Check:** To verify checkpoint integrity, the recovery test suite must re-instantiate the Loop Engine using a saved checkpoint and confirm that the subsequent iteration matches the original run's output byte-for-byte.
* **Zero Behavioral Drift:** Re-executing a loop from any checkpoint must result in identical state transitions and outputs.

---

## 3. Human Approval Gate Validation

The validation suite verifies the human approval checkpoints under three policy models:
* **Mandatory Approval:** Pipeline pauses and waits indefinitely for explicit user input.
* **Optional Approval:** Pipeline prompts the user but continues automatically if no input is received within the timeout threshold.
* **Timeout Approval:** Pipeline pauses but auto-aborts/fails the execution if the user does not respond within a configurable timeout duration (e.g. 5 minutes).
