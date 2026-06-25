# Phase 13A - Token Reduction Benchmark Plan

This document outlines the benchmark strategy for measuring context reduction and token savings across the platform.

---

## 1. Objectives

To evaluate the mathematical compression performance of the context optimizer, ast compiler, and semantic packer layers.

---

## 2. Metrics Definition

* **Token Compression Ratio**:
  \[
  \text{Compression Ratio} = \frac{\text{Packed Tokens}}{\text{Raw Tokens}}
  \end{align*}
  \]
* **Token Savings**:
  \[
  \text{Token Savings} = 1 - \text{Compression Ratio}
  \]
* **Context Fidelity Score**: Matches the presence of target-related dependencies. Must be **1.0 (100%)** to ensure no loss of relevant context.

---

## 3. Evaluation Datasets

* **Django**: Web app codebase testing import collapsing and schema compression.
* **BBCMath**: Testing mathematical helper functions.
* **Wikipedia**: Ingestion of large markdown files testing structural compaction.
* **Polyglot Repository**: Testing compression across diverse languages.

---

## 4. Benchmark Target Thresholds

* **Target Compression Ratio**: $\le 0.80$ (Minimum 20% token savings).
* **Target Context Reduction**: $\ge 50\%$ (Token preservation ratio $\le 0.50$ for feature scopes).
* **Fidelity Threshold**: **100%** (Zero critical dependencies dropped during optimization).
