# Phase 13A - Production Repository Structure

This document outlines the clean, finalized directory structure of the productized BBC-AOS platform.

---

## 1. Directory Tree Layout

The production layout separates the application runtime, tests, public documentation, and developer examples:

```
bbc-aos/
├── bbc_aos/                   # Main library package
│   ├── agents/                # Planner, Context, Coder, Tester, Verification agents
│   ├── approval/              # Risk-based human approval managers
│   ├── commit/                # Diffs parser, rollback snapshot, and commit managers
│   ├── core/                  # BBCScalar, MatrixOps, and constraint governor engines
│   ├── knowledge/             # SimHash indexes and polyglot quantizers
│   ├── loops/                 # Checkpoint control and loop execution runtime
│   ├── memory/                # Persistent working and semantic layer interfaces
│   └── main.py                # Command-line entrypoint (CLI)
├── tests/                     # Unit and integration test suites
│   ├── agents/
│   ├── core/
│   └── integration/
├── docs/                      # Operations, configuration, and API reference
│   ├── cli/
│   └── obsidian/
├── examples/                  # Developer usage recipes and scripts
├── pyproject.toml             # Package definition and dependencies metadata
└── README.md                  # Main entrypoint documentation
```

---

## 2. Structural Isolation Rules

* **Single CLI Entrypoint**: All commands route through `bbc_aos/main.py` which is mapped to the `bbc` script command.
* **Separation of Tests**: Test scripts must not reside inside `bbc_aos/`. All tests use standard PyTest configuration inside `/tests`.
* **Zero Sandbox Pollution**: The transient sandbox directory `BBC_MASTER_BBCMath-main_SANDBOX` must be created outside of the repository root (e.g. in OS temp folder or user directory) to avoid git history pollution during execution.
