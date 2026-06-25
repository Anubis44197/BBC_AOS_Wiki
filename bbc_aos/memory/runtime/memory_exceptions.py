class MemoryException(Exception):
    """Base exception for all Memory subsystem runtime operations."""
    ERROR_CODE = -33000
    ERROR_MESSAGE = "Memory execution error"

    def __init__(self, message: str = None) -> None:
        super().__init__(message or self.ERROR_MESSAGE)


class MemoryFrozenRegistryException(MemoryException):
    """Raised when trying to modify the memory registry after startup."""
    ERROR_CODE = -33001
    ERROR_MESSAGE = "Memory registry is frozen"


class MemoryLifecycleException(MemoryException):
    """Raised when an invalid memory lifecycle state transition is attempted."""
    ERROR_CODE = -33002
    ERROR_MESSAGE = "Invalid memory lifecycle state transition"


class MemoryPromotionException(MemoryException):
    """Raised when a cross-layer promotion fails validation or lacks approval."""
    ERROR_CODE = -33003
    ERROR_MESSAGE = "Memory promotion failed"


class MemoryVisibilityException(MemoryException):
    """Raised when visibility constraints or scopes are breached."""
    ERROR_CODE = -33004
    ERROR_MESSAGE = "Memory visibility breach"


class MemoryConflictException(MemoryException):
    """Raised when write conflicts or duplicate indexing hashes are detected."""
    ERROR_CODE = -33005
    ERROR_MESSAGE = "Memory record conflict detected"
