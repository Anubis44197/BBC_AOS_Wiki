# Failure Memory Report

Implemented `src/bbc_aos/memory/failure_memory.py`.

Storage:
- `.bbc/failure_memory.jsonl`

Behavior:
- Repeated failures increment `occurrence_count`.
- Search is supported by `bbc failures search "<query>"`.
- Root CLI listing is supported by `bbc failures`.

Validation:
- Repeated `MISSING_IMPORT` records incremented correctly in `scratch/validate_phase_c8.py`.
