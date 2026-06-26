# Subsystem Dependency Matrix - Phase 9A

This document specifies the dependency matrix, health status check contracts, and startup/shutdown/recovery sequences.

## 1. Subsystem Dependency Rules

To prevent dependency cycles and maintain a strict hierarchy, subsystems are restricted to the following directed dependencies:

| Subsystem | Allowed Direct Dependencies | Forbidden Dependencies |
| :--- | :--- | :--- |
| **Agent Runtime** | None (Orchestrator acts as Broker) | Memory Runtime, Obsidian Runtime, Loop Runtime, Core |
| **Loop Runtime** | Deterministic Core | Agent Runtime, Memory Runtime, Obsidian Runtime |
| **Memory Runtime** | None | Agent Runtime, Loop Runtime, Obsidian Runtime |
| **Obsidian Runtime** | None | Memory Runtime, Agent Runtime, Loop Runtime |
| **Deterministic Core** | None | All Subsystems (Pure mathematical layer) |
| **Agent Orchestrator**| All Subsystems (Central broker) | None |

---

## 2. Health Status Contracts

Every subsystem must expose a standard health check method returning a JSON payload.

### Schema:
```json
{
  "subsystem": "string",
  "status": "OK | DEGRADED | UNHEALTHY",
  "is_frozen": "boolean",
  "active_contexts": "integer",
  "last_audit_hash": "string",
  "timestamp": "string"
}
```

* **Deterministic Core health:** Always OK, stateless. Exposes whether weights are loaded.
* **Agent Runtime health:** Exposes number of registered agents and active dispatches.
* **Loop Runtime health:** Exposes active loop engine contexts and active budgets.
* **Memory Runtime health:** Exposes registry freeze state, append-only logs size, and last audit record hash.
* **Obsidian Runtime health:** Exposes vault indexing status, pending proposals count, and audit log tail.

---

## 3. System Lifecycle Sequences

### A. Startup Sequence
1. **Bootstrap Config:** Load central configurations (`BBCConfig`).
2. **Initialize Core:** Initialize `ConstraintsEngine` and verify weights.
3. **Initialize Memory:** Instantiate `MemoryRegistry` -> Register layers -> Call `MemoryRegistry.freeze()`.
4. **Initialize Obsidian:** Instantiate `ObsidianRegistry` -> Register vault scopes -> Call `ObsidianRegistry.freeze()`.
5. **Initialize Loops:** Instantiate `LoopRegistry` -> Register loop runtimes -> Call `LoopRegistry.freeze()`.
6. **Initialize Agents:** Instantiate `AgentRegistry` -> Register agents -> Call `AgentRegistry.freeze()`.
7. **Instantiate Orchestrator:** Load `AgentOrchestrator` wrapping all frozen registries and gateways.
8. **Health Check:** Perform E2E health sweep.

### B. Shutdown Sequence
1. **Halt Despatches:** Broker rejects new incoming user requests.
2. **Drain Loops:** Wait for running iterations to terminate or cancel active loops. Save checkpoints.
3. **Commit Memory:** Force write flush of memory buffers to append-only files.
4. **Log Shutdown Events:** Write final immutable audit events.
5. **Freeze State:** Write final state persistence JSON records.
6. **De-allocate:** Clear memory registry instances.

### C. Recovery Sequence
1. **Read Crash Checkpoint:** Retrieve the latest checkpoint record matching `trace_id` / `replay_id` from Episodic Memory.
2. **Verify State Integrity:** Compute the deterministic hash of the checkpoint to verify no tampering.
3. **Re-initialize registries:** Initialize all runtime skeletons to frozen state.
4. **Re-hydrate Loop Context:** Call `LoopEngine.resume_from_checkpoint()`.
5. **Notify Orchestrator:** Complete recovery sweep and resume loop iterations.
