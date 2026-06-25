# Loop Safety Constraints Specification - Phase 7C

This document defines the safety boundaries, execution limits, and supervisor checks designed to prevent non-deterministic loops in `bbc_aos`.

---

## 1. Safety Boundaries

To prevent infinite execution, resource exhaustion, and code corruption, the Loop Engine operates under strict safety constraints:
* **No Self-Spawning Loops:** Loop structures are static. The Loop Engine is prohibited from spawning child loops or delegating loop executions to agents.
* **No Recursive Execution:** Loops cannot call themselves. The execution stack depth is flat:
  $$\text{MAX\_LOOP\_DEPTH} = 1$$
* **No Infinite Loops:** Loops are bound to a strict limit of:
  $$\text{MAX\_ITERATIONS} = 5$$
* **No Adaptive Self-Routing:** The execution path is static and defined entirely by the orchestrator task list. The Loop Engine cannot dynamically change routing policies based on intermediate LLM outputs.
* **No Direct LLM Queries:** The Loop Engine does not communicate with LLM gateways. It dispatches calls through the orchestrator validation gateway.

---

## 2. LoopSupervisor Budget Checks

The `LoopSupervisor` continuously monitors execution boundaries:

### A. Iteration Budget
* Tracks iteration counts. If iterations exceed the limit of 5, the loop is aborted and transitioned to the `FAILED` state.

### B. Token Budget
* Tracks cumulative prompt and output token counts. If cumulative tokens exceed the session budget limit (e.g. 100,000 tokens), the loop is terminated.

### C. Time Budget
* Tracks elapsed execution time. If execution exceeds the timeout threshold (e.g. 60 seconds), the loop triggers a timeout error.

### D. Safety Budget
* Tracks permissions and file accesses. If any step attempts directory writes outside the workspace boundary, the loop is halted, and a safety breach escalation is triggered.
