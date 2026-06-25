# CoderAgent Determinism Report
**Phase 11C — BBC-AOS Determinism Certification**
**Status:** CERTIFIED (Zero Variance)
**Date:** 2026-06-24

---

## 1. Determinism Strategy

The `CoderAgent` achieves full determinism through the `_DeterministicDiffEngine`. All output variance is eliminated by:

1. **SHA-256 Seed Hash**
   ```python
   seed_hash = SHA256(f"{task_id}:{trace_id}:{description}")
   ```

2. **Per-file Hash Derivation**
   ```python
   file_hash = SHA256(f"{seed_hash}_{idx}_{file_path}")
   ```

3. **Deterministic Selector**
   ```python
   op_selector = int(file_hash[:2], 16) % max(len(allowed_ops), 1)
   ```

4. **Output Hash**
   ```python
   deterministic_hash = SHA256(f"{task_id}_{trace_id}_{json.dumps(diff_result, sort_keys=True)}")
   ```

All intermediate values are derived mathematically from the input with zero entropy sources (no `random`, no `time`, no thread state).

---

## 2. Replay Test Results

| Metric | Value |
|---|---|
| Total Iterations | 100 |
| Matching Hashes | 100/100 (100.0%) |
| Hash Variance | 0 |
| `modified_files` Variance | 0 |
| `patch` Content Variance | 0 |
| Statistical Variance | **ZERO** |

---

## 3. Cross-Input Isolation

Different inputs produce different outputs (no hash collision):

| Input Pair | Same Hash? |
|---|---|
| task_id="task_A" vs task_id="task_B" | No (expected) ✅ |
| description="fix X" vs description="refactor X" | No (expected) ✅ |
| trace_id="tr_1" vs trace_id="tr_2" | No (expected) ✅ |

---

## 4. Operation Determinism by Type

| Operation | Always Produces Same Output? |
|---|---|
| bugfix | ✅ Yes |
| refactor | ✅ Yes |
| feature | ✅ Yes |
| review | ✅ Yes (always empty diff) |

---

## 5. Replay ID Propagation

The `replay_id` is propagated from input `metadata` to `CodeDiff.replay_id` without modification, enabling downstream `ReplayEngine` to reconstruct execution sequences correctly.

```
Input:  metadata.replay_id = "rp_001"
Output: result.replay_id  = "rp_001"  ✅
```
