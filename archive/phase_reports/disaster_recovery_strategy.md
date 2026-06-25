# Disaster Recovery Strategy - Phase 10A

This document details the disaster recovery models, objectives, and rollback procedures for BBC-AOS.

## 1. Recovery Objectives and SLAs

* **Recovery Time Objective (RTO):** The maximum tolerable duration to restore system execution from a crash is **< 500ms** (excluding human approval gates).
* **Recovery Point Objective (RPO):** The maximum data loss limit is **0 records**. The system preserves this via append-only logs and immediate checkpoint commits.
* **Production SLA:** E2E system availability must meet **99.9%** stability. All calculations must remain deterministic.

---

## 2. Disaster Recovery Workflow

```mermaid
graph TD
    Crash([System Crash / Failure Detected]) --> Halt[1. Halt All Active Execution Threads]
    Halt --> CheckState[2. Query Local File Persistence for Checkpoint]
    
    subgraph "Re-hydration"
        CheckState --> ReadCheck[3. Read Last Valid Checkpoint]
        ReadCheck --> VerifyHash{"4. Hash Integrity Valid?"}
        VerifyHash -- No --> RollbackParent[5. Rollback to Parent Checkpoint]
        VerifyHash -- Yes --> Rehydrate[6. Rehydrate Skeletons state]
    end
    
    RollbackParent --> Rehydrate
    Rehydrate --> HealthCheck[7. Perform E2E Health Sweep]
    
    HealthCheck --> Recovered{"8. Health Status OK?"}
    Recovered -- Yes --> Resume[9. Resume Loop execution]
    Recovered -- No --> Escalate[10. Escalate & Prompt Human]
```

---

## 3. Subsystem Recovery Workflow

The sequence below runs when the supervisor initiates a recovery run:

```mermaid
sequenceDiagram
    autonumber
    participant Orchestrator as AgentOrchestrator
    participant Supervisor as IntegrationSupervisor
    participant Registry as SubsystemRegistry
    participant Memory as MemoryManager
    
    Orchestrator->>Supervisor: Recover(checkpoint_id, trace_id)
    Supervisor->>Memory: Get Checkpoint Payload
    Memory-->>Supervisor: Checkpoint Payload + Hash
    Supervisor->>Supervisor: Verify Payload Hash integrity
    Supervisor->>Registry: Sweep Subsystems health
    Registry-->>Supervisor: Health Status OK
    Supervisor->>Memory: Rehydrate State values
    Supervisor-->>Orchestrator: Recovery Complete (Status: OK)
```

---

## 4. Rollback Procedures

1. **State Isolation:** The active database lists are locked, preventing dirty writes.
2. **Revert State:** The engine reads the `parent_checkpoint_id` pointer from the last audited checkpoint and reverts parameters to the corresponding state snapshot.
3. **Commit Rollback Audit:** Write an immutable audit log entry documenting the rollback (`event_type: "rollback_commit"`), referencing the `trace_id` and new state hash.
4. **Notify Client:** Respond to the client with the rolled-back context ID to trigger execution restart.
