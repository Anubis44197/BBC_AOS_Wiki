# Loop Failure Recovery Specification - Phase 7C

This document establishes the error recovery policies, rollback procedures, and escalation workflows for the Loop Engine of `bbc_aos`.

---

## 1. Failure Recovery Actions

When an error is detected during loop execution, the `LoopEngine` dispatches one of the following recovery actions:

```
[Error Detected] ──> [Is Transient?] ────> Yes ──> [Retry Iteration]
                     └──> No ──> [Rollback State] ──> [Escalate / Terminate]
```

* **`Retry`:** Re-dispatches the iteration step with adjusted parameters (e.g., modified context prompts). Only allowed for transient syntax or parsing issues.
* **`Rollback`:** Restores the system state, files, and index databases to the last validated `LoopCheckpoint`.
* **`Escalate`:** Halts execution, raises an RPC error code, logs details to the system, and prompts for manual intervention.
* **`Terminate`:** Forcefully aborts loop execution, transitions the state machine to `TERMINATED`, and cleans up all uncommitted temporary transaction states.

---

## 2. LoopPolicy Definitions

The `LoopPolicy` defines the boundaries, conditions, and requirements governing loop state recovery:

* **Retry Limits:**
  * Capped at a maximum of 3 retry attempts per iteration.
  * Triggered by transient syntax errors, parsing issues, or JSON-RPC schema validation failures.
* **Escalation Thresholds:**
  * Triggers when the iteration retry limit is exhausted (attempts == 3).
  * Triggers when any safety budget check is breached (e.g., attempt to write outside sandbox).
  * Triggers when the state persistence engine encounters unrecoverable corruption.
* **Rollback Thresholds:**
  * Triggers immediately on any syntax check failure or verification failure that cannot be healed in place.
  * Reverts the project workspace files to the exact git and state checkpoint recorded at the start of the current iteration.
* **Approval Requirements:**
  * Defines human approval requirements for execution steps. Supports three gate options:
    1. *Mandatory approval:* Execution pauses indefinitely until user explicitly approves.
    2. *Optional approval:* Prompts the user but auto-proceeds if no response occurs within a limit.
    3. *Timeout approval:* Pauses and auto-terminates/fails the execution if the user does not respond within a configurable timeout duration (default: 5 minutes).

---

## 3. Workflow Diagrams

### A. Failure Recovery Workflow

```mermaid
sequenceDiagram
    autonumber
    participant LE as LoopEngine
    participant LS as LoopSupervisor
    participant Core as BBC Core Validator
    participant SM as StateManager

    LE->>Core: validate_iteration_step()
    
    alt Verification fails (e.g. Syntax Error)
        Core-->>LE: Error: Syntax Invalid
        LE->>LE: Check Retry Counter (< 3)
        LE->>LE: State: RETRYING
        LE->>LE: Re-dispatch execution step
    else Retry Limit Exceeded (Attempts == 3)
        LE->>LE: State: FAILED
        LE->>SM: rollback_to_last_checkpoint()
        SM-->>LE: State Rolled Back
        LE->>LE: Trigger Escalation
    end
```

### B. Human Approval Workflow

```mermaid
sequenceDiagram
    autonumber
    participant LE as LoopEngine
    participant LS as LoopSupervisor
    participant Client as User client UI
    
    LE->>LS: check_approval_requirement()
    LS-->>LE: Approval Required (MANDATORY)
    
    LE->>LE: State: WAITING_APPROVAL
    LE->>Client: Send approval request (Checkpoint detail)
    
    alt Approval Granted
        Client-->>LE: Approve
        LE->>LE: State: RUNNING
        LE->>LE: Resume loop execution
    else Approval Denied / Timeout
        Client-->>LE: Deny / Timeout
        LE->>LE: State: TERMINATED
    end
```

### C. Checkpoint Recovery Workflow

```mermaid
sequenceDiagram
    autonumber
    participant AO as AgentOrchestrator
    participant LE as LoopEngine
    participant SM as StateManager
    participant Storage as FileStateStorage

    AO->>LE: resume_from_checkpoint(session_id)
    LE->>SM: load_state(session_id)
    SM->>Storage: load_state_file(session_id)
    Storage-->>SM: State Metrics & Last Checkpoint
    SM-->>LE: Restored Checkpoint Data
    
    LE->>LE: State: READY
    LE->>LE: State: RUNNING (Iteration resumes deterministically)
```
