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
        "ignore_all_instructions": r"ignore\s+all\s+instructions?",
        "forget_all_instructions": r"forget\s+(?:all\s+)?instructions?",
        "you_are_chatgpt": r"you\s+are\s+chatgpt",
        "system_prompt": r"system\s+prompt",
        "execute_this": r"execute\s+this",
        "run_this_command": r"run\s+this\s+command",
        "run_shell_commands": r"run\s+(?:shell\s+)?commands?",
        "subprocess_shell_true": r"\bsubprocess\b.*\bshell\s*=\s*True\b",
        "shell_true": r"\bshell\s*=\s*True\b",
        "powershell": r"\bpowershell(?:\.exe)?\b",
        "cmd_exe": r"\bcmd\.exe\b|\bcmd\s+/c\b",
        "os_system": r"\bos\.system\s*\(",
        "act_as": r"\bact\s+as\b",
        "developer_instructions": r"developer\s+instructions?",
        "assistant_instructions": r"assistant\s+instructions?",
        "reveal_hidden_prompt": r"\breveal\s+(?:the\s+)?hidden\s+prompt\b",
        "delete_repository": r"\bdelete\s+(?:the\s+)?(?:repository|repo|project)\b",
        "modify_outside_workspace": r"\bmodify\s+files?\s+outside\s+(?:the\s+)?workspace\b",
        "disable_approval": r"\bdisable\s+(?:the\s+)?approval\s+system\b",
        "ignore_approval": r"\bignore\s+(?:the\s+)?approval\b",
        "overwrite_policy": r"\boverwrite\s+(?:the\s+)?(?:approval\s+)?policy\b",
        "mark_safe": r"\bmark\s+(?:this\s+)?(?:malicious\s+request\s+as\s+)?safe\b",
        "turn_off_verification": r"\bturn\s+off\s+verification\b|\bdisable\s+verification\b",
        "skip_approval": r"\bskip\s+(?:the\s+)?approval\s+gate\b|\bbypass\s+(?:the\s+)?approval\b",
        "read_secrets": r"\bread\s+(?:the\s+)?secrets?\b|\bexfiltrate\s+(?:secrets?|tokens?|credentials?)\b",
        "environment_secrets": r"\b(?:print|show|dump|read)\s+(?:environment\s+)?secrets?\b|\benvironment\s+variables?\b",
        "bypass_sandbox": r"\bbypass\s+(?:the\s+)?sandbox\b",
        "copy_env": r"\bcopy\s+\.env\b|\.env\s+to\s+(?:a\s+)?public\s+folder\b",
        "persist_outside_workspace": r"\b(?:persist|persistence|install\s+persistence)\s+outside\s+(?:the\s+)?workspace\b",
        "write_absolute_path": r"\bwrite\s+[A-Za-z]:[\\/][^\s]+",
        "dangerous_delete": r"\brm\s+-rf\b|\bshutil\.rmtree\s*\(",
        "delete_all_files": r"\bdelete\s+all\s+files?\b|\bdelete\s+.*recursively\b",
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
