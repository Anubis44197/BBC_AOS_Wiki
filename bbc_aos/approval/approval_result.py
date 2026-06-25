"""BBC-AOS ApprovalResult

Defines the structure of the approval resolution result.
"""

from typing import Any, Dict


class ApprovalResult:
    """Immutable representation of the approval request resolution.

    Attributes:
        approval_id: Associated approval request ID.
        approval_hash: Deterministic approval hash.
        status: Resolved status (APPROVED, REJECTED, EXPIRED, etc.).
        timestamp: Iso-formatted timestamp.
    """

    __slots__ = (
        "approval_id",
        "approval_hash",
        "status",
        "timestamp",
    )

    def __init__(
        self,
        approval_id: str,
        approval_hash: str,
        status: str,
        timestamp: str,
    ) -> None:
        object.__setattr__(self, "approval_id", approval_id)
        object.__setattr__(self, "approval_hash", approval_hash)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "timestamp", timestamp)

    def __setattr__(self, key: str, value: Any) -> None:
        raise AttributeError("ApprovalResult is immutable.")

    def to_dict(self) -> Dict[str, Any]:
        """Converts ApprovalResult properties into a dictionary."""
        return {
            "approval_id": self.approval_id,
            "approval_hash": self.approval_hash,
            "status": self.status,
            "timestamp": self.timestamp,
        }
