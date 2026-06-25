"""BBC-AOS Approval Subsystem Package

Exposes public classes and exceptions for risk-based human approval gates.
"""

from bbc_aos.approval.approval_manager import ApprovalManager
from bbc_aos.approval.approval_request import ApprovalRequest
from bbc_aos.approval.approval_result import ApprovalResult
from bbc_aos.approval.approval_policy import ApprovalPolicy
from bbc_aos.approval.approval_checkpoint import ApprovalCheckpoint
from bbc_aos.approval.approval_audit_log import ApprovalAuditLog
from bbc_aos.approval.approval_exceptions import (
    ApprovalException,
    InvalidTransitionException,
    ApprovalTimeoutException,
    ApprovalPolicyException,
)

__all__ = [
    "ApprovalManager",
    "ApprovalRequest",
    "ApprovalResult",
    "ApprovalPolicy",
    "ApprovalCheckpoint",
    "ApprovalAuditLog",
    "ApprovalException",
    "InvalidTransitionException",
    "ApprovalTimeoutException",
    "ApprovalPolicyException",
]
