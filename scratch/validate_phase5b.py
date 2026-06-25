import sys
import os
import json
import traceback
import asyncio

SCRATCH_DIR = os.path.dirname(os.path.abspath(__file__))
WIKI_ROOT = os.path.dirname(SCRATCH_DIR)

sys.path.insert(0, os.path.join(WIKI_ROOT, "Legacy_BBC"))
sys.path.insert(0, WIKI_ROOT)

print("[*] Phase 5B Validation Script Initialized.")

# Helper for dict comparison
def dict_equals(d1, d2):
    return json.dumps(d1, sort_keys=True) == json.dumps(d2, sort_keys=True)

success = True

# 1 & 2. Import & Syntax Validation
try:
    print("[*] Step 1 & 2: Performing Import & Syntax Validation...")
    from bbc_core.hmpu_engine import HMPUEngine as LegacyEngine
    from bbc_aos.core.orchestrator import HMPUEngine as NewEngine
    from bbc_aos.core.orchestrator import (
        RecipeConstraint, BaseRecipe, CodeStructureRecipe,
        LogTelemetryRecipe, ConfigJsonRecipe, DocumentationRecipe, MultiRecipePipeline
    )
    from bbc_aos.memory.working.state_manager import StateManager
    
    print("[+] Import & Syntax Validation: SUCCESS")
except Exception as e:
    print(f"[-] Import & Syntax Validation: FAILED\n{traceback.format_exc()}")
    sys.exit(1)

# Paths for Golden Master
GM_DIR = os.path.join(SCRATCH_DIR, "golden_master")

# 3. Pipeline Equivalence & Golden Master Replay Suite
print("[*] Step 3 & 7: Executing Golden Master Replay Suite (Byte-by-Byte/Deep Equality Check)...")
try:
    # Reset state managers
    from bbc_core.state_manager import StateManager as LegacyStateManager
    LegacyStateManager._reset_for_testing()
    leg_sm = LegacyStateManager()
    leg_engine = LegacyEngine(leg_sm)
    
    StateManager._reset_for_testing()
    new_sm = StateManager()
    new_engine = NewEngine(new_sm)
    
    replays = ["code", "log", "config", "doc", "hybrid"]
    replay_count = 0
    replay_matched = 0
    
    for name in replays:
        ext = ".py" if name == "code" else ".log" if name == "log" else ".json" if name == "config" else ".md" if name == "doc" else ".txt"
        input_path = os.path.join(GM_DIR, f"input_{name}{ext}")
        legacy_path = os.path.join(GM_DIR, f"output_{name}_legacy.json")
        
        with open(input_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        with open(legacy_path, "r", encoding="utf-8") as f:
            legacy_output = json.load(f)
            
        # Run through new engine
        loop = asyncio.get_event_loop()
        new_output = loop.run_until_complete(new_engine.create_recipe(content))
        
        # Byte-for-byte / char-for-char string comparison of raw dumped JSON
        legacy_bytes = json.dumps(legacy_output, sort_keys=True, ensure_ascii=False).encode('utf-8')
        new_bytes = json.dumps(new_output, sort_keys=True, ensure_ascii=False).encode('utf-8')
        
        match = legacy_bytes == new_bytes
        replay_count += 1
        if match:
            replay_matched += 1
            print(f"    [+] Golden Master Replay '{name}': MATCH (Byte-for-byte equivalent)")
        else:
            print(f"    [-] Golden Master Replay '{name}': MISMATCH")
            print("Legacy keys:", list(legacy_output.keys()))
            print("New keys:", list(new_output.keys()))
            success = False
            
    pipeline_equivalence_ok = (replay_matched == replay_count)
    if pipeline_equivalence_ok:
        print("[+] Golden Master Replay Suite: SUCCESS")
    else:
        success = False
except Exception as e:
    print(f"[-] Golden Master Replay Suite: EXCEPTION\n{traceback.format_exc()}")
    success = False

# 4. API Contract Validation
print("[*] Step 4: API Contract Check...")
try:
    required_classes = [
        RecipeConstraint, BaseRecipe, CodeStructureRecipe,
        LogTelemetryRecipe, ConfigJsonRecipe, DocumentationRecipe, MultiRecipePipeline, NewEngine
    ]
    contract_ok = True
    for cls in required_classes:
        if not cls:
            print(f"[-] API Contract: Class '{cls.__name__}' is missing")
            contract_ok = False
            
    # Check HMPUEngine methods
    engine_methods = ["analyze_file", "create_recipe", "get_aura_confidence", "get_stats"]
    for method in engine_methods:
        if not hasattr(NewEngine, method) or not callable(getattr(NewEngine, method)):
            print(f"[-] API Contract: HMPUEngine method '{method}' is missing or not callable")
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
    # Run recipe creation twice on config input
    input_path = os.path.join(GM_DIR, "input_config.json")
    with open(input_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    loop = asyncio.get_event_loop()
    run1 = loop.run_until_complete(new_engine.create_recipe(content))
    run2 = loop.run_until_complete(new_engine.create_recipe(content))
    
    if dict_equals(run1, run2):
        print("[+] Determinism Check: SUCCESS")
    else:
        print("[-] Determinism Check: FAILED")
        success = False
except Exception as e:
    print(f"[-] Determinism Check: EXCEPTION\n{traceback.format_exc()}")
    success = False

# 6. Telemetry & State Manager Equivalence Validation
print("[*] Step 6: Telemetry Equivalence Check...")
try:
    # Reset stats
    LegacyStateManager._reset_for_testing()
    leg_sm2 = LegacyStateManager()
    leg_eng2 = LegacyEngine(leg_sm2)
    
    StateManager._reset_for_testing()
    new_sm2 = StateManager()
    new_eng2 = NewEngine(new_sm2)
    
    input_path = os.path.join(GM_DIR, "input_code.py")
    with open(input_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    loop = asyncio.get_event_loop()
    loop.run_until_complete(leg_eng2.create_recipe(content))
    loop.run_until_complete(new_eng2.create_recipe(content))
    
    leg_stats = leg_sm2.get_stats()
    new_stats = new_sm2.get_stats()
    
    # Ignore dynamic session ID
    leg_stats["session_id"] = "fixed"
    new_stats["session_id"] = "fixed"
    
    if dict_equals(leg_stats, new_stats):
        print("[+] Telemetry Equivalence Check: SUCCESS")
    else:
        print("[-] Telemetry Equivalence Mismatch:")
        print("Legacy stats:", leg_stats)
        print("New stats:", new_stats)
        success = False
except Exception as e:
    print(f"[-] Telemetry Equivalence: EXCEPTION\n{traceback.format_exc()}")
    success = False

# Calculate additional metrics
print("[*] Calculating Phase 5B Metrics...")
try:
    fidelity_score = 1.0 if pipeline_equivalence_ok and contract_ok else 0.0
    replay_accuracy = float(replay_matched / replay_count) if replay_count > 0 else 1.0
    e2e_deterministic = 1.0 if dict_equals(run1, run2) else 0.0
    telemetry_compat = 1.0 if dict_equals(leg_stats, new_stats) else 0.0
    
    print(f"    - Engine Behavior Fidelity Score: {fidelity_score:.3f}")
    print(f"    - Pipeline Replay Accuracy: {replay_accuracy:.3f}")
    print(f"    - End-to-End Deterministic Score: {e2e_deterministic:.3f}")
    print(f"    - Telemetry Compatibility Score: {telemetry_compat:.3f}")
except Exception as e:
    print(f"[-] Metric Calculations: EXCEPTION\n{traceback.format_exc()}")

if success:
    print("[+] Phase 5B Validation: ALL PASSED")
    sys.exit(0)
else:
    print("[-] Phase 5B Validation: FAILED")
    sys.exit(1)
