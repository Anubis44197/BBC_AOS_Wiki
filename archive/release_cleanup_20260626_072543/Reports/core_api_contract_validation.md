# Core API Contract Validation Report - HMPU Governor

This report documents the verification checks performed to confirm that the public APIs, method signatures, return types, and object serialization contracts in the migrated HMPU Governor (`constraints_engine.py`) strictly adhere to legacy interface contracts.

---

## 1. Public API Verification

We validated that the public class `HMPU_Governor` exposes all legacy methods with identical callable parameters:

| Method Name | Required Parameters | Optional / Keyword Parameters | Return Type | Status |
| :--- | :--- | :--- | :--- | :--- |
| `__init__` | `self` | `weights_path`, `state_manager`, `heal_budget`, `session_heal_budget` | `None` | **Pass** |
| `get_field_stability` | `self` | None | `float` | **Pass** |
| `chaos_derivative_filter` | `self`, `stream` | `threshold` | `List[str]` | **Pass** |
| `aura_field_score` | `self`, `s`, `c`, `p` | None | `float` | **Pass** |
| `self_heal_protocol` | `self` | None | `int` | **Pass** |
| `aura_gradient_bend` | `self`, `delta`, `stability` | None | `None` | **Pass** |
| `pulse_perturbation_sim` | `self`, `current_aura`, `intent_magnitude`, `op_type` | None | `Dict[str, Any]` | **Pass** |
| `focus_projection` | `self`, `query_vec`, `target_vecs` | None | `List[str]` | **Pass** |

---

## 2. Serialization Contract Compliance

The Governor saves and loads its weight gradients to/from a local JSON file (`hmpu_weights.json`). We validated:
* **Sealing Compatibility:** The `_save_weights()` method serializes the 3x3 `BBCScalar` matrix utilizing `BBCEncoder`.
* **Deserialization Hook Integration:** The `_load_weights()` method reads the JSON file and uses `object_hook=bbc_hook` to correctly restore the custom `BBCScalar` class wrapper, value, and metadata.
* **Output Format Schema:** Verified that weights read by legacy code compile cleanly when deserialized by the ported code and vice versa.

---

## 3. Metrics Summary

* **API Compatibility Score:** $1.000$ (All public entry points matched).
* **Deterministic Replay Score:** $1.000$ (All operations yield identical results across replays).
