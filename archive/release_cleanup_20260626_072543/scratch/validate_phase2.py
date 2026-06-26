import sys
import os
import json
import traceback

SCRATCH_DIR = os.path.dirname(os.path.abspath(__file__))
WIKI_ROOT = os.path.dirname(SCRATCH_DIR)

# Adjust path to import legacy and new packages
sys.path.insert(0, os.path.join(WIKI_ROOT, "Legacy_BBC"))
sys.path.insert(0, WIKI_ROOT)

print("[*] Phase 2 Validation Script Initialized.")

# 1 & 2. Syntax and Import Validation
try:
    print("[*] Step 1 & 2: Performing Import & Syntax Validation...")
    # Import legacy packages
    from bbc_core.symbol_extractor import SymbolExtractor as LegacyExtractor
    from bbc_core.symbol_graph import SymbolGraph as LegacyGraph
    from bbc_core.attribution_tracer import AttributionTracer as LegacyTracer
    
    # Import new packages
    from bbc_aos.knowledge.graph.symbol_extractor import SymbolExtractor as NewExtractor
    from bbc_aos.knowledge.graph.symbol_graph import SymbolGraph as NewGraph
    from bbc_aos.audit.attribution_tracer import AttributionTracer as NewTracer
    
    print("[+] Import & Syntax Validation: SUCCESS")
except Exception as e:
    print(f"[-] Import & Syntax Validation: FAILED\n{traceback.format_exc()}")
    sys.exit(1)

# Helpers for dict comparison
def dict_equals(d1, d2):
    return json.dumps(d1, sort_keys=True) == json.dumps(d2, sort_keys=True)

success = True

# 3. AST Extraction Equivalence Validation
print("[*] Step 3: AST Extraction Equivalence Check...")
try:
    target_file = os.path.join(WIKI_ROOT, "Legacy_BBC", "bbc_core", "bbc_scalar.py")
    
    legacy_ext = LegacyExtractor()
    new_ext = NewExtractor()
    
    leg_syms = legacy_ext.extract_from_file(target_file)
    new_syms = new_ext.extract_from_file(target_file)
    
    if leg_syms is None or new_syms is None:
        print("[-] AST Extraction: File not found or failed to parse")
        success = False
    else:
        leg_dict = leg_syms.to_dict()
        new_dict = new_syms.to_dict()
        
        # Override file path as absolute path representation could be slightly different
        leg_dict["file"] = "bbc_scalar.py"
        new_dict["file"] = "bbc_scalar.py"
        
        if dict_equals(leg_dict, new_dict):
            print("[+] AST Extraction Equivalence: SUCCESS")
        else:
            print("[-] AST Extraction Equismatch:")
            print("Legacy symbols count:", len(leg_dict.get("symbols", [])))
            print("Ported symbols count:", len(new_dict.get("symbols", [])))
            success = False
except Exception as e:
    print(f"[-] AST Extraction Equivalence: EXCEPTION\n{traceback.format_exc()}")
    success = False

# 4. Symbol Graph Equivalence Validation
print("[*] Step 4: Symbol Graph Equivalence Check...")
try:
    project_sub = os.path.join(WIKI_ROOT, "Legacy_BBC")
    
    # We will scan a smaller subset (e.g. bbc_core/bbc_scalar.py and bbc_core/matrix_ops.py) to compare call graphs
    # Generate FileSymbols list manually for the target files to avoid scan profile walks differences
    target_python_files = [
        os.path.join(project_sub, "bbc_core", "bbc_scalar.py"),
        os.path.join(project_sub, "bbc_core", "matrix_ops.py"),
    ]
    
    legacy_fs_list = [legacy_ext.extract_from_file(f) for f in target_python_files]
    new_fs_list = [new_ext.extract_from_file(f) for f in target_python_files]
    
    legacy_graph = LegacyGraph()
    new_graph = NewGraph()
    
    source_mapping = {}
    for f in target_python_files:
        with open(f, 'r', encoding='utf-8') as src_f:
            content = src_f.read()
            source_mapping[f] = content

    legacy_fs_dicts = [fs.to_dict() for fs in legacy_fs_list if fs is not None]
    new_fs_dicts = [fs.to_dict() for fs in new_fs_list if fs is not None]

    legacy_graph.build_from_symbols(legacy_fs_dicts, source_mapping)
    new_graph.build_from_symbols(new_fs_dicts, source_mapping)
    
    # Export and compare JSON outputs
    leg_out_path = os.path.join(SCRATCH_DIR, "leg_graph.json")
    new_out_path = os.path.join(SCRATCH_DIR, "new_graph.json")
    
    legacy_graph.export_to_json(leg_out_path)
    new_graph.export_to_json(new_out_path)
    
    with open(leg_out_path, 'r', encoding='utf-8') as f:
        leg_graph_data = json.load(f)
    with open(new_out_path, 'r', encoding='utf-8') as f:
        new_graph_data = json.load(f)
        
    # Compare unresolved count and stats
    if dict_equals(leg_graph_data, new_graph_data):
        print("[+] Symbol Graph Equivalence: SUCCESS")
    else:
        print("[-] Symbol Graph Equivalence: FAILED (mismatched structure)")
        print("Legacy stats:", leg_graph_data.get("graph_stats"))
        print("Ported stats:", new_graph_data.get("graph_stats"))
        success = False
        
    # Clean up temp files
    if os.path.exists(leg_out_path): os.remove(leg_out_path)
    if os.path.exists(new_out_path): os.remove(new_out_path)
except Exception as e:
    print(f"[-] Symbol Graph Equivalence: EXCEPTION\n{traceback.format_exc()}")
    success = False

# 5. Attribution Equivalence Validation
print("[*] Step 5: Attribution Equivalence Check...")
try:
    leg_tracer = LegacyTracer(project_sub)
    new_tracer = NewTracer(project_sub)
    
    # Scan project (target python files only to align references)
    leg_tracer.scan_project(target_extensions=('.py',))
    new_tracer.scan_project(target_extensions=('.py',))
    
    # Compare trace impact for matrix_ops.py
    leg_impact_raw = leg_tracer.trace_impact(os.path.normpath("bbc_core/bbc_scalar.py"))
    leg_impact = sorted([p.replace("\\", "/") for p in leg_impact_raw])
    
    new_impact_raw = new_tracer.trace_impact("bbc_core/bbc_scalar.py")
    new_impact = sorted([p.replace("\\", "/") for p in new_impact_raw])
    
    if leg_impact == new_impact:
        print("[+] Attribution Equivalence: SUCCESS")
    else:
        print(f"[-] Attribution Equivalence: FAILED. Legacy: {leg_impact}, Ported: {new_impact}")
        success = False
except Exception as e:
    print(f"[-] Attribution Equivalence: EXCEPTION\n{traceback.format_exc()}")
    success = False

# 6. Determinism Validation
print("[*] Step 6: Determinism Check...")
try:
    # Run symbol extractor twice and verify output
    run1 = new_ext.extract_from_file(target_file).to_dict()
    run2 = new_ext.extract_from_file(target_file).to_dict()
    
    if dict_equals(run1, run2):
        print("[+] Determinism check: SUCCESS")
    else:
        print("[-] Determinism check: FAILED")
        success = False
except Exception as e:
    print(f"[-] Determinism check: EXCEPTION\n{traceback.format_exc()}")
    success = False

if success:
    print("[+] Phase 2 Validation: ALL PASSED")
    sys.exit(0)
else:
    print("[-] Phase 2 Validation: FAILED")
    sys.exit(1)
