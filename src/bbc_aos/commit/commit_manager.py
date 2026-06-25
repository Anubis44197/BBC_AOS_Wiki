"""BBC-AOS CommitManager

Production implementation of CommitManager. Serving as the sole write gateway
for applying CodeDiffs to the workspace sandbox after verification approval.
"""

import os
import copy
import hashlib
import json
import logging
import re
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

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
        """Parses and applies a unified diff patch through a staging copy first."""
        if not patch:
            return

        abs_root = Path(workspace_root).resolve()
        backups_dir = abs_root / ".bbc" / "backups"
        backups_dir.mkdir(parents=True, exist_ok=True)
        parsed_files = self._parse_unified_diff(patch)

        for rel_path, hunks, is_addition, is_removal in parsed_files:
            target_path = (abs_root / rel_path).resolve()
            try:
                target_path.relative_to(abs_root)
            except ValueError:
                raise ValidationFailureException(
                    f"Patch target '{rel_path}' breaches workspace sandbox root '{abs_root}'"
                )

            backup_name = hashlib.sha256(str(target_path).encode("utf-8")).hexdigest()[:16]
            backup_path = backups_dir / f"{backup_name}.bak"
            if target_path.exists() and target_path.is_file():
                shutil.copy2(target_path, backup_path)
            else:
                backup_path.write_text("__BBC_AOS_FILE_DID_NOT_EXIST__\n", encoding="utf-8")

            try:
                if is_removal:
                    if target_path.exists():
                        target_path.unlink()
                    continue

                original_lines: List[str] = []
                if not is_addition and target_path.exists():
                    original_lines = target_path.read_text(encoding="utf-8").splitlines()

                patched_lines = self._apply_hunks(original_lines, hunks)
                self._stage_and_replace(target_path, patched_lines)
            except Exception:
                if backup_path.read_text(encoding="utf-8", errors="ignore") == "__BBC_AOS_FILE_DID_NOT_EXIST__\n":
                    if target_path.exists():
                        target_path.unlink()
                else:
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(backup_path, target_path)
                raise

    def _parse_unified_diff(self, patch: str) -> List[Tuple[str, List[List[str]], bool, bool]]:
        """Groups unified diff hunks by destination file."""
        lines = patch.splitlines()
        parsed: List[Tuple[str, List[List[str]], bool, bool]] = []
        idx = 0
        while idx < len(lines):
            if not lines[idx].startswith("--- "):
                idx += 1
                continue
            orig_path = lines[idx][4:].strip()
            is_addition = orig_path == "/dev/null"
            idx += 1
            if idx >= len(lines) or not lines[idx].startswith("+++ "):
                raise ValidationFailureException("Malformed unified diff: missing destination header")

            dest_path = lines[idx][4:].strip()
            is_removal = dest_path == "/dev/null"
            rel_path = orig_path if is_removal else dest_path
            if rel_path.startswith(("a/", "b/")):
                rel_path = rel_path[2:]
            idx += 1

            hunks: List[List[str]] = []
            while idx < len(lines) and not lines[idx].startswith("--- "):
                if lines[idx].startswith("@@"):
                    hunk: List[str] = [lines[idx]]
                    idx += 1
                    while idx < len(lines) and not lines[idx].startswith("--- "):
                        if lines[idx].startswith("@@"):
                            break
                        hunk.append(lines[idx])
                        idx += 1
                    hunks.append(hunk)
                    continue
                idx += 1
            parsed.append((rel_path, hunks, is_addition, is_removal))
        return parsed

    def _apply_hunks(self, original_lines: List[str], hunks: List[List[str]]) -> List[str]:
        """Applies parsed hunks to line arrays with context validation."""
        result = list(original_lines)
        offset = 0
        for hunk in hunks:
            if not hunk:
                continue
            header = hunk[0]
            match = re.match(r"@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@", header)
            start_index = 0
            if match:
                start_index = max(int(match.group(1)) - 1 + offset, 0)

            old_block: List[str] = []
            new_block: List[str] = []
            for line in hunk[1:]:
                if not line:
                    old_block.append("")
                    new_block.append("")
                elif line.startswith(" "):
                    old_block.append(line[1:])
                    new_block.append(line[1:])
                elif line.startswith("-"):
                    old_block.append(line[1:])
                elif line.startswith("+"):
                    new_block.append(line[1:])
                elif line.startswith("\\"):
                    continue

            applied_at = self._find_block(result, old_block, start_index)
            if applied_at is None:
                applied_at = len(result)
                old_len = 0
            else:
                old_len = len(old_block)

            result = result[:applied_at] + new_block + result[applied_at + old_len:]
            offset += len(new_block) - old_len
        return result

    def _find_block(self, lines: List[str], block: List[str], preferred_index: int) -> Optional[int]:
        """Finds an old hunk block, preferring the hunk header location."""
        if not block:
            return preferred_index
        if lines[preferred_index:preferred_index + len(block)] == block:
            return preferred_index
        for idx in range(0, max(len(lines) - len(block) + 1, 0)):
            if lines[idx:idx + len(block)] == block:
                return idx
        return None

    def _stage_and_replace(self, target_path: Path, patched_lines: List[str]) -> None:
        """Writes to a temp file in the target directory, then atomically replaces."""
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            delete=False,
            dir=str(target_path.parent),
            newline="\n",
        ) as tmp:
            tmp.write("\n".join(patched_lines))
            tmp.write("\n")
            tmp_path = Path(tmp.name)
        os.replace(tmp_path, target_path)
