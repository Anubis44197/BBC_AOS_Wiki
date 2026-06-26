# Obsidian Synchronization Model - Phase 7F

This document specifies the synchronization policies, transition stages, and replay models designed to integrate human-edited notes deterministically.

---

## 1. Synchronization Policies

To prevent unauthorized modification of human documents, three synchronization policies are enforced:

* **Pull-Only:** The system reads markdown files and YAML frontmatter headers to extract lessons or instructions. No writes or proposals are dispatched to the vault directory.
* **Proposal-Based Push:** The system compiles a `ProposalArtifact` containing proposed changes. It writes a separate sidecar file (e.g. `note.proposal.md`) containing the diff and safety assessment, leaving the original human note completely unmodified.
* **Approval-Required Merge:** The system proposes changes to existing notes, but modifications are merged into the target markdown files **only** after explicit, mandatory human approval is received. **Automatic merges are strictly forbidden.**

---

## 2. Synchronization Workflow Diagram

```mermaid
sequenceDiagram
    autonumber
    participant System as LoopEngine/Orchestrator
    participant SS as SyncSupervisor
    participant SP as SyncPlanner
    participant H as Human Operator
    participant Disk as Local Vault Notes

    System->>SS: request_sync(note_id, trace_info)
    SS->>SP: compute_differences(note_id)
    SP-->>SS: Note Diffs and Rationale
    
    SS->>SS: Generate ProposalArtifact (.proposal.md)
    SS->>H: Render Proposal details & diffs
    
    alt Human Approves Proposal
        H-->>SS: Approve Sync
        SS->>Disk: Apply diffs to human note (Immutable Write)
        SS->>SS: Log sync audit log
        SS-->>System: Sync Completed (Success)
    else Human Rejects / Timeout
        H-->>SS: Reject
        SS->>SS: Discard Proposal (Keep original note intact)
        SS->>SS: Log rejection audit log
        SS-->>System: Sync Cancelled
    end
```

---

## 3. Replay Workflow Diagram

Replaying note synchronizations ensures that rebuilding state history remains deterministic and repeatable across Golden Master certification test runs.

```mermaid
sequenceDiagram
    autonumber
    participant AO as AgentOrchestrator
    participant SS as SyncSupervisor
    participant VI as VaultIndexer
    participant OAL as ObsidianAuditLog
    participant Disk as Local Vault Notes

    AO->>SS: replay_sync_event(replay_id, trace_id)
    SS->>OAL: lookup_audit_record(replay_id)
    OAL-->>SS: Logged Event Details (deterministic_hash, note_version)
    
    SS->>VI: load_historical_version(note_id, note_version)
    VI->>Disk: Load file states
    Disk-->>VI: Target version note content
    VI-->>SS: Note data block
    
    SS->>SS: Recalculate hash (Must match deterministic_hash)
    SS-->>AO: Replayed Note Content (Zero Behavioral Drift)
```
