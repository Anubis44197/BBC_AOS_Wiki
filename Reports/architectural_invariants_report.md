# Architectural Invariants Report

Implemented `src/bbc_aos/security/invariant_engine.py`.

Configuration:
- `.bbc/invariants.yaml`

Supported invariants:
- `forbidden_paths`
- `must_not_modify`
- `max_files_per_commit`
- `require_tests`
- `require_docstrings`
- `forbidden_imports`

VerificationAgent now rejects execution when invariant violations are detected.
