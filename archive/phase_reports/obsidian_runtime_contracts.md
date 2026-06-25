# Obsidian Runtime Contracts - Phase 8B

This document specifies the interface contracts, typing scopes, and schemas for all transactions in the Human Knowledge Layer and Obsidian subsystem.

## 1. Immutable Note Contract (`NoteRecord`)

The `NoteRecord` represents the local-first note metadata and content:

| Field | Type | Description |
| :--- | :--- | :--- |
| `note_id` | `str` | Unique note key identifier. |
| `note_type` | `str` | Category (Decision, Architecture, Lesson, etc.). |
| `version` | `int` | Sequential version index count. |
| `created_at` | `str` | ISO 8601 creation timestamp. |
| `updated_at` | `str` | ISO 8601 update timestamp. |
| `trace_id` | `str` | Request tracing UUID. |
| `replay_id` | `str` | Replay matching UUID. |
| `deterministic_hash` | `str` | Content payload SHA-256 fingerprint. |
| `originating_agent` | `str` | Identifier of agent who proposed or edited the note. |
| `title` | `str` | Human-readable title of the note. |
| `content` | `str` | Raw markdown body text. |
| `state` | `NoteLifecycleState` | Current status (DRAFT, PROPOSED, etc.). |
| `metadata` | `Dict[str, Any]` | JSON dictionary of arbitrary property tags. |

---

## 2. Proposal Artifact Contract (`ProposalArtifact`)

Every change proposed to a note is wrapped in an immutable proposal:

| Field | Type | Description |
| :--- | :--- | :--- |
| `proposal_id` | `str` | Unique proposal key identifier. |
| `trace_id` | `str` | Request tracing UUID. |
| `replay_id` | `str` | Replay matching UUID. |
| `deterministic_hash` | `str` | Proposed content SHA-256 fingerprint. |
| `rationale` | `str` | Explanation justifying the requested edits. |
| `safety_assessment` | `Dict[str, Any]` | Risk and safety metadata. |
| `originating_agent` | `str` | Identifier of agent submitting the proposal. |
| `proposed_note` | `NoteRecord` | Target note record instance containing the changes. |
| `metadata` | `Dict[str, Any]` | Additional tracking metadata. |

---

## 3. Telemetry and Exceptions Mapping

The `ObsidianGateway` maps errors directly to standard JSON-RPC 2.0 error blocks:

* `ObsidianException` (-34000): General execution error.
* `ObsidianFrozenRegistryException` (-34001): Attempt to alter vault configurations after registry freeze.
* `ObsidianNoteLifecycleException` (-34002): Invalid lifecycle transition attempted on notes.
* `ObsidianSyncException` (-34003): Synchronization validation or automatic merge violation.
* `ObsidianSandboxViolationException` (-34004): Unauthorized write or directory boundary breach.
