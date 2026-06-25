# ODA-MATH: Matrix Operations and Singularities
def matrix_calculations():
    # Full rank matrix A
    A = [
        [1.0, 0.0, 0.0],
        [0.75, 0.15, 0.10],
        [0.70, 0.10, 0.20]
    ]
    
    # Singular matrix B
    B = [
        [1.0, 2.0, 3.0],
        [2.0, 4.0, 6.0],
        [3.0, 6.0, 9.0]
    ]
    
    # Near-singular matrix C (high condition number)
    C = [
        [1.0, 1.0],
        [1.0, 1.0000000001]
    ]
    
    return A, B, C
