# Phase 13A - Repository Cleanup Plan

This plan details the scans, classification, and restructuring rules for productizing the BBC-AOS codebase.

---

## 1. File Classification Matrix

All files inside the current workspace are categorized under the following classification matrix:

| Classification | Target Paths / Directory | Purpose |
| :--- | :--- | :--- |
| **PRODUCTION** | `bbc_aos/` | Live application code, modules, interfaces, and core orchestrators. |
| **TEST** | `tests/` | Standard PyTest verification suites. |
| **DOCUMENTATION** | `docs/`, `Reports/`, `README.md` | System design specifications, usage manuals, and phase reports. |
| **MIGRATION** | `scratch/validate_*` | Validation scripts used during extraction phases. |
| **LEGACY** | `Legacy_BBC/` | Original legacy code used as references during development. |
| **ARCHIVE** | `Reports/` (old) | Old phase-specific reports and legacy logs. |
| **TEMPORARY** | `scratch/certification_data/` | Dynamic data generated during E2E pilot runs. |

---

## 2. Cleanup Guidelines

To ensure repository hygiene, the following guidelines are established:
* **No Unused Skeletons**: Remove any placeholder files or skeleton scripts in the production directory.
* **No Temporary Datasets**: Purge `.pytest_cache`, `.pytest-tmp`, and runtime logs before release.
* **Consolidated Documentation**: Sync all generated reports under a single `/Reports` folder and reference them inside `docs/`.
