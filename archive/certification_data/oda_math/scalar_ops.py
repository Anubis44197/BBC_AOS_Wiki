# ODA-MATH: Scalar Edge Cases and Mathematical Operations
def evaluate_scalars():
    val1 = 5.0
    val2 = -0.0
    val3 = 1e-15
    val4 = float('nan')
    val5 = float('inf')
    
    # Division by zero boundary
    div_zero = val1 / 0.0
    
    # Multiplications
    mult_neg_zero = val1 * val2
    
    # Underflow/overflow
    underflow = val3 * 1e-320
    overflow = 1e308 * 10.0
    
    return div_zero, mult_neg_zero, underflow, overflow
