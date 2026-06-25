# Engine Validation Strategy

**Date:** 2026-06-24  
**Status:** Planning & Draft  

This document outlines the testing protocols, test inputs, and target equivalence checks to verify the Phase 5 core migration.

---

## 1. Automated Test Suites (`validate_phase5.py`)

A custom test validation script `scratch/validate_phase5.py` will be created to verify:
1. **Syntax and Import Resolution:** Ensure `constraints_engine.py` and `orchestrator.py` compile and resolve all package imports under `bbc_aos.core`.
2. **Governor Equivalence:**
   * Test base matrix initialization and weights loading/saving.
   * Verify condition number stability matching up to float tolerance $10^{-12}$.
   * Test Shannon Chaos Density math calculation.
   * Verify dC/dt Chaos Derivative Filter outcomes.
   * Validate matrix convergence score iteration matches legacy outputs exactly.
3. **Engine Orchestration Equivalence:**
   * Test standalone recipes (`CodeStructureRecipe`, `LogTelemetryRecipe`, `ConfigJsonRecipe`, `DocumentationRecipe`) with specific inputs and compare extracted dictionaries.
   * Validate constraint tuning logic (Aura dynamic adjustment).
   * Test segment-splitting and pipeline processing.
4. **CVP Exception Handling:**
   * Force constraint violations (e.g. including forbidden words or exceeding budget limit) and verify that CVP triggers proper abort/discard dictionaries.
5. **Self-Healing Loop Budget Verification:**
   * Populate degrading weights and verify that the healing protocol consumes the StateManager budget and eventually triggers degeneracy blocks.
6. **Determinism Verification:**
   * Run the same processes sequentially under standardized timestamps and compare JSON exports.

---

## 2. Validation Metrics & Targets

We define the following success criteria for the validation run:

* **Engine Output Parity:** $100.0\%$ (All generated recipes, segment results, and metrics match legacy).
* **CVP Enforcement Fidelity:** $1.000$ (All constraint violations are correctly trapped with matching severity levels).
* **Chaos Calculation Error:** $0.000$ (Perfect parity in chaos derivative extraction).
* **Heal Protocol Parity:** $1.000$ (Weight promotions and budget deductions match legacy exactly).
