import os
import sys
import shutil
import unittest
import json

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))

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

        with self.assertRaises(ValidationFailureException):
            self.manager.execute_commit(verdict_rej, code_diff, self.workspace_root)

        with self.assertRaises(ValidationFailureException):
            self.manager.dry_run_commit(verdict_rej, code_diff, self.workspace_root)

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

    def test_rollback_correctness(self) -> None:
        """3. Verify rollback restores modified files and deletes added files."""
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

        module_3_path = os.path.join(self.workspace_root, "module_3.py")
        self.assertTrue(os.path.exists(module_3_path))
        with open(self.file_1, "r", encoding="utf-8") as f:
            m1_content = f.read()
        self.assertIn("# Appended Line", m1_content)

        rollback_res = self.manager.rollback_commit("tr_1", "rp_1", self.workspace_root)
        self.assertEqual(rollback_res["status"], "ROLLED_BACK")

        self.assertFalse(os.path.exists(module_3_path))

        with open(self.file_1, "r", encoding="utf-8") as f:
            m1_restored = f.read()
        self.assertNotIn("# Appended Line", m1_restored)
        self.assertEqual(m1_restored, "# Original Line 1\n# Original Line 2\n")

    def test_checkpoint_generation_and_depth(self) -> None:
        """4. Verify checkpoints are created and rollback depth limit is enforced."""
        verdict = self._make_verdict_data()
        
        for i in range(12):
            diff = self._make_code_diff(
                modified=["module_1.py"],
                patch=f"--- a/module_1.py\n+++ b/module_1.py\n@@ -1,2 +1,2 @@\n+# Change {i}"
            )
            self.manager.execute_commit(verdict, diff, self.workspace_root)

        self.assertEqual(len(self.manager.rollback_stack), 10)

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

        with open(self.file_1, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertNotIn("# Dry run addition", content)

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

    def test_file_count_limits(self) -> None:
        """8. Verify limit checking blocks commits with > 20 affected files."""
        verdict = self._make_verdict_data()
        files = [f"file_{i}.py" for i in range(21)]
        diff = self._make_code_diff(modified=files)

        with self.assertRaises(ValidationFailureException) as ctx:
            self.manager.execute_commit(verdict, diff, self.workspace_root)
        self.assertIn("exceeds maximum allowed limit", str(ctx.exception))

    def test_sandbox_restrictions(self) -> None:
        """9. Verify sandbox bounds checks block paths escaping target directory."""
        verdict = self._make_verdict_data()
        diff = self._make_code_diff(modified=["../outside_file.py"])

        with self.assertRaises(ValidationFailureException) as ctx:
            self.manager.execute_commit(verdict, diff, self.workspace_root)
        self.assertIn("breaches workspace sandbox root", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
