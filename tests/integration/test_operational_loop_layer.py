import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))

from bbc_aos.operations.loop_budget import LoopBudget, LoopBudgetStore
from bbc_aos.operations.loop_exceptions import LoopBudgetExceededError
from bbc_aos.operations.loop_manager import LoopManager
from bbc_aos.operations.loop_mode import LoopModeStore
from bbc_aos.operations.loop_pattern_registry import LoopPatternRegistry
from bbc_aos.operations.loop_readiness import LoopReadinessAuditor
from bbc_aos.operations.loop_run_log import LoopRunRecord, LoopRunLog
from bbc_aos.operations.loop_state import LoopStateStore, OperationalLoopState
from bbc_aos.runtime_paths import loop_dir, reports_dir, wiki_vault_dir


class TestOperationalLoopLayerProduction(unittest.TestCase):
    def setUp(self) -> None:
        import tempfile
        from pathlib import Path

        self._old_workspace_env = os.environ.get("BBC_AOS_WORKSPACES")
        self._ghost_root = Path(tempfile.mkdtemp()) / "BBC_WORKSPACES"
        os.environ["BBC_AOS_WORKSPACES"] = str(self._ghost_root)

    def tearDown(self) -> None:
        if self._old_workspace_env is None:
            os.environ.pop("BBC_AOS_WORKSPACES", None)
        else:
            os.environ["BBC_AOS_WORKSPACES"] = self._old_workspace_env

    def test_loop_modes_persist_correctly(self) -> None:
        with self.subTest("mode persistence"):
            root = self._tmp()
            manager = LoopManager(root)
            manager.init()
            manager.set_mode("l1")
            self.assertEqual(LoopModeStore(root).get().mode.value, "L1")
            manager.set_mode("l3")
            self.assertEqual(LoopModeStore(root).get().mode.value, "L3")

    def test_readiness_scores_are_deterministic(self) -> None:
        root = self._tmp()
        (root / "README.md").write_text("# demo\n", encoding="utf-8")
        (root / "tests").mkdir()
        first = LoopReadinessAuditor(root).audit()
        second = LoopReadinessAuditor(root).audit()
        self.assertEqual(first, second)
        self.assertEqual(first["readiness_score"], second["readiness_score"])

    def test_pattern_registry_loads_defaults(self) -> None:
        patterns = LoopPatternRegistry(self._tmp()).all()
        names = [pattern.name for pattern in patterns]
        self.assertIn("security_scan", names)
        self.assertIn("release_preparation", names)

    def test_budget_limits_are_enforced(self) -> None:
        root = self._tmp()
        store = LoopBudgetStore(root)
        with self.assertRaises(LoopBudgetExceededError):
            store.enforce(LoopBudget(max_iterations=4))

    def test_state_transitions_are_deterministic(self) -> None:
        root = self._tmp()
        store = LoopStateStore(root)
        store.save(store.load())
        first = store.transition(OperationalLoopState.RUNNING)
        second = store.load()
        self.assertEqual(first.to_dict(), second.to_dict())

    def test_run_log_appends_history(self) -> None:
        root = self._tmp()
        log = LoopRunLog(root)
        log.append(
            LoopRunRecord(
                trace_id="tr_1",
                replay_id="rp_1",
                loop_id="loop_1",
                mode="L2",
                goal="test",
                start_time="s",
                end_time="e",
                status="COMPLETED",
            )
        )
        log.append(
            LoopRunRecord(
                trace_id="tr_2",
                replay_id="rp_2",
                loop_id="loop_2",
                mode="L2",
                goal="test2",
                start_time="s",
                end_time="e",
                status="FAILED",
            )
        )
        self.assertEqual([row.trace_id for row in log.history(last=2)], ["tr_1", "tr_2"])

    def test_kill_switch_terminates_loop(self) -> None:
        root = self._tmp()
        manager = LoopManager(root)
        manager.init()
        result = manager.kill()
        self.assertEqual(result["status"], "STOPPED")
        self.assertTrue((loop_dir(root) / "kill_switch.json").exists())
        self.assertTrue((loop_dir(root) / "KILL_SWITCH").exists())
        self.assertFalse((root / ".bbc").exists())
        with self.assertRaises(RuntimeError):
            manager.start("daily_triage", "must not run")

    def test_history_and_metrics_are_deterministic(self) -> None:
        root = self._tmp()
        manager = LoopManager(root)
        manager.init()
        manager.start("security_scan")
        manager.budget_store.record_execution(runtime_ms=100, failed=False)
        history = manager.history()
        metrics = manager.metrics()
        self.assertEqual(len(history), 1)
        self.assertEqual(metrics["success_rate"], 100)
        self.assertEqual(metrics["executions"], 2)
        self.assertEqual(metrics["average_runtime_ms"], 50)

    def test_human_readable_state_export(self) -> None:
        root = self._tmp()
        manager = LoopManager(root)
        manager.init()
        state_path = wiki_vault_dir(root) / "Loop" / "STATE.md"
        self.assertTrue(state_path.exists())
        self.assertIn("BBC-AOS Loop State", state_path.read_text(encoding="utf-8"))
        self.assertFalse((root / "BBC_KNOWLEDGE").exists())

    def test_pilot_readiness_score_is_at_least_l2(self) -> None:
        root = self._tmp()
        (root / "README.md").write_text("# pilot\n", encoding="utf-8")
        (root / "tests").mkdir()
        manager = LoopManager(root)
        manager.init()
        result = manager.audit()
        self.assertGreaterEqual(result["readiness_score"], 80)
        self.assertIn(result["level"], {"L2", "L3"})
        self.assertTrue((reports_dir(root) / "loop_readiness_report.json").exists())
        self.assertFalse((root / "loop_readiness_report.json").exists())

    def _tmp(self):
        import tempfile
        from pathlib import Path

        return Path(tempfile.mkdtemp())


if __name__ == "__main__":
    unittest.main()
