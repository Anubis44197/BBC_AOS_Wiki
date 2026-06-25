# Legacy to BBC-AOS Component Mapping

This document provides a line-item mapping of files from the legacy `Legacy_BBC` repository to their new destinations inside the `bbc_aos` structure, detailing the specific classes, functions, and adapters required.

---

## 1. Core Component Mapping Table

| Legacy File | Target BBC-AOS File | Mapped Classes / Functions / Data | Required Adapters / Bridges |
| :--- | :--- | :--- | :--- |
| [`bbc_scalar.py`](file:///C:/Users/90535/Desktop/BBC_AOS_Wiki/Legacy_BBC/bbc_core/bbc_scalar.py) | [`validation_models.py`](file:///C:/Users/90535/Desktop/BBC_AOS_Wiki/bbc_aos/models/validation_models.py) | `BBCScalar`, `OmegaOperator`, `BBCEncoder`, `bbc_hook`, `STATE_MULT_BASIC`, state constants | None (Pure mathematical port) |
| [`matrix_ops.py`](file:///C:/Users/90535/Desktop/BBC_AOS_Wiki/Legacy_BBC/bbc_core/matrix_ops.py) | [`constraints_engine.py`](file:///C:/Users/90535/Desktop/BBC_AOS_Wiki/bbc_aos/core/constraints_engine.py) | `MatrixOps.gauss_jordan_inverse`, `MatrixOps.pseudo_inverse`, `MatrixOps.condition_number` | Integration with `BBCScalar` imports inside AOS. |
| [`hmpu_core.py`](file:///C:/Users/90535/Desktop/BBC_AOS_Wiki/Legacy_BBC/bbc_core/hmpu_core.py) | [`constraints_engine.py`](file:///C:/Users/90535/Desktop/BBC_AOS_Wiki/bbc_aos/core/constraints_engine.py) | `HMPU_Governor` class, Aura Base/Weight matrices, operators OP-01, OP-02, OP-03, OP-04 | State bridge to load budget configuration from the new `execution_context.py`. |
| [`hmpu_engine.py`](file:///C:/Users/90535/Desktop/BBC_AOS_Wiki/Legacy_BBC/bbc_core/hmpu_engine.py) | [`orchestrator.py`](file:///C:/Users/90535/Desktop/BBC_AOS_Wiki/bbc_aos/core/orchestrator.py) | `HMPUEngine` class, `RecipeConstraint`, `BaseRecipe`, `CodeStructureRecipe`, `LogTelemetryRecipe`, `MultiRecipePipeline` | Bridges to link the math operators to the async pipeline executors. |
| [`symbol_extractor.py`](file:///C:/Users/90535/Desktop/BBC_AOS_Wiki/Legacy_BBC/bbc_core/symbol_extractor.py) | [`repository_scanner.py`](file:///C:/Users/90535/Desktop/BBC_AOS_Wiki/bbc_aos/tools/repository_scanner.py) | `PythonSymbolExtractor`, `SymbolType`, `Symbol`, `FileSymbols` | Filter configuration parser adapter. |
| [`symbol_graph.py`](file:///C:/Users/90535/Desktop/BBC_AOS_Wiki/Legacy_BBC/bbc_core/symbol_graph.py) | [`graph_tools.py`](file:///C:/Users/90535/Desktop/BBC_AOS_Wiki/bbc_aos/tools/graph_tools.py) | `SymbolGraph` builder class, `SymbolNode`, `Call`, `CallType` | JSON serializer to save outputs to `/data/graphs/`. |
| [`context_optimizer.py`](file:///C:/Users/90535/Desktop/BBC_AOS_Wiki/Legacy_BBC/bbc_core/context_optimizer.py) | [`context_reducer.py`](file:///C:/Users/90535/Desktop/BBC_AOS_Wiki/bbc_aos/core/context_reducer.py) | `SymbolResolver` class, `ImpactLevel`, `ContextOptimizerError` | Graph parser adaptor to read JSON graph representations. |
| [`context_compiler.py`](file:///C:/Users/90535/Desktop/BBC_AOS_Wiki/Legacy_BBC/bbc_core/context_compiler.py) | [`context_builder.py`](file:///C:/Users/90535/Desktop/BBC_AOS_Wiki/bbc_aos/core/context_builder.py) | `TaskContextCompiler`, `TASK_PROFILES` configuration | Config adapter to interface with new global settings. |
| [`semantic_packer.py`](file:///C:/Users/90535/Desktop/BBC_AOS_Wiki/Legacy_BBC/bbc_core/semantic_packer.py) | [`memory_tools.py`](file:///C:/Users/90535/Desktop/BBC_AOS_Wiki/bbc_aos/tools/memory_tools.py) | `SemanticPacker` class | Compression metrics exporter. |
| [`hmpu_indexer.py`](file:///C:/Users/90535/Desktop/BBC_AOS_Wiki/Legacy_BBC/bbc_core/hmpu_indexer.py) | [`knowledge_store.py`](file:///C:/Users/90535/Desktop/BBC_AOS_Wiki/bbc_aos/core/knowledge_store.py) | `HMPUIndexer` class, SimHash functions (`compute_simhash`, `hamming_distance`, `similarity_score`) | Database adapter to save/load binaries from `/state/indices/`. |
| [`attribution_tracer.py`](file:///C:/Users/90535/Desktop/BBC_AOS_Wiki/Legacy_BBC/bbc_core/attribution_tracer.py) | [`tracing.py`](file:///C:/Users/90535/Desktop/BBC_AOS_Wiki/bbc_aos/observability/tracing.py) | `AttributionTracer` class | Subprocess/git binding adapter for blame logs. |
| [`state_manager.py`](file:///C:/Users/90535/Desktop/BBC_AOS_Wiki/Legacy_BBC/bbc_core/state_manager.py) | [`execution_context.py`](file:///C:/Users/90535/Desktop/BBC_AOS_Wiki/bbc_aos/core/execution_context.py) | `StateManager` class | Daemon thread adapters, telemetry event logging hooks. |

---

## 2. Structural Mapping Detail

### `state/` directory integration
Legacy parameters dynamically saved to `.bbc/` folder will be redirected to:
* `/state/sessions/` (active state session json configurations).
* `/state/indices/` (128-bit SimHash indexed databases).

### `models/` directory integration
Data validation and configuration model objects reside under `bbc_aos/models/`:
* `validation_models.py`: Houses validation state metadata schema (`BBCScalar`).
* `agent_models.py`: Houses definitions for the system agent candidates.
