# Architecture Report - Legacy BBC Analysis

This report evaluates the architecture of the legacy BBC codebase (`Legacy_BBC`), analyzing its design patterns, reusable parts, and systemic bottlenecks.

---

## 1. Architectural Design Patterns

The legacy BBC repository operates as a **Monolithic CLI-Driven Guardrail System**. It is structured into three distinct execution layers:

1. **CLI & Daemon Integration Layer:** Initiated by `bbc.py` or `bbc_daemon.py`, it interacts with the file system using native shell adapters (`native_adapter.py`) and editor file event listeners (`ide_hooks.py`).
2. **Context Compilation & Optimization Layer:** Processes files using specialized heuristic schemas called "recipes" (defined in `hmpu_engine.py`) to compress context size.
3. **Riemann Manifold Mathematical Core:** Implements a strict, deterministic, state-propagating algebra (`bbc_scalar.py`, `matrix_ops.py`, `hmpu_core.py`) to check mathematical stability scores.

---

## 2. Reusable Core Modules

The following legacy components are high-quality mathematical and structural implementations that can be ported directly:

* **Matrix Ops (`matrix_ops.py`):** Gauss-Jordan elimination, pseudo-inverse, and condition number calculations. Highly self-contained and easily reusable in any Python 3.x environment.
* **BBC Scalar Type (`bbc_scalar.py`):** Solid class handling state representation (Stable to Degenerate), value quantization, and metadata origin checking.
* **Symbol Extractor (`symbol_extractor.py`):** Uses Python's native AST parser to extract symbols, classes, and function declarations. Extremely fast and lightweight.
* **Telemetry Logger (`telemetry.py`):** Clean JSON-L file writing implementation, enabling easy parsing of events.

---

## 3. Candidate Agent Modules

These legacy components contain complex heuristic rules and decision parameters that should be refactored into autonomous **agent roles** in the new BBC-AOS:

* **`hallucination_guard.py` (Hallucination Guard Agent):** Extracts referenced code symbols and matches them against the sealed context, while checking for speculative vocabulary patterns (e.g., `probably`, `might`, `guess`).
* **`adaptive_mode.py` (Boundary Compliance Agent):** Enforces strict limits and issues `BBCViolation` errors when responses venture outside the context.
* **`auto_patcher.py` (Refactoring & Patching Agent):** Detects problems (like unused imports) and automatically writes and applies code patches.

---

## 4. Systemic Bottlenecks & Design Flaws

During our repository inventory, we identified several critical bottlenecks:

### A. Subprocess & Native Command Spawning
The legacy system regularly spawns system subshells (`subprocess.run`) in `native_adapter.py`, `auto_detector.py`, and `ai_integration.py` to compile code or run diagnostics. This is an **extreme security risk** and blocks execution, leading to performance lags.

### B. Synchronous Matrix Iterations
The matrix calculations in `hmpu_core.py` (Aura field iteration, Gauss-Jordan inverse) run synchronously on the main thread. If massive codebases or high-concurrency RPC requests are processed, this will block the JSON-RPC HTTP server (`http_server.py`) and increase request latency.

### C. Overlapping State Definitions
The state management uses overlapping, duplicated singletons: `state_manager.py` tracks budget, but `telemetry.py` handles event logs, while `realtime_token_counter.py` manages active token states. In a modern Operating System, these must be consolidated into a unified State/Telemetry Daemon.
