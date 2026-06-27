"""Hard-deny guard for approval and policy-integrity bypass attempts."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class PromptGuardFinding:
    rule_id: str
    evidence: str


class PolicyIntegrityGuard:
    """Blocks attempts to bypass, overwrite, or mislabel safety policy."""

    PATTERNS: dict[str, str] = {
        "ignore_approval": r"\bignore\s+(?:the\s+)?approval\b",
        "overwrite_policy": r"\boverwrite\s+(?:the\s+)?(?:approval\s+)?policy\b",
        "mark_safe": r"\bmark\s+(?:this\s+)?(?:malicious\s+request\s+as\s+)?safe\b",
        "disable_policy": r"\bdisable\s+(?:the\s+)?(?:security\s+)?policy\b",
        "approval_bypass": r"\b(?:bypass|skip)\s+(?:the\s+)?approval\b",
    }

    def scan(self, prompt: str) -> list[PromptGuardFinding]:
        text = prompt or ""
        findings: list[PromptGuardFinding] = []
        for rule_id, pattern in self.PATTERNS.items():
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                findings.append(PromptGuardFinding(rule_id, match.group(0)))
        return findings
