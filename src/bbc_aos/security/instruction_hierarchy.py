"""Trusted/untrusted instruction boundary enforcement."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from bbc_aos.security.prompt_firewall import PromptFirewall


class TrustLevel(str, Enum):
    TRUSTED = "trusted"
    UNTRUSTED = "untrusted"


TRUSTED_SOURCES = {"system", "system_prompt", "agent_instruction", "security_policy"}
UNTRUSTED_SOURCES = {
    "readme",
    "comments",
    "docstrings",
    "markdown",
    "obsidian",
    "tool_output",
    "external_text",
    "retrieved_file",
    "user_file",
}


@dataclass(frozen=True)
class InstructionBoundaryResult:
    allowed: bool
    trust_level: TrustLevel
    sanitized_text: str
    violations: list[str]
    detected_patterns: list[str]

    def to_dict(self) -> dict[str, object]:
        return {
            "allowed": self.allowed,
            "trust_level": self.trust_level.value,
            "sanitized_text": self.sanitized_text,
            "violations": self.violations,
            "detected_patterns": self.detected_patterns,
        }


class InstructionHierarchy:
    """Prevents retrieved content from overriding trusted agent policy."""

    def __init__(self) -> None:
        self._firewall = PromptFirewall()

    def classify_source(self, source: str) -> TrustLevel:
        normalized = (source or "").strip().lower()
        if normalized in TRUSTED_SOURCES:
            return TrustLevel.TRUSTED
        if normalized in UNTRUSTED_SOURCES:
            return TrustLevel.UNTRUSTED
        return TrustLevel.UNTRUSTED

    def validate_boundary(self, content: str, source: str = "retrieved_file") -> InstructionBoundaryResult:
        trust_level = self.classify_source(source)
        if trust_level == TrustLevel.TRUSTED:
            return InstructionBoundaryResult(True, trust_level, content or "", [], [])

        firewall_result = self._firewall.scan(content or "", source=source)
        violations = []
        if firewall_result.blocked:
            violations.append("Untrusted content attempted to carry instructions.")
        return InstructionBoundaryResult(
            allowed=not firewall_result.blocked,
            trust_level=trust_level,
            sanitized_text=firewall_result.sanitized_text,
            violations=violations,
            detected_patterns=firewall_result.detected_patterns,
        )
