# Phase 13A - Archive Candidates

This report lists obsolete files, old reports, validation scripts, and legacy remnants targeted for archiving to keep the production repository clean.

---

## 1. Archive Candidates List

| Path / File Pattern | Description | Recommendation |
| :--- | :--- | :--- |
| `Legacy_BBC/` | Full legacy math repository copy. | Move to a separate backup or archive repository. |
| `scratch/validate_phase*.py` | Modular validation scripts used during core extraction. | Archive under a `legacy_validation/` archive folder. |
| `scratch/validate_phase1.py` | Equivalency tests for phase 1. | Archive. |
| `scratch/validate_phase11a.py` | Verification tests for agent registries. | Archive. |
| `scratch/validate_phase11b.py` | Verification tests for ContextAgent. | Archive. |
| `scratch/validate_phase11c.py` | Verification tests for CoderAgent. | Archive. |
| `scratch/validate_phase11d.py` | Verification tests for TesterAgent. | Archive. |
| `scratch/validate_phase11e.py` | Verification tests for VerificationAgent. | Archive. |
| `scratch/validate_phase11f.py` | Verification tests for AgentOrchestrator. | Archive. |
| `scratch/validate_phase11g.py` | Verification tests for CommitManager. | Archive. |
| `scratch/validate_phase11h.py` | Verification tests for ApprovalManager. | Archive. |
| `scratch/certification_data/` | Certification datasets (Wikipedia, math, polyglot). | Move to testing assets subdirectory. |
| `Reports/migration_phase*.md` | Early stage extraction reports. | Archive or merge into a consolidated history. |

---

## 2. Rationale

Archiving these artifacts prevents developer confusion, minimizes package size, reduces repository clutter, and ensures that developers focus entirely on the productized codebase structure.
