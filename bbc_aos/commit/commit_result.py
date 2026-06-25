"""BBC-AOS CommitResult

Defines the structure of the commit operation result.
"""

from typing import Any, Dict, List


class CommitResult:
    """Immutable representation of a successful or dry-run commit result.

    Attributes:
        commit_hash: Deterministic SHA-256 commit hash.
        trace_id: Propagated trace identifier.
        replay_id: Propagated replay identifier.
        timestamp: Iso-formatted timestamp.
        status: SUCCESS or DRY_RUN.
        affected_files: Sorted list of modified/added/removed files.
    """

    __slots__ = (
        "commit_hash",
        "trace_id",
        "replay_id",
        "timestamp",
        "status",
        "affected_files",
    )

    def __init__(
        self,
        commit_hash: str,
        trace_id: str,
        replay_id: str,
        timestamp: str,
        status: str,
        affected_files: List[str],
    ) -> None:
        object.__setattr__(self, "commit_hash", commit_hash)
        object.__setattr__(self, "trace_id", trace_id)
        object.__setattr__(self, "replay_id", replay_id)
        object.__setattr__(self, "timestamp", timestamp)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "affected_files", sorted(list(set(affected_files))))

    def __setattr__(self, key: str, value: Any) -> None:
        raise AttributeError("CommitResult is immutable.")

    def to_dict(self) -> Dict[str, Any]:
        """Converts the CommitResult instance to a standard dictionary."""
        return {
            "commit_hash": self.commit_hash,
            "trace_id": self.trace_id,
            "replay_id": self.replay_id,
            "timestamp": self.timestamp,
            "status": self.status,
            "affected_files": self.affected_files,
        }
