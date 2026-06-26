# Deterministic Certification Suite - Phase 6

This document describes the structure and execution procedure of the Golden Master certification suite built to validate `bbc_aos` against the legacy code.

## 1. Suite Architecture

The certification suite consists of two programmatic python scripts:
1. [`generate_certification_datasets.py`](file:///C:/Users/90535/.gemini/antigravity/brain/af9c3fab-d929-4fa5-983e-c6a18632dcc0/scratch/generate_certification_datasets.py):
   * Programmatically builds isolated folders containing representative files for ODA-MATH, Wikipedia, Django, and Polyglot repos.
2. [`run_certification_suite.py`](file:///C:/Users/90535/.gemini/antigravity/brain/af9c3fab-d929-4fa5-983e-c6a18632dcc0/scratch/run_certification_suite.py):
   * Performs the actual certification runs and edge-case evaluations.

---

## 2. Test Execution Details

### A. Run Sequence
The certification runner script executes 7 sequential phases:
1. **BBCScalar edge values:** Arithmetic checks on NaN, infinity, overflow, underflow, and negative zero.
2. **Matrix certification:** Gauss-Jordan inversion, rank deficient checks, singular matrices, near-singular matrices, condition number evaluations, and pivot healing.
3. **Hallucination guard invariants:** Extracting referenced symbols and evaluating speculative keywords.
4. **Compression parity:** Optimizing and compiling tasks side-by-side using legacy and modular packages.
5. **Chaos engineering:** Verifying that corrupted state files and simulated disk write failures are handled gracefully without crashing the engine.
6. **Golden Master replays:** Byte-for-byte matching of generated orchestrator JSON outputs against legacy outputs.
7. **100 deterministic loops:** Executing 100 iterations per dataset to ensure 0 output variance.

### B. Output Logs & Persistence
All results are stored in [`certification_results.json`](file:///C:/Users/90535/.gemini/antigravity/brain/af9c3fab-d929-4fa5-983e-c6a18632dcc0/scratch/certification_results.json). This file contains binary flags representing scenario statuses and the final certification verdict.

---

## 3. How to Execute

To manually execute the certification suite, run:
```powershell
$env:PYTHONPATH="Legacy_BBC;."
python C:\Users\90535\.gemini\antigravity\brain\af9c3fab-d929-4fa5-983e-c6a18632dcc0\scratch\run_certification_suite.py
```

Expected stdout output:
```text
==============================================
    FINAL VERDICT: CERTIFIED (100% Equivalence)
==============================================
```
Any failure during scenario execution will immediately halt the suite and output `NOT CERTIFIED`.
