# BBC-AOS v1.0.0 Release Notes

## Major Features

- Real AST-informed patch generation for bugfix, feature, refactor, review, and test tasks.
- Interactive bounded daemon loop with checkpoints, retry, recovery, and max iteration control.
- Security guardrails for dangerous commands, dynamic execution, pickle loading, secrets, and forbidden paths.
- Obsidian-compatible knowledge vault workflow with wiki search and status commands.
- Reflection, failure memory, shadow mode, architectural invariants, and audit reporting.
- Real repository benchmark harness and deterministic release validation tools.

## Architecture Overview

BBC-AOS is organized around planner, context, coder, tester, and verification agents. Verification now routes proposed changes through blast radius checks, security guardrails, hallucination detection, permission checks, and architectural invariants before approval.

## Validation Summary

- Pytest: 59 passed, 0 failed.
- Ruff: passed.
- Mypy: passed.
- Release determinism: 1000 iterations per scenario, zero variance.
- Security validation: 8 of 8 malicious scenarios blocked.
- Clean install: wheel install and core CLI commands passed.
- Shadow mode: checksum unchanged.

## Known Limitations

- Repository cleanup still requires explicit approval for broad root reorganization.
- Real external repository benchmark metrics are placeholder-only until network-enabled benchmark execution is run.
- Docker build was not executed in this validation pass.
- Empty wiki vault reports `Vault Healthy: NO` until notes are generated or imported.
