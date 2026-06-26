# Deterministic Core Inventory - BBC-AOS

This inventory catalogs the specific mathematical variables, constants, equations, matrices, and algorithms to be extracted from the legacy repository.

---

## 1. System Constants & State Tables

### A. State Constants
Defined in `bbc_scalar.py`:
* `STABLE = "STABLE"`
* `WEAK = "WEAK"`
* `SLEEPING = "SLEEPING"`
* `NEG_ZERO = "NEG_ZERO"`
* `SATURATED = "SATURATED"`
* `UNSTABLE = "UNSTABLE"`
* `DEGENERATE = "DEGENERATE"`

### B. State Multiplication Table (`STATE_MULT_BASIC`)
Computes mathematical state combinations during scalar arithmetic (e.g., adding a `WEAK` and `STABLE` scalar results in a `WEAK` state).

---

## 2. Core Matrices & Vectors

### A. Aura Base Matrix (`self._Aura_Base`)
Defined in `hmpu_core.py`:
```python
[
    [1.00, 0.00, 0.00],  # S (Structural Anchor)
    [0.75, 0.15, 0.10],  # C (Chaos Density)
    [0.70, 0.10, 0.20]   # P (Pulse Alpha)
]
```
Represented using `BBCScalar` variables.

### B. Aura Weight Matrix (`self._Aura_Weights`)
Initial matrix:
```python
[
    [0.0, 0.0, 0.0],
    [0.0, 0.0, 0.0],
    [0.0, 0.0, 0.0]
]
```
Persistent weights updated dynamically using the gradient formula.

### C. State Input Vector ($v$)
Holds the current state values:
\[
v = [S, C, P]^T
\]
where:
* $S$: match_ratio of symbols.
* $C$: Shannon chaos density score.
* $P$: Pulse / freshness multiplier.

---

## 3. Mathematical Equations & Solvers

### A. Chaos Calculation (Shannon Entropy)
Evaluated in `hmpu_core.py` and `hallucination_guard.py`:
\[
H(X) = \sum_{x \in X} - P(x) \log_2 P(x)
\]
Calculated over character frequency occurrences in target code blocks.

### B. HMPU Operator Formulas
* **OP-01 ($dC/dt$ - Noise Filter):**
  \[
  dC/dt = | H(X_t) - H(X_{t-1}) |
  \]
  If $dC/dt > 0.40$, the signal is isolated.
* **OP-02 ($\nabla A$ - Aura Gradient Adaptation):**
  \[
  W_{i,i} = W_{i,i} + \Delta \cdot \text{learning\_rate} \quad (\text{if stable})
  \]
  If unstable, states downgrade ($\text{STABLE} \rightarrow \text{WEAK} \rightarrow \text{UNSTABLE} \rightarrow \text{NEG\_ZERO}$).
* **OP-03 ($P_{t+1}$ - Perturbation Stability Check):**
  \[
  P_{t+1} = \text{current\_aura} \cdot (1 - (\text{impact\_factor} \cdot \text{intent\_magnitude}))
  \]
  Blocked if $P_{t+1} \leq 0.65$.
* **OP-04 ($F_{\perp}$ - Orthogonal Projection):**
  \[
  \cos^2(\theta) = \frac{(\vec{q} \cdot \vec{t})^2}{\|\vec{q}\|^2 \|\vec{t}\|^2} > \text{threshold}^2
  \]
  Calculated without square root evaluations.

### C. Matrix Solvers
Implemented in `matrix_ops.py`:
* **Gauss-Jordan Inverse Solver:** Pivoted inverse solver utilizing state-healing hooks.
* **Condition Number Estimator:**
  \[
  \kappa(A) = \|A\|_{\infty} \cdot \|A^{-1}\|_{\infty}
  \]
  Used to map HMPU matrix stability to system confidence percentage:
  \[
  \text{Confidence} = \frac{1.0}{1.0 + \log_{10}(\kappa)}
  \]

### D. Text Fingerprinting & Distance Metrics
Implemented in `hmpu_indexer.py`:
* **128-bit SimHash (SHA-256 base):**
  Maps features $W$ (words) of a text to a 128-dimensional vector $v$:
  \[
  v_i = \sum_{w \in W} \text{sgn}(\text{hash}(w)_i) \cdot \text{weight}(w)
  \]
  where:
  \[
  \text{sgn}(x) = \begin{cases} 1 & \text{if bit is set} \\ -1 & \text{if bit is not set} \end{cases}
  \]
  The 128-bit fingerprint is formed by thresholding:
  \[
  f_i = \begin{cases} 1 & \text{if } v_i > 0 \\ 0 & \text{otherwise} \end{cases}
  \]
* **Hamming Distance:**
  Counts differing bits between two 128-bit fingerprints:
  \[
  D_H(f_1, f_2) = \text{popcount}(f_1 \oplus f_2)
  \]
* **Similarity Score:**
  Converts Hamming distance to a percentage score:
  \[
  \text{Similarity} = \max\left(0, 100 - \frac{D_H(f_1, f_2)}{128} \cdot 100\right)
  \]
* **Aura-Weighted Feature Scaling:**
  Adjusts word weights in SimHash based on Aura values:
  * For word length $> 5$: $\text{weight} = \text{freq} \cdot (1.0 + (S \cdot 0.2))$
  * For word length $< 4$: $\text{weight} = \text{freq} \cdot (1.0 - (C \cdot 0.3))$

---

## 4. Algorithms to Port

1. **Gauss-Jordan Solver with Pivot Healing:** Implements pivot selection and triggers `OmegaOperator.trigger(pivot)` if pivot state degrades.
2. **Sinkhorn-like Aura Field Iteration:** Performs iterative matrix multiplication of the combined base+weights matrix against the state vector for 5 iterations.
3. **CVP Post-Validation Protocol:** Iterates results against whitelist fields, maximum token size constraints, and scans output text strings for forbidden phrases (e.g. `probably`, `commentary`, `guess`).
4. **Hybrid Search Scoring:** Calculates search similarity as:
   \[
   \text{Score}_{\text{hybrid}} = 0.6 \cdot \text{Similarity}_{\text{simhash}} + 0.4 \cdot \text{Similarity}_{\text{keyword}}
   \]
