"""Bounded local workload runner for BBC-AOS smoke and stress checks."""

from __future__ import annotations

import concurrent.futures
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parent
MAX_ASK_WORKERS = 4
MAX_FAST_WORKERS = 4


@dataclass(frozen=True)
class CommandResult:
    label: str
    command: list[str]
    returncode: int
    output: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


def bbc_cmd(*args: str) -> list[str]:
    return [sys.executable, "-m", "bbc_aos.main", *args]


def run_cmd(label: str, command: list[str]) -> CommandResult:
    env = os.environ.copy()
    src = str(ROOT / "src")
    env["PYTHONPATH"] = src + os.pathsep + env.get("PYTHONPATH", "")
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return CommandResult(label, command, completed.returncode, completed.stdout)


def run_batch(name: str, commands: Iterable[tuple[str, list[str]]], workers: int) -> list[CommandResult]:
    print(f"Starting {name}")
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(run_cmd, label, command) for label, command in commands]
        results = [future.result() for future in futures]
    failed = [result for result in results if not result.ok]
    print(f"{name}: {len(results) - len(failed)}/{len(results)} passed")
    for result in failed[:5]:
        print(f"[FAILED] {result.label}: {' '.join(result.command)}")
        print(result.output.strip()[:1200])
    return results


def latest_replay_ids(limit: int) -> list[str]:
    audit_path = ROOT / ".bbc" / "logs" / "integration_audit.jsonl"
    if not audit_path.exists():
        return []
    replay_ids: list[str] = []
    seen: set[str] = set()
    for line in reversed(audit_path.read_text(encoding="utf-8", errors="ignore").splitlines()):
        try:
            replay_id = str(json.loads(line).get("replay_id", ""))
        except json.JSONDecodeError:
            continue
        if replay_id and replay_id not in seen:
            seen.add(replay_id)
            replay_ids.append(replay_id)
        if len(replay_ids) >= limit:
            break
    return replay_ids


def main() -> int:
    results: list[CommandResult] = []

    phase3 = [
        (f"ask-realistic-{i}", bbc_cmd("ask", "--shadow", f"realistic task {i}"))
        for i in range(12)
    ]
    results.extend(run_batch("Phase 3: bounded shadow tasks", phase3, MAX_ASK_WORKERS))

    large_changes = [
        "Unified Search API",
        "Redis cache layer",
        "OpenTelemetry integration",
        "Global error middleware",
        "Authentication refactor",
    ]
    phase4 = [
        (f"ask-large-{name}", bbc_cmd("ask", "--shadow", f"simulate large change: {name}"))
        for name in large_changes
    ]
    results.extend(run_batch("Phase 4: large shadow changes", phase4, MAX_ASK_WORKERS))

    phase5 = [
        ("loop-init", bbc_cmd("loop", "init")),
        ("loop-start-ci", bbc_cmd("loop", "start", "ci_sweeper", "--goal", "runner workload")),
        ("loop-start-docs", bbc_cmd("loop", "start", "documentation_refresh", "--goal", "runner workload")),
        ("loop-audit", bbc_cmd("loop", "audit")),
        ("loop-status", bbc_cmd("loop", "status")),
    ]
    results.extend(run_batch("Phase 5: loop commands", phase5, 1))

    phase6 = [
        (f"security-shadow-{i}", bbc_cmd("ask", "--shadow", f"malicious prompt {i}"))
        for i in range(10)
    ]
    results.extend(run_batch("Phase 6: security shadow tasks", phase6, MAX_ASK_WORKERS))

    replay_ids = latest_replay_ids(20)
    phase7 = [(f"replay-{replay_id}", bbc_cmd("replay", replay_id)) for replay_id in replay_ids]
    if phase7:
        results.extend(run_batch("Phase 7: replay existing ids", phase7, MAX_FAST_WORKERS))
    else:
        print("Phase 7: skipped, no replay ids found in .bbc/logs/integration_audit.jsonl")

    failed = [result for result in results if not result.ok]
    print(f"All workloads completed. Passed={len(results) - len(failed)} Failed={len(failed)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
