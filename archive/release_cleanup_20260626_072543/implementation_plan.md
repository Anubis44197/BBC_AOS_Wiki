# Implementation Plan - Phase 11B ContextAgent Real Implementation

This plan outlines the production implementation of the `ContextAgent` under `bbc_aos/agents/context_agent.py`. The agent is responsible for resolving task-focused context for AI coding systems deterministically, interacting exclusively through standard core packages and the memory subsystem.

---

## Proposed Changes

### 1. [MODIFY] [context_agent.py](file:///C:/Users/90535/.gemini/antigravity/scratch/BBC_AOS_Wiki/bbc_aos/agents/context_agent.py)

We will modify the agent class to implement:
* **Lifecycle Hooks:** Standard base class lifecycle methods (`initialize()`, `validate_input()`, `execute()`, `validate_output()`, `finalize()`).
* **Memory Subsystem Queries:** Retrieve the symbol graph and full context from the `semantic` memory layer via `MemoryManager`.
* **Context Reduction & Optimization:** Run `ContextOptimizer` to resolve symbol blast radius and prioritize dependencies.
* **Context Compilation:** Run `TaskContextCompiler` to subset files based on task profiles ('bugfix', 'feature', 'refactor', 'review').
* **Context Packing:** Run `SemanticPacker` to apply lossless compression on the compiled dictionary.
* **Strict Constraints:**
  * Maximum selected files capped at 50.
  * Maximum dependency depth capped at 5.
  * No direct filesystem or Obsidian API access.
  * No direct communication with other agents.
  * Deterministic hashing of output payload.
  * Self-validation via `ValidationGateway` and appending of dispatches to `IntegrationAuditLog`.
  * Fully PEP 484 typed and documented under Google docstring conventions.

### 2. [NEW] [validate_phase11b.py](file:///C:/Users/90535/.gemini/antigravity/scratch/BBC_AOS_Wiki/scratch/validate_phase11b.py)

We will create a verification test suite programmatically asserting:
* **Syntax and Imports:** Correct classes are imported, and execution functions match expected schemas.
* **Deterministic Replay:** Running the agent 100 times with identical input parameters yields 100% matching outputs and deterministic hashes.
* **Complexity Limits:** Selected files count $\le 50$, task/file dependency depth $\le 5$.
* **Audit Event Generation:** Verification that agent execution appends correct trace details to `IntegrationAuditLog`.
* **Packing Equivalence:** Asserting that packed outputs align with standard compiler/packer metrics.

### 3. [NEW] Reports

We will generate the following reports under the `Reports/` directory:
1. **`context_agent_implementation_report.md`**: Overall details of the ContextAgent implementation and its interaction flows.
2. **`context_agent_validation_report.md`**: Programmatic verification logs and test execution results.
3. **`context_agent_determinism_report.md`**: Determinism metrics and zero-variance test verification.
4. **`context_agent_api_contract_report.md`**: Input parameter and output result schema contract specifications.

---

## Global Impact Analysis (GEA)

* **Kapsam (Scope):** Modifies `bbc_aos/agents/context_agent.py`, creates `scratch/validate_phase11b.py`, and generates 4 reports in `Reports/`.
* **Bağımlılıklar (Dependencies):** Connects to `ContextOptimizer`, `ContextCompiler`, `SemanticPacker`, and `MemoryManager`. No other subsystems are affected.
* **Risk:** Extremely low. The agent is read-only, executes deterministically, and implements strict sandbox checks.

---

## Verification Plan

We will programmatically execute the validation suite:
```powershell
python scratch/validate_phase11b.py
```
And verify that all tests pass without errors or regressions. We will also run the final system-wide certification suite:
```powershell
python scratch/run_final_certification.py
```

---

## Open Questions

No open questions. All requirements are fully specified.

Please approve this plan to begin execution.
