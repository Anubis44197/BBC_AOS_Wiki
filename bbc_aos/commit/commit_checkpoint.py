"""BBC-AOS CommitCheckpoint

Saves immutable snapshots of file contents to allow transaction rollbacks.
"""

import os
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("bbc_aos.commit.commit_checkpoint")


class CommitCheckpoint:
    """Manages snapshot backups of files affected by a commit."""

    def __init__(
        self,
        checkpoint_id: str,
        trace_id: str,
        replay_id: str,
        commit_hash: str,
        timestamp: str,
    ) -> None:
        """Initializes CommitCheckpoint.

        Args:
            checkpoint_id: Unique identifier for this checkpoint.
            trace_id: Active trace ID.
            replay_id: Active replay ID.
            commit_hash: Associated commit hash.
            timestamp: Iso-formatted timestamp.
        """
        self.checkpoint_id: str = checkpoint_id
        self.trace_id: str = trace_id
        self.replay_id: str = replay_id
        self.commit_hash: str = commit_hash
        self.timestamp: str = timestamp
        # Maps relative file paths to their original content (or None if they did not exist)
        self.backup_data: Dict[str, Optional[str]] = {}

    def create_snapshot(self, affected_files: List[str], workspace_root: str) -> None:
        """Saves a snapshot copy of the original state of all affected files.

        Args:
            affected_files: List of files targeted by the commit.
            workspace_root: Target workspace sandbox directory.
        """
        abs_root = os.path.abspath(workspace_root)
        for rel_path in affected_files:
            abs_path = os.path.abspath(os.path.join(abs_root, rel_path))
            if os.path.exists(abs_path) and os.path.isfile(abs_path):
                try:
                    with open(abs_path, "r", encoding="utf-8") as f:
                        self.backup_data[rel_path] = f.read()
                except Exception as e:
                    logger.warning(f"Could not snapshot file '{rel_path}': {e}")
                    self.backup_data[rel_path] = None
            else:
                self.backup_data[rel_path] = None

        logger.info(f"Checkpoint '{self.checkpoint_id}' snapshot created. Backed up {len(self.backup_data)} paths.")

    def restore_snapshot(self, workspace_root: str) -> None:
        """Restores all files in the snapshot to their original pre-commit content.

        Args:
            workspace_root: Target workspace sandbox directory.
        """
        abs_root = os.path.abspath(workspace_root)
        for rel_path, original_content in self.backup_data.items():
            abs_path = os.path.abspath(os.path.join(abs_root, rel_path))
            if original_content is None:
                # File did not exist before the commit, so remove it
                if os.path.exists(abs_path):
                    try:
                        os.remove(abs_path)
                        logger.info(f"Rollback: deleted added file '{rel_path}'")
                    except Exception as e:
                        logger.error(f"Rollback: failed to delete file '{rel_path}': {e}")
            else:
                # Restore original content
                try:
                    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
                    with open(abs_path, "w", encoding="utf-8") as f:
                        f.write(original_content)
                    logger.info(f"Rollback: restored file '{rel_path}'")
                except Exception as e:
                    logger.error(f"Rollback: failed to restore file '{rel_path}': {e}")
