# Obsidian Runtime Report - Phase 8B

This report details the package layout, component structures, and synchronization safety constraints implemented in the `bbc_aos` Human Knowledge Layer runtime skeletons.

## 1. Directory Structure Layout

The skeleton framework is implemented under the [`bbc_aos/knowledge/human/`](file:///C:/Users/90535/Desktop/BBC_AOS_Wiki/bbc_aos/knowledge/human/) package directory:

```
bbc_aos/knowledge/human/
├── __init__.py                # Package exports for all Obsidian components
├── obsidian_exceptions.py     # Custom RPC-compatible exceptions
├── obsidian_registry.py       # Thread-safe vault scope registry with freeze lock
├── note_record.py             # Immutable NoteRecord structure and state enum
├── proposal_artifact.py       # Immutable change proposal artifact
├── sync_policy.py             # Synchronization policies and modes
├── sync_result.py             # Structured synchronization execution outputs
├── vault_indexer.py           # Local-first vault directory scanner
├── note_parser.py             # Markdown and YAML frontmatter serialization parser
├── sync_planner.py            # Local-to-remote change plan generator
├── promotion_reviewer.py      # Promotion gates with human approval callbacks
├── obsidian_audit_log.py      # Append-only transaction audit logger
├── sync_supervisor.py         # Validation, approval enforcement, merge check, replay history
└── obsidian_gateway.py        # Sole orchestrator gateway with hooks
```

---

## 2. Note Lifecycle and Immutable Structures

* **Frozen Dataclass:** `NoteRecord` is defined using Python's `@dataclass(frozen=True)`. Attempting to modify properties after creation raises an `AttributeError`.
* **State Machine States:** The note transitions deterministically between the following states:
  * `DRAFT`
  * `PROPOSED`
  * `REVIEW_PENDING`
  * `APPROVED`
  * `REJECTED`
  * `ARCHIVED`
* **Proposal Serialization:** Changes to local notes generate a `ProposalArtifact` containing proposal metadata, trace and replay identifiers, a deterministic hash, rationale, safety assessments, and the originating agent's identifier.

---

## 3. Supervised Synchronization and Merge Safeguards

* **Sync Modes:** Validated through `SyncPolicy` settings:
  * `pull-only`
  * `proposal-based push`
  * `approval-required merge`
* **Zero Automatic Merges:** Per strict constraints, automatic merges are entirely forbidden. Any merge requires manual human intervention and approval.
* **Supervisor Responsibilities:** The `SyncSupervisor` enforces:
  * Proposal structural validation.
  * Human approval verification.
  * Prohibition of automatic merges.
  * Generation of append-only audit records.
  * Playback/replay history queries.
