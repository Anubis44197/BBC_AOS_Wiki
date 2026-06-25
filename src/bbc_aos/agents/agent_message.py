from typing import Any, Dict, Optional
import uuid

class AgentMessage:
    """
    Represents a JSON-RPC 2.0 message request with BBC extensions.
    """
    def __init__(
        self,
        method: str,
        params: Dict[str, Any],
        message_id: Optional[str] = None,
        jsonrpc: str = "2.0"
    ) -> None:
        self.jsonrpc: str = jsonrpc
        self.id: str = message_id or str(uuid.uuid4())
        self.method: str = method
        self.params: Dict[str, Any] = params

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the message request to a dictionary payload."""
        return {
            "jsonrpc": self.jsonrpc,
            "id": self.id,
            "method": self.method,
            "params": self.params
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentMessage':
        """Deserializes a dictionary payload back to an AgentMessage instance."""
        if "method" not in data or "params" not in data:
            raise ValueError("Invalid JSON-RPC request format")
        return cls(
            method=data["method"],
            params=data["params"],
            message_id=data.get("id"),
            jsonrpc=data.get("jsonrpc", "2.0")
        )
