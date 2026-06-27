"""Hard-deny guard for system prompt and hidden instruction disclosure."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class PromptGuardFinding:
    rule_id: str
    evidence: str


class SystemPromptLeakGuard:
    """Blocks attempts to reveal hidden/system/developer instructions."""

    PATTERNS: dict[str, str] = {
        "reveal_hidden_prompt": r"\breveal\s+(?:the\s+)?hidden\s+prompt\b",
        "show_system_prompt": r"\bshow\s+(?:the\s+)?system\s+prompt\b",
        "hidden_instructions": r"\b(?:hidden|internal)\s+(?:prompt|instructions?)\b",
        "developer_instructions": r"\bshow\s+(?:the\s+)?developer\s+instructions?\b",
    }

    def scan(self, prompt: str) -> list[PromptGuardFinding]:
        text = prompt or ""
        findings: list[PromptGuardFinding] = []
        for rule_id, pattern in self.PATTERNS.items():
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                findings.append(PromptGuardFinding(rule_id, match.group(0)))
        return findings
