# Repository Structure Report - BBC-AOS Skeleton Setup

This report outlines the implementation details of the BBC Agent Operating System (BBC-AOS) repository skeleton, created in strict accordance with `07_BBC-AOS Directory Structure Specification.docx`.

---

## 1. Directory Structure Overview & Core Concept

The BBC-AOS repository structure is designed to enforce a **deterministic, modular architecture** that decouples the system authority layer from worker agents and human-readable documentation. It enforces the following hierarchy:

* **System Authority Layer (`core/`, `knowledge/`):** Contains the authoritative decision engines, constraints, and validation protocols. Only this layer is permitted to approve execution or write outputs.
* **Worker Agent Swarm (`agents/`):** Contains non-authoritative worker agents (e.g. planner, coder, tester) that execute tasks but cannot bypass validation.
* **Execution & Lifecycle Management (`loop/`):** Orchestrates agent lifecycles, recovery checkpoints, and state replays.
* **Cognitive State & Memory (`memory/`, `state/`, `cache/`):** Persists episodic, semantic, and procedural agent memory, and holds temporary runtime session states.
* **Human-Facing Wiki & Obsidian Integration (`wiki/`, `vault/`):** Provides sync utilities to export logs, lessons, and conceptual documents to a non-authoritative human-facing Obsidian vault.

---

## 2. Directory Mapping & Purpose

| Directory | Type | Purpose | Key Initial Placeholders |
|---|---|---|---|
| `core/` | System Authority | Enforces constraints, builds and reduces context, manages validation rules. | `resolver.py`, `validator.py`, `orchestrator.py`, `constraints_engine.py` |
| `agents/` | Swarm Workers | Defines roles and logic for worker agents. | `base_agent.py`, `planner_agent.py`, `coder_agent.py`, `wiki_agent.py` |
| `knowledge/` | Authority Data | Stores machine-authoritative metadata, graphs, and ontologies. | `recipe/`, `ontology/`, `graph/`, `constraints/` |
| `memory/` | Cognitive Memory | Stores persistent episodic logs, reflections, and semantic vectors. | `working/`, `semantic/`, `episodic/`, `procedural/` |
| `loop/` | State Machine | Manages engine loops, checkpoint retries, and failure recovery. | `loop_engine.py`, `state_machine.py`, `checkpoint_manager.py` |
| `wiki/` | Wiki Compiler | Builds backlinks, concepts, and handles syncing to Obsidian vaults. | `compiler.py`, `obsidian_sync.py`, `backlink_builder.py` |
| `vault/` | Documentation Vault | Persistent human-readable index files and reports (Non-Authoritative). | `entities/`, `concepts/`, `lessons_learned/`, `index.md` |
| `api/` | Interfaces | Houses external endpoints (REST, stdio-MCP, Websockets, gRPC). | `rest/server.py`, `mcp/stdio_wrapper.py` |
| `adapters/` | Bridges | IDE plugins and model adapters. | `vscode/`, `cursor/`, `copilot/`, `gemini/`, `claude/` |
| `models/` | Domain Models | System-wide schema declarations. | `execution_plan.py`, `agent_result.py`, `memory_models.py` |
| `schemas/` | Serialization | JSON schemas and Pydantic validation files. | `api/`, `memory/`, `validation/`, `loop/` |
| `tools/` | Utilities | Helper modules (token counters, repository scanners). | `token_counter.py`, `repository_scanner.py` |
| `security/` | Policy & Guards | Houses permission controls and hallucination detectors. | `guardrails.py`, `hallucination_detector.py`, `policy_engine.py` |
| `observability/` | Monitoring | Collects live traces, performance reports, and diagnostic statistics. | `metrics.py`, `tracing.py` |

---

## 3. Legacy Migration Code Mapping

To guide the upcoming migration phase, we map the legacy `Legacy_BBC` files to their new target locations in the BBC-AOS skeleton:

| Legacy Module | Target Destination | Refactoring Strategy |
|---|---|---|
| `bbc_core/bbc_scalar.py` | `bbc_aos/models/validation_models.py` | Port as standard value classes. |
| `bbc_core/matrix_ops.py` | `bbc_aos/core/constraints_engine.py` | Encapsulate as private mathematical solvers. |
| `bbc_core/hmpu_core.py` | `bbc_aos/core/constraints_engine.py` | Refactor the HMPU Governor into a deterministic constraints auditor. |
| `bbc_core/hmpu_engine.py` | `bbc_aos/core/orchestrator.py` | Port recipe selectors and dynamic constraint calibrators here. |
| `bbc_core/verifier.py` | `bbc_aos/core/validator.py` | Rebuild syntax checkers and symbol mismatch checks as the main validation gate. |
| `bbc_core/hallucination_guard.py` | `bbc_aos/security/hallucination_detector.py` | Enforce check loops in the security guardrails. |
| `bbc_core/adaptive_mode.py` | `bbc_aos/security/policy_engine.py` | Migrate Strict/Relaxed mode checks here. |
| `bbc_core/auto_patcher.py` | `bbc_aos/agents/coder_agent.py` | Expose file-fixing as a worker tool for the coder agent. |
| `bbc_core/state_manager.py` | `bbc_aos/core/execution_context.py` | Enforce singleton budgets inside the authoritative context. |
| `bbc_core/telemetry.py` | `bbc_aos/telemetry/` | Write events into structured metrics under the telemetry package. |
| `bbc_core/http_server.py` | `bbc_aos/api/rest/server.py` | Wrap as the external server interface. |
| `bbc_core/agent_adapter.py` | `bbc_aos/adapters/` | Modularize into specific subdirectory adapters (e.g. `adapters/cursor/`). |
| `bbc_core/symbol_graph.py` | `bbc_aos/knowledge/graph/` | Write static symbol representations to JSON within the knowledge layer. |

---

## 4. System Architectural Laws (Directory Law compliance)
* **AR-1 (Core is Authoritative):** No worker agent is allowed to write changes directly to the target environment without `core/validator.py` approval.
* **AR-2 (Agents are Workers):** `agents/` modules do not hold validation state or execute raw commands.
* **AR-3 (Vault is Non-Authoritative):** Human edits to files under `vault/` are treated as documentation only and never loaded as runtime configurations.
* **AR-5 (Runtime State Isolation):** All active checkpoints, sessions, and snapshots must live under `state/`. Nothing is cached or stored in-memory outside these namespaces.
