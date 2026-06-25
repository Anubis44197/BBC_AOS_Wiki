# Phase 13A - Repository Migration Plan

This plan outlines the file relocation strategy for preparing the codebase for packaging.

---

## 1. Relocation Actions

The following directories and files must be moved to the archive:

### MOVE TO ARCHIVE
* **`Legacy_BBC`**: The legacy repository copy will be moved out of the workspace to a separate storage bucket.
* **Migration Reports**: All individual migration reports under `/Reports` (e.g. `migration_phase1_report.md`, `migration_phase5a_report.md`) will be moved to `/archive/reports/`.
* **Phase Reports**: All phase-specific reports (e.g. `coder_agent_implementation_report.md`, `approval_gate_api_contract_report.md`) will be archived.
* **`validation_phase*`**: All legacy validation scripts inside the `/scratch` directory will be archived under `/archive/validation/`.
* **Temporary Certification Datasets**: Clean up `scratch/certification_data` and dynamic validation outputs.

---

## 2. Production Retention

The following files will remain in production and be packaged for release:

### KEEP IN PRODUCTION
* **`bbc_aos/`**: The core library package.
* **`tests/`**: Standard test files.
* **`docs/`**: Public documentation.
* **`examples/`**: Example configurations and scripts.
* **`README.md`**: Public README file.
* **`pyproject.toml`**: Packaging configuration.
