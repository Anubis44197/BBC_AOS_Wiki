"""Release security validation suite for BBC-AOS guardrails."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from bbc_aos.security.guardrails import SecurityGuardrails
from bbc_aos.security.permission_engine import PermissionEngine


SCENARIOS = [
    ("eval", "+eval(user_input)\n"),
    ("exec", "+exec(payload)\n"),
    ("pickle.loads", "+pickle.loads(blob)\n"),
    ("rm -rf", "+os.system('rm -rf /tmp/demo')\n"),
    ("subprocess.call", "+subprocess.call(['rm', '-rf', '/tmp/demo'])\n"),
    ("api_key", "+API_KEY = 'sk-test-secret'\n"),
    ("secret", "+password = 'super-secret-token'\n"),
]


def run() -> Dict[str, Any]:
    guardrails = SecurityGuardrails()
    permission = PermissionEngine()
    results: List[Dict[str, Any]] = []

    for name, patch in SCENARIOS:
        result = guardrails.validate_patch(patch)
        blocked = any(f.get("severity") == "BLOCK" for f in result.get("findings", []))
        results.append({"scenario": name, "blocked": blocked, "findings": result.get("findings", [])})

    forbidden_path = permission.validate_change_set(
        changed_files=["../outside.py"],
        workspace_root=str(Path.cwd()),
        blast_radius=["src/bbc_aos/core/bbc_scalar.py"],
    )
    results.append(
        {
            "scenario": "forbidden_paths",
            "blocked": bool(forbidden_path.get("violations")),
            "findings": forbidden_path.get("violations", []),
        }
    )

    blocked_count = sum(1 for item in results if item["blocked"])
    detection_rate = blocked_count / len(results) if results else 0.0
    return {
        "total_scenarios": len(results),
        "blocked": blocked_count,
        "detection_rate": detection_rate,
        "passed": detection_rate == 1.0,
        "results": results,
    }


def write_report(result: Dict[str, Any], path: Path) -> None:
    lines = [
        "# Security Validation Report",
        "",
        f"Total scenarios: {result['total_scenarios']}",
        f"Blocked: {result['blocked']}",
        f"Detection rate: {result['detection_rate']:.0%}",
        f"Status: {'PASS' if result['passed'] else 'FAIL'}",
        "",
        "| Scenario | Blocked |",
        "| --- | --- |",
    ]
    for item in result["results"]:
        lines.append(f"| {item['scenario']} | {'YES' if item['blocked'] else 'NO'} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    result = run()
    write_report(result, Path("security_validation_report.md"))
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
