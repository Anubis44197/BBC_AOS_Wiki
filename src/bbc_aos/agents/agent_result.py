from typing import Any, Dict, Optional

class AgentResult:
    """
    Represents a JSON-RPC 2.0 response result wrapper.
    """
    def __init__(
        self,
        message_id: str,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[Dict[str, Any]] = None,
        jsonrpc: str = "2.0"
    ) -> None:
        self.jsonrpc: str = jsonrpc
        self.id: str = message_id
        self.result: Optional[Dict[str, Any]] = result
        self.error: Optional[Dict[str, Any]] = error

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the response payload to a dictionary representation."""
        payload = {
            "jsonrpc": self.jsonrpc,
            "id": self.id
        }
        if self.error is not None:
            payload["error"] = self.error
        else:
            payload["result"] = self.result or {}
        return payload

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentResult':
        """Deserializes a dictionary payload back to an AgentResult instance."""
        if "id" not in data:
            raise ValueError("Invalid JSON-RPC response format: missing ID")
        return cls(
            message_id=data["id"],
            result=data.get("result"),
            error=data.get("error"),
            jsonrpc=data.get("jsonrpc", "2.0")
        )
