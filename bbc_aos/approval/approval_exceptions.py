"""BBC-AOS Approval Subsystem Exceptions

Custom exceptions for the human approval gates subsystem.
"""

class ApprovalException(Exception):
    """Base exception for all approval subsystem errors."""
    pass


class InvalidTransitionException(ApprovalException):
    """Raised when an invalid state transition is attempted on an approval request."""
    pass


class ApprovalTimeoutException(ApprovalException):
    """Raised when an expired approval request is accessed or acted upon."""
    pass


class ApprovalPolicyException(ApprovalException):
    """Raised when an operation violates approval routing policies."""
    pass
