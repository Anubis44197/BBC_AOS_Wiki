"""Prompt-injection firewall for untrusted retrieved content."""

from __future__ import annotations

import base64
import binascii
import logging
import re
from dataclasses import dataclass
from typing import List

logger = logging.getLogger("bbc_aos.security.prompt_firewall")


@dataclass(frozen=True)
class PromptFirewallResult:
    sanitized_text: str
    risk_score: int
    detected_patterns: List[str]
    blocked: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "sanitized_text": self.sanitized_text,
            "risk_score": self.risk_score,
            "detected_patterns": self.detected_patterns,
            "blocked": self.blocked,
        }


class PromptFirewall:
    """Treats retrieved text as untrusted and neutralizes instruction payloads."""

    INSTRUCTION_PATTERNS = {
        "ignore_previous_instructions": r"ignore\s+(?:all\s+)?previous\s+instructions?",
        "forget_all_instructions": r"forget\s+(?:all\s+)?instructions?",
        "you_are_chatgpt": r"you\s+are\s+chatgpt",
        "system_prompt": r"system\s+prompt",
        "execute_this": r"execute\s+this",
        "run_this_command": r"run\s+this\s+command",
        "act_as": r"\bact\s+as\b",
        "developer_instructions": r"developer\s+instructions?",
        "assistant_instructions": r"assistant\s+instructions?",
    }
    STRUCTURAL_PATTERNS = {
        "xml_tag": r"</?[A-Za-z][A-Za-z0-9:_-]*(?:\s+[^<>]*)?>",
        "html_hidden_prompt": r"(?is)<(?:input|textarea|div|span|p|section)[^>]*(?:hidden|display\s*:\s*none|visibility\s*:\s*hidden)[^>]*>.*?</(?:textarea|div|span|p|section)>|<input[^>]*(?:hidden|display\s*:\s*none|visibility\s*:\s*hidden)[^>]*>",
        "html_comment": r"(?s)<!--.*?-->",
        "markdown_hidden_block": r"(?m)^\s*\[//\]:\s*(?:#|<).*|<details\b.*?</details>",
        "control_character": r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]",
    }
    BASE64_CANDIDATE = re.compile(r"\b[A-Za-z0-9+/]{24,}={0,2}\b")

    def scan(self, text: str, source: str = "untrusted") -> PromptFirewallResult:
        raw = text or ""
        sanitized = raw
        detected: List[str] = []

        for rule_id, pattern in {**self.INSTRUCTION_PATTERNS, **self.STRUCTURAL_PATTERNS}.items():
            if re.search(pattern, raw, flags=re.IGNORECASE):
                detected.append(rule_id)
                sanitized = re.sub(pattern, "[UNTRUSTED_CONTENT_REMOVED]", sanitized, flags=re.IGNORECASE)

        decoded_hits = self._scan_base64_payloads(raw)
        detected.extend(decoded_hits)
        if decoded_hits:
            sanitized = self.BASE64_CANDIDATE.sub("[UNTRUSTED_CONTENT_REMOVED]", sanitized)

        unique = sorted(set(detected))
        risk_score = min(100, len(unique) * 20)
        if unique:
            logger.warning(
                "Prompt firewall detection source=%s risk=%d patterns=%s",
                source,
                risk_score,
                ",".join(unique),
            )
        return PromptFirewallResult(
            sanitized_text=sanitized,
            risk_score=risk_score,
            detected_patterns=unique,
            blocked=bool(unique),
        )

    def _scan_base64_payloads(self, text: str) -> List[str]:
        hits: List[str] = []
        for match in self.BASE64_CANDIDATE.finditer(text):
            candidate = match.group(0)
            try:
                decoded = base64.b64decode(candidate, validate=True).decode("utf-8", errors="ignore")
            except (binascii.Error, ValueError):
                continue
            for rule_id, pattern in self.INSTRUCTION_PATTERNS.items():
                if re.search(pattern, decoded, flags=re.IGNORECASE):
                    hits.append(f"base64_{rule_id}")
        return hits
