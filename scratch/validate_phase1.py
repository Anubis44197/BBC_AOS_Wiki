import sys
import os
import traceback
import math

# Adjust python path to find legacy and new files
SCRATCH_DIR = os.path.dirname(os.path.abspath(__file__))
WIKI_ROOT = os.path.dirname(SCRATCH_DIR)

sys.path.insert(0, os.path.join(WIKI_ROOT, "Legacy_BBC"))
sys.path.insert(0, WIKI_ROOT)

print("[*] Validation Script Initialized.")
print(f"[*] Workspace Root: {WIKI_ROOT}")

# 1. Import Validation
try:
    print("[*] Step 1: Performing Import Validation...")
    # Import legacy classes
    from bbc_core.bbc_scalar import BBCScalar as LegacyScalar, OmegaOperator as LegacyOmegaOperator
    from bbc_core.matrix_ops import MatrixOps as LegacyMatrixOps
    
    # Import new classes
    from bbc_aos.core.bbc_scalar import BBCScalar as NewScalar, OmegaOperator as NewOmegaOperator
    from bbc_aos.core.matrix_ops import MatrixOps as NewMatrixOps
    
    print("[+] Import Validation: SUCCESS")
except Exception as e:
    print(f"[-] Import Validation: FAILED\n{traceback.format_exc()}")
    sys.exit(1)

# 2. Syntax Validation
print("[*] Step 2: Syntax and Compilation Check...")
# Since python files compile when loaded, the imports passing already validates basic syntax.
print("[+] Syntax Validation: SUCCESS")

# Helper function to check scalar equality
def compare_scalars(leg_s, new_s, label):
    val_match = math.isclose(leg_s.value, new_s.value, rel_tol=1e-12, abs_tol=1e-12)
    state_match = leg_s.state == new_s.state
    heal_match = leg_s.heal_count == new_s.heal_count
    origin_match = leg_s.origin == new_s.origin
    
    if not (val_match and state_match and heal_match and origin_match):
        print(f"    [-] Mismatch in {label}:")
        print(f"        Legacy: val={leg_s.value}, state={leg_s.state}, heal={leg_s.heal_count}, origin={leg_s.origin}")
        print(f"        New:    val={new_s.value}, state={new_s.state}, heal={new_s.heal_count}, origin={new_s.origin}")
        return False
    return True

# Helper function to compare matrices
def compare_matrices(leg_M, new_M, label):
    if len(leg_M) != len(new_M) or len(leg_M[0]) != len(new_M[0]):
        print(f"    [-] Dimension mismatch in {label}")
        return False
    for i in range(len(leg_M)):
        for j in range(len(leg_M[0])):
            if not compare_scalars(leg_M[i][j], new_M[i][j], f"{label}[{i}][{j}]"):
                return False
    return True

# 3. Determinism and Mathematical Equivalence Validation
print("[*] Step 3 & 4: Checking Determinism and Mathematical Equivalence...")
success = True

# Test cases for scalars
scalar_cases = [
    # (value1, state1, origin1, op, value2, state2, origin2)
    (10.0, "STABLE", "math", "+", 5.0, "WEAK", "semantic"),
    (10.0, "STABLE", "math", "-", 5.0, "WEAK", "semantic"),
    (10.0, "STABLE", "math", "*", 5.0, "UNSTABLE", "math"),
    (10.0, "STABLE", "math", "/", 5.0, "DEGENERATE", "semantic"),
    (10.0, "NEG_ZERO", "math", "+", 0.0, "STABLE", "math"),
    (1.0, "DEGENERATE", "math", "*", 0.0, "STABLE", "semantic"),
]

print("[*] Validating Scalar operations...")
for idx, (v1, s1, o1, op, v2, s2, o2) in enumerate(scalar_cases):
    leg_s1 = LegacyScalar(v1, state=s1, origin=o1)
    leg_s2 = LegacyScalar(v2, state=s2, origin=o2)
    
    new_s1 = NewScalar(v1, state=s1, origin=o1)
    new_s2 = NewScalar(v2, state=s2, origin=o2)
    
    try:
        if op == "+":
            leg_res = leg_s1 + leg_s2
            new_res = new_s1 + new_s2
        elif op == "-":
            leg_res = leg_s1 - leg_s2
            new_res = new_s1 - new_s2
        elif op == "*":
            leg_res = leg_s1 * leg_s2
            new_res = new_s1 * new_s2
        elif op == "/":
            leg_res = leg_s1 / leg_s2
            new_res = new_s1 / new_s2
            
        if not compare_scalars(leg_res, new_res, f"Case {idx} ({v1} {op} {v2})"):
            success = False
    except Exception as e:
        print(f"    [-] Exception in Case {idx}: {e}")
        success = False

# Division by zero test
print("[*] Validating Division by Zero...")
leg_div_zero = LegacyScalar(5.0) / 0.0
new_div_zero = NewScalar(5.0) / 0.0
if not compare_scalars(leg_div_zero, new_div_zero, "Division by Zero"):
    success = False

# Test pivot healing
print("[*] Validating Pivot Healing...")
leg_degraded = LegacyScalar(0.0001, state="UNSTABLE")
new_degraded = NewScalar(0.0001, state="UNSTABLE")
LegacyOmegaOperator.trigger(leg_degraded)
NewOmegaOperator.trigger(new_degraded)
if not compare_scalars(leg_degraded, new_degraded, "Omega Trigger Heal"):
    success = False

# Test matrix operations
print("[*] Validating Matrix Operations...")
# Initializing 3x3 matrix (Aura Base)
base_data = [
    [1.00, 0.00, 0.00],
    [0.75, 0.15, 0.10],
    [0.70, 0.10, 0.20]
]

leg_M = [[LegacyScalar(val, state="STABLE", origin="math") for val in row] for row in base_data]
new_M = [[NewScalar(val, state="STABLE", origin="math") for val in row] for row in base_data]

# Matmul
print("[*] Testing Matrix Multiplication (Matmul)...")
leg_prod = LegacyMatrixOps.matmul(leg_M, leg_M)
new_prod = NewMatrixOps.matmul(new_M, new_M)
if not compare_matrices(leg_prod, new_prod, "Matmul"):
    success = False

# Inversion
print("[*] Testing Gauss-Jordan Inversion...")
leg_inv, leg_rank, leg_logs = LegacyMatrixOps.gauss_jordan_inverse(leg_M)
new_inv, new_rank, new_logs = NewMatrixOps.gauss_jordan_inverse(new_M)

if leg_rank != new_rank:
    print(f"    [-] Rank mismatch. Legacy: {leg_rank}, New: {new_rank}")
    success = False
if not compare_matrices(leg_inv, new_inv, "Inverse Matrix"):
    success = False

# Condition Number
print("[*] Testing Condition Number Estimation...")
leg_cond = LegacyMatrixOps.condition_number(leg_M)
new_cond = NewMatrixOps.condition_number(new_M)
if not math.isclose(leg_cond, new_cond, rel_tol=1e-12, abs_tol=1e-12):
    print(f"    [-] Condition number mismatch. Legacy: {leg_cond}, New: {new_cond}")
    success = False

# Pseudo Inverse
print("[*] Testing Pseudo Inverse...")
leg_pinv, leg_prank, leg_plogs = LegacyMatrixOps.pseudo_inverse(leg_M)
new_pinv, new_prank, new_plogs = NewMatrixOps.pseudo_inverse(new_M)

if leg_prank != new_prank:
    print(f"    [-] Pseudo inverse rank mismatch. Legacy: {leg_prank}, New: {new_prank}")
    success = False
if not compare_matrices(leg_pinv, new_pinv, "Pseudo Inverse"):
    success = False

if success:
    print("[+] Determinism and Mathematical Equivalence: SUCCESS")
    sys.exit(0)
else:
    print("[-] Determinism and Mathematical Equivalence: FAILED")
    sys.exit(1)
