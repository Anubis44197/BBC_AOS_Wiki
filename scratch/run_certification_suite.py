import sys
import os
import json
import math
import asyncio
import traceback
import shutil

WIKI_ROOT = "C:/Users/90535/.gemini/antigravity/scratch/BBC_AOS_Wiki"
SCRATCH_DIR = os.path.dirname(os.path.abspath(__file__))

# Set path environment to load legacy and new packages
sys.path.insert(0, os.path.join(WIKI_ROOT, "Legacy_BBC"))
sys.path.insert(0, WIKI_ROOT)

from bbc_core.bbc_scalar import BBCScalar as LegacyScalar, STABLE, WEAK, SLEEPING, NEG_ZERO, SATURATED, UNSTABLE, DEGENERATE, OmegaOperator as LegacyOmegaOperator
from bbc_aos.core.bbc_scalar import BBCScalar as NewScalar, STABLE as N_STABLE, WEAK as N_WEAK, NEG_ZERO as N_NEG_ZERO, SATURATED as N_SATURATED, UNSTABLE as N_UNSTABLE, DEGENERATE as N_DEGENERATE, OmegaOperator as NewOmegaOperator

from bbc_core.matrix_ops import MatrixOps as LegacyMatrixOps
from bbc_aos.core.matrix_ops import MatrixOps as NewMatrixOps

from bbc_core.hallucination_guard import HallucinationGuard as LegacyHallucinationGuard

from bbc_core.context_optimizer import ContextOptimizer as LegacyOptimizer
from bbc_core.context_compiler import TaskContextCompiler as LegacyCompiler
from bbc_core.semantic_packer import SemanticPacker as LegacyPacker

from bbc_aos.core.context_optimizer import ContextOptimizer as NewOptimizer
from bbc_aos.core.context_compiler import TaskContextCompiler as NewCompiler
from bbc_aos.core.semantic_packer import SemanticPacker as NewPacker

from bbc_core.hmpu_engine import HMPUEngine as LegacyEngine
from bbc_aos.core.orchestrator import HMPUEngine as NewEngine

from bbc_aos.memory.working.state_manager import StateManager
from bbc_core.state_manager import StateManager as LegacyStateManager
from bbc_aos.memory.interfaces.file_state_storage import FileStateStorage

print("[*] Master Certification Suite Initialized.")

# Setup EPSILON for floating point comparison
EPSILON = 1e-12

def approx_equal(v1, v2):
    if math.isnan(v1) and math.isnan(v2):
        return True
    if math.isinf(v1) and math.isinf(v2):
        return (v1 > 0) == (v2 > 0)
    return abs(v1 - v2) < EPSILON

def scalar_equal(s1, s2):
    return approx_equal(s1.value, s2.value) and s1.state == s2.state and s1.heal_count == s2.heal_count

def matrix_equal(m1, m2):
    if m1 is None or m2 is None:
        return m1 == m2
    if len(m1) != len(m2) or len(m1[0]) != len(m2[0]):
        return False
    for r in range(len(m1)):
        for c in range(len(m1[0])):
            if not scalar_equal(m1[r][c], m2[r][c]):
                return False
    return True

def get_test_graph():
    from bbc_core.symbol_extractor import SymbolExtractor
    from bbc_core.symbol_graph import SymbolGraph
    
    project_sub = os.path.join(WIKI_ROOT, "Legacy_BBC")
    target_python_files = [
        os.path.join(project_sub, "bbc_core", "bbc_scalar.py"),
        os.path.join(project_sub, "bbc_core", "matrix_ops.py"),
    ]
    ext = SymbolExtractor()
    fs_list = [ext.extract_from_file(f) for f in target_python_files]
    fs_dicts = [fs.to_dict() for fs in fs_list if fs is not None]
    
    source_mapping = {}
    for f in target_python_files:
        with open(f, 'r', encoding='utf-8') as src_f:
            source_mapping[f] = src_f.read()
            
    graph = SymbolGraph()
    graph.build_from_symbols(fs_dicts, source_mapping)
    return graph.to_dict()

results = {
    "syntax_import_pass": True,
    "bbc_scalar_edge_states_pass": True,
    "matrix_certification_pass": True,
    "hallucination_guard_pass": True,
    "compression_certification_pass": True,
    "chaos_engineering_pass": True,
    "golden_master_pass": True,
    "deterministic_replay_pass": True,
    "metrics": {
        "deterministic_stability_score": 0.0,
        "replay_consistency_score": 0.0,
        "cross_module_fidelity_score": 0.0,
        "recovery_reliability_score": 0.0,
        "production_readiness_score": 0.0
    },
    "verdict": "NOT CERTIFIED"
}

# 1. BBCScalar Edge States Certification
print("\n[Scenario 1] Certifying BBCScalar Edge States...")
try:
    edge_values = [
        (-0.0, NEG_ZERO),
        (1e308 * 10.0, SATURATED),
        (0.0, DEGENERATE),
        (0.0, UNSTABLE),
        (float('nan'), STABLE),
        (float('inf'), STABLE),
        (-float('inf'), STABLE),
        (1.5e-323, STABLE)  # Underflow
    ]
    
    scalar_ok = True
    for val, init_state in edge_values:
        s_leg = LegacyScalar(val, state=init_state)
        s_new = NewScalar(val, state=init_state)
        
        # Test basic addition
        add_leg = s_leg + 5.0
        add_new = s_new + 5.0
        if not scalar_equal(add_leg, add_new):
            print(f"[-] Scalar mismatch on addition (val={val}, state={init_state})")
            print(f"    Legacy: {add_leg}, New: {add_new}")
            scalar_ok = False
            
        # Test division by zero
        div_leg = s_leg / 0.0
        div_new = s_new / 0.0
        if not scalar_equal(div_leg, div_new):
            print(f"[-] Scalar mismatch on div by zero (val={val}, state={init_state})")
            scalar_ok = False
            
        # Test healing
        heal_leg = LegacyOmegaOperator.trigger(s_leg)
        heal_new = NewOmegaOperator.trigger(s_new)
        if not scalar_equal(heal_leg, heal_new):
            print(f"[-] Scalar mismatch on Omega trigger (val={val}, state={init_state})")
            scalar_ok = False
            
    if scalar_ok:
        print("[+] BBCScalar Edge States: PASS")
    else:
        results["bbc_scalar_edge_states_pass"] = False
except Exception as e:
    print(f"[-] BBCScalar Edge States Exception:\n{traceback.format_exc()}")
    results["bbc_scalar_edge_states_pass"] = False

# 2. Matrix Certification
print("\n[Scenario 2] Certifying Matrix Operations...")
try:
    matrix_ok = True
    # A. Singular Matrix
    sing_leg = [[LegacyScalar(1.0), LegacyScalar(2.0)], [LegacyScalar(2.0), LegacyScalar(4.0)]]
    sing_new = [[NewScalar(1.0), NewScalar(2.0)], [NewScalar(2.0), NewScalar(4.0)]]
    
    inv_leg, r_leg, logs_leg = LegacyMatrixOps.gauss_jordan_inverse(sing_leg)
    inv_new, r_new, logs_new = NewMatrixOps.gauss_jordan_inverse(sing_new)
    if not matrix_equal(inv_leg, inv_new) or r_leg != r_new:
        print("[-] Singular Matrix Gauss-Jordan Mismatch")
        matrix_ok = False
        
    p_inv_leg, pr_leg, plogs_leg = LegacyMatrixOps.pseudo_inverse(sing_leg)
    p_inv_new, pr_new, plogs_new = NewMatrixOps.pseudo_inverse(sing_new)
    if not matrix_equal(p_inv_leg, p_inv_new) or pr_leg != pr_new:
        print("[-] Singular Matrix Pseudo Inverse Mismatch")
        matrix_ok = False
        
    cond_leg = LegacyMatrixOps.condition_number(sing_leg)
    cond_new = NewMatrixOps.condition_number(sing_new)
    if not approx_equal(cond_leg, cond_new):
        print(f"[-] Condition number mismatch: Legacy={cond_leg}, New={cond_new}")
        matrix_ok = False

    # B. Near Singular Matrix (High condition number)
    near_sing_leg = [[LegacyScalar(1.0), LegacyScalar(1.0)], [LegacyScalar(1.0), LegacyScalar(1.0000000001)]]
    near_sing_new = [[NewScalar(1.0), NewScalar(1.0)], [NewScalar(1.0), NewScalar(1.0000000001)]]
    
    inv_leg_ns, r_leg_ns, _ = LegacyMatrixOps.gauss_jordan_inverse(near_sing_leg)
    inv_new_ns, r_new_ns, _ = NewMatrixOps.gauss_jordan_inverse(near_sing_new)
    if not matrix_equal(inv_leg_ns, inv_new_ns) or r_leg_ns != r_new_ns:
        print("[-] Near-Singular Gauss-Jordan Mismatch")
        matrix_ok = False
        
    cond_leg_ns = LegacyMatrixOps.condition_number(near_sing_leg)
    cond_new_ns = NewMatrixOps.condition_number(near_sing_new)
    if not approx_equal(cond_leg_ns, cond_new_ns):
        print(f"[-] Near-Singular Condition Number Mismatch")
        matrix_ok = False
        
    # C. Pivot Healing
    heal_mat_leg = [[LegacyScalar(1e-10, state=UNSTABLE), LegacyScalar(2.0)], [LegacyScalar(2.0), LegacyScalar(4.0)]]
    heal_mat_new = [[NewScalar(1e-10, state=UNSTABLE), NewScalar(2.0)], [NewScalar(2.0), NewScalar(4.0)]]
    
    h_inv_leg, hr_leg, _ = LegacyMatrixOps.gauss_jordan_inverse(heal_mat_leg)
    h_inv_new, hr_new, _ = NewMatrixOps.gauss_jordan_inverse(heal_mat_new)
    if not matrix_equal(h_inv_leg, h_inv_new) or hr_leg != hr_new:
        print("[-] Gauss-Jordan Inverse with Pivot Healing Mismatch")
        matrix_ok = False

    if matrix_ok:
        print("[+] Matrix Operations: PASS")
    else:
        results["matrix_certification_pass"] = False
except Exception as e:
    print(f"[-] Matrix Certification Exception:\n{traceback.format_exc()}")
    results["matrix_certification_pass"] = False

# 3. Hallucination Guard Certification
print("\n[Scenario 3] Certifying Hallucination Guard Invariants...")
try:
    mock_context_data = {
        "code_structure": [
            {
                "path": "django_repo/models.py",
                "structure": {
                    "classes": ["Article"],
                    "functions": ["__str__", "is_recently_published"],
                    "imports": ["models"]
                }
            }
        ]
    }
    
    mock_ctx_path = os.path.join(SCRATCH_DIR, "mock_context.json")
    with open(mock_ctx_path, "w", encoding="utf-8") as f:
        json.dump(mock_context_data, f)
        
    guard = LegacyHallucinationGuard(mock_ctx_path)
    
    # Check 1: Unknown symbols
    code_unknown = """def my_view(request):
    obj = Article()
    fake_func_call(obj) # unknown function
"""
    ref_symbols = guard._extract_referenced_symbols(code_unknown)
    unknown_syms = [s for s in ref_symbols if s not in guard.known_symbols and s != "Article" and s != "my_view"]
    
    # Check 2: Speculative patterns
    speculative_code = """# I think this code probably works
def run():
    pass
"""
    entropy = guard._calculate_chaos(speculative_code)
    
    guard_ok = ("fake_func_call" in unknown_syms) and (entropy > 0.0)
    
    if os.path.exists(mock_ctx_path):
        os.remove(mock_ctx_path)
        
    if guard_ok:
        print("[+] Hallucination Guard Invariants: PASS")
    else:
        print("[-] Hallucination Guard Mismatch in symbol extraction or chaos estimation")
        results["hallucination_guard_pass"] = False
except Exception as e:
    print(f"[-] Hallucination Guard Exception:\n{traceback.format_exc()}")
    results["hallucination_guard_pass"] = False

# 4. Compression and Token Reduction Certification
print("\n[Scenario 4] Certifying Compression & Token Reduction Parity...")
try:
    legacy_context_file = os.path.join(WIKI_ROOT, "Legacy_BBC", ".bbc", "bbc_context.json")
    
    graph_data = get_test_graph()
    leg_opt = LegacyOptimizer(graph_data, min_reduction_ratio=0.0)
    new_opt = NewOptimizer(graph_data, min_reduction_ratio=0.0)
    
    leg_comp = LegacyCompiler(legacy_context_file)
    new_comp = NewCompiler(legacy_context_file)
    
    leg_packer = LegacyPacker(aggressive=True)
    new_packer = NewPacker(aggressive=True)
    
    comp_ok = True
    for task in ["bugfix", "feature"]:
        leg_c = leg_comp.compile(task, target_file="bbc_core/bbc_scalar.py")
        new_c = new_comp.compile(task, target_file="bbc_core/bbc_scalar.py")
        
        leg_c["generated_at"] = "fixed"
        new_c["generated_at"] = "fixed"
        
        leg_p = leg_packer.pack(leg_c)
        new_p = new_packer.pack(new_c)
        
        leg_p["generated_at"] = "fixed"
        new_p["generated_at"] = "fixed"
        
        if json.dumps(leg_p, sort_keys=True) != json.dumps(new_p, sort_keys=True):
            print(f"[-] Compression mismatch on profile '{task}'")
            comp_ok = False
            
    if comp_ok:
        print("[+] Compression & Token Reduction Parity: PASS")
    else:
        results["compression_certification_pass"] = False
except Exception as e:
    print(f"[-] Compression Certification Exception:\n{traceback.format_exc()}")
    results["compression_certification_pass"] = False

# 5. Chaos Engineering Certification
print("\n[Scenario 5] Certifying Chaos Engineering / Robustness...")
try:
    chaos_ok = True
    
    # A. Corrupted state file load test
    corrupt_state_dir = os.path.join(SCRATCH_DIR, "corrupt_state_dir")
    os.makedirs(corrupt_state_dir, exist_ok=True)
    
    corrupt_file_path = os.path.join(corrupt_state_dir, "corrupt_sess_state.json")
    with open(corrupt_file_path, "w", encoding="utf-8") as f:
        f.write("{invalid_json_format...")
        
    storage = FileStateStorage(base_dir=corrupt_state_dir)
    StateManager._reset_for_testing()
    sm = StateManager(storage=storage)
    sm.session_id = "corrupt_sess"
    
    loaded = storage.load_state("corrupt_sess")
    if loaded is not None:
        print("[-] Corrupted state load didn't return None")
        chaos_ok = False
        
    # B. Disk write failure simulation
    class FailingStorage(FileStateStorage):
        def save_state(self, session_id: str, state_data: dict) -> None:
            raise IOError("Disk write simulation failure")
            
    fail_state_dir = os.path.join(SCRATCH_DIR, "fail_state_dir")
    os.makedirs(fail_state_dir, exist_ok=True)
    
    try:
        sm_fail = StateManager(storage=FailingStorage(base_dir=fail_state_dir))
        loop = asyncio.get_event_loop()
        new_engine = NewEngine(sm_fail)
        loop.run_until_complete(new_engine.create_recipe("print('hello')"))
    except Exception as e:
        print(f"[-] Disk write failure triggered unhandled crash: {e}")
        chaos_ok = False
        
    try:
        shutil.rmtree(corrupt_state_dir, ignore_errors=True)
        shutil.rmtree(fail_state_dir, ignore_errors=True)
    except Exception as e:
        print(f"[Warning] Failed to clean up temp directories: {e}")
        
    if chaos_ok:
        print("[+] Chaos Engineering / Robustness: PASS")
    else:
        results["chaos_engineering_pass"] = False
except Exception as e:
    print(f"[-] Chaos Engineering Exception:\n{traceback.format_exc()}")
    results["chaos_engineering_pass"] = False

# 6. Golden Master Replay Suite
print("\n[Scenario 6] Running Golden Master Replay Suite...")
try:
    GM_DIR = os.path.join(WIKI_ROOT, "scratch", "golden_master")
    replays = ["code", "log", "config", "doc", "hybrid"]
    gm_ok = True
    
    LegacyStateManager._reset_for_testing()
    leg_sm = LegacyStateManager()
    leg_eng = LegacyEngine(leg_sm)
    
    StateManager._reset_for_testing()
    new_sm = StateManager()
    new_eng = NewEngine(new_sm)
    
    loop = asyncio.get_event_loop()
    
    for name in replays:
        ext = ".py" if name == "code" else ".log" if name == "log" else ".json" if name == "config" else ".md" if name == "doc" else ".txt"
        input_path = os.path.join(GM_DIR, f"input_{name}{ext}")
        legacy_path = os.path.join(GM_DIR, f"output_{name}_legacy.json")
        
        with open(input_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        with open(legacy_path, "r", encoding="utf-8") as f:
            legacy_output = json.load(f)
            
        new_output = loop.run_until_complete(new_eng.create_recipe(content))
        
        leg_str = json.dumps(legacy_output, sort_keys=True, ensure_ascii=False)
        new_str = json.dumps(new_output, sort_keys=True, ensure_ascii=False)
        
        if leg_str != new_str:
            print(f"[-] Golden Master Replay Mismatch on '{name}'")
            gm_ok = False
            
    if gm_ok:
        print("[+] Golden Master Replay Suite: PASS")
    else:
        results["golden_master_pass"] = False
except Exception as e:
    print(f"[-] Golden Master Exception:\n{traceback.format_exc()}")
    results["golden_master_pass"] = False

# 7. 100-Run Deterministic Replay on Dataset Files
print("\n[Scenario 7] Executing 100-Iteration Deterministic Replay Runs...")
try:
    datasets_dir = os.path.join(SCRATCH_DIR, "certification_data")
    test_files = [
        os.path.join(datasets_dir, "oda_math", "scalar_ops.py"),
        os.path.join(datasets_dir, "wikipedia", "ai_article.md"),
        os.path.join(datasets_dir, "django_repo", "views.py"),
        os.path.join(datasets_dir, "mixed_polyglot", "runner.py")
    ]
    
    det_ok = True
    loop = asyncio.get_event_loop()
    
    for filepath in test_files:
        if not os.path.exists(filepath):
            print(f"[-] Test file missing: {filepath}")
            det_ok = False
            continue
            
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            
        prev_output_str = None
        for run_idx in range(100):
            StateManager._reset_for_testing()
            sm_iter = StateManager()
            eng_iter = NewEngine(sm_iter)
            
            output = loop.run_until_complete(eng_iter.create_recipe(content))
            output_str = json.dumps(output, sort_keys=True, ensure_ascii=False)
            
            if prev_output_str is not None and output_str != prev_output_str:
                print(f"[-] Non-determinism detected on {filepath} at iteration {run_idx}")
                det_ok = False
                break
            prev_output_str = output_str
            
    if det_ok:
        print("[+] 100-Iteration Deterministic Replay Runs: PASS")
    else:
        results["deterministic_replay_pass"] = False
except Exception as e:
    print(f"[-] Deterministic Replay Exception:\n{traceback.format_exc()}")
    results["deterministic_replay_pass"] = False

# Calculate Certification Scores
print("\n[Score Calculation] Computing Certification Metrics...")
try:
    scores = results["metrics"]
    scores["deterministic_stability_score"] = 1.0 if results["deterministic_replay_pass"] else 0.0
    scores["replay_consistency_score"] = 1.0 if results["golden_master_pass"] else 0.0
    scores["cross_module_fidelity_score"] = 1.0 if results["compression_certification_pass"] and results["matrix_certification_pass"] else 0.5
    scores["recovery_reliability_score"] = 1.0 if results["chaos_engineering_pass"] else 0.0
    
    metric_keys = [
        "deterministic_stability_score",
        "replay_consistency_score",
        "cross_module_fidelity_score",
        "recovery_reliability_score"
    ]
    avg_score = sum(scores[k] for k in metric_keys) / len(metric_keys)
    scores["production_readiness_score"] = avg_score
    
    print(f"    - Deterministic Stability Score: {scores['deterministic_stability_score']:.3f}")
    print(f"    - Replay Consistency Score: {scores['replay_consistency_score']:.3f}")
    print(f"    - Cross-Module Fidelity Score: {scores['cross_module_fidelity_score']:.3f}")
    print(f"    - Recovery Reliability Score: {scores['recovery_reliability_score']:.3f}")
    print(f"    - Production Readiness Score: {scores['production_readiness_score']:.3f}")
    
    # Certification Verdict
    all_passed = (
        results["bbc_scalar_edge_states_pass"] and
        results["matrix_certification_pass"] and
        results["hallucination_guard_pass"] and
        results["compression_certification_pass"] and
        results["chaos_engineering_pass"] and
        results["golden_master_pass"] and
        results["deterministic_replay_pass"]
    )
    
    if all_passed:
        results["verdict"] = "CERTIFIED"
        print("\n==============================================")
        print("    FINAL VERDICT: CERTIFIED (100% Equivalence)")
        print("==============================================")
    else:
        results["verdict"] = "NOT CERTIFIED"
        print("\n==============================================")
        print("    FINAL VERDICT: NOT CERTIFIED (Behavioral Drift)")
        print("==============================================")
        
except Exception as e:
    print(f"[-] Score calculation failed: {e}")

# Save JSON results
output_results_path = os.path.join(SCRATCH_DIR, "certification_results.json")
with open(output_results_path, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=4)
print(f"[*] Saved results summary to: {output_results_path}")

if results["verdict"] == "CERTIFIED":
    sys.exit(0)
else:
    sys.exit(1)
