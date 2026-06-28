"""Operational loop readiness audit."""

from __future__ import annotations

import json
import importlib.util
from pathlib import Path
from typing import Any

from bbc_aos.runtime_paths import reports_dir


READINESS_CRITERIA: tuple[tuple[str, str, int], ...] = (
    ("goal_clarity", "README.md", 8),
    ("verification_coverage", "tests", 10),
    ("independent_evaluator", "src/bbc_aos/agents/verification_agent.py", 10),
    ("stop_conditions", "src/bbc_aos/operations/loop_state.py", 8),
    ("budget_limits", "src/bbc_aos/operations/loop_budget.py", 8),
    ("rollback_strategy", "src/bbc_aos/commit", 8),
    ("sandbox_isolation", "src/bbc_aos/security", 8),
    ("human_approval", "src/bbc_aos/approval", 10),
    ("replay_support", "src/bbc_aos/integration/replay_engine.py", 8),
    ("observability", "src/bbc_aos/audit", 6),
    ("failure_memory", "src/bbc_aos/memory/failure_memory.py", 8),
    ("security_guardrails", "src/bbc_aos/security/guardrails.py", 8),
)


class LoopReadinessAuditor:
    """Deterministic project readiness scorer."""

    def __init__(self, project_root: str | Path = ".") -> None:
        self.project_root = Path(project_root)
        self.report_path = reports_dir(self.project_root) / "loop_readiness_report.json"

    def audit(self) -> dict[str, Any]:
        covered: list[str] = []
        missing: list[str] = []
        score = 0
        for criterion, path, weight in READINESS_CRITERIA:
            if self._covered(path):
                covered.append(criterion)
                score += weight
            else:
                missing.append(criterion)
        level = self._level(score)
        report: dict[str, Any] = {
            "readiness_score": score,
            "level": level,
            "covered": covered,
            "missing": missing,
            "criteria": [
                {"name": name, "path": path, "weight": weight}
                for name, path, weight in READINESS_CRITERIA
            ],
        }
        self.report_path.parent.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
        return report

    def _covered(self, path: str) -> bool:
        if (self.project_root / path).exists():
            return True
        if not path.startswith("src/bbc_aos/"):
            return False
        package_path = path.removeprefix("src/").replace("/", ".")
        if package_path.endswith(".py"):
            package_path = package_path[:-3]
        spec = importlib.util.find_spec(package_path)
        return spec is not None

    @staticmethod
    def _level(score: int) -> str:
        if score >= 85:
            return "L3"
        if score >= 65:
            return "L2"
        if score >= 40:
            return "L1"
        return "L0"
