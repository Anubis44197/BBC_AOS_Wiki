# Engine Dependency Matrix

**Date:** 2026-06-24  
**Status:** Planning & Draft  

This document details the public API surface, internal package imports, and hidden external system dependencies of `hmpu_core.py` and `hmpu_engine.py`.

---

## 1. Public API Surface

### A. Core Governor (`hmpu_core.py` / `constraints_engine.py`)
* `__init__(self, weights_path: str = None, state_manager=None, heal_budget: int = 5, session_heal_budget: int = 5)`: Initializes base and gradient matrices and binds StateManager.
* `get_field_stability(self) -> float`: Calculates the condition number of combined base + gradient weight matrices.
* `chaos_derivative_filter(self, stream: List[str], threshold: float = 0.4) -> List[str]`: Filters stream segments based on chaos derivative thresholds.
* `aura_field_score(self, s: float, c: float, p: float) -> float`: Performs vector-matrix multiplication iterations to calculate convergence scores. Raises `RuntimeError` on DEGENERATE state detection.
* `self_heal_protocol(self) -> int`: Performs weight recovery operations using the Omega Trigger, enforcing budget constraints.
* `aura_gradient_bend(self, delta: float, stability: bool) -> None`: Dynamically adapts weights based on validation feedback delta.
* `pulse_perturbation_sim(self, current_aura: float, intent_magnitude: float, op_type: str) -> Dict[str, Any]`: Predicts potential chaotic collapses prior to compilation.
* `focus_projection(self, query_vec: List[float], target_vecs: List[Dict[str, Any]]) -> List[str]`: Projects vectors and filters orthogonal noise.

### B. Engine Orchestrator (`hmpu_engine.py` / `orchestrator.py`)
* `__init__(self, state_manager: StateManager)`: Registers recipes, loads the governor, and sets up pipelines.
* `get_aura_confidence(self) -> float`: Translates matrix stability to a normalized confidence level $[0.0, 1.0]$.
* `analyze_file(self, file_path: str, analysis_type: str = "auto") -> Dict[str, Any]`: High-level entry point to read and process source code.
* `create_recipe(self, content: str, max_recipe_size: int = 5000) -> Dict[str, Any]`: Main logic selector for choosing recipe pipelines or standalone templates.

---

## 2. Internal Package Dependencies

The components depend on previously migrated core authority classes:

```
[hmpu_engine.py / orchestrator.py]
       |
       v (imports / integrates)
[hmpu_core.py / constraints_engine.py]
       |
       +---> [state_manager.py / execution_context.py] (Budget & Telemetry)
       |
       +---> [matrix_ops.py / matrix_solvers] (Condition number solver)
       |
       +---> [bbc_scalar.py / validation_models] (BBCScalar, OmegaOperator, constant states)
```

---

## 3. Hidden System Dependencies

* **Disk I/O Operations:**
  * Read/Write access to weights file `hmpu_weights.json`.
  * Read access to source code files during file analysis.
  * Append-only write access to telemetry files (`.bbc/logs/telemetry.jsonl`).
* **Python Standard Library Imports:**
  * `re` (regular expressions for file splitting/parsing).
  * `math` (logarithms for entropy calculations).
  * `time` (timestamp generation).
  * `json` (de/serialization).
  * `threading` (uses `threading.RLock` to synchronize matrix mutations).
