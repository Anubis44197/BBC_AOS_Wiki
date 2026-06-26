"""BBC-AOS CommitAuditLog

Appends immutable logs of all commit actions to commit_audit.jsonl.
"""

import os
import json
import logging
from typing import Dict, Any, List
from bbc_aos.config.config import BBCConfig

logger = logging.getLogger("bbc_aos.commit.commit_audit_log")


class CommitAuditLog:
    """Manages the persistence of commit execution events."""

    def __init__(self, project_root: str = ".") -> None:
        """Initializes CommitAuditLog.

        Args:
            project_root: Workspace root directory.
        """
        self.project_root: str = os.path.abspath(project_root)
        bbc_dir = BBCConfig.get_bbc_dir(self.project_root)
        self.log_path: str = os.path.join(bbc_dir, "commit_audit.jsonl")

    def append(
        self,
        trace_id: str,
        replay_id: str,
        deterministic_hash: str,
        commit_hash: str,
        timestamp: str,
        affected_files: List[str],
    ) -> None:
        """Appends a new commit audit record to the log file.

        Args:
            trace_id: Active trace ID.
            replay_id: Active replay ID.
            deterministic_hash: Verdict deterministic hash.
            commit_hash: Generated commit hash.
            timestamp: Iso-formatted timestamp.
            affected_files: List of files modified/added/removed.
        """
        record = {
            "trace_id": trace_id,
            "replay_id": replay_id,
            "deterministic_hash": deterministic_hash,
            "commit_hash": commit_hash,
            "timestamp": timestamp,
            "affected_files": affected_files,
        }
        
        try:
            os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
            logger.info(f"Audit log entry appended for commit '{commit_hash}'.")
        except Exception as e:
            logger.error(f"Failed to write commit audit log entry: {e}")

    def get_events(self) -> List[Dict[str, Any]]:
        """Reads and parses all commit log events from the log file.

        Returns:
            A list of commit log event dictionaries.
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
            logger.error(f"Failed to read commit audit log: {e}")

        return events
