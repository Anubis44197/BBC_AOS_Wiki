class AgentException(Exception):
    """Base exception for all Agent Layer errors."""
    def __init__(self, message: str, error_code: int = -32000) -> None:
        super().__init__(message)
        self.error_code: int = error_code
        self.message: str = message

class InvalidRequestException(AgentException):
    """Exception raised when the RPC request violates message schemas."""
    def __init__(self, message: str = "Invalid Request") -> None:
        super().__init__(message, error_code=-32600)

class MethodNotFoundException(AgentException):
    """Exception raised when the called method is missing from allowlists."""
    def __init__(self, message: str = "Method Not Found") -> None:
        super().__init__(message, error_code=-32601)

class InvalidParamsException(AgentException):
    """Exception raised when parameters do not match schema constraints."""
    def __init__(self, message: str = "Invalid Params") -> None:
        super().__init__(message, error_code=-32602)

class SignatureVerificationException(AgentException):
    """Exception raised when the input signature verification fails."""
    def __init__(self, message: str = "Signature Verification Failure") -> None:
        super().__init__(message, error_code=-32001)

class SafetyBreachException(AgentException):
    """Exception raised when an action violates directory safety boundaries."""
    def __init__(self, message: str = "Safety Boundary Breach") -> None:
        super().__init__(message, error_code=-32002)

class StatePersistException(AgentException):
    """Exception raised when state persistence transactions fail."""
    def __init__(self, message: str = "State Persist Failure") -> None:
        super().__init__(message, error_code=-32003)
