# Loop Execution Model Specification - Phase 7C

This document details the deterministic loop execution lifecycle, checkpointing mechanisms, and workflow sequences in `bbc_aos`.

---

## 1. Deterministic Execution Parameters

Every execution loop must be fully traceable, repeatable, and audited. Each iteration generates the following tracking parameters:
* **`trace_id`** (UUIDv4): Unique identifier tracking the parent request context.
* **`replay_id`** (UUIDv4): Tracing identifier matching Golden Master tests.
* **`iteration_id`** (UUIDv4): Unique identifier generated for the specific loop iteration step.
* **`deterministic_hash`** (SHA-256): Hash fingerprint of inputs and state variables to guarantee repeatability.

---

## 2. Checkpointing and State Persistence

To ensure loops can be replayed and resumed:
1. **Mandatory Iteration Checkpoint:** The `LoopEngine` must capture and save a `LoopCheckpoint` through the `StateManager` at the end of *every* iteration.
2. **Replayability:** A checkpoint must contain all the state required (memory logs, variables, last code AST) to rebuild and resume the loop from that specific step without behavioral drift.

---

## 3. Execution Sequence Diagrams

### A. Single-Step Deterministic Loop Execution

```mermaid
sequenceDiagram
    autonumber
    participant AO as AgentOrchestrator
    participant LE as LoopEngine
    participant LS as LoopSupervisor
    participant Core as BBC Core Validator
    participant SM as StateManager

    AO->>LE: execute_loop(task)
    LE->>LE: Initialize (State: CREATED -> READY)
    LE->>LS: check_budgets()
    LS-->>LE: Budgets OK
    
    LE->>LE: State: RUNNING
    LE->>Core: validate_iteration_step()
    Core-->>LE: Step Validated (deterministic_hash generated)
    
    LE->>SM: save_checkpoint(LoopCheckpoint)
    SM-->>LE: Checkpoint Saved
    
    LE->>LE: State: COMPLETED
    LE-->>AO: LoopResult
```

### B. Multi-Step Deterministic Loop Execution

```mermaid
sequenceDiagram
    autonumber
    participant AO as AgentOrchestrator
    participant LE as LoopEngine
    participant LS as LoopSupervisor
    participant Core as BBC Core Validator
    participant SM as StateManager

    AO->>LE: execute_loop(task)
    LE->>LE: Initialize (State: CREATED -> READY)
    
    loop Iterations (1 to 5)
        LE->>LS: check_budgets()
        LS-->>LE: Budgets OK (Iteration <= 5)
        LE->>LE: State: RUNNING (New iteration_id generated)
        
        LE->>Core: validate_step()
        Core-->>LE: Step Validated
        
        LE->>SM: save_checkpoint(LoopCheckpoint)
        SM-->>LE: Checkpoint Saved
        
        alt Step condition met (Task complete)
            LE->>LE: State: COMPLETED
        else Continue Loop
            LE->>LE: State: RETRYING
        end
    end
    
    LE-->>AO: LoopResult
```
