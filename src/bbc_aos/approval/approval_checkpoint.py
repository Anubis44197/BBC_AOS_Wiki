"""BBC-AOS ApprovalCheckpoint

Provides snapshots of approval gate requests for transaction recovery.
"""

import copy
import logging
from typing import Dict
from bbc_aos.approval.approval_request import ApprovalRequest

logger = logging.getLogger("bbc_aos.approval.approval_checkpoint")


class ApprovalCheckpoint:
    """Saves immutable snapshots of all active approval requests."""

    def __init__(self, checkpoint_id: str, timestamp: str) -> None:
        """Initializes ApprovalCheckpoint.

        Args:
            checkpoint_id: Unique checkpoint ID.
            timestamp: Iso-formatted timestamp.
        """
        self.checkpoint_id: str = checkpoint_id
        self.timestamp: str = timestamp
        # Snapshotted copies of approval requests map
        self.requests_snapshot: Dict[str, ApprovalRequest] = {}

    def capture(self, active_requests: Dict[str, ApprovalRequest]) -> None:
        """Deep-copies and captures the current active request states.

        Args:
            active_requests: Dictionary of approval requests in the manager.
        """
        # We deep-copy requests map
        self.requests_snapshot = copy.deepcopy(active_requests)
        logger.info(f"ApprovalCheckpoint '{self.checkpoint_id}' captured {len(self.requests_snapshot)} records.")

    def restore(self, active_requests: Dict[str, ApprovalRequest]) -> None:
        """Restores the requests mapping in ApprovalManager to this snapshot.

        Args:
            active_requests: The target manager requests dictionary to restore.
        """
        active_requests.clear()
        for key, val in self.requests_snapshot.items():
            active_requests[key] = copy.deepcopy(val)
        logger.info(f"ApprovalCheckpoint '{self.checkpoint_id}' restored successfully.")
