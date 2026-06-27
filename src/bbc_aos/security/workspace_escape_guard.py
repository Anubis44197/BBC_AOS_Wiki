"""Hard-deny guard for filesystem and workspace escape attempts."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class PromptGuardFinding:
    rule_id: str
    evidence: str


class WorkspaceEscapeGuard:
    """Blocks attempts to move secrets or persistence outside the workspace."""

    PATTERNS: dict[str, str] = {
        "copy_env": r"\bcopy\s+\.env\b|\bcopy\s+.*\b(?:secret|token|credential)s?\b",
        "public_env": r"\.env\s+to\s+(?:a\s+)?public\s+folder\b",
        "persist_outside_workspace": r"\b(?:persist|persistence|install\s+persistence)\s+outside\s+(?:the\s+)?workspace\b",
        "outside_workspace": r"\boutside\s+(?:the\s+)?workspace\b",
        "absolute_user_path": r"\b[A-Za-z]:[\\/](?:Users|Windows|ProgramData)[\\/]",
    }

    def scan(self, prompt: str) -> list[PromptGuardFinding]:
        text = prompt or ""
        findings: list[PromptGuardFinding] = []
        for rule_id, pattern in self.PATTERNS.items():
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                findings.append(PromptGuardFinding(rule_id, match.group(0)))
        return findings
