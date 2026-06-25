from typing import Dict

class LoopBudget:
    """
    Tracks execution resource budgets for Loop Engine runs.
    Supports soft warning limits and hard exception-triggering limits.
    """
    def __init__(
        self,
        max_iterations: int = 5,
        warn_iterations: int = 4,
        max_tokens: int = 100000,
        warn_tokens: int = 80000,
        max_time_seconds: float = 60.0,
        warn_time_seconds: float = 45.0,
        max_safety_violations: int = 0
    ) -> None:
        # Hard limits
        self.max_iterations: int = max_iterations
        self.max_tokens: int = max_tokens
        self.max_time_seconds: float = max_time_seconds
        self.max_safety_violations: int = max_safety_violations

        # Soft limits
        self.warn_iterations: int = warn_iterations
        self.warn_tokens: int = warn_tokens
        self.warn_time_seconds: float = warn_time_seconds

        # Active counters
        self.current_iterations: int = 0
        self.current_tokens: int = 0
        self.current_time_seconds: float = 0.0
        self.current_safety_violations: int = 0

    def record_iteration(self) -> None:
        """Increments iteration counts."""
        self.current_iterations += 1

    def consume_tokens(self, count: int) -> None:
        """Records token consumption."""
        self.current_tokens += count

    def add_time(self, seconds: float) -> None:
        """Records elapsed execution time."""
        self.current_time_seconds += seconds

    def record_safety_violation(self) -> None:
        """Records safety violations."""
        self.current_safety_violations += 1

    def check_hard_limits(self) -> None:
        """
        Validates active counters against hard limits.
        
        Raises:
            LoopBudgetExceededException: If iterations, tokens, or time limits are breached.
            LoopSafetyViolationException: If safety boundaries are crossed.
        """
        from bbc_aos.loops.loop_exceptions import LoopBudgetExceededException, LoopSafetyViolationException

        if self.current_iterations > self.max_iterations:
            raise LoopBudgetExceededException(
                f"Iterations limit exceeded: {self.current_iterations} > {self.max_iterations}"
            )
        if self.current_tokens > self.max_tokens:
            raise LoopBudgetExceededException(
                f"Tokens limit exceeded: {self.current_tokens} > {self.max_tokens}"
            )
        if self.current_time_seconds > self.max_time_seconds:
            raise LoopBudgetExceededException(
                f"Execution time limit exceeded: {self.current_time_seconds}s > {self.max_time_seconds}s"
            )
        if self.current_safety_violations > self.max_safety_violations:
            raise LoopSafetyViolationException(
                f"Safety violations limit breached: {self.current_safety_violations} > {self.max_safety_violations}"
            )

    def check_soft_limits(self) -> Dict[str, bool]:
        """
        Checks counters against soft limit thresholds.
        
        Returns:
            Dict[str, bool]: Map of warnings triggered (True if threshold reached).
        """
        return {
            "iterations_warn": self.current_iterations >= self.warn_iterations,
            "tokens_warn": self.current_tokens >= self.warn_tokens,
            "time_warn": self.current_time_seconds >= self.warn_time_seconds,
        }
