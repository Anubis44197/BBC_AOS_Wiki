from typing import Any, Dict

class AgentContext:
    """
    Encapsulates task execution scope parameters, validation constraints, and tracing metadata.
    """
    def __init__(
        self,
        task_id: str,
        context_data: Dict[str, Any],
        constraints: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> None:
        self.task_id: str = task_id
        self.context_data: Dict[str, Any] = context_data
        self.constraints: Dict[str, Any] = constraints
        self.metadata: Dict[str, Any] = metadata

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieves a configuration value from the context data."""
        return self.context_data.get(key, default)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the context wrapper to a dictionary payload."""
        return {
            "task_id": self.task_id,
            "context_data": self.context_data,
            "constraints": self.constraints,
            "metadata": self.metadata
        }
