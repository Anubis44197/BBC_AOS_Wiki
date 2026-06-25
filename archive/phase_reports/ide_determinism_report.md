# Phase 12B - IDE Determinism Report

This report documents the verification of E2E determinism inside the IDE workflow loop.

---

## 1. Overview and Goal

To guarantee that the IDE sidecar generates predictable, inspectable, and reproducible outcomes, identical developer requests must yield identical pipeline outputs (hashes, task steps, and verification verdicts).

---

## 2. Determinism Metrics

Determinism was verified by executing each scenario 100 times with identical input parameters and asserting that the resulting output hashes and verdicts matched the baseline run.

### Scenario Outcomes

| Scenario | Runs | Identical Verdicts | Identical Hashes | Determinism Rate |
| :--- | :---: | :---: | :---: | :---: |
| **bugfix** | 100 | 100/100 | 100/100 | **100.0%** |
| **feature** | 100 | 100/100 | 100/100 | **100.0%** |
| **refactor** | 100 | 100/100 | 100/100 | **100.0%** |
| **documentation** | 100 | 100/100 | 100/100 | **100.0%** |

---

## 3. RNG Hashing Mechanism

* **Planner Seeds**: The task planner extracts ASTs and selects tasks based on the hash of the developer's original prompt.
* **Orchestrator Stage Hashing**: The orchestrator verifies that intermediate state outputs from the Context, Coder, and Tester stages remain completely immutable and locked under the designated `trace_id` and `replay_id` hashes.
* **Approval Hashes**: Approval IDs and verification hashes incorporate the developer's prompt structure, ensuring approval gates can be replayed and re-validated cleanly during audits.
