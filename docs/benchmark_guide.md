# Benchmark Reference Guide

This document defines the 9 mandatory metrics and evaluation datasets used to measure the reliability, determinism, and performance of BBC-AOS.

## Mandatory Metrics

1. **Hallucinated File Access Rate**: Percentage of file-write or file-read requests targeting paths outside the index (Target: **0%**).
2. **Invalid Symbol Rate**: Percentage of references targeting non-existent classes, methods, or variables (Target: **0%**).
3. **Wrong Import Rate**: Percentage of compiled imports that fail Python syntax or module resolution (Target: **0%**).
4. **Wrong File Edit Rate**: Percentage of unified diff patches that fail to apply to target files (Target: **0%**).
5. **Replay Fidelity**: Percentage of identical output hashes during E2E re-execution tests (Target: **100%**).
6. **Rollback Frequency**: Number of times the commit manager rolled back due to validation failures (Target: **0** in stable runs).
7. **Human Approval Rate**: Percentage of successful approvals resolved by the manager.
8. **Average Latency**: Duration in milliseconds of E2E execution cycles.
9. **Token Compression Ratio**: Ratio of packed tokens to raw tokens (Typical target: **~0.767**).

## Benchmark Datasets

* **Django**: Mock web application repository testing framework routes, models, and circular import traps.
* **BBCMath**: Mathematical codebase (Legacy_BBC) testing multi-module references, floating-point precision, and Gaussian algorithms.
* **Wikipedia**: Markdown database vault testing text documents, frontmatter tags, and Obsidian note syncing.
* **Polyglot**: Multi-language workspace (Python, JS, shell) testing parser quantization limits.
