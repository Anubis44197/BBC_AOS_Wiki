# Agent Registry Report - Phase 7B

This document details the registry mappings and allowlisted RPC actions registered in the `AgentRegistry` singleton of `bbc_aos`.

---

## 1. Registry Inventory

The following agent classes are successfully registered in the central system lookup registry:

| Agent Identifier (`AGENT_ID`) | Python Target Class | Version | Allowlisted RPC Actions (`SUPPORTED_ACTIONS`) |
| :--- | :--- | :---: | :--- |
| **`planner_agent`** | `PlannerAgent` | 1.0.0 | `create_plan` |
| **`context_agent`** | `ContextAgent` | 1.0.0 | `get_symbol_context`, `get_file_context` |
| **`resolver_agent`** | `ResolverAgent` | 1.0.0 | `resolve_dependencies`, `calculate_blast_radius` |
| **`compression_agent`** | `CompressionAgent` | 1.0.0 | `optimize_context`, `semantic_pack` |
| **`verification_agent`** | `VerificationAgent` | 1.0.0 | `check_hallucinations`, `verify_syntax` |
| **`documentation_agent`** | `DocumentationAgent` | 1.0.0 | `generate_notes` |
| **`execution_agent`** | `ExecutionAgent` | 1.0.0 | `generate_patch`, `apply_patch` |

---

## 2. Dispatch Control Rules

* **Method Allowlist Checks:** Calls targeting unregistered agents or actions outside `SUPPORTED_ACTIONS` will be rejected immediately, returning error code `-32601` (Method Not Found).
* **Direct Call Prohibitions:** All dispatch operations are strictly routed through `AgentOrchestrator.dispatch()`. Agents are prohibited from importing `AgentRegistry` or other agent modules directly to make execution calls.
* **Sandbox Verification:** The orchestrator intercepts all input parameters. If any path parameter falls outside the authorized workspace folder boundary, a `SafetyBreachException` (`-32002`) is thrown before the agent is invoked.
