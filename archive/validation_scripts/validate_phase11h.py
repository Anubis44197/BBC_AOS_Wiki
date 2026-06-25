"""Phase 11H Validation Suite - Human Approval Gates

Validates:
1. Risk-based routing (LOW auto-approves, MEDIUM/HIGH pending, CRITICAL escalates)
2. State transitions (approve, reject, timeout, escalate)
3. Invalid transitions checking (raises InvalidTransitionException)
4. Timeout/expiration behavior
5. Escalation routing
6. Rollback correctness of pending requests (checkpoint restoration)
7. Deterministic approval hashes (100 runs matching hashes)
8. Audit event generation (logs formatted events inside approval_audit.jsonl)
"""

import os
import sys
import shutil
import unittest

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from bbc_aos.approval.approval_manager import ApprovalManager
from bbc_aos.approval.approval_audit_log import ApprovalAuditLog
from bbc_aos.approval.approval_exceptions import InvalidTransitionException


class TestApprovalGatesSubsystem(unittest.TestCase):

    def setUp(self) -> None:
        self.workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "sandbox_app_test"))
        os.makedirs(self.workspace_root, exist_ok=True)

        self.audit_log = ApprovalAuditLog(project_root=self.workspace_root)
        self.manager = ApprovalManager(audit_log=self.audit_log)

        self.commit_payload = {
            "modified_files": ["module_1.py"],
            "added_files": [],
            "removed_files": [],
            "patch": "--- a/module_1.py\n+++ b/module_1.py",
        }

    def tearDown(self) -> None:
        if os.path.exists(self.workspace_root):
            shutil.rmtree(self.workspace_root)

    def test_risk_routing(self) -> None:
        """1. Verify risk routing: LOW auto-approves, MEDIUM/HIGH pending, CRITICAL escalates."""
        # LOW
        res_low = self.manager.request_approval("tr_low", "rp_low", "LOW", self.commit_payload)
        self.assertEqual(res_low["status"], "APPROVED")

        # MEDIUM
        res_med = self.manager.request_approval("tr_med", "rp_med", "MEDIUM", self.commit_payload)
        self.assertEqual(res_med["status"], "PENDING")

        # HIGH
        res_high = self.manager.request_approval("tr_high", "rp_high", "HIGH", self.commit_payload)
        self.assertEqual(res_high["status"], "PENDING")

        # CRITICAL
        res_crit = self.manager.request_approval("tr_crit", "rp_crit", "CRITICAL", self.commit_payload)
        self.assertEqual(res_crit["status"], "ESCALATED")

        print("[PASS] test_risk_routing")

    def test_status_transitions(self) -> None:
        """2. Verify state transitions (approve, reject, timeout, escalate)."""
        # Test Approve
        res_pending = self.manager.request_approval("tr_t1", "rp_t1", "MEDIUM", self.commit_payload)
        app_id = res_pending["approval_id"]
        self.assertEqual(self.manager.get_status(app_id)["status"], "PENDING")

        res_app = self.manager.approve(app_id)
        self.assertEqual(res_app["status"], "APPROVED")
        self.assertEqual(self.manager.get_status(app_id)["status"], "APPROVED")

        # Test Reject
        res_pending2 = self.manager.request_approval("tr_t2", "rp_t2", "MEDIUM", self.commit_payload)
        app_id2 = res_pending2["approval_id"]
        res_rej = self.manager.reject(app_id2)
        self.assertEqual(res_rej["status"], "REJECTED")

        # Test Timeout
        res_pending3 = self.manager.request_approval("tr_t3", "rp_t3", "MEDIUM", self.commit_payload)
        app_id3 = res_pending3["approval_id"]
        res_to = self.manager.timeout(app_id3)
        self.assertEqual(res_to["status"], "EXPIRED")

        # Test Escalate
        res_pending4 = self.manager.request_approval("tr_t4", "rp_t4", "MEDIUM", self.commit_payload)
        app_id4 = res_pending4["approval_id"]
        res_esc = self.manager.escalate(app_id4)
        self.assertEqual(res_esc["status"], "ESCALATED")

        # Can approve escalated request
        res_esc_app = self.manager.approve(app_id4)
        self.assertEqual(res_esc_app["status"], "APPROVED")

        print("[PASS] test_status_transitions")

    def test_invalid_transitions(self) -> None:
        """3. Assert that invalid transitions raise InvalidTransitionException."""
        # APPROVED cannot be rejected, escalated, or timed out
        res_low = self.manager.request_approval("tr_err", "rp_err", "LOW", self.commit_payload)
        app_id = res_low["approval_id"]

        with self.assertRaises(InvalidTransitionException):
            self.manager.approve(app_id)
        with self.assertRaises(InvalidTransitionException):
            self.manager.reject(app_id)
        with self.assertRaises(InvalidTransitionException):
            self.manager.timeout(app_id)
        with self.assertRaises(InvalidTransitionException):
            self.manager.escalate(app_id)

        print("[PASS] test_invalid_transitions")

    def test_rollback_correctness(self) -> None:
        """4. Verify rollback removes/reverts request mapping states."""
        # Initial requests count = 0
        self.assertEqual(len(self.manager.requests), 0)

        res = self.manager.request_approval("tr_roll", "rp_roll", "MEDIUM", self.commit_payload)
        app_id = res["approval_id"]
        self.assertEqual(len(self.manager.requests), 1)

        # Rollback requests state
        self.manager.rollback_request(app_id)
        self.assertEqual(len(self.manager.requests), 0)
        with self.assertRaises(KeyError):
            self.manager.get_status(app_id)

        print("[PASS] test_rollback_correctness")

    def test_deterministic_hashes(self) -> None:
        """5. Validate replay determinism: 100 runs yield identical hashes."""
        res_first = self.manager.request_approval("tr_det", "rp_det", "MEDIUM", self.commit_payload)
        first_hash = res_first["approval_hash"]

        # Run 100 times in memory
        for i in range(100):
            # Clean requests to allow unique creation on identical trace/replay
            self.manager.requests.clear()
            res = self.manager.request_approval("tr_det", "rp_det", "MEDIUM", self.commit_payload)
            self.assertEqual(res["approval_hash"], first_hash)

        print("[PASS] test_deterministic_hashes (100 runs, zero variance)")

    def test_audit_generation(self) -> None:
        """6. Verify audit records are logged to approval_audit.jsonl."""
        res = self.manager.request_approval("tr_aud", "rp_aud", "MEDIUM", self.commit_payload)
        app_id = res["approval_id"]
        self.manager.approve(app_id)

        events = self.audit_log.get_events()
        self.assertEqual(len(events), 2)
        # first event is pending
        self.assertEqual(events[0]["approval_id"], app_id)
        self.assertEqual(events[0]["status"], "PENDING")
        self.assertEqual(events[0]["risk_level"], "MEDIUM")
        # second event is approved
        self.assertEqual(events[1]["approval_id"], app_id)
        self.assertEqual(events[1]["status"], "APPROVED")

        print("[PASS] test_audit_generation")


if __name__ == "__main__":
    print("=" * 60)
    print("Phase 11H Validation Suite - Human Approval Gates")
    print("=" * 60)
    unittest.main()
