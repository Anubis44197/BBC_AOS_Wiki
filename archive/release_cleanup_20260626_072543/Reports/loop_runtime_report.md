# Phase 7D - Loop Runtime Report

This report summarizes the design, directory structure, and runtime execution constraints implemented for the `bbc_aos` Loop Engine skeleton framework.

## 1. Directory Structure Layout

The skeleton framework is implemented under the [`bbc_aos/loops/`](file:///C:/Users/90535/Desktop/BBC_AOS_Wiki/bbc_aos/loops/) package directory:

```
bbc_aos/loops/
├── __init__.py           # Package exports for all loop components
├── loop_budget.py        # Budget tracking with hard and soft limits
├── loop_checkpoint.py    # Checkpoint persistence models
├── loop_context.py       # Immutable execution parameter models
├── loop_engine.py        # Sole loop runtime executor
├── loop_exceptions.py    # Structured RPC-compatible exceptions
├── loop_policy.py        # Retries, timeouts, escalations, rollbacks configuration
├── loop_registry.py      # Runtime registration and freeze lock lifecycle
├── loop_state_machine.py  # Deterministic loop execution state machine
└── loop_supervisor.py     # Budget and directory sandbox supervisor
```

---

## 2. Caller Restriction Mechanics

To satisfy the constraint that **`LoopEngine` may only be invoked by `AgentOrchestrator`**, stack frame inspection is performed at instantiation and key entry points in [`loop_engine.py`](file:///C:/Users/90535/Desktop/BBC_AOS_Wiki/bbc_aos/loops/loop_engine.py):

* **Stack Inspection:** Using `inspect.stack()`, the engine searches the active call stack frames for an instance of `AgentOrchestrator`.
* **Protection Enforcement:** If no class named `AgentOrchestrator` is detected in the stack, a `LoopSafetyViolationException` is raised immediately.
* **Resulting Security:** This prevents any external script, component, or agent from direct execution or spawning of loops.

---

## 3. Loop Budget and Policy Management

* **Hard and Soft Limits:** The `LoopBudget` monitors limits for:
  * Iterations (`max_iterations = 5`)
  * Time (`max_time_seconds = 60.0`)
  * Tokens (`max_tokens = 100000`)
  * Safety violations (`max_safety_violations = 0`)
  Soft limits generate warnings on observability logs, while hard limits raise `LoopBudgetExceededException`.
* **State Recovery Policies:** The `LoopPolicy` holds the configured rules for retries, timeouts, escalations, rollbacks, and approval gate models.

---

## 4. State Machine Lifecycle

Execution states strictly follow the state chart:
`CREATED` -> `READY` -> `RUNNING` -> `WAITING_APPROVAL` -> `RETRYING` -> `COMPLETED` / `FAILED` / `TERMINATED`.
Transitions are validated against allowed targets to maintain state consistency.
