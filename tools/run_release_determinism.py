"""Release determinism stress validation for BBC-AOS."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

from bbc_aos.agents.coder_agent import CoderAgent


SCENARIOS = [
    ("bugfix", "Fix bug in scalar calculations"),
    ("feature", "Add deterministic release marker feature"),
    ("refactor", "Refactor scalar helper for clarity"),
    ("review", "Review scalar implementation"),
    ("test", "Write tests for scalar helper"),
]


def _params(task_id: str, description: str, action: str) -> Dict[str, Any]:
    return {
        "context": {
            "selected_files": ["src/bbc_aos/core/bbc_scalar.py"],
            "task": {
                "task_id": task_id,
                "description": description,
                "action": action,
                "priority": 1,
                "dependencies": [],
            },
            "packed_context": {
                "selected_files": ["src/bbc_aos/core/bbc_scalar.py"],
                "packed_context": {
                    "project_skeleton": {
                        "root": str(Path.cwd()),
                        "hierarchy": ["src/bbc_aos/core/bbc_scalar.py"],
                    }
                },
            },
        },
        "metadata": {"trace_id": "release_trace", "replay_id": "release_replay"},
    }


def _stable_hash(payload: Dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def run(iterations: int = 1000) -> Dict[str, Any]:
    agent = CoderAgent()
    scenario_results: List[Dict[str, Any]] = []
    overall_pass = True

    for action, description in SCENARIOS:
        hashes = set()
        replay_ids = set()
        outputs = set()
        for _ in range(iterations):
            result = agent.execute(_params(f"release_{action}", description, action))
            hashes.add(result["deterministic_hash"])
            replay_ids.add(result["replay_id"])
            outputs.add(_stable_hash(result))

        passed = len(hashes) == 1 and len(replay_ids) == 1 and len(outputs) == 1
        overall_pass = overall_pass and passed
        scenario_results.append(
            {
                "scenario": action,
                "iterations": iterations,
                "unique_hashes": len(hashes),
                "unique_replay_ids": len(replay_ids),
                "unique_outputs": len(outputs),
                "passed": passed,
            }
        )

    return {
        "iterations_per_scenario": iterations,
        "scenarios": scenario_results,
        "zero_variance": overall_pass,
    }


def write_report(result: Dict[str, Any], path: Path) -> None:
    lines = [
        "# Release Determinism Report",
        "",
        f"Iterations per scenario: {result['iterations_per_scenario']}",
        f"Zero variance: {'YES' if result['zero_variance'] else 'NO'}",
        "",
        "| Scenario | Unique hashes | Unique replay ids | Unique outputs | Status |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for item in result["scenarios"]:
        lines.append(
            f"| {item['scenario']} | {item['unique_hashes']} | "
            f"{item['unique_replay_ids']} | {item['unique_outputs']} | "
            f"{'PASS' if item['passed'] else 'FAIL'} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    result = run()
    write_report(result, Path("release_determinism_report.md"))
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["zero_variance"] else 1)


if __name__ == "__main__":
    main()
