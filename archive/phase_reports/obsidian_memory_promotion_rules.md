# Obsidian Memory Promotion Rules - Phase 7F

This document establishes the transition states and cross-layer promotion rules governing human notes and experience memory items.

---

## 1. Note Lifecycle States

Every note and proposal moves through the following states:

```mermaid
stateDiagram-v2
    [*] --> DRAFT : Note created/edited
    DRAFT --> PROPOSED : Sync proposal generated
    PROPOSED --> REVIEW_PENDING : User review notified
    REVIEW_PENDING --> APPROVED : User approved sync
    REVIEW_PENDING --> REJECTED : User rejected sync
    APPROVED --> ARCHIVED : Superceded by newer version
    REJECTED --> DRAFT : Reverted to draft for edits
    ARCHIVED --> [*]
```

* **`DRAFT`:** Active workspace modifications.
* **`PROPOSED`:** `ProposalArtifact` written as sidecar diff.
* **`REVIEW_PENDING`:** Waiting for human operator authorization.
* **`APPROVED`:** Confirmed by operator; changes merged.
* **`REJECTED`:** Denied by operator; changes discarded.
* **`ARCHIVED`:** Replaced by newer notes or deprecated.

---

## 2. Knowledge Promotion Workflow Diagram

```mermaid
sequenceDiagram
    autonumber
    participant EX as Experience Memory
    participant MS as MemorySupervisor
    participant H as Human Operator
    participant Disk as Local Vault Notes
    participant SE as Semantic Memory

    rect rgb(200, 220, 240)
        Note over EX, Disk: Promotion Flow 1: Experience to Obsidian Note
        EX->>MS: promote_to_obsidian(experience_trace_id)
        MS->>H: Notify Human Review
        H-->>MS: Confirm note draft
        MS->>Disk: Write new markdown note (DRAFT state)
    end

    rect rgb(240, 200, 200)
        Note over Disk, SE: Promotion Flow 2: Obsidian Note to Semantic Memory
        Disk->>MS: promote_to_semantic(note_id)
        MS->>H: Request explicit Human Approval (Mandatory)
        H-->>MS: Approved
        MS->>SE: Commit verified recipe/rule (No direct write allowed)
    end
```

---

## 3. Proposal Lifecycle Workflow Diagram

The `ProposalArtifact` transitions determine how system-proposed changes are safely merged into the human vault.

```mermaid
stateDiagram-v2
    [*] --> GENERATED : SyncPlanner compiles differences
    GENERATED --> VALIDATED : SyncSupervisor verifies safety
    VALIDATED --> PENDING_REVIEW : Sidecar .proposal.md file written
    PENDING_REVIEW --> COMMITTED : User approves merge proposal
    PENDING_REVIEW --> DISCARDED : User rejects or proposal times out
    COMMITTED --> [*]
    DISCARDED --> [*]
```
