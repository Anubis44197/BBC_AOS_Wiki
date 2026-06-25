import sys
import os
import json
import traceback

SCRATCH_DIR = os.path.dirname(os.path.abspath(__file__))
WIKI_ROOT = os.path.dirname(SCRATCH_DIR)

# Adjust path to import legacy and new packages
sys.path.insert(0, os.path.join(WIKI_ROOT, "Legacy_BBC"))
sys.path.insert(0, WIKI_ROOT)

print("[*] Phase 3 Validation Script Initialized.")

# Helper for dict comparison
def dict_equals(d1, d2):
    return json.dumps(d1, sort_keys=True) == json.dumps(d2, sort_keys=True)

success = True

# 1 & 2. Import & Syntax Validation
try:
    print("[*] Step 1 & 2: Performing Import & Syntax Validation...")
    # Legacy Imports
    from bbc_core.context_optimizer import ContextOptimizer as LegacyOptimizer
    from bbc_core.context_compiler import TaskContextCompiler as LegacyCompiler
    from bbc_core.semantic_packer import SemanticPacker as LegacyPacker
    
    # New Imports
    from bbc_aos.core.context_optimizer import ContextOptimizer as NewOptimizer
    from bbc_aos.core.context_compiler import TaskContextCompiler as NewCompiler
    from bbc_aos.core.semantic_packer import SemanticPacker as NewPacker
    
    print("[+] Import & Syntax Validation: SUCCESS")
except Exception as e:
    print(f"[-] Import & Syntax Validation: FAILED\n{traceback.format_exc()}")
    sys.exit(1)

# Helper to load/generate symbol graph for Optimizer testing
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

graph_data = get_test_graph()
context_path = os.path.join(WIKI_ROOT, "Legacy_BBC", ".bbc", "bbc_context.json")

# 3. Context Reduction Equivalence Validation
print("[*] Step 3: Context Reduction Equivalence Check (ContextOptimizer)...")
try:
    legacy_opt = LegacyOptimizer(graph_data, min_reduction_ratio=0.0)
    new_opt = NewOptimizer(graph_data, min_reduction_ratio=0.0)
    
    # Run optimization for target symbol
    target_sym = "BBCScalar"
    leg_dec = legacy_opt.optimize(target_sym)
    new_dec = new_opt.optimize(target_sym)
    
    leg_dict = leg_dec.to_dict()
    new_dict = new_dec.to_dict()
    
    # Overwrite dynamic fields like file paths or times if they differ (they shouldn't)
    if dict_equals(leg_dict, new_dict):
        print("[+] Context Reduction Equivalence: SUCCESS")
    else:
        print("[-] Context Reduction Mismatch:")
        print("Legacy decision keys:", leg_dict.keys())
        print("New decision keys:", new_dict.keys())
        print("Legacy primary:", leg_dict.get("primary"))
        print("New primary:", new_dict.get("primary"))
        print("Legacy direct:", len(leg_dict.get("direct", [])))
        print("New direct:", len(new_dict.get("direct", [])))
        success = False
except Exception as e:
    print(f"[-] Context Reduction Equivalence: EXCEPTION\n{traceback.format_exc()}")
    success = False

# 4. Token Reduction Equivalence Validation
print("[*] Step 4: Token Reduction Equivalence Check (ContextCompiler)...")
try:
    legacy_comp = LegacyCompiler(context_path)
    new_comp = NewCompiler(context_path)
    
    comp_success = True
    for task in ["bugfix", "feature", "refactor", "review"]:
        leg_compiled = legacy_comp.compile(task, target_file="bbc_core/bbc_scalar.py")
        new_compiled = new_comp.compile(task, target_file="bbc_core/bbc_scalar.py")
        
        # Override volatile timestamp/generated_at field
        leg_compiled["generated_at"] = "fixed"
        new_compiled["generated_at"] = "fixed"
        
        if not dict_equals(leg_compiled, new_compiled):
            print(f"[-] Token Reduction Mismatch in profile '{task}'")
            comp_success = False
            
    if comp_success:
        print("[+] Token Reduction Equivalence: SUCCESS")
    else:
        success = False
except Exception as e:
    print(f"[-] Token Reduction Equivalence: EXCEPTION\n{traceback.format_exc()}")
    success = False

# 5. Semantic Packing Equivalence Validation
print("[*] Step 5: Semantic Packing Equivalence Check (SemanticPacker)...")
try:
    legacy_packer_safe = LegacyPacker(aggressive=False)
    new_packer_safe = NewPacker(aggressive=False)
    
    legacy_packer_aggr = LegacyPacker(aggressive=True)
    new_packer_aggr = NewPacker(aggressive=True)
    
    # Use bugfix compiled context for packing tests
    compiler = NewCompiler(context_path)
    compiled_ctx = compiler.compile("bugfix", target_file="bbc_core/bbc_scalar.py")
    
    leg_packed_safe = legacy_packer_safe.pack(compiled_ctx)
    new_packed_safe = new_packer_safe.pack(compiled_ctx)
    
    leg_packed_aggr = legacy_packer_aggr.pack(compiled_ctx)
    new_packed_aggr = new_packer_aggr.pack(compiled_ctx)
    
    # Compare safe packed results
    # Volatile fields inside metrics could differ due to timestamp, let's normalize generated_at
    leg_packed_safe["generated_at"] = "fixed"
    new_packed_safe["generated_at"] = "fixed"
    leg_packed_aggr["generated_at"] = "fixed"
    new_packed_aggr["generated_at"] = "fixed"
    
    if dict_equals(leg_packed_safe, new_packed_safe) and dict_equals(leg_packed_aggr, new_packed_aggr):
        print("[+] Semantic Packing Equivalence: SUCCESS")
    else:
        print("[-] Semantic Packing Mismatch:")
        print("Safe mode savings (Legacy/New):", leg_packed_safe["metrics"].get("packing_savings_pct"), new_packed_safe["metrics"].get("packing_savings_pct"))
        print("Aggressive mode savings (Legacy/New):", leg_packed_aggr["metrics"].get("packing_savings_pct"), new_packed_aggr["metrics"].get("packing_savings_pct"))
        success = False
except Exception as e:
    print(f"[-] Semantic Packing Equivalence: EXCEPTION\n{traceback.format_exc()}")
    success = False

# 6. Determinism Validation
print("[*] Step 6: Determinism Check...")
try:
    # Optimizer twice
    opt_run1 = new_opt.optimize("BBCScalar").to_dict()
    opt_run2 = new_opt.optimize("BBCScalar").to_dict()
    
    # Compiler twice
    comp_run1 = new_comp.compile("bugfix", target_file="bbc_core/bbc_scalar.py")
    comp_run2 = new_comp.compile("bugfix", target_file="bbc_core/bbc_scalar.py")
    comp_run1["generated_at"] = "fixed"
    comp_run2["generated_at"] = "fixed"
    
    # Packer twice
    pack_run1 = new_packer_safe.pack(comp_run1)
    pack_run2 = new_packer_safe.pack(comp_run1)
    
    if dict_equals(opt_run1, opt_run2) and dict_equals(comp_run1, comp_run2) and dict_equals(pack_run1, pack_run2):
        print("[+] Determinism Check: SUCCESS")
    else:
        print("[-] Determinism Check: FAILED")
        success = False
except Exception as e:
    print(f"[-] Determinism Check: EXCEPTION\n{traceback.format_exc()}")
    success = False

# Metric Calculations
print("[*] Calculating Validation Metrics...")
try:
    # Use feature task compiled and packed for metrics reporting
    test_compiled = new_comp.compile("feature", target_file="bbc_core/bbc_scalar.py")
    test_packed = new_packer_safe.pack(test_compiled)
    
    before_bytes = test_packed["metrics"]["packing_before_bytes"]
    after_bytes = test_packed["metrics"]["packing_after_bytes"]
    
    # Compression Ratio
    compression_ratio = after_bytes / before_bytes if before_bytes > 0 else 1.0
    print(f"    - Compression Ratio (Safe Mode): {compression_ratio:.3f} (Packed: {after_bytes} B / Unpacked: {before_bytes} B)")
    
    # Token Preservation Ratio
    original_tokens = test_compiled["metrics"]["full_context_tokens_est"]
    compiled_tokens = test_compiled["metrics"]["compiled_tokens_est"]
    token_preservation_ratio = compiled_tokens / original_tokens if original_tokens > 0 else 1.0
    print(f"    - Token Preservation Ratio (Compiler): {token_preservation_ratio:.3f} (Compiled: {compiled_tokens} t / Original: {original_tokens} t)")
    
    # Context Fidelity Score
    # Verify that the primary/target file ('bbc_core/bbc_scalar.py') and its direct dependencies are preserved in code_structure
    included_files = [recipe["path"] for recipe in test_compiled["code_structure"]]
    target_in_context = "bbc_core/bbc_scalar.py" in included_files
    # Check if direct dependencies of bbc_scalar are in included_files
    direct_deps = new_comp._get_direct_deps("bbc_core/bbc_scalar.py")
    deps_preserved = all(dep in included_files for dep in direct_deps)
    fidelity_score = 1.0 if (target_in_context and deps_preserved) else 0.5
    print(f"    - Context Fidelity Score: {fidelity_score:.1f} (Target & Dependencies intact)")
    
    # Hallucination Guard Compatibility
    # Verify that decision safety warnings exist and match legacy format
    decision = new_opt.optimize("BBCScalar")
    guard_compatible = len(decision.safety) > 0 and any("imzası korunmalı" in r for r in decision.safety)
    print(f"    - Hallucination Guard Compatibility: {'YES' if guard_compatible else 'NO'}")
except Exception as e:
    print(f"[-] Metric Calculations: EXCEPTION\n{traceback.format_exc()}")

if success:
    print("[+] Phase 3 Validation: ALL PASSED")
    sys.exit(0)
else:
    print("[-] Phase 3 Validation: FAILED")
    sys.exit(1)
