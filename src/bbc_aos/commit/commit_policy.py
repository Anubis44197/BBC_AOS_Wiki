"""BBC-AOS CommitPolicy

Enforces transaction limits, sandboxing boundaries, and verification gates.
"""

import os
import logging
from typing import Dict, Any, List
from bbc_aos.commit.commit_exceptions import ValidationFailureException

logger = logging.getLogger("bbc_aos.commit.commit_policy")


class CommitPolicy:
    """Enforces correctness validation rules on commit requests."""

    MAX_FILES_LIMIT: int = 20

    def validate(
        self,
        verdict: str,
        affected_files: List[str],
        workspace_root: str,
    ) -> None:
        """Validates verdict, file counts, and path sandboxes.

        Args:
            verdict: VerificationAgent verdict (APPROVED/REJECTED).
            affected_files: List of all files changed by this commit.
            workspace_root: Target workspace sandbox directory.

        Raises:
            ValidationFailureException: If a validation rule is violated.
        """
        # 1. Verification Gate check
        if verdict != "APPROVED":
            error_msg = f"Commit validation failed: verdict is '{verdict}' (expected APPROVED)"
            logger.error(error_msg)
            raise ValidationFailureException(error_msg)

        # 2. Maximum files per commit limit check
        if len(affected_files) > self.MAX_FILES_LIMIT:
            error_msg = (
                f"Commit validation failed: affected files ({len(affected_files)}) "
                f"exceeds maximum allowed limit of {self.MAX_FILES_LIMIT}"
            )
            logger.error(error_msg)
            raise ValidationFailureException(error_msg)

        # 3. Path sandboxing check
        abs_root = os.path.abspath(workspace_root)
        for rel_path in affected_files:
            abs_path = os.path.abspath(os.path.join(abs_root, rel_path))
            if not abs_path.startswith(abs_root):
                error_msg = (
                    f"Commit validation failed: file path '{rel_path}' breaches "
                    f"workspace sandbox root '{abs_root}'"
                )
                logger.error(f"[SAFETY VIOLATION] {error_msg}")
                raise ValidationFailureException(error_msg)
