class LoopException(Exception):
    """Base exception for all Loop Engine runtime operations."""
    ERROR_CODE = -32000
    ERROR_MESSAGE = "Loop execution error"

    def __init__(self, message: str = None) -> None:
        super().__init__(message or self.ERROR_MESSAGE)


class LoopBudgetExceededException(LoopException):
    """Raised when resource budgets (tokens, time, iterations) are exhausted."""
    ERROR_CODE = -32001
    ERROR_MESSAGE = "Loop budget exceeded"


class LoopSafetyViolationException(LoopException):
    """Raised when safety limits or sandboxes are violated."""
    ERROR_CODE = -32002
    ERROR_MESSAGE = "Loop safety violation"


class LoopFrozenRegistryException(LoopException):
    """Raised when attempting to modify a frozen registry."""
    ERROR_CODE = -32003
    ERROR_MESSAGE = "Loop registry is frozen"


class LoopStateMachineException(LoopException):
    """Raised when invalid state transitions are attempted."""
    ERROR_CODE = -32004
    ERROR_MESSAGE = "Invalid state transition"


class LoopCheckpointException(LoopException):
    """Raised when checkpoint persistence or recovery fails."""
    ERROR_CODE = -32005
    ERROR_MESSAGE = "Loop checkpoint error"
