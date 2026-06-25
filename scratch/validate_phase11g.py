"""Phase 11G Validation Suite - Commit Subsystem Pipeline

Validates:
1. Approved-only commits (verdict must be APPROVED)
2. Deterministic commit hashes (identical inputs yield matching hashes)
3. Rollback correctness (restores original file content and deletes added files)
4. Checkpoint generation (checkpoints are created and capped at rollback depth of 10)
5. Dry-run correctness (validates but makes no filesystem mutations)
6. Replay correctness (100 runs yield identical hashes)
7. Audit log generation (asserts correct format in commit_audit.jsonl)
8. File count limits (raises error if affected files > 20)
9. Sandbox restrictions (raises safety breach if file is outside workspace)
"""

import os
import sys
import shutil
import unittest
import json

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from bbc_aos.commit.commit_manager import CommitManager
from bbc_aos.commit.commit_audit_log import CommitAuditLog
from bbc_aos.commit.commit_exceptions import ValidationFailureException, RollbackException


class TestCommitPipelineSubsystem(unittest.TestCase):

    def setUp(self) -> None:
        self.workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "sandbox_test_dir"))
        os.makedirs(self.workspace_root, exist_ok=True)

        # Create dummy initial files
        self.file_1 = os.path.join(self.workspace_root, "module_1.py")
        with open(self.file_1, "w", encoding="utf-8") as f:
            f.write("# Original Line 1\n# Original Line 2\n")

        self.file_2 = os.path.join(self.workspace_root, "module_2.py")
        with open(self.file_2, "w", encoding="utf-8") as f:
            f.write("# Original Line 3\n# Original Line 4\n")

        # Setup manager with localized audit log in sandbox
        self.audit_log = CommitAuditLog(project_root=self.workspace_root)
        self.manager = CommitManager(audit_log=self.audit_log)

    def tearDown(self) -> None:
        if os.path.exists(self.workspace_root):
            shutil.rmtree(self.workspace_root)

    def _make_code_diff(self, modified=None, added=None, removed=None, patch="") -> dict:
        return {
            "modified_files": modified or [],
            "added_files": added or [],
            "removed_files": removed or [],
            "patch": patch,
        }

    def _make_verdict_data(self, verdict="APPROVED", trace_id="tr_1", replay_id="rp_1", det_hash="a" * 64) -> dict:
        return {
            "verdict": verdict,
            "trace_id": trace_id,
            "replay_id": replay_id,
            "deterministic_hash": det_hash,
        }

    def test_approved_only_commits(self) -> None:
        """1. Verify that only APPROVED verdicts are accepted by CommitManager."""
        verdict_rej = self._make_verdict_data(verdict="REJECTED")
        code_diff = self._make_code_diff(modified=["module_1.py"])

        # Execute fails
        with self.assertRaises(ValidationFailureException):
            self.manager.execute_commit(verdict_rej, code_diff, self.workspace_root)

        # Dry run fails
        with self.assertRaises(ValidationFailureException):
            self.manager.dry_run_commit(verdict_rej, code_diff, self.workspace_root)

        print("[PASS] test_approved_only_commits")

    def test_deterministic_commit_hashes(self) -> None:
        """2. Validate that commit hashes are fully deterministic."""
        verdict = self._make_verdict_data()
        code_diff = self._make_code_diff(
            modified=["module_1.py"],
            patch="--- a/module_1.py\n+++ b/module_1.py\n@@ -1,2 +1,3 @@\n+# Change"
        )

        res1 = self.manager.dry_run_commit(verdict, code_diff, self.workspace_root)
        res2 = self.manager.dry_run_commit(verdict, code_diff, self.workspace_root)

        self.assertEqual(res1["commit_hash"], res2["commit_hash"])
        self.assertEqual(len(res1["commit_hash"]), 64)

        print("[PASS] test_deterministic_commit_hashes")

    def test_rollback_correctness(self) -> None:
        """3. Verify rollback restores modified files and deletes added files."""
        # Execute addition + modification
        verdict = self._make_verdict_data()
        patch = (
            "--- a/module_1.py\n"
            "+++ b/module_1.py\n"
            "@@ -1,2 +1,3 @@\n"
            " # Original Line 1\n"
            "+# Appended Line\n"
            " # Original Line 2\n"
            "--- /dev/null\n"
            "+++ b/module_3.py\n"
            "@@ -0,0 +1,2 @@\n"
            "+# Added File content\n"
        )
        code_diff = self._make_code_diff(
            modified=["module_1.py"],
            added=["module_3.py"],
            patch=patch
        )

        status = self.manager.execute_commit(verdict, code_diff, self.workspace_root)
        self.assertEqual(status["status"], "SUCCESS")

        # Verify filesystem mutated
        module_3_path = os.path.join(self.workspace_root, "module_3.py")
        self.assertTrue(os.path.exists(module_3_path))
        with open(self.file_1, "r", encoding="utf-8") as f:
            m1_content = f.read()
        self.assertIn("# Appended Line", m1_content)

        # Rollback commit
        rollback_res = self.manager.rollback_commit("tr_1", "rp_1", self.workspace_root)
        self.assertEqual(rollback_res["status"], "ROLLED_BACK")

        # Verify module_3 deleted
        self.assertFalse(os.path.exists(module_3_path))

        # Verify module_1 restored
        with open(self.file_1, "r", encoding="utf-8") as f:
            m1_restored = f.read()
        self.assertNotIn("# Appended Line", m1_restored)
        self.assertEqual(m1_restored, "# Original Line 1\n# Original Line 2\n")

        print("[PASS] test_rollback_correctness")

    def test_checkpoint_generation_and_depth(self) -> None:
        """4. Verify checkpoints are created and rollback depth limit is enforced."""
        verdict = self._make_verdict_data()
        
        # Trigger 12 sequential commits
        for i in range(12):
            diff = self._make_code_diff(
                modified=["module_1.py"],
                patch=f"--- a/module_1.py\n+++ b/module_1.py\n@@ -1,2 +1,2 @@\n+# Change {i}"
            )
            self.manager.execute_commit(verdict, diff, self.workspace_root)

        # Check stack depth is capped at 10
        self.assertEqual(len(self.manager.rollback_stack), 10)

        print("[PASS] test_checkpoint_generation_and_depth")

    def test_dry_run_correctness(self) -> None:
        """5. Verify dry run performs validation but does not mutate the filesystem."""
        verdict = self._make_verdict_data()
        patch = (
            "--- a/module_1.py\n"
            "+++ b/module_1.py\n"
            "@@ -1,2 +1,3 @@\n"
            "+# Dry run addition\n"
        )
        diff = self._make_code_diff(modified=["module_1.py"], patch=patch)

        res = self.manager.dry_run_commit(verdict, diff, self.workspace_root)
        self.assertEqual(res["status"], "DRY_RUN")

        # Verify file on disk not changed
        with open(self.file_1, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertNotIn("# Dry run addition", content)

        print("[PASS] test_dry_run_correctness")

    def test_replay_correctness(self) -> None:
        """6. Validate replay correctness: running 100 times yields identical hashes."""
        verdict = self._make_verdict_data()
        diff = self._make_code_diff(
            modified=["module_1.py"],
            patch="--- a/module_1.py\n+++ b/module_1.py\n@@ -1,2 +1,2 @@\n+# Replay change"
        )

        res_first = self.manager.dry_run_commit(verdict, diff, self.workspace_root)
        first_hash = res_first["commit_hash"]

        for i in range(100):
            res = self.manager.dry_run_commit(verdict, diff, self.workspace_root)
            self.assertEqual(res["commit_hash"], first_hash)

        print("[PASS] test_replay_correctness (100 runs, zero variance)")

    def test_audit_generation(self) -> None:
        """7. Verify execution appends correct audit records to jsonl log."""
        verdict = self._make_verdict_data(det_hash="det_hash_val")
        diff = self._make_code_diff(modified=["module_1.py"])

        status = self.manager.execute_commit(verdict, diff, self.workspace_root)
        commit_hash = status["commit_hash"]

        events = self.audit_log.get_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["commit_hash"], commit_hash)
        self.assertEqual(events[0]["deterministic_hash"], "det_hash_val")
        self.assertEqual(events[0]["affected_files"], ["module_1.py"])

        print("[PASS] test_audit_generation")

    def test_file_count_limits(self) -> None:
        """8. Verify limit checking blocks commits with > 20 affected files."""
        verdict = self._make_verdict_data()
        # Create 21 affected files
        files = [f"file_{i}.py" for i in range(21)]
        diff = self._make_code_diff(modified=files)

        with self.assertRaises(ValidationFailureException) as ctx:
            self.manager.execute_commit(verdict, diff, self.workspace_root)
        self.assertIn("exceeds maximum allowed limit", str(ctx.exception))

        print("[PASS] test_file_count_limits")

    def test_sandbox_restrictions(self) -> None:
        """9. Verify sandbox bounds checks block paths escaping target directory."""
        verdict = self._make_verdict_data()
        # Escape path
        diff = self._make_code_diff(modified=["../outside_file.py"])

        with self.assertRaises(ValidationFailureException) as ctx:
            self.manager.execute_commit(verdict, diff, self.workspace_root)
        self.assertIn("breaches workspace sandbox root", str(ctx.exception))

        print("[PASS] test_sandbox_restrictions")


if __name__ == "__main__":
    print("=" * 60)
    print("Phase 11G Validation Suite - Commit Subsystem Pipeline")
    print("=" * 60)
    unittest.main()
