# Validation Checklist - Phase 2 Core Migration

**Date:** 2026-06-24  
**Status:** Completed & Frozen

This checklist tracks the compliance of the migrated Phase 2 components against the legacy behavior. All tests have been executed via `scratch/validate_phase2.py` and passed successfully.

---

### [x] 1. Syntax Validation
- **Requirement:** Migrated Python source code files must compile and execute under Python 3.10+ without compilation or interpreter errors.
- **Verification Command:** `python -m py_compile bbc_aos/knowledge/graph/symbol_extractor.py bbc_aos/knowledge/graph/symbol_graph.py bbc_aos/audit/attribution_tracer.py`
- **Result:** `PASS`

---

### [x] 2. Import Validation
- **Requirement:** Migrated files must be clean of relative import errors under the target modular namespaces (`bbc_aos.knowledge.graph` and `bbc_aos.audit`).
- **Verification Method:** Checked by verifying namespace loads in `validate_phase2.py`.
- **Result:** `PASS`

---

### [x] 3. AST Extraction Equivalence Validation
- **Requirement:** `SymbolExtractor` output must match the legacy symbol extractor output for a target test file (`bbc_scalar.py`).
- **Verification Method:** Extracted symbols from `bbc_scalar.py` and compared the serialized symbol dictionary keys, line numbers, classes, and types.
- **Result:** `PASS`

---

### [x] 4. Symbol Graph Equivalence Validation
- **Requirement:** Assembled call graphs (node structures, stats, calls, called_by references) must match the legacy call graph output structure exactly.
- **Verification Method:** Extracted calls from `bbc_scalar.py` and `matrix_ops.py`, built graphs using legacy and new implementations, and compared output structures.
- **Result:** `PASS` (Parity resolved on Call dict `column` representation and fallback call relation type classification).

---

### [x] 5. Attribution Equivalence Validation
- **Requirement:** `AttributionTracer` must correctly scan codebases, find symbols and references, and output the identical blast radius impact list for modified files.
- **Verification Method:** Scanned `Legacy_BBC` using both tracers and compared the files impacted by a fault in `bbc_scalar.py`.
- **Result:** `PASS` (Normalizing backslashes to forward slashes resolves OS path differences).

---

### [x] 6. Determinism Validation
- **Requirement:** Migrated components must exhibit deterministic behavior, yielding identical JSON outputs across multiple sequential runs.
- **Verification Method:** Ran extraction twice on `bbc_scalar.py` and compared outputs.
- **Result:** `PASS`

---

## Validation Summary
All Phase 2 verification steps have been successfully validated. Migration is complete, verified, and locked.
