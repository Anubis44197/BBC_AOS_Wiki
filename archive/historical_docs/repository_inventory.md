# Legacy BBC Repository Inventory

The following is an inventory of all files and folders discovered inside the legacy repository `Legacy_BBC` copied from `BBC_MASTER_BBCMath-main`.

---

## 1. Top-Level Repository Files & Folders

| File / Folder Name | Type | Description |
|---|---|---|
| `.bbc/` | Folder | Contains core model parameters, JSON-RPC contexts, rules, and cache files. |
| `.github/` | Folder | GitHub Actions workflows and CI configurations. |
| `bbc_core/` | Folder | The core source code containing mathematical and adaptational modules. |
| `benchmarks/` | Folder | Legacy benchmark files (includes `README.md`). |
| `tests/` | Folder | Unit and integration test suites. |
| `__pycache__/` | Folder | Compiled bytecode cache files. |
| `.gitignore` | File | Git exclusion filters. |
| `bbc.py` | File | Main execution CLI script (66,226 bytes). |
| `bbc.sh` | File | Shell script helper for running the main CLI. |
| `bbc_daemon.py` | File | Daemon service script for background execution (17,694 bytes). |
| `bbc_installer.py` | File | Auto-install utility script (12,329 bytes). |
| `BBC_TECHNICAL_REFERENCE_EN.md` | File | Technical English reference guide (5,777 bytes). |
| `INSTALLATION.txt` | File | Text-based installation notes. |
| `LICENSE` | File | MIT/Apache license declaration. |
| `pyproject.toml` | File | Build system requirements and tooling configuration. |
| `QUICK_START.md` | File | Quick start instructions. |
| `README.md` | File | Standard project readme. |
| `requirements.txt` | File | Project pip requirements list. |
| `run_bbc.py` | File | Direct runner file for launching BBC loops (8,991 bytes). |
| `setup.bat` | File | Windows setup script. |
| `setup.ps1` | File | PowerShell setup script. |
| `setup.py` | File | Legacy package setup installer. |
| `setup.sh` | File | Unix setup script. |
| `USER_GUIDE.md` | File | Reference guide for end-users. |
| `YAPILANLAR.md` | File | Turkish development updates and changelog. |

---

## 2. Detailed Source Code Inventory (`Legacy_BBC/bbc_core/`)

The `bbc_core` directory houses the key logical modules of the legacy system:

| File Name | Size (Bytes) | Description / Function |
|---|---|---|
| `adapter.py` | 2,599 | Interface adapter definitions. |
| `adaptive_mode.py` | 20,221 | Logic for handling HMPU grad A adaptive calibration. |
| `agent_adapter.py` | 65,490 | Manages agent communications and state translation layers. |
| `ai_integration.py` | 9,108 | Interfacing layers with LLM APIs and token managers. |
| `attribution_tracer.py` | 4,920 | Tracks file modifications and agent credits. |
| `auto_detector.py` | 12,628 | Detects code modifications, file extensions, and environments. |
| `auto_patcher.py` | 15,903 | Automated code refactoring and hot-fixing mechanics. |
| `bbc_logger.py` | 2,493 | Custom logging formatter and stdout writer. |
| `bbc_scalar.py` | 9,273 | Mathematical utilities for handling scalar inputs. |
| `change_tracker.py` | 7,580 | Monitored diff analyzer for tracking structural edits. |
| `cli.py` | 80,173 | Command-line interface definitions and parser routing. |
| `config.py` | 3,333 | System config loader (.env, JSON configuration). |
| `context_compiler.py` | 14,656 | Compiles and packs agent instructions and contexts. |
| `context_optimizer.py` | 36,712 | Context compression and token utilization rules. |
| `git_hooks.py` | 5,153 | Auto-installs pre-commit/post-commit hooks. |
| `global_menu.py` | 5,270 | Interactive curses/console menu router. |
| `global_setup.py` | 8,046 | Environment setup and system configuration check. |
| `hallucination_guard.py` | 10,941 | Guardrails for filtering nonsensical token streams. |
| `hmpu_core.py` | 11,887 | Low-level HMPU mathematical matrix computations. |
| `hmpu_engine.py` | 27,718 | High-level HMPU flow manager coordinating dC/dt, grad A, and P_t+1. |
| `hmpu_indexer.py` | 11,284 | Handles indexing logic on manifolds for prompt retrieval. |
| `hmpu_quantizer.py` | 7,126 | Low-bit quantizer for prompt embeddings. |
| `http_server.py` | 6,327 | JSON-RPC HTTP server endpoint for remote integrations. |
| `ide_auto_config.py` | 36,926 | Configuration scripts for VS Code and other IDE extensions. |
| `ide_hooks.py` | 12,637 | Event listener hooks for IDE editors. |
| `ide_parser.py` | 4,517 | Parsing ASTs of active project code. |
| `impact_analyzer.py` | 15,944 | Simulates and scores structural modifications. |
| `matrix_ops.py` | 5,187 | Dense matrix multiplication and Sinkhorn normalization logic. |
| `memory_store.py` | 4,974 | Persistent local database store for vector embeddings. |
| `migrator_engine.py` | 4,922 | System migration coordinator. |
| `native_adapter.py` | 25,102 | Connects Python operations directly with operating system commands. |
| `project_hygiene.py` | 13,838 | Analyzes code complexity, style formats, and warnings. |
| `realtime_token_counter.py` | 5,640 | Live token count trackers using tiktoken. |
| `requirements_core.txt` | 272 | Internal python requirements manifest. |
| `scan_profile.py` | 5,062 | Profiles of files and directories to audit/scan. |
| `semantic_packer.py` | 13,563 | Packs fragments of code context based on semantic similarity. |
| `state_manager.py` | 5,625 | Handles system states (e.g., active, waiting, blocked). |
| `symbol_extractor.py` | 19,073 | Extracts class/function/type definitions from source code. |
| `symbol_graph.py` | 31,063 | Graph-based dependency tree of extracted symbols. |
| `telemetry.py` | 7,936 | Collects performance metrics, token savings, and system alerts. |
| `terminal_monitor.py` | 7,127 | Monitors active terminal/shell streams. |
| `token_optimizer.py` | 15,016 | Minimizes token loads using compression algorithms. |
| `verifier.py` | 30,747 | Post-execution verification checks. |
| `__init__.py` | 423 | Package entry point. |
| `__main__.py` | 1,485 | CLI routing main handler. |

---

## 3. Internal Rules & Contexts (`Legacy_BBC/.bbc/`)

Contains runtime instructions, schemas, and configurations:
* `bbc_context.json` (88,964 bytes) - Full active parameters and model metadata.
* `bbc_context.md` (5,283 bytes) - Context specification document.
* `BBC_INSTRUCTIONS.md` (4,833 bytes) - Instructions for LLM integration.
* `bbc_rules.md` (544 bytes) - Safety rules and guards.
* `change_index.json` (13,123 bytes) - Tracked changes index.
* `context_segments.json` (61,934 bytes) - Extracted prompt segments.

---

## 4. Discovered Unit Tests (`Legacy_BBC/tests/`)

* `conftest.py` (1,685 bytes) - Pytest setup configurations.
* `test_agent_adapter_invariants.py` (2,899 bytes) - Dynamic checks on agent communication stability.
* `test_auto_detect.py` (3,988 bytes) - Tests file extension auto-detection.
* `test_bbc_cli_surface.py` (5,623 bytes) - Asserts CLI parameter validation.
* `test_math.py` (662 bytes) - Checks matrix operations and entropy math.
* `test_new_modules.py` (2,740 bytes) - Checks module loading.
* `test_project_hygiene.py` (2,196 bytes) - Checks complex code hygiene patterns.
* `test_scan_profile.py` (2,400 bytes) - Checks target scan limits.
* `test_server.py` (886 bytes) - Tests HTTP/JSON-RPC integration.
* `test_telemetry.py` (1,247 bytes) - Validates counter telemetry data.
* `test_verifier.py` (1,320 bytes) - Tests validation assertions.
