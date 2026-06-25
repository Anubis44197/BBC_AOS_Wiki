# Changelog

All notable changes to the BBC-AOS project will be documented in this file.

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
