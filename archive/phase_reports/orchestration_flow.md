# Orchestration Flow - Phase 9A

This document details the user request orchestration sequence and visualizes the interaction between subsystems.

## 1. User Request Flow Sequence

When a user submits a task, it traverses the system according to the following sequence:

1. **User Request Initiation:** The user sends a request to the system.
2. **Orchestrator Parsing:** The `AgentOrchestrator` receives the request, generates a unique `trace_id`, a `replay_id`, and validates security boundaries.
3. **Agent Dispatch:** The orchestrator dispatches the task to the `PlannerAgent` inside the `Agent Runtime` to create an execution plan.
4. **Loop Engine Handshake:** The orchestrator routes the execution plan to the `LoopEngine` to perform iterative tasks.
5. **Core Evaluation:** The `LoopEngine` evaluates equations and calculations by calling the functional `Deterministic Core` (evaluating Shannon chaos, matrix pivots).
6. **Memory Operations:** During and after the loop iterations, state and checkpoints are persisted by sending write requests through the orchestrator to `MemoryManager`.
7. **Validation Check:** The execution result is sent to the `BBC Validation Layer` where the `VerificationAgent` runs equivalence tests.
8. **User Response:** The validated result is packaged into a JSON-RPC 2.0 success response and returned to the user.

---

## 2. Orchestration Flow Diagram

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Orchestrator as AgentOrchestrator
    participant Agent as Agent Runtime
    participant Loop as LoopEngine
    participant Core as Deterministic Core
    participant Mem as MemoryManager
    participant Val as Validation Layer

    User->>Orchestrator: User Request (task)
    Note over Orchestrator: Generate trace_id, replay_id, & hash
    Orchestrator->>Agent: Dispatch Task (PlannerAgent)
    Agent-->>Orchestrator: Execution Plan
    Orchestrator->>Loop: Execute Plan
    
    loop Iteration Loop
        Loop->>Core: Evaluate Core Equations
        Core-->>Loop: Math Results (Chaos, Aura)
        Loop->>Orchestrator: Request Persistence
        Orchestrator->>Mem: Write Checkpoint / State
        Mem-->>Orchestrator: Audit Hash
        Orchestrator-->>Loop: Checkpoint ID
    end
    
    Loop-->>Orchestrator: Raw Execution Result
    Orchestrator->>Val: Validate Output
    Val->>Val: Run Verification Checks
    Val-->>Orchestrator: Validation Verdict (Pass/Fail)
    Orchestrator-->>User: JSON-RPC Response (Result + trace_id)
```
