"""Operational loop pattern registry."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from bbc_aos.operations.loop_exceptions import UnknownLoopPatternError


@dataclass(frozen=True)
class LoopPattern:
    """A deterministic operational loop recipe."""

    name: str
    description: str
    schedule: str
    mode: str
    required_permissions: tuple[str, ...]
    human_gate: str
    stop_condition: str

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["required_permissions"] = list(self.required_permissions)
        return data


DEFAULT_PATTERNS: tuple[LoopPattern, ...] = (
    LoopPattern("daily_triage", "Review project state and summarize next actions.", "daily", "L1", ("read",), "none", "summary_generated"),
    LoopPattern("ci_sweeper", "Inspect failing CI and propose remediation.", "on_ci_failure", "L2", ("read", "propose"), "required", "ci_green_or_escalated"),
    LoopPattern("dependency_update", "Review dependency drift and propose safe updates.", "weekly", "L2", ("read", "propose"), "required", "no_updates_or_pr_ready"),
    LoopPattern("security_scan", "Run security checks and escalate BLOCK findings.", "daily", "L2", ("read", "scan"), "required", "no_block_findings"),
    LoopPattern("issue_triage", "Classify and prioritize open issues.", "daily", "L1", ("read",), "none", "issues_labeled"),
    LoopPattern("documentation_refresh", "Update docs from completed changes.", "weekly", "L2", ("read", "propose"), "required", "docs_current"),
    LoopPattern("benchmark_runner", "Run deterministic benchmark suite.", "weekly", "L2", ("read", "execute"), "required", "benchmark_report_written"),
    LoopPattern("release_preparation", "Prepare release validation and checklists.", "manual", "L2", ("read", "execute", "propose"), "required", "release_ready_or_blocked"),
)


class LoopPatternRegistry:
    """Load and describe loop patterns."""

    def __init__(self, project_root: str | Path = ".") -> None:
        self.project_root = Path(project_root)
        self.patterns_path = Path(__file__).with_name("patterns.yaml")

    def all(self) -> list[LoopPattern]:
        return sorted(DEFAULT_PATTERNS, key=lambda pattern: pattern.name)

    def get(self, name: str) -> LoopPattern:
        for pattern in self.all():
            if pattern.name == name:
                return pattern
        raise UnknownLoopPatternError(f"Unknown loop pattern: {name}")

    def write_default_yaml(self) -> Path:
        lines = ["patterns:"]
        for pattern in self.all():
            lines.append(f"  - name: {pattern.name}")
            lines.append(f"    description: {pattern.description}")
            lines.append(f"    schedule: {pattern.schedule}")
            lines.append(f"    mode: {pattern.mode}")
            lines.append("    required_permissions:")
            for permission in pattern.required_permissions:
                lines.append(f"      - {permission}")
            lines.append(f"    human_gate: {pattern.human_gate}")
            lines.append(f"    stop_condition: {pattern.stop_condition}")
        self.patterns_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return self.patterns_path
