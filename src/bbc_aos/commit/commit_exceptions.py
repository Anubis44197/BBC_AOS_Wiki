"""BBC-AOS Commit Subsystem Exceptions

Custom exceptions for the deterministic commit pipeline.
"""

class CommitException(Exception):
    """Base exception for all commit pipeline errors."""
    pass


class ValidationFailureException(CommitException):
    """Raised when a verification verdict, sandbox check, or policy rule fails."""
    pass


class LimitExceededException(CommitException):
    """Raised when hard limits (max files or rollback depth) are exceeded."""
    pass


class RollbackException(CommitException):
    """Raised when a commit rollback operation fails."""
    pass
