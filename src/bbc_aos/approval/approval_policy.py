"""BBC-AOS ApprovalPolicy

Governs the routing of approval requests based on risk levels.
"""

import logging

logger = logging.getLogger("bbc_aos.approval.approval_policy")


class ApprovalPolicy:
    """Enforces risk-based human approval routing policies."""

    @staticmethod
    def get_initial_status(risk_level: str) -> str:
        """Determines the initial status of an approval request based on risk.

        Args:
            risk_level: Risk level (LOW/MEDIUM/HIGH/CRITICAL).

        Returns:
            The initial status string (APPROVED, PENDING, ESCALATED).
        """
        level = risk_level.upper()
        if level == "LOW":
            logger.info("ApprovalPolicy: LOW risk auto-approved.")
            return "APPROVED"
        elif level == "CRITICAL":
            logger.info("ApprovalPolicy: CRITICAL risk routed to ESCALATED status immediately.")
            return "ESCALATED"
        else:
            logger.info(f"ApprovalPolicy: {level} risk routed to PENDING human gate.")
            return "PENDING"
