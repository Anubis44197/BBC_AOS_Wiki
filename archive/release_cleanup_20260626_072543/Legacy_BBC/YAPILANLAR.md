# Changelog

This file summarizes user-visible BBC improvements. Local machine paths, private field-project names, and temporary test artifacts are intentionally excluded from the public changelog.

## 2026-06-16 - v8.6 Hardening and Release Preparation

### Product Hygiene and Release Safety

- Added `bbc doctor` for quiet environment, context, IDE signal, token usage source, and Git hygiene checks.
- Added `bbc init` for one-shot analyze, inject, and doctor setup without starting the daemon/watch loop.
- Added `bbc self-test` for local installation health checks against a temporary project.
- Added `bbc benchmark` for token reduction and context readiness reporting from an existing sealed context.
- Added `bbc integrations`, `bbc preview`, `bbc readiness`, `bbc security-check`, `bbc rule-health`, and `bbc mode` for safer setup previews, integration visibility, release readiness, and rule integrity checks.
- Fixed a core CLI `inject` scope issue that could break silent injection during self-test.
- Added `bbc publish-check` to block publish-time BBC traces and local personal path markers before a target project is pushed.
- Added `bbc clean` retention and size controls for `.bbc/` runtime logs/cache without touching project source files.
- Added `setup.ps1` for PowerShell-first Windows setup while preserving one-command setup behavior.
- Added GitHub Actions CI for Windows, Linux, and macOS across Python 3.10, 3.11, and 3.12.
- Added dynamic import dependency detection for common Python `importlib.import_module()` and `__import__()` patterns.
- Added integration-style tests for publish hygiene, runtime cleanup, and dynamic import dependency mapping.
- Added README stress-test evidence from a real legal MCP project: `165,641` source tokens reduced to `15,455` sealed-context tokens, plus a hallucination guard test that returned `HALLUCINATION_DETECTED`.
- Streamlined README for developer evaluation: purpose, measured results, privacy/security, IDE/tool coverage, install, commands, and development checks.

### Core Reliability

- Fixed project-scoped telemetry loading and command logging.
- Fixed transaction footer metrics so reports read the target project's `.bbc/bbc_context.json`.
- Suppressed transaction footers for machine-readable `--json` output.
- Fixed relative path handling for `bbc check <file> --path <project>`.
- Normalized Windows and POSIX path separators in impact radius traversal.
- Fixed verifier freshness checks for the current `stats.hash` context schema.
- Added UTF-8 BOM tolerant source reads for Windows editor and PowerShell workflows.
- Refreshed incremental caches after full analyze so daemon/incremental runs do not reuse stale segment token metrics.
- Added per-segment `token_model` metadata so cached token metrics are recomputed when the tokenizer/model changes.

### IDE and AI Tool Integration

- Improved active IDE/extension detection from process, environment, existing rule files, and extension signals.
- Kept BBC IDE-agnostic: no single IDE is required or privileged.
- Removed synthetic VS Code/Windsurf token usage placeholders. Unsupported or inaccessible IDE usage stores now return a safe fallback.
- Cursor SQLite usage parsing is tested with a synthetic SQLite fixture.
- Added broader `.gitignore` coverage for BBC-generated target-project traces and AI tool rule files.
- Added reuse-first AI rules so adapters tell coding tools to check verified symbols, imports, and installed dependencies before adding new code or dependencies.
- Added adapter invariant tests to keep evidence-only, no-hallucination, and reuse-first rules present across generated agent surfaces.
- Added `benchmarks/README.md` with repeatable local benchmark guidance for token reduction, hallucination guard, adapter invariants, and publish hygiene.

### Memory and CLI

- Added top-level `remember`, `recall`, and `usage` commands.
- Added `MemoryStore` for project-scoped episodic memory with conflict detection, force overwrite, recall, and markdown export.
- Prevented `remember`/`recall` and other read/guard commands from printing unrelated transaction footers.

### Server and Packaging

- Verified `bbc.py serve` with a real `/health` HTTP check.
- Added `httpx2` to requirements for the current FastAPI/Starlette test client stack.
- Updated package metadata and documentation links to the public repository.
- Rewrote README, quick start, installation, and user guide docs with clean ASCII text and accurate feature claims.

### Validation

- Unit test suite: `22 passed`.
- Field workflow validation covered analyze, verify, inject, check, impact, pack, compile, audit, telemetry, daemon live re-analysis, and server health.
- Final daemon validation confirmed live edits re-seal successfully and token metrics remain stable.

## 2026-06-15 - v8.6 Field-Test Fixes

- Improved dependency graph construction for normalized module names as well as raw import statements.
- Added recursive dependency cascade support for stale-file impact detection.
- Improved existing-rule-file detection so BBC preserves active AI tool integrations.
- Added tests for dependency graph behavior and active-rule detection.

## 2026-06-14 - v8.6 Baseline Stabilization

- Improved Windows console UTF-8 handling across CLI entry points.
- Consolidated runtime dependencies into the main requirements file.
- Added verifier, telemetry, server, math, and auto-detection tests.
- Standardized visible version references around v8.6.
