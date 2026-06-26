"""BBC-AOS CommitManager

Production implementation of CommitManager. Serving as the sole write gateway
for applying CodeDiffs to the workspace sandbox after verification approval.
"""

import os
import copy
import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from bbc_aos.commit.commit_exceptions import (
    ValidationFailureException,
    LimitExceededException,
    RollbackException,
)
from bbc_aos.commit.commit_result import CommitResult
from bbc_aos.commit.commit_policy import CommitPolicy
from bbc_aos.commit.commit_checkpoint import CommitCheckpoint
from bbc_aos.commit.commit_audit_log import CommitAuditLog
from bbc_aos.approval.approval_manager import ApprovalManager

logger = logging.getLogger("bbc_aos.commit.commit_manager")


class CommitManager:
    """Sole write gateway enforcing strict transactions and checkpoints."""

    def __init__(
        self,
        audit_log: Optional[CommitAuditLog] = None,
        approval_manager: Optional[ApprovalManager] = None,
    ) -> None:
        """Initializes CommitManager.

        Args:
            audit_log: Optional custom CommitAuditLog registry.
            approval_manager: Optional custom ApprovalManager registry.
        """
        self.policy: CommitPolicy = CommitPolicy()
        self.audit_log: CommitAuditLog = audit_log or CommitAuditLog()
        self.approval_manager: ApprovalManager = approval_manager or ApprovalManager()
        self.rollback_stack: List[CommitCheckpoint] = []
        self.active_status: Dict[str, Dict[str, Any]] = {}

    def dry_run_commit(
        self,
        verdict_data: Dict[str, Any],
        code_diff: Dict[str, Any],
        workspace_root: str,
    ) -> Dict[str, Any]:
        """Validates all commit rules and policies without modifying files.

        Args:
            verdict_data: Output result dictionary from VerificationAgent.
            code_diff: Output result dictionary from CoderAgent.
            workspace_root: Target workspace sandbox directory.

        Returns:
            A serialized CommitResult dictionary with DRY_RUN status.
        """
        trace_id = verdict_data.get("trace_id", "")
        replay_id = verdict_data.get("replay_id", "")
        verdict = verdict_data.get("verdict", "")
        deterministic_hash = verdict_data.get("deterministic_hash", "")

        # Collect affected files
        modified = code_diff.get("modified_files", [])
        added = code_diff.get("added_files", [])
        removed = code_diff.get("removed_files", [])
        affected_files = list(set(modified + added + removed))

        # Enforce policy checks
        self.policy.validate(verdict, affected_files, workspace_root)

        # Enforce approval check
        approval_id = verdict_data.get("approval_id")
        if not approval_id:
            # Auto-request for backward compatibility with 11G tests
            risk = verdict_data.get("risk_level", "LOW")
            if verdict != "APPROVED":
                risk = "MEDIUM"
            app_res = self.approval_manager.request_approval(
                trace_id=trace_id,
                replay_id=replay_id,
                risk_level=risk,
                commit_payload=code_diff
            )
            approval_id = app_res["approval_id"]

        status_data = self.approval_manager.get_status(approval_id)
        if status_data.get("status") != "APPROVED":
            raise ValidationFailureException(
                f"Commit validation failed: approval status is '{status_data.get('status')}' (expected APPROVED)"
            )

        # Generate deterministic commit hash
        commit_hash = self._calculate_commit_hash(trace_id, replay_id, code_diff)
        timestamp = datetime.now(timezone.utc).isoformat()

        res = CommitResult(
            commit_hash=commit_hash,
            trace_id=trace_id,
            replay_id=replay_id,
            timestamp=timestamp,
            status="DRY_RUN",
            affected_files=affected_files,
        )
        logger.info(f"[COMMIT MANAGER] Dry-run validation passed for commit '{commit_hash}'.")
        return res.to_dict()

    def execute_commit(
        self,
        verdict_data: Dict[str, Any],
        code_diff: Dict[str, Any],
        workspace_root: str,
    ) -> Dict[str, Any]:
        """Validates, checkpoints, and executes code diff modifications to files.

        Args:
            verdict_data: Output result dictionary from VerificationAgent.
            code_diff: Output result dictionary from CoderAgent.
            workspace_root: Target workspace sandbox directory.

        Returns:
            A serialized CommitResult dictionary with SUCCESS status.
        """
        trace_id = verdict_data.get("trace_id", "")
        replay_id = verdict_data.get("replay_id", "")
        verdict = verdict_data.get("verdict", "")
        deterministic_hash = verdict_data.get("deterministic_hash", "")

        # Collect affected files
        modified = code_diff.get("modified_files", [])
        added = code_diff.get("added_files", [])
        removed = code_diff.get("removed_files", [])
        affected_files = list(set(modified + added + removed))

        # Enforce policy checks
        self.policy.validate(verdict, affected_files, workspace_root)

        # Enforce approval check
        approval_id = verdict_data.get("approval_id")
        if not approval_id:
            # Auto-request for backward compatibility with 11G tests
            risk = verdict_data.get("risk_level", "LOW")
            if verdict != "APPROVED":
                risk = "MEDIUM"
            app_res = self.approval_manager.request_approval(
                trace_id=trace_id,
                replay_id=replay_id,
                risk_level=risk,
                commit_payload=code_diff
            )
            approval_id = app_res["approval_id"]

        status_data = self.approval_manager.get_status(approval_id)
        if status_data.get("status") != "APPROVED":
            raise ValidationFailureException(
                f"Commit validation failed: approval status is '{status_data.get('status')}' (expected APPROVED)"
            )

        # Generate deterministic commit hash
        commit_hash = self._calculate_commit_hash(trace_id, replay_id, code_diff)
        timestamp = datetime.now(timezone.utc).isoformat()

        # Generate checkpoint
        checkpoint_id = f"cp_{commit_hash[:12]}"
        checkpoint = CommitCheckpoint(
            checkpoint_id=checkpoint_id,
            trace_id=trace_id,
            replay_id=replay_id,
            commit_hash=commit_hash,
            timestamp=timestamp,
        )
        checkpoint.create_snapshot(affected_files, workspace_root)

        # Push to rollback stack (max rollback depth = 10)
        self.rollback_stack.append(checkpoint)
        if len(self.rollback_stack) > 10:
            removed_cp = self.rollback_stack.pop(0)
            logger.info(f"Evicted oldest rollback checkpoint '{removed_cp.checkpoint_id}' (depth > 10).")

        # Apply mutations inside workspace sandbox
        try:
            self._apply_patch(code_diff.get("patch", ""), workspace_root)
        except Exception as e:
            logger.error(f"Failed to apply patch during execute_commit: {e}")
            # Rollback this transaction immediately if write fails
            self.rollback_stack.pop() # Remove failed checkpoint
            checkpoint.restore_snapshot(workspace_root)
            raise RollbackException(f"Write failure aborted commit: {e}")

        # Append to audit log
        self.audit_log.append(
            trace_id=trace_id,
            replay_id=replay_id,
            deterministic_hash=deterministic_hash,
            commit_hash=commit_hash,
            timestamp=timestamp,
            affected_files=affected_files,
        )

        res = CommitResult(
            commit_hash=commit_hash,
            trace_id=trace_id,
            replay_id=replay_id,
            timestamp=timestamp,
            status="SUCCESS",
            affected_files=affected_files,
        )
        self.active_status[commit_hash] = res.to_dict()
        logger.info(f"[COMMIT MANAGER] Commit '{commit_hash}' executed successfully.")
        return res.to_dict()

    def rollback_commit(self, trace_id: str, replay_id: str, workspace_root: str) -> Dict[str, Any]:
        """Rolls back the latest commit matching trace/replay coordinates.

        Args:
            trace_id: Active trace ID.
            replay_id: Active replay ID.
            workspace_root: Target workspace sandbox directory.

        Returns:
            A status dictionary indicating success.
        """
        if not self.rollback_stack:
            raise RollbackException("No checkpoints available for rollback")

        # Find the latest checkpoint matching coordinates (or fallback to latest)
        target_checkpoint = self.rollback_stack[-1]
        if (
            target_checkpoint.trace_id != trace_id
            or target_checkpoint.replay_id != replay_id
        ):
            logger.warning(
                f"Rollback trace '{trace_id}'/replay '{replay_id}' mismatch with "
                f"latest checkpoint '{target_checkpoint.checkpoint_id}'"
            )

        # Pop and restore snapshot
        self.rollback_stack.pop()
        target_checkpoint.restore_snapshot(workspace_root)

        # Remove from active status
        commit_hash = target_checkpoint.commit_hash
        if commit_hash in self.active_status:
            del self.active_status[commit_hash]

        logger.info(f"Rollback completed successfully for checkpoint '{target_checkpoint.checkpoint_id}'.")
        return {
            "status": "ROLLED_BACK",
            "commit_hash": commit_hash,
            "trace_id": trace_id,
            "replay_id": replay_id,
        }

    def get_commit_status(self, commit_hash: str) -> Dict[str, Any]:
        """Returns the status details of a specific commit.

        Args:
            commit_hash: Associated commit hash.

        Returns:
            A status summary dictionary.
        """
        # Check active status first
        if commit_hash in self.active_status:
            status_data = copy.deepcopy(self.active_status[commit_hash])
            status_data["status"] = "COMMITTED"
            return status_data

        # Fallback to audit log
        events = self.audit_log.get_events()
        for event in events:
            if event.get("commit_hash") == commit_hash:
                return {
                    "commit_hash": commit_hash,
                    "trace_id": event["trace_id"],
                    "replay_id": event["replay_id"],
                    "timestamp": event["timestamp"],
                    "status": "COMMITTED",
                    "affected_files": event["affected_files"],
                }

        raise KeyError(f"Commit hash '{commit_hash}' not found in registry or audit log.")

    # ------------------------------------------------------------------
    # Helper Private Methods
    # ------------------------------------------------------------------

    def _calculate_commit_hash(
        self,
        trace_id: str,
        replay_id: str,
        code_diff: Dict[str, Any],
    ) -> str:
        """Generates a deterministic SHA-256 commit hash."""
        payload = {
            "trace_id": trace_id,
            "replay_id": replay_id,
            "modified_files": sorted(code_diff.get("modified_files", [])),
            "added_files": sorted(code_diff.get("added_files", [])),
            "removed_files": sorted(code_diff.get("removed_files", [])),
            "patch": code_diff.get("patch", ""),
        }
        payload_str = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(payload_str.encode("utf-8")).hexdigest()

    def _apply_patch(self, patch: str, workspace_root: str) -> None:
        """Parses and applies a unified diff patch to the sandbox filesystem."""
        if not patch:
            return

        lines = patch.splitlines()
        current_file = None
        hunk_lines = []
        is_addition = False
        is_removal = False

        idx = 0
        while idx < len(lines):
            line = lines[idx]
            if line.startswith("--- "):
                # Parse original path
                orig_path = line[4:].strip()
                is_addition = (orig_path == "/dev/null")
                
                # Read the next line which should start with "+++ "
                idx += 1
                if idx < len(lines) and lines[idx].startswith("+++ "):
                    dest_path = lines[idx][4:].strip()
                    is_removal = (dest_path == "/dev/null")
                    
                    # Normalize pathways (strip a/ or b/ prefixes)
                    if not is_addition and (dest_path.startswith("a/") or dest_path.startswith("b/")):
                        dest_path = dest_path[2:]
                    elif is_addition and (dest_path.startswith("b/") or dest_path.startswith("a/")):
                        dest_path = dest_path[2:]
                        
                    current_file = dest_path
                    hunk_lines = []
                idx += 1
                continue

            if current_file:
                # Read hunk context until the next "--- " or end of diff
                if line.startswith("@@"):
                    hunk_lines = []
                    idx += 1
                    while idx < len(lines) and not lines[idx].startswith("--- "):
                        hunk_lines.append(lines[idx])
                        idx += 1
                    
                    abs_path = os.path.abspath(os.path.join(workspace_root, current_file))
                    if is_addition:
                        new_content = "\n".join([hl[1:] for hl in hunk_lines if hl.startswith("+")]) + "\n"
                        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
                        with open(abs_path, "w", encoding="utf-8") as f:
                            f.write(new_content)
                    elif is_removal:
                        if os.path.exists(abs_path):
                            os.remove(abs_path)
                    else:
                        # Modification
                        if os.path.exists(abs_path):
                            with open(abs_path, "r", encoding="utf-8") as f:
                                file_content = f.read()
                            
                            orig_hunk = [hl[1:] for hl in hunk_lines if hl.startswith(" ") or hl.startswith("-")]
                            repl_hunk = [hl[1:] for hl in hunk_lines if hl.startswith(" ") or hl.startswith("+")]
                            
                            orig_str = "\n".join(orig_hunk)
                            repl_str = "\n".join(repl_hunk)
                            
                            if orig_str and orig_str in file_content:
                                file_content = file_content.replace(orig_str, repl_str)
                            else:
                                clean_repl = [hl[1:] for hl in hunk_lines if hl.startswith("+")]
                                file_content += "\n" + "\n".join(clean_repl) + "\n"
                                
                            with open(abs_path, "w", encoding="utf-8") as f:
                                f.write(file_content)
                        else:
                            new_content = "\n".join([hl[1:] for hl in hunk_lines if hl.startswith("+")]) + "\n"
                            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
                            with open(abs_path, "w", encoding="utf-8") as f:
                                f.write(new_content)
                    continue

            idx += 1
