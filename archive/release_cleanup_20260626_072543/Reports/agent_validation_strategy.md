# Agent Validation Strategy - Phase 7A

This document establishes the testing protocols, verification steps, and observability requirements for validating the `bbc_aos` Agent Layer.

---

## 1. Multi-Tiered Validation Strategy

To certify the Agent Layer, we execute validation across three distinct testing tiers:

```
[Tier 1: Unit & Schema] ──> [Tier 2: E2E Contract Replays] ──> [Tier 3: Observability Audits]
```

### Tier 1: Unit & Schema Validation
* **Schema Conformity:** Every JSON-RPC request and response must be verified against its corresponding agent JSON schema before execution.
* **Method Allowlist Checks:** Verify that callers cannot invoke methods outside the allowlist.
* **Unit Tests:** Direct mock tests checking that agents (e.g. `ContextAgent`, `ResolverAgent`) return correct JSON outputs when provided with mock inputs.

### Tier 2: E2E Contract Replays
* **Golden Master Replays:** Run simulated agent workflow chains on standard ODA-MATH, Wikipedia, Django, and Polyglot datasets.
* **Trace Parity:** Confirm that the sequence of generated sub-tasks and trace IDs match legacy execution graphs.
* **Determinism Testing:** Run the orchestrator-to-agent pipeline 100 times sequentially and assert that intermediate state records and final outputs are identical.

### Tier 3: Observability Audits
* **Telemetry Verification:** Verify that all transaction logs, state updates, warning logs, and execution times are successfully appended to `telemetry.jsonl`.
* **State Recovery Verification:** Force execution interrupts between agent steps, restore state from state files, and verify that the transaction successfully resumes.

---

## 2. Observability & Tracing Metrics

To monitor Agent Layer performance and security status, the following metrics must be tracked in the `StateManager` and written to telemetry:

* **Agent Execution Latency:** Time elapsed between dispatching a request and receiving a response.
* **Token Reduction Ratio:** $\text{Reduction} = 1 - \frac{\text{Packed Prompt Tokens}}{\text{Raw Prompt Tokens}}$
* **Hallucination Detection Rate:** Ratio of proposed patches flagged as containing untrusted symbols.
* **Heal Budget Degradation:** Counter of remaining scalar heal attempts.
* **Escalation Frequency:** Count of safety violations and retry exhaustions.

---

## 3. Implementation Verification Steps

Before declaring the Agent Layer fully operational, the following criteria must be satisfied:
1. All JSON-RPC schemas compile without errors.
2. The allowlist validation layer is configured as a decorator on the Orchestrator routing methods.
3. The `validate_agents.py` suite passes all integration checks with 100% success.
4. The final certification verdict returns: `AGENT_LAYER_CERTIFIED`.
