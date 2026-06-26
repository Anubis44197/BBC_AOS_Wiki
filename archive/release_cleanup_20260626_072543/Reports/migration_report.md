# Migration Report - BBC-AOS

This report outlines the migration strategy for porting the legacy BBC codebase (`Legacy_BBC`) to the new BBC Agent Operating System (BBC-AOS) in accordance with the authoritative specification guidelines.

---

## 1. Migration Strategy Overview

The migration follows a **Clean Isolation & Layered Wrap** strategy. We must maintain the strict separation between the deterministic mathematical core and the non-deterministic agentic modules.

```
┌────────────────────────────────────────────────────────┐
│               Legacy_BBC Repository                    │
└──────────────────────────┬─────────────────────────────┘
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
┌──────────────────────────┐   ┌─────────────────────────┐
│  Deterministic Modules   │   │  Agent Candidate /      │
│  (Direct Port / Reuse)   │   │  Scraper Modules        │
└────────────┬─────────────┘   └─────────┬───────────────┘
             │                           │
             │ (Optimize & Test)         │ (Refactor into Interfaces)
             ▼                           ▼
┌──────────────────────────┐   ┌─────────────────────────┐
│     BBC-AOS Core Engine   │   │   BBC-AOS Agent Loops   │
│     & Guardrail API      │   │   & External Services   │
└──────────────────────────┘   └─────────────────────────┘
```

---

## 2. Reuse & Porting Recommendations

### A. Reusable Deterministic Core Modules
The mathematical calculations and AST extraction mechanisms are highly stable and should be reused with minimal modifications:
1. **`bbc_scalar.py` / `matrix_ops.py` / `hmpu_core.py`:** Keep as the primary deterministic calculation suite. These modules implement state transformations (STABLE to DEGENERATE), Gauss-Jordan inverses, and Condition Number evaluations.
2. **`symbol_extractor.py` / `symbol_graph.py` / `verifier.py`:** Excellent base for AST-based symbol parsing and code syntax checking.
3. **`context_optimizer.py` / `semantic_packer.py`:** Keep for managing token budgets and context chunking.

### B. Modules Requiring Refactoring (Agent Candidates & Adapters)
1. **`hallucination_guard.py` / `adaptive_mode.py`:** Refactor into an autonomous **Safety Agent / Guardrail Agent** module that monitors outputs and injects correction prompts instead of directly terminating sessions.
2. **`auto_patcher.py`:** Rebuild as a specialized **Patch Agent** that receives instructions from the RLM Brain to construct git-style diffs safely.
3. **`agent_adapter.py`:** Convert into a modular registry pattern to easily plug in new IDE/AI formatters without modifying the core file.
4. **`native_adapter.py`:** Needs thorough security sandboxing. Legacy native operations directly invoke subshell commands; in the new OS, these must pass through a strict approval or containerized layer.

---

## 3. Migration Roadmap Steps

### Step 1: Core Porting & Unit Test Baseline
* Extract the deterministic mathematical layers (`BBCScalar`, `MatrixOps`, `HMPU_Governor`) into a clean `bbc_aos.core` library.
* Ensure all legacy mathematical tests (`test_math.py`, `test_verifier.py`) pass on the new core library.

### Step 2: Sandbox Native Adapters
* Replace raw shell calls in `native_adapter.py` and `auto_detector.py` with secure OS execution interfaces.
* Implement user permission hooks and audit logging for all write/run actions.

### Step 3: Implement Agent Adaptations
* Port `adaptive_mode.py` and `hallucination_guard.py` to act as middleware layers in the agent request pipeline.
* Integrate RLM (Reinforcement Learning Manager) rewards and penalty scores into the `state_manager.py` session logger.

### Step 4: UI/CLI & Obsidian Sync
* Port `cli.py` to a clean command router.
* Setup automated JSON-RPC endpoints in `http_server.py` to enable seamless integration with Obsidian vaults as specified in the docs.
