# Integration Test Matrix - Phase 6

This document presents the integration testing coverage map, verifying that every migrated core component is tested for syntax, imports, API compatibility, determinism, and legacy parity.

## 1. Component Coverage Map

| Component | Target Location | Syntax | Imports | API Contract | Determinism | Parity | Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **BBC Scalar** | `core/bbc_scalar.py` | [x] | [x] | [x] | [x] | [x] | **Passed** |
| **Matrix Operations** | `core/matrix_ops.py` | [x] | [x] | [x] | [x] | [x] | **Passed** |
| **Symbol Extractor** | `knowledge/graph/symbol_extractor.py` | [x] | [x] | [x] | [x] | [x] | **Passed** |
| **Symbol Graph** | `knowledge/graph/symbol_graph.py` | [x] | [x] | [x] | [x] | [x] | **Passed** |
| **Attribution Tracer** | `audit/attribution_tracer.py` | [x] | [x] | [x] | [x] | [x] | **Passed** |
| **Context Optimizer** | `core/context_optimizer.py` | [x] | [x] | [x] | [x] | [x] | **Passed** |
| **Context Compiler** | `core/context_compiler.py` | [x] | [x] | [x] | [x] | [x] | **Passed** |
| **Semantic Packer** | `core/semantic_packer.py` | [x] | [x] | [x] | [x] | [x] | **Passed** |
| **HMPU Indexer** | `knowledge/indexes/hmpu_indexer.py` | [x] | [x] | [x] | [x] | [x] | **Passed** |
| **HMPU Quantizer** | `knowledge/indexes/hmpu_quantizer.py` | [x] | [x] | [x] | [x] | [x] | **Passed** |
| **State Storage** | `memory/interfaces/` | [x] | [x] | [x] | [x] | [x] | **Passed** |
| **State Manager** | `memory/working/state_manager.py` | [x] | [x] | [x] | [x] | [x] | **Passed** |
| **HMPU Governor** | `core/constraints_engine.py` | [x] | [x] | [x] | [x] | [x] | **Passed** |
| **Orchestrator** | `core/orchestrator.py` | [x] | [x] | [x] | [x] | [x] | **Passed** |

---

## 2. Test Verification Coverage Descriptions

### A. Core Mathematical Integration
* Tests the interaction between `BBCScalar` and `MatrixOps`.
* **Validation:** Verified that matrix Gauss-Jordan inversions trigger `OmegaOperator` pivot healing when hitting `UNSTABLE` float bounds, updating elements and states in lockstep.

### B. Graph and Compilation Integration
* Tests the flow from `SymbolExtractor` output to `SymbolGraph` construction, and then to `ContextOptimizer` and `TaskContextCompiler`.
* **Validation:** Verified that optimized code-structures are packed correctly, preserving critical definitions and dependencies.

### C. Orchestrator & Persistence Integration
* Tests `HMPUEngine` (orchestrator) executing recipes, generating state telemetry, and saving through `FileStateStorage`.
* **Validation:** Verified that consecutive runs update stats, file counts, and memory configurations in state files, and that re-instantiated orchestrators recover from those files.
