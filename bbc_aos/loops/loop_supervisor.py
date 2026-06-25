import os
import logging
from bbc_aos.loops.loop_budget import LoopBudget
from bbc_aos.loops.loop_policy import LoopPolicy
from bbc_aos.loops.loop_exceptions import LoopSafetyViolationException

logger = logging.getLogger("bbc_aos.loops.loop_supervisor")

class LoopSupervisor:
    """
    Supervisor daemon validating running loop budgets, state parameters, and directory safety.
    """
    def __init__(
        self,
        budget: LoopBudget,
        policy: LoopPolicy,
        workspace_root: str = r"C:\Users\90535\.gemini\antigravity\scratch\BBC_AOS_Wiki"
    ) -> None:
        self.budget: LoopBudget = budget
        self.policy: LoopPolicy = policy
        self.workspace_root: str = os.path.abspath(workspace_root)

    def validate_budgets(self) -> None:
        """
        Continuously validates active loop execution budget states.
        Triggers exceptions on hard budget violations.
        """
        self.budget.check_hard_limits()
        
        # Log warnings if soft limits are met
        warnings = self.budget.check_soft_limits()
        for limit_name, triggered in warnings.items():
            if triggered:
                logger.warning(f"[BUDGET WARNING] Soft limit reached for: {limit_name}")

    def validate_safety_sandbox(self, target_path: str) -> None:
        """
        Validates that file paths manipulated during execution remain within the sandbox.
        
        Args:
            target_path: The absolute or relative file path to check.
            
        Raises:
            LoopSafetyViolationException: If sandbox is breached.
        """
        abs_target = os.path.abspath(target_path)
        # Check if the target is outside workspace root directory
        if not abs_target.startswith(self.workspace_root):
            self.budget.record_safety_violation()
            error_msg = f"Path '{target_path}' breaches workspace sandbox root '{self.workspace_root}'"
            logger.error(f"[SAFETY VIOLATION] {error_msg}")
            raise LoopSafetyViolationException(error_msg)
