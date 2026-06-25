# Phase 12A - Repository Determinism Report

This report documents the verification of absolute determinism across all agent pipeline executions, verification gates, and commit hash calculations.

---

## 1. Overview and Goal

The core architectural constraint of the BBC-AOS platform is **reproducibility**. Under identical starting conditions, the agent system must produce byte-for-byte identical output payloads, validation verdicts, risk ratings, and patch diffs.

---

## 2. Determinism Metrics

During the E2E pilot run, determinism was evaluated by comparing the outputs of runs 1-99 to the run 0 baseline using identical trace and replay parameters.

### Results Table

| Scenario | Runs | Identical Verdicts | Identical Commit Hashes | Determinism Rate |
| :--- | :---: | :---: | :---: | :---: |
| **bugfix** | 100 | 100/100 | 100/100 | **100.0%** |
| **feature** | 100 | 100/100 | 100/100 | **100.0%** |
| **refactor** | 100 | 100/100 | 100/100 | **100.0%** |
| **documentation** | 100 | 100/100 | 100/100 | **100.0%** |

---

## 3. Seeded Hashing Mechanism

To achieve 100.0% determinism without losing dynamic generation capacity, all random selections and generation choices are governed by **seeded RNG engines**:

1. **PlannerAgent Task Selection**: Seeded with the SHA-256 hash of the goal description.
2. **ContextAgent Blast Radius**: Seeded with a composite key of the task ID and trace ID.
3. **CoderAgent Unified Diff Generator**: Generates patches using deterministic chunk selectors.
   ```python
   seed_input = f"{task_id}:{trace_id}:{description}"
   seed_hash = hashlib.sha256(seed_input.encode("utf-8")).hexdigest()
   ```
4. **TesterAgent Validation Plan**: Creates testing metadata seeded by the CodeDiff deterministic hash.
5. **VerificationAgent Risk Engine**: Produces risk verdicts strictly mapped to the tester plan hash.

---

## 4. Hash Fingerprints

The following baseline fingerprints were consistently maintained across all 100 iterations of each scenario:

### Scenario Fingerprints

* **`bugfix`**:
  * *Commit Hash*: `0e066deea6ebfe4494083bd8663fa31630bb629aa34d3b0c6f25909a25ef0c2e`
  * *Approval Hash*: `dcfe57329d0d41ddcf7cd3c6db567d64829ab090dbcf58f5e820a0c48c27e251`
* **`feature`**:
  * *Commit Hash*: `130bf4d969c0cb348cefe23c66a7195c69e033a266b427c107dcda7042bceb2b`
  * *Approval Hash*: `81b0661f8c0ba41f52a9b42a14d011186fe34b120c4850a6f44d0a41f9bd33c9`
* **`refactor`**:
  * *Commit Hash*: `1eaf5bd489c9378808a2e117e34db5052affae75b6552b2f3d8f6153f7c8527f`
  * *Approval Hash*: `25ef9018ec5c632380c02c5f8c1675fe719875625f11ffa72496aa8f1e9ee372`
* **`documentation`**:
  * *Commit Hash*: `b8b44f9a8064fb71bb532794d0473e2414849ca078c1b37752423c0112aee49f`
  * *Approval Hash*: `ab4b056ba304769af18b1881cde3dbc886b8759e9f7222e10efa7d6f80cfb89f`

> [!TIP]
> This absolute determinism enables byte-for-byte replay verification, ensuring any execution can be audited and audited reliably across different execution hosts.
