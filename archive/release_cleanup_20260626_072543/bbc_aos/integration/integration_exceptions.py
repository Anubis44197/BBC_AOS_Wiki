class IntegrationException(Exception):
    """Base exception for all integration subsystem operations."""
    ERROR_CODE = -32000
    ERROR_MESSAGE = "Integration error"

    def __init__(self, message: str = None) -> None:
        super().__init__(message or self.ERROR_MESSAGE)


class IntegrationFrozenRegistryException(IntegrationException):
    """Raised when trying to modify the subsystem registry after startup freeze."""
    ERROR_CODE = -32001
    ERROR_MESSAGE = "Subsystem registry is frozen"


class IntegrationValidationException(IntegrationException):
    """Raised when validation check fails on outputs or inputs."""
    ERROR_CODE = -32002
    ERROR_MESSAGE = "Validation boundary breach"


class IntegrationSyncException(IntegrationException):
    """Raised when synchronization or transaction validation fails."""
    ERROR_CODE = -32003
    ERROR_MESSAGE = "Integration synchronization failure"


class IntegrationLifecycleException(IntegrationException):
    """Raised when an invalid integration transition or startup sequence is attempted."""
    ERROR_CODE = -32004
    ERROR_MESSAGE = "Invalid integration lifecycle state"
