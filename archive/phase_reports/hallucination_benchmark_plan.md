# Phase 13A - Hallucination Benchmark Plan

This document details the benchmark design for comparing LLM-agent hallucination rates with BBC-AOS guardrails turned ON versus OFF.

---

## 1. Objectives

To measure and compare the effectiveness of the static analysis engines, memory managers, and validation gateway layers in preventing:
1. Access to non-existent (hallucinated) files.
2. References to invalid classes or functions.
3. Ingestion of wrong/circular imports.
4. Deployment of invalid edits (malformed patches).

---

## 2. Mandatory Evaluation Metrics

All benchmark runs must record the following metrics:

* **Hallucinated File Access Rate**: Percentage of file-write or file-read requests targeting paths outside the index.
* **Invalid Symbol Rate**: Percentage of references targeting non-existent classes, methods, or variables.
* **Wrong Import Rate**: Percentage of compiled imports that fail Python syntax or module resolution.
* **Wrong File Edit Rate**: Percentage of unified diff patches that fail to apply to target files.
* **Replay Fidelity**: Percentage of identical output hashes during E2E re-execution tests.
* **Rollback Frequency**: Number of times the commit manager rolled back due to verification failure.
* **Human Approval Rate**: Percentage of successful approvals resolved by the manager.
* **Average Latency**: Duration in milliseconds of E2E execution cycles.
* **Token Compression Ratio**: Ratio of packed tokens to raw tokens.

---

## 3. Benchmark Datasets

Evaluation must run across four distinct benchmark repositories:

* **Django**: Mock web application repository testing framework routes, models, and circular import traps.
* **BBCMath**: Mathematical codebase (Legacy_BBC) testing multi-module references, floating-point precision, and Gaussian algorithms.
* **Wikipedia**: Markdown database vault testing text documents, frontmatter tags, and Obsidian note syncing.
* **Polyglot Repository**: Multi-language workspace (Python, JS, shell) testing parser quantization limits.

---

## 4. Comparison Framework

| Metric | BBC OFF (Baseline LLM Agent) | BBC ON (BBC-AOS sidecar active) |
| :--- | :---: | :---: |
| **Hallucinated File Access Rate** | High (5% - 15%) | **0%** (Blocked by compiler) |
| **Invalid Symbol Rate** | Moderate (8% - 12%) | **0%** (Blocked by indexer) |
| **Wrong Import Rate** | High (10% - 18%) | **0%** (Verified by AST parser) |
| **Wrong File Edit Rate** | Moderate (5% - 8%) | **0%** (Verified by CommitManager) |
| **Replay Fidelity** | Extremely Low (Reasoning drift) | **100.0%** (Deterministic seeding) |
