# Core Extraction Plan - BBC-AOS Deterministic Layer

This plan outlines the detailed analysis and extraction strategy for the deterministic core components of the legacy repository. It details each component's responsibilities, dependencies, deterministic importance, migration difficulty, target BBC-AOS location, and required adapters.

---

## 1. Detailed Component Analysis

### 1. `bbc_scalar.py`
* **Responsibilities:**
  * Defines the `BBCScalar` class representing values with 7 mathematical states (`STABLE`, `WEAK`, `SLEEPING`, `NEG_ZERO`, `SATURATED`, `UNSTABLE`, `DEGENERATE`).
  * Enforces state promotion tables for scalar arithmetic and linear algebra.
  * Tracks value metadata, including security flags (`MATH_CORE_DEGENERATION_ANOMALY`) and origin hints ("math" vs "semantic") to prevent origin spoofing.
  * Implements `OmegaOperator` for pivot healing protocols.
* **Dependencies:** None (Pure Python, standard `json` library).
* **Deterministic Importance:** **Critical (10/10)**. Provides the fundamental data type for all HMPU matrix and vector calculations.
* **Migration Difficulty:** **Low**. The logic is self-contained and mathematical.
* **Target BBC-AOS Location:** [validation_models.py](file:///C:/Users/90535/Desktop/BBC_AOS_Wiki/bbc_aos/models/validation_models.py)
* **Required Adapters:** None.

### 2. `matrix_ops.py`
* **Responsibilities:**
  * Implements deterministic linear algebra algorithms operating directly on `BBCScalar` types.
  * Gauss-Jordan elimination with partial pivoting and self-healing hooks.
  * Infinity-norm condition number estimator ($\kappa(A) = \|A\|_{\infty} \cdot \|A^{-1}\|_{\infty}$).
  * Simplified pseudo-inverse solver ($A^+ = (A^T A)^{-1} A^T$).
* **Dependencies:** `bbc_scalar.py`.
* **Deterministic Importance:** **Critical (10/10)**. Solves matrix operations and quantifies stability scores.
* **Migration Difficulty:** **Low**. Mathematical methods with no external package bindings (e.g. no NumPy).
* **Target BBC-AOS Location:** [constraints_engine.py](file:///C:/Users/90535/Desktop/BBC_AOS_Wiki/bbc_aos/core/constraints_engine.py) (internal utility functions).
* **Required Adapters:** None.

### 3. `hmpu_core.py`
* **Responsibilities:**
  * Implements the `HMPU_Governor` class controlling mathematical state iterations.
  * Stores the static `_Aura_Base` matrix and manages the dynamic `_Aura_Weights` matrix.
  * Implements the 4 HMPU Operators:
    * **OP-01 ($dC/dt$):** Chaos derivative noise filter using Shannon entropy over signals.
    * **OP-02 ($\nabla A$):** Aura gradient adaptation hyper-plane bending.
    * **OP-03 ($P_{t+1}$):** Pulse stability perturbation simulator.
    * **OP-04 ($F_{\perp}$):** Orthogonal focus projection (square-root-free vector comparison).
  * Executes the Self-Heal Protocol (Omega trigger) to recover degraded pivot elements.
* **Dependencies:** `bbc_scalar.py`, `matrix_ops.py`, `state_manager.py`.
* **Deterministic Importance:** **Critical (10/10)**. The central gatekeeper validating execution stability.
* **Migration Difficulty:** **Medium**. Requires decoupling from the legacy singleton `StateManager` class and integrating with the new execution context.
* **Target BBC-AOS Location:** [constraints_engine.py](file:///C:/Users/90535/Desktop/BBC_AOS_Wiki/bbc_aos/core/constraints_engine.py) (main Governor class and mathematical operators).
* **Required Adapters:** Requires configuration adapters to load state limits from `core/execution_context.py`.

### 4. `hmpu_engine.py`
* **Responsibilities:**
  * Manages base validation recipes (e.g., `CodeStructureRecipe`, `LogTelemetryRecipe`, `ConfigJsonRecipe`, `DocumentationRecipe`).
  * Enforces the BBC Constraint Constitution via the Constraint Violation Protocol (CVP).
  * Coordinates multi-recipe analysis pipelines (segment-based parsing).
  * Measures context size reduction and token savings ratios.
* **Dependencies:** `state_manager.py`, `hmpu_core.py`.
* **Deterministic Importance:** **High (8/10)**. Orchestrates the flow of validation recipes.
* **Migration Difficulty:** **Medium**. Needs decoupling from legacy IDE/terminal adapters.
* **Target BBC-AOS Location:** [orchestrator.py](file:///C:/Users/90535/Desktop/BBC_AOS_Wiki/bbc_aos/core/orchestrator.py)
* **Required Adapters:** Needs adapters to convert raw pipeline data to/from the validation structure.

### 5. `symbol_extractor.py`
* **Responsibilities:**
  * Walks source code files to build ASTs (Abstract Syntax Trees) for Python.
  * Uses regex-based pattern matching for polyglot files (JS, TS, C++, Java, etc.).
  * Extracts class names, function signatures, methods, imports, decorators, and docstrings.
  * Honors scan profiles and skip filters.
* **Dependencies:** Standard library (`ast`, `re`).
* **Deterministic Importance:** **High (8/10)**. Builds the symbol knowledge base of the codebase.
* **Migration Difficulty:** **Low**. The extraction logic is purely deterministic and self-contained.
* **Target BBC-AOS Location:** [repository_scanner.py](file:///C:/Users/90535/Desktop/BBC_AOS_Wiki/bbc_aos/tools/repository_scanner.py)
* **Required Adapters:** None.

### 6. `symbol_graph.py`
* **Responsibilities:**
  * Constructs and manages the dependency call graph of the project's codebase.
  * Resolves references and handles aliases/imports dynamically.
  * Identifies recursive, internal, external, and unknown calls.
  * Computes symbol metrics (e.g. churn, call counts).
* **Dependencies:** Standard library (`ast`, `json`).
* **Deterministic Importance:** **High (8/10)**. Traces file-to-file and symbol-to-symbol relationships.
* **Migration Difficulty:** **Low**.
* **Target BBC-AOS Location:** [graph_tools.py](file:///C:/Users/90535/Desktop/BBC_AOS_Wiki/bbc_aos/tools/graph_tools.py)
* **Required Adapters:** Requires JSON serializers to save graphs to disk.

### 7. `context_optimizer.py`
* **Responsibilities:**
  * Analyzes the symbol graph to calculate the blast radius of proposed changes.
  * Grades symbols into importance tiers (`PRIMARY`, `DIRECT`, `INDIRECT`, `DISTANT`, `IGNORE`).
  * Resolves ambiguous or short symbol names to their fully qualified targets.
  * Formulates deterministic context reduction decisions.
* **Dependencies:** Standard library.
* **Deterministic Importance:** **High (8/10)**. Essential for trimming prompt sizes without losing critical symbols.
* **Migration Difficulty:** **Low**.
* **Target BBC-AOS Location:** [context_reducer.py](file:///C:/Users/90535/Desktop/BBC_AOS_Wiki/bbc_aos/core/context_reducer.py)
* **Required Adapters:** None.

### 8. `context_compiler.py`
* **Responsibilities:**
  * Compiles customized context payloads based on task profiles (`bugfix`, `feature`, `refactor`, `review`).
  * Structures context JSON layouts.
  * Optimizes token limits and budget allocation rules.
* **Dependencies:** Standard library, `config.py`.
* **Deterministic Importance:** **High (8/10)**. Guarantees consistent inputs for LLMs.
* **Migration Difficulty:** **Low**.
* **Target BBC-AOS Location:** [context_builder.py](file:///C:/Users/90535/Desktop/BBC_AOS_Wiki/bbc_aos/core/context_builder.py)
* **Required Adapters:** Config adapters to read token limit variables.

### 9. `semantic_packer.py`
* **Responsibilities:**
  * Applies loss-less compression stages to compiled contexts (e.g., removing empty lists, deduplicating shared imports, path aliasing).
  * Collapses low-value files into summary lines.
  * Strips LLM-irrelevant metadata (e.g. hash strings).
* **Dependencies:** Standard library.
* **Deterministic Importance:** **Medium (7/10)**. Optimizes the physical token size.
* **Migration Difficulty:** **Low**.
* **Target BBC-AOS Location:** [memory_tools.py](file:///C:/Users/90535/Desktop/BBC_AOS_Wiki/bbc_aos/tools/memory_tools.py)
* **Required Adapters:** None.

### 10. `hmpu_indexer.py`
* **Responsibilities:**
  * Computes 128-bit SimHash values for text segments using SHA-256.
  * Implements Hamming distance and percentage similarity scoring.
  * Implements `compute_bbc_simhash` utilizing the Aura vector to scale keyword weights and evaluate validation states.
  * Executes hybrid memory search (60% SimHash structural similarity + 40% keyword density).
  * Handles index saving and loading from disk.
* **Dependencies:** `bbc_scalar.py`.
* **Deterministic Importance:** **High (8/10)**. Acts as the vector database for storing and querying context segments.
* **Migration Difficulty:** **Medium**. Needs separation of path parameters.
* **Target BBC-AOS Location:** [knowledge_store.py](file:///C:/Users/90535/Desktop/BBC_AOS_Wiki/bbc_aos/core/knowledge_store.py)
* **Required Adapters:** Serialization adapters to handle large binary integers.

### 11. `attribution_tracer.py`
* **Responsibilities:**
  * Extracts code definitions and tracks references across the project.
  * Traces faulty modifications back to files to define the "blast radius" of code errors.
  * Implements a polyglot reference scanner.
* **Dependencies:** Standard library.
* **Deterministic Importance:** **Medium (6/10)**. Traces blame and dependencies for debugging.
* **Migration Difficulty:** **Low**.
* **Target BBC-AOS Location:** [tracing.py](file:///C:/Users/90535/Desktop/BBC_AOS_Wiki/bbc_aos/observability/tracing.py)
* **Required Adapters:** None.

### 12. `state_manager.py`
* **Responsibilities:**
  * Manages global and session healing budgets.
  * Records critical `DEGENERATE` state mutations.
  * Measures token savings, processed data bytes, and files analyzed.
  * Dispatches telemetry logs.
* **Dependencies:** Telemetry and logging modules.
* **Deterministic Importance:** **High (9/10)**. Controls execution budget and acts as the system-wide watchdog.
* **Migration Difficulty:** **Medium**. Conversion from singleton to state management daemon.
* **Target BBC-AOS Location:** [execution_context.py](file:///C:/Users/90535/Desktop/BBC_AOS_Wiki/bbc_aos/core/execution_context.py)
* **Required Adapters:** Needs JSON storage adapters to snapshot sessions under `/state/sessions/`.
