"""BBC-AOS ApprovalAuditLog

Logs approval requests, verdicts, timeouts, and escalations.
"""

import os
import json
import logging
from typing import Dict, Any, List
from bbc_aos.config.config import BBCConfig

logger = logging.getLogger("bbc_aos.approval.approval_audit_log")


class ApprovalAuditLog:
    """Manages persistence of human approval gate audit traces."""

    def __init__(self, project_root: str = ".") -> None:
        """Initializes ApprovalAuditLog.

        Args:
            project_root: Workspace root directory.
        """
        self.project_root: str = os.path.abspath(project_root)
        bbc_dir = BBCConfig.get_bbc_dir(self.project_root)
        self.log_path: str = os.path.join(bbc_dir, "approval_audit.jsonl")

    def append(
        self,
        trace_id: str,
        replay_id: str,
        approval_id: str,
        approval_hash: str,
        status: str,
        timestamp: str,
        risk_level: str,
    ) -> None:
        """Appends an approval event record to the log file.

        Args:
            trace_id: Active trace ID.
            replay_id: Active replay ID.
            approval_id: Approval request ID.
            approval_hash: Deterministic approval hash.
            status: New/updated request status.
            timestamp: Iso-formatted timestamp.
            risk_level: Request risk level.
        """
        record = {
            "trace_id": trace_id,
            "replay_id": replay_id,
            "approval_id": approval_id,
            "approval_hash": approval_hash,
            "status": status,
            "timestamp": timestamp,
            "risk_level": risk_level,
        }
        
        try:
            os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
            logger.info(f"Approval audit record appended for request '{approval_id}': status='{status}'.")
        except Exception as e:
            logger.error(f"Failed to write approval audit log: {e}")

    def get_events(self) -> List[Dict[str, Any]]:
        """Reads all approval log records.

        Returns:
            A list of log event dictionaries.
        """
        events: List[Dict[str, Any]] = []
        if not os.path.exists(self.log_path):
            return events

        try:
            with open(self.log_path, "r", encoding="utf-8") as f:
                for line in f:
                    line_str = line.strip()
                    if line_str:
                        events.append(json.loads(line_str))
        except Exception as e:
            logger.error(f"Failed to read approval audit log: {e}")

        return events
