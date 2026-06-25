from typing import Dict, Any

class LoopPolicy:
    """
    Defines configuration parameters and recovery rules for Loop Engine execution.
    Includes retry limits, timeouts, escalation conditions, approval behaviors, and rollback actions.
    """
    def __init__(
        self,
        max_retries: int = 3,
        timeout_seconds: float = 60.0,
        escalation_threshold: int = 3,
        rollback_on_failure: bool = True,
        approval_mode: str = "MANDATORY"  # Allowed: MANDATORY, OPTIONAL, TIMEOUT
    ) -> None:
        # Retry Policy parameters
        self.max_retries: int = max_retries
        self.retry_triggers = {"SYNTAX_ERROR", "SCHEMA_VALIDATION_ERROR"}

        # Timeout Policy parameters
        self.timeout_seconds: float = timeout_seconds

        # Escalation Policy parameters
        self.escalation_threshold: int = escalation_threshold

        # Rollback Policy parameters
        self.rollback_on_failure: bool = rollback_on_failure

        # Approval Policy parameters
        # Support mandatory approval, optional approval, timeout approval
        if approval_mode not in {"MANDATORY", "OPTIONAL", "TIMEOUT"}:
            raise ValueError(f"Invalid approval mode: {approval_mode}")
        self.approval_mode: str = approval_mode

    def should_retry(self, attempt_count: int, error_type: str) -> bool:
        """Determines if a retry attempt should be scheduled."""
        return attempt_count < self.max_retries and error_type in self.retry_triggers

    def should_escalate(self, attempt_count: int) -> bool:
        """Determines if the execution failures warrant escalation."""
        return attempt_count >= self.escalation_threshold

    def should_rollback(self) -> bool:
        """Determines if rollback should execute on iteration failure."""
        return self.rollback_on_failure
