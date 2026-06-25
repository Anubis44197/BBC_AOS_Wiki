import logging
from typing import List, Optional, Tuple
from .bbc_scalar import BBCScalar, UNSTABLE, DEGENERATE, OmegaOperator

# Set up structured logging for matrix operations
logger = logging.getLogger("bbc_aos.core.matrix_ops")

class MatrixOps:
    """
    MatrixOps implements linear algebra operations operating directly on BBCScalar objects.
    All mathematical operations, pivoting, and state healing protocols are preserved exactly.
    """

    @staticmethod
    def identity(n: int) -> List[List[BBCScalar]]:
        """
        Generates an n x n identity matrix containing BBCScalar elements.

        Args:
            n: Dimension of the square identity matrix.

        Returns:
            An n x n identity matrix represented as a list of lists.
        """
        return [[BBCScalar(1.0 if i == j else 0.0) for j in range(n)] for i in range(n)]

    @staticmethod
    def matmul(A: List[List[BBCScalar]], B: List[List[BBCScalar]]) -> List[List[BBCScalar]]:
        """
        Multiplies two matrices containing BBCScalar elements.

        Args:
            A: Left matrix of dimensions (rows_A x cols_A).
            B: Right matrix of dimensions (rows_B x cols_B).

        Returns:
            The product matrix of dimensions (rows_A x cols_B).

        Raises:
            ValueError: If matrix dimensions mismatch (cols_A != rows_B).
        """
        rows_A = len(A)
        cols_A = len(A[0])
        rows_B = len(B)
        cols_B = len(B[0])

        if cols_A != rows_B:
            logger.error(f"Dimension mismatch in matrix multiplication: A cols={cols_A}, B rows={rows_B}")
            raise ValueError("Matrix dimensions mismatch")

        result = [[BBCScalar(0.0) for _ in range(cols_B)] for _ in range(rows_A)]
        for i in range(rows_A):
            for j in range(cols_B):
                sum_val = BBCScalar(0.0)
                for k in range(cols_A):
                    sum_val = sum_val + (A[i][k] * B[k][j])
                result[i][j] = sum_val
        return result

    @staticmethod
    def gauss_jordan_inverse(matrix: List[List[BBCScalar]]) -> Tuple[Optional[List[List[BBCScalar]]], int, List[str]]:
        """
        Calculates the inverse of a square matrix using Gauss-Jordan elimination with partial pivoting
        and self-healing hooks.

        Args:
            matrix: Square input matrix of size n x n containing BBCScalar elements.

        Returns:
            A tuple of (inverse_matrix, rank, log_info) where:
                inverse_matrix: The calculated inverse matrix, or None if inversion failed.
                rank: The computed numerical rank of the matrix.
                log_info: List of logging strings detailing steps and warnings.
        """
        n = len(matrix)
        # Deep copy to augment
        M = [[BBCScalar(x.value, x.state, x.heal_count) for x in row] for row in matrix]
        eye_matrix = MatrixOps.identity(n)
        
        # Augment M with I -> [M | I]
        aug = [M[i] + eye_matrix[i] for i in range(n)]
        
        log_info: List[str] = []
        rank = n

        try:
            for i in range(n):
                # Partial pivoting
                pivot_idx = i
                max_val = abs(aug[i][i].value)
                for k in range(i + 1, n):
                    if abs(aug[k][i].value) > max_val:
                        max_val = abs(aug[k][i].value)
                        pivot_idx = k
                
                if max_val < 1e-9:  # Singular or near-singular
                    rank -= 1
                    msg = f"Singularity detected at col {i}, max_val {max_val}"
                    log_info.append(msg)
                    logger.warning(f"[GAUSS-JORDAN INVERSE WARNING] {msg}")
                    # If singular, we might not be able to fully invert, 
                    # but we continue to process what we can or return early.
                    # For strict inversion, this is a failure.
                    # We will mark it as rank deficient.
                    continue 
                
                # Swap rows
                aug[i], aug[pivot_idx] = aug[pivot_idx], aug[i]
                
                # Normalize pivot row
                pivot = aug[i][i]
                # Check for state issues and trigger healing
                if pivot.state in [UNSTABLE, DEGENERATE]:
                     OmegaOperator.trigger(pivot)
                     msg = f"Healed pivot at {i},{i}"
                     log_info.append(msg)
                     logger.info(f"[GAUSS-JORDAN INVERSE INFO] {msg}")
                     # Re-read value after heal
                     pivot = aug[i][i]

                # If pivot became 0 after heal (rare but possible), skip
                if abs(pivot.value) < 1e-12:
                    rank -= 1
                    continue

                for j in range(i, 2 * n):
                    aug[i][j] = aug[i][j] / pivot
                
                # Eliminate other rows
                for k in range(n):
                    if k != i:
                        factor = aug[k][i]
                        for j in range(i, 2 * n):
                            aug[k][j] = aug[k][j] - factor * aug[i][j]

        except Exception as e:
            msg = f"Gauss-Jordan failed: {str(e)}"
            log_info.append(msg)
            logger.error(f"[GAUSS-JORDAN INVERSE EXCEPTION] {msg}")
            return None, 0, log_info

        # Extract inverse
        inv = [row[n:] for row in aug]
        
        return inv, rank, log_info

    @staticmethod
    def pseudo_inverse(matrix: List[List[BBCScalar]]) -> Tuple[Optional[List[List[BBCScalar]]], int, List[str]]:
        """
        Calculates a simplified pseudo-inverse using left inverse formula: A^+ = (A^T * A)^-1 * A^T.

        Args:
            matrix: Input matrix of dimensions rows x cols containing BBCScalar elements.

        Returns:
            A tuple of (inverse_matrix, rank, log_info) where:
                inverse_matrix: The calculated pseudo-inverse, or None if inversion failed.
                rank: The computed numerical rank of the columns matrix.
                log_info: List of logging strings detailing steps and warnings.
        """
        try:
            # Transpose
            rows = len(matrix)
            cols = len(matrix[0])
            T = [[matrix[j][i] for j in range(rows)] for i in range(cols)]
            
            # A^T * A
            ATA = MatrixOps.matmul(T, matrix)
            
            # Inverse of ATA
            ATA_inv, rank, logs = MatrixOps.gauss_jordan_inverse(ATA)
            
            if ATA_inv is None or rank < cols:  # Assuming full column rank for left inverse
                 msg = "Pseudo-inverse failed at ATA inversion"
                 logger.error(f"[PSEUDO-INVERSE ERROR] {msg}")
                 return None, rank, logs + [msg]
                
            # Result = ATA_inv * A^T
            res = MatrixOps.matmul(ATA_inv, T)
            return res, rank, logs + ["Calculated pseudo-inverse"]
        except Exception as e:
             msg = f"Pseudo-inverse exception: {str(e)}"
             logger.error(f"[PSEUDO-INVERSE EXCEPTION] {msg}")
             return None, 0, [msg]

    @staticmethod
    def condition_number(matrix: List[List[BBCScalar]]) -> float:
        """
        Estimates the condition number of a square matrix based on the Infinity Norm.
        ||A||_inf * ||A^-1||_inf

        Args:
            matrix: Square input matrix containing BBCScalar elements.

        Returns:
            The calculated condition number (float), or infinity (float('inf')) if singular.
        """
        # Norm(A)
        norm_A = 0.0
        for row in matrix:
            row_sum = sum(abs(x.value) for x in row)
            if row_sum > norm_A:
                norm_A = row_sum
        
        # Inverse
        inv, rank, _ = MatrixOps.gauss_jordan_inverse(matrix)
        if not inv or rank < len(matrix):
            logger.info("[CONDITION NUMBER] Matrix is rank deficient or singular. Returning infinity.")
            return float('inf')
            
        # Norm(A^-1)
        norm_Inv = 0.0
        for row in inv:
            row_sum = sum(abs(x.value) for x in row)
            if row_sum > norm_Inv:
                norm_Inv = row_sum
                
        cond = norm_A * norm_Inv
        logger.debug(f"[CONDITION NUMBER] Estimated condition number: {cond}")
        return cond
