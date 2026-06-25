# BBC Wiki Integration Guide

The BBC Wiki acts as a human-readable, Obsidian-compatible local markdown documentation store. It maps the internal runtime state of BBC-AOS onto standard, well-structured documentation notes for developers.

## 1. Directory Structure

Running `bbc wiki init` sets up the following folder structure inside the root directory of the project:

```
BBC_Wiki/
├── README.md
├── Decisions/          # Architecture decision logs (ADRs)
├── Architecture/       # Subsystem dependency blueprints and schemas
├── Executions/         # Task proposal notes that have been successfully approved and committed
├── Failures/           # Details on execution failures, error codes, and audit rollbacks
├── Replays/            # Replay transaction mappings and verification logs
├── Approvals/          # Pending note proposals (awaiting manual developer approval)
│   └── rejected/       # Note proposals that were rejected during review
└── Lessons_Learned/    # Optimization strategies and post-mortem guidelines
```

---

## 2. Note Structure and Frontmatter

Every wiki note has a standard YAML frontmatter block that defines metadata:

```markdown
---
id: prop_rp_1720000000
title: Proposal for task: Add JWT Authentication
type: Execution
status: PROPOSED
trace_id: tr_1720000000
replay_id: rp_1720000000
commit_hash: a1b2c3d4e5f6...
risk_level: MEDIUM
verdict: APPROVED
created_at: 2026-06-25T11:30:00Z
---

# Proposal: Add JWT Authentication
...
```

### Note States
1. **PROPOSED**: The note proposal is awaiting developer verification in `BBC_Wiki/Approvals/`.
2. **APPROVED**: The note has been promoted to its final category folder (e.g. `Executions/`) and loaded into semantic memory.
3. **REJECTED**: The note proposal has been moved to the `Approvals/rejected/` subfolder.

---

## 3. Review & Promotion Workflow

1. **Automatic Proposal**: Upon successful E2E task execution (`bbc ask "..."`), a proposal note is generated under `BBC_Wiki/Approvals/prop_<replay_id>.md`.
2. **List Pending**: Check pending proposals using:
   ```bash
   bbc wiki pending
   ```
3. **Approve Note**:
   ```bash
   bbc wiki approve prop_<replay_id>.md
   ```
   This updates the note status to `APPROVED`, moves it to `Executions/` (or another folder based on type), and registers the note into semantic memory.
4. **Reject Note**:
   ```bash
   bbc wiki reject prop_<replay_id>.md
   ```
   This updates the status to `REJECTED` and moves the file to `Approvals/rejected/`.
