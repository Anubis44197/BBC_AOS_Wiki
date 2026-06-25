# Obsidian Validation Strategy - Phase 7F

This document establishes the validation checks, testing methodologies, and verification plans designed to secure the human-in-the-loop Obsidian integration.

---

## 1. Testing Tiers

Verification is organized into four distinct testing tiers:

```
[Markdown & YAML Parsing] ──> [Proposal Verification] ──> [Merge Sandbox Audits] ──> [Deterministic Replay Checks]
```

1. **Markdown & YAML Parsing:** Validates that frontmatter headers comply with schema properties (`note_id`, `version`, `deterministic_hash`, etc.) and parse correctly under various newline formats.
2. **Proposal Verification:** Assures that `ProposalArtifact` instances correctly capture recommended changes and contain valid `safety_assessment` signatures before displaying to the human operator.
3. **Merge Sandbox Audits:** Simulates sync commands and checks that the system does not execute write actions to original user notes unless explicit human approval is simulated.
4. **Deterministic Replay Checks:** Replays historical synchronizations from `obsidian_audit.jsonl` logs, verifying that recalculating note hashes yields identical values byte-for-byte.

---

## 2. Telemetry and Safety Validation Checks

The `SyncSupervisor` executes the following validation rules during every integration run:

* **Uniqueness Auditing:** Verifies that no two notes in the vault share the same `note_id`.
* **Version Monotonicity Check:** Validates that proposed note version updates increase by exactly 1 (`note_version = parent_version + 1`).
* **Format Preservation Check:** Verifies that proposals do not corrupt markdown syntax or strip non-YAML text blocks.
* **Deterministic Replay Verification:** To verify sync integrity, the replay runner loads historical note states and asserts that subsequent actions produce identical transition states.
