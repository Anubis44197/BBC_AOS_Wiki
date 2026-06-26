"""BBC-AOS ApprovalRequest

Defines the structure of an active or resolved human approval request.
"""

from typing import Any, Dict


class ApprovalRequest:
    """Represents a human approval gate transaction request.

    Attributes:
        approval_id: Unique approval request identifier.
        trace_id: Associated trace ID.
        replay_id: Associated replay ID.
        risk_level: Target risk level (LOW/MEDIUM/HIGH/CRITICAL).
        status: Current status (PENDING, APPROVED, REJECTED, EXPIRED, ESCALATED).
        commit_payload: Associated CodeDiff commit payload dictionary.
        timestamp: Iso-formatted timestamp.
    """

    __slots__ = (
        "approval_id",
        "trace_id",
        "replay_id",
        "risk_level",
        "status",
        "commit_payload",
        "timestamp",
    )

    def __init__(
        self,
        approval_id: str,
        trace_id: str,
        replay_id: str,
        risk_level: str,
        status: str,
        commit_payload: Dict[str, Any],
        timestamp: str,
    ) -> None:
        object.__setattr__(self, "approval_id", approval_id)
        object.__setattr__(self, "trace_id", trace_id)
        object.__setattr__(self, "replay_id", replay_id)
        object.__setattr__(self, "risk_level", risk_level)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "commit_payload", commit_payload)
        object.__setattr__(self, "timestamp", timestamp)

    def __setattr__(self, key: str, value: Any) -> None:
        # Custom helper allows modifying mutable status field while maintaining slot immutability on others
        if key == "status":
            object.__setattr__(self, "status", value)
        else:
            raise AttributeError("ApprovalRequest attributes (except status) are immutable.")

    def __deepcopy__(self, memo: Dict[int, Any]) -> "ApprovalRequest":
        import copy
        return ApprovalRequest(
            approval_id=self.approval_id,
            trace_id=self.trace_id,
            replay_id=self.replay_id,
            risk_level=self.risk_level,
            status=self.status,
            commit_payload=copy.deepcopy(self.commit_payload, memo),
            timestamp=self.timestamp,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Converts the instance properties into a plain dictionary."""
        return {
            "approval_id": self.approval_id,
            "trace_id": self.trace_id,
            "replay_id": self.replay_id,
            "risk_level": self.risk_level,
            "status": self.status,
            "commit_payload": self.commit_payload,
            "timestamp": self.timestamp,
        }
