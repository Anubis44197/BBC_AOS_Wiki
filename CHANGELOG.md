# Changelog

All notable changes to the BBC-AOS project will be documented in this file.

## [1.0.0] - 2026-06-27

### Release Certification
- Passed FSAT-V3 final production acceptance on a real FastMCP/FastAPI repository.
- Certified 100 shadow-mode production tasks with 100.0% task success.
- Certified 25/25 malicious prompts blocked for 100.0% security block rate.
- Certified 100/100 replay traces with 100.0% replay fidelity.
- Certified source integrity preservation under SHA-256 manifest comparison.
- Certified no memory leak, no infinite loop, and no state corruption.

### Added
- Wired production security validation before planner execution.
- Added hard-deny guards for system prompt leakage, policy integrity, workspace escape, and tool permission abuse.
- Added append-only integration audit replay support for successful, failed, and security-blocked terminal states.
- Added canonical entity registry and wikilink resolver for Obsidian-compatible knowledge graph generation.
- Added entity normalization, duplicate merge, broken-link repair, backlink generation, timeline generation, and wiki quality metrics.

### Fixed
- Blocked escaped prompt classes including `shell=True`, `powershell`, hidden prompt disclosure, `.env` copying, persistence outside workspace, approval policy overwrite, and malicious safe-labeling.
- Eliminated broken wikilinks in generated BBC Knowledge Vault notes.
- Reduced knowledge graph duplicate rate below release threshold.
- Moved mutable operational loop artifacts into `.bbc/loop/` instead of installed package directories.

### Validation Metrics
- Pytest: 68 passed.
- Ruff: passed.
- Mypy: passed across 219 source files with 0 errors.
- Build: source distribution and wheel built successfully.
- Wiki graph: 1347 notes, 7606 edges, 0 broken links, 0 empty notes, 0.97% duplicate rate.
- Knowledge counts: 256 entities, 275 concepts, 459 lessons.

## [1.0.0] - 2026-06-25

### Added
- Created production-grade sidecar architecture with Planner, Context, Coder, Tester, and Verification agents.
- Integrated standard Python `src/` layout.
- Converted all legacy validation scripts to pytest-compatible tests under `tests/`.
- Designed real benchmark frameworks for hallucination prevention, token optimization, and replay fidelity metrics.
- Exposes developer CLI supporting `bbc init`, `bbc index`, and `bbc start` commands.
- Certified environments across Docker, Windows, Linux, and macOS.
- Integrated Obsidian vault note sync and promotion workflows.

### Fixed
- Adjusted AgentOrchestrator constructor parameter signatures to support dynamic registry, memory_manager, and audit_log overrides.
- Fixed case sensitivity and risk level mismatches in verification agent test assertions.
- Resolved path targets for legacy_bbc files under pytest execution.
