import sys
import os
import json
import traceback
import time
import math

SCRATCH_DIR = os.path.dirname(os.path.abspath(__file__))
WIKI_ROOT = os.path.dirname(SCRATCH_DIR)

sys.path.insert(0, os.path.join(WIKI_ROOT, "Legacy_BBC"))
sys.path.insert(0, WIKI_ROOT)

print("[*] Phase 5A Validation Script Initialized.")

# Helper for dict comparison
def dict_equals(d1, d2):
    return json.dumps(d1, sort_keys=True) == json.dumps(d2, sort_keys=True)

success = True

# 1 & 2. Import & Syntax Validation
try:
    print("[*] Step 1 & 2: Performing Import & Syntax Validation...")
    from bbc_core.hmpu_core import HMPU_Governor as LegacyGovernor
    from bbc_aos.core.constraints_engine import HMPU_Governor as NewGovernor
    from bbc_aos.core.bbc_scalar import BBCScalar, STABLE, WEAK, UNSTABLE, DEGENERATE, NEG_ZERO
    from bbc_aos.memory.working.state_manager import StateManager
    
    print("[+] Import & Syntax Validation: SUCCESS")
except Exception as e:
    print(f"[-] Import & Syntax Validation: FAILED\n{traceback.format_exc()}")
    sys.exit(1)

# Paths for weights
leg_weights = os.path.join(SCRATCH_DIR, "leg_weights.json")
new_weights = os.path.join(SCRATCH_DIR, "new_weights.json")
if os.path.exists(leg_weights): os.remove(leg_weights)
if os.path.exists(new_weights): os.remove(new_weights)

# 3. Mathematical Equivalence Validation
print("[*] Step 3: Mathematical Equivalence Check...")
try:
    from bbc_aos.core.bbc_scalar import bbc_hook
    StateManager._reset_for_testing()
    leg_gov = LegacyGovernor(weights_path=leg_weights)
    new_gov = NewGovernor(weights_path=new_weights)
    
    # Check chaos density calculation
    test_signal = "Lorem ipsum dolor sit amet, consectetur adipiscing elit."
    leg_chaos = leg_gov._calculate_chaos(test_signal)
    new_chaos = new_gov._calculate_chaos(test_signal)
    
    chaos_match = abs(leg_chaos - new_chaos) < 1e-12
    
    # Check chaos derivative filter
    stream = ["hello world", "stable matrix calculation", "chaos density shift anomaly!!!", "normal code line"]
    leg_filtered = leg_gov.chaos_derivative_filter(stream, threshold=0.3)
    new_filtered = new_gov.chaos_derivative_filter(stream, threshold=0.3)
    
    filter_match = leg_filtered == new_filtered
    
    # Check stability condition numbers
    # Normalize time by mocking time.time() or ignoring it in comparison
    leg_stability = leg_gov.get_field_stability()
    new_stability = new_gov.get_field_stability()
    
    # The condition stability calculation includes: time.time() % 3600 / 3600000.0
    # Difference should be extremely small (reflecting only execution time difference)
    stability_match = abs(leg_stability - new_stability) < 1e-5
    
    # Check aura convergence score
    leg_score = leg_gov.aura_field_score(0.9, 0.2, 0.1)
    new_score = new_gov.aura_field_score(0.9, 0.2, 0.1)
    
    score_match = abs(leg_score - new_score) < 1e-12
    
    # Check focus projection (Operator 4)
    query_vec = [1.0, 0.0, 0.0]
    target_vecs = [
        {"name": "t1", "vec": [0.95, 0.05, 0.0]},
        {"name": "t2", "vec": [0.1, 0.1, 0.8]},
    ]
    leg_focused = leg_gov.focus_projection(query_vec, target_vecs)
    new_focused = new_gov.focus_projection(query_vec, target_vecs)
    
    focused_match = leg_focused == new_focused
    
    if chaos_match and filter_match and stability_match and score_match and focused_match:
        print("[+] Mathematical Equivalence: SUCCESS")
    else:
        print("[-] Mathematical Equivalence Mismatch:")
        print(f"Chaos: legacy={leg_chaos}, new={new_chaos} (Match: {chaos_match})")
        print(f"Filter: legacy={leg_filtered}, new={new_filtered} (Match: {filter_match})")
        print(f"Stability: legacy={leg_stability}, new={new_stability} (Match: {stability_match})")
        print(f"Field Score: legacy={leg_score}, new={new_score} (Match: {score_match})")
        print(f"Focus: legacy={leg_focused}, new={new_focused} (Match: {focused_match})")
        success = False
except Exception as e:
    print(f"[-] Mathematical Equivalence: EXCEPTION\n{traceback.format_exc()}")
    success = False

# 4. API Contract Validation
print("[*] Step 4: API Contract Check...")
try:
    required_methods = [
        "get_field_stability", "chaos_derivative_filter", "aura_field_score",
        "self_heal_protocol", "aura_gradient_bend", "pulse_perturbation_sim",
        "focus_projection"
    ]
    contract_ok = True
    for method in required_methods:
        if not hasattr(NewGovernor, method) or not callable(getattr(NewGovernor, method)):
            print(f"[-] API Contract: Method '{method}' is missing or not callable")
            contract_ok = False
            
    if contract_ok:
        print("[+] API Contract: SUCCESS")
    else:
        success = False
except Exception as e:
    print(f"[-] API Contract: EXCEPTION\n{traceback.format_exc()}")
    success = False

# 5. Determinism Validation
print("[*] Step 5: Determinism Check...")
try:
    # Run twice
    score_run1 = new_gov.aura_field_score(0.8, 0.4, 0.2)
    score_run2 = new_gov.aura_field_score(0.8, 0.4, 0.2)
    
    pert_run1 = new_gov.pulse_perturbation_sim(0.85, 0.2, "Refactor")
    pert_run2 = new_gov.pulse_perturbation_sim(0.85, 0.2, "Refactor")
    pert_run1["timestamp"] = 0.0
    pert_run2["timestamp"] = 0.0
    
    if score_run1 == score_run2 and dict_equals(pert_run1, pert_run2):
        print("[+] Determinism Check: SUCCESS")
    else:
        print("[-] Determinism Check: FAILED")
        success = False
except Exception as e:
    print(f"[-] Determinism Check: EXCEPTION\n{traceback.format_exc()}")
    success = False

# 6. Serialization Validation
print("[*] Step 6: Serialization Check...")
try:
    # Mutate weight to some state and save
    new_gov._Aura_Weights[0][0].state = WEAK
    new_gov._Aura_Weights[0][0].value = 0.05
    new_gov._save_weights()
    
    # Reload weights using both Legacy and New hooks
    with open(new_weights, 'r', encoding='utf-8') as f:
        leg_data_raw = json.load(f, object_hook=bbc_hook)
        
    # Re-verify that loaded object has correct structure
    load_success = isinstance(leg_data_raw[0][0], BBCScalar) and leg_data_raw[0][0].state == WEAK
    
    if load_success:
        print("[+] Serialization Check: SUCCESS")
    else:
        print("[-] Serialization Check: FAILED (failed to correctly parse hook objects)")
        success = False
except Exception as e:
    print(f"[-] Serialization Check: EXCEPTION\n{traceback.format_exc()}")
    success = False

# Clean up weights files
for f in [leg_weights, new_weights]:
    if os.path.exists(f):
        try: os.remove(f)
        except Exception: pass

# Calculate additional metrics
print("[*] Calculating Phase 5A Metrics...")
try:
    fidelity_score = 1.0 if score_match and chaos_match and focused_match else 0.0
    api_compat = 1.0 if contract_ok else 0.0
    replay_score = 1.0 if (score_run1 == score_run2) else 0.0
    
    print(f"    - Core Behavior Fidelity Score: {fidelity_score:.3f}")
    print(f"    - API Compatibility Score: {api_compat:.3f}")
    print(f"    - Deterministic Replay Score: {replay_score:.3f}")
except Exception as e:
    print(f"[-] Metric Calculations: EXCEPTION\n{traceback.format_exc()}")

if success:
    print("[+] Phase 5A Validation: ALL PASSED")
    sys.exit(0)
else:
    print("[-] Phase 5A Validation: FAILED")
    sys.exit(1)
