# Obsidian Note Specification - Phase 7F

This document establishes the structural specifications, YAML frontmatter schemas, and markdown conventions for notes stored within the Obsidian vault.

---

## 1. Mandatory Frontmatter Schema

Every note managed by the synchronization layer must contain the following YAML frontmatter header block:

```yaml
---
note_id: "doc_9bc0e5bc_12ab"
note_type: "decision"
version: 1
created_at: "2026-06-24T18:10:00Z"
updated_at: "2026-06-24T18:10:00Z"
trace_id: "893c5c99-0d1a-4d92-a1de-50cbfa192be4"
replay_id: "402e9a5c-5b12-4fe0-be12-9de8e50b7bca"
deterministic_hash: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
originating_agent: "planner_agent"
---
```

* **`note_id`:** Unique document key.
* **`note_type`:** Categorized class of the document.
* **`version`:** Incremental count tracking document changes.
* **`deterministic_hash`:** SHA-256 fingerprint generated from frontmatter parameters and markdown content.

---

## 2. Note Types Definitions

* **Decision Notes (`decision`):** Captures design choices, architectural changes, or algorithm overrides approved by the user.
* **Architecture Notes (`architecture`):** System architecture designs and component relationship specifications (e.g. Phase reports).
* **Lessons Learned (`lesson`):** Records failure patterns or syntax corrections encountered by agents to prevent repeating errors.
* **Execution Reports (`execution`):** Outlines successfully completed task metrics and details.
* **Failure Reports (`failure`):** Tracks loop budget errors, validation alerts, and exceptions.
* **Replay Reports (`replay`):** Records Golden Master certification outputs and determinism comparison tables.

---

## 3. Markdown Note Structure Example (Lessons Learned)

```markdown
---
note_id: "lesson_0012bc"
note_type: "lesson"
version: 1
created_at: "2026-06-24T18:10:00Z"
updated_at: "2026-06-24T18:10:00Z"
trace_id: "893c5c99-0d1a-4d92-a1de-50cbfa192be4"
replay_id: "402e9a5c-5b12-4fe0-be12-9de8e50b7bca"
deterministic_hash: "3a9f8b7c6d5e4f3a..."
originating_agent: "verification_agent"
---

# Lesson: Fix Gauss-Jordan Pivot Healing Exception

## Context
During high-condition matrix calculations, pivot healing checks were bypassed.

## Correction
Ensure that pivot operations verify thresholds before division.
```
