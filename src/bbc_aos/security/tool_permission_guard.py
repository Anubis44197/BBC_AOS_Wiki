"""Hard-deny guard for direct tool and shell execution requests."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class PromptGuardFinding:
    rule_id: str
    evidence: str


class ToolPermissionGuard:
    """Blocks shell/tool execution requests before planning."""

    PATTERNS: dict[str, str] = {
        "subprocess_shell_true": r"\bsubprocess\b.*\bshell\s*=\s*True\b",
        "shell_true": r"\bshell\s*=\s*True\b",
        "powershell": r"\bpowershell(?:\.exe)?\b",
        "cmd_exe": r"\bcmd\.exe\b|\bcmd\s+/c\b",
        "direct_tool_execution": r"\bexecute\s+(?:this\s+)?(?:tool|command)\b",
    }

    def scan(self, prompt: str) -> list[PromptGuardFinding]:
        text = prompt or ""
        findings: list[PromptGuardFinding] = []
        for rule_id, pattern in self.PATTERNS.items():
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                findings.append(PromptGuardFinding(rule_id, match.group(0)))
        return findings
