"""Operational loop exceptions."""


class LoopOperationError(Exception):
    """Base class for operational loop failures."""


class InvalidLoopModeError(LoopOperationError):
    """Raised when an unknown loop rollout mode is requested."""


class InvalidLoopStateError(LoopOperationError):
    """Raised when a loop state transition is not allowed."""


class LoopBudgetExceededError(LoopOperationError):
    """Raised when a hard loop budget limit is exceeded."""


class UnknownLoopPatternError(LoopOperationError):
    """Raised when a loop pattern is not registered."""
