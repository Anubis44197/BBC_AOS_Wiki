# Agent Memory Contracts - Phase 7A

This document defines memory visibility limits, state transaction protocols, and isolation boundaries for agents operating in `bbc_aos`.

---

## 1. Stateless Agent Isolation

To guarantee execution determinism and prevent race conditions, all agents must operate under a strict **stateless execution model**:
* **No Local State:** Agents are prohibited from maintaining instance-level variables, class-level caches, or global state containers.
* **No File writes:** Agents must not write temporary files or logs directly to disk. All logs and results must be returned to the Orchestrator via JSON-RPC payloads.
* **Functional Purity:** Given the same JSON-RPC parameters, an agent must produce the exact same output. Execution must be side-effect free.

---

## 2. Session Context Visibility Rules

Agents do not have raw query access to the global repository context or database indexes. Instead, they operate under strict context scopes delegated by the orchestrator:

```
[Agent Scope] ──(Restricted Parameter Context)──> [Orchestrator Scope] ──(Pluggable Database)──> [Persisted Storage]
```

### Visibility Levels by Role

1. **PlannerAgent:**
   * *Visibility Scope:* Limited to the task description string, project manifest summary, and configuration style guidelines. No code files.
2. **ContextAgent:**
   * *Visibility Scope:* Query-scoped access to specific file paths or symbol names returned by graph builders. No visibility into unqueried modules.
3. **ResolverAgent:**
   * *Visibility Scope:* Symbol dependency graph nodes and edges. No access to the raw file code contents.
4. **CompressionAgent:**
   * *Visibility Scope:* Raw context payload string. Access is isolated to the token optimization step.
5. **VerificationAgent:**
   * *Visibility Scope:* Target file AST, proposed patch, and known symbol lookup index.
6. **DocumentationAgent:**
   * *Visibility Scope:* Completed transaction diff and target Obsidian catalog paths.
7. **ExecutionAgent:**
   * *Visibility Scope:* Specific target python file to patch, target patch diff, and Git checkout context.

---

## 3. State Transaction Protocol

Shared mutable state is strictly forbidden. Any change to the system state (e.g. updating stats, modifying code, saving context indexes) must follow a structured **Three-Phase Commit Transaction Protocol** coordinated by the Orchestrator and `StateManager`:

```
Orchestrator                    StateManager                  FileStateStorage
    │                                │                                │
    ├────── 1. Propose state ───────>│                                │
    │                                ├──── 2. Verify bounds & budget ─>│
    │                                │     (Is budget exceeded?)      │
    │<───── 3. Commit Approved ──────┤                                │
    │                                ├───────── 4. Persist ──────────>│
```

1. **Proposal Phase:** The agent proposes a state update (e.g., `increment_files_analyzed`) in its RPC response payload to the Orchestrator.
2. **Verification Phase:** The Orchestrator intercepts the payload, extracts state updates, and forwards them to the `StateManager` to check bounds (e.g., verifying remaining heal budget limits).
3. **Commit Phase:** If verified, the `StateManager` commits the update via `StateStorageInterface` to the persistent transaction storage, updating the session metadata on disk.
