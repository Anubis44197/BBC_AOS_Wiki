"""Patch-level security guardrails for BBC-AOS."""

import re
from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class GuardrailFinding:
    severity: str
    rule_id: str
    message: str
    evidence: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "severity": self.severity,
            "rule_id": self.rule_id,
            "message": self.message,
            "evidence": self.evidence,
        }


class SecurityGuardrails:
    """Detects dangerous code or command patterns in proposed patches."""

    BLOCK_PATTERNS = {
        "write_env": r"(?m)^\+.*(?:\.env|secrets/|credentials/)",
        "os_system": r"(?m)^\+.*\bos\.system\s*\(",
        "subprocess_call": r"(?m)^\+.*\bsubprocess\.(?:call|Popen|run)\s*\(",
        "api_secret": r"(?im)^\+.*(?:sk-[A-Za-z0-9_-]{12,}|Bearer\s+[A-Za-z0-9._-]+|(?:api[_-]?key|password|secret|token)\s*=)",
        "rm_rf": r"(?m)^\+.*\brm\s+-rf\b",
        "shutil_rmtree": r"(?m)^\+.*\bshutil\.rmtree\s*\(",
        "path_unlink_recursive": r"(?m)^\+.*\bPath\([^)]*\)\.unlink\s*\([^)]*recursive\s*=\s*True",
        "eval": r"(?m)^\+.*\beval\s*\(",
        "exec": r"(?m)^\+.*\bexec\s*\(",
        "pickle_loads": r"(?m)^\+.*\bpickle\.loads\s*\(",
    }

    WARN_PATTERNS = {
        "sys_exit": r"(?m)^\+.*\bsys\.exit\s*\(",
        "dynamic_import": r"(?m)^\+.*\b__import__\s*\(",
    }

    def scan_patch(self, patch: str) -> List[GuardrailFinding]:
        findings: List[GuardrailFinding] = []
        for rule_id, pattern in self.BLOCK_PATTERNS.items():
            findings.extend(self._scan(pattern, patch, "BLOCK", rule_id))
        for rule_id, pattern in self.WARN_PATTERNS.items():
            findings.extend(self._scan(pattern, patch, "WARN", rule_id))
        return findings

    def validate_patch(self, patch: str) -> Dict[str, object]:
        findings = self.scan_patch(patch)
        blocked = any(f.severity == "BLOCK" for f in findings)
        return {
            "allowed": not blocked,
            "findings": [f.to_dict() for f in findings],
        }

    def _scan(
        self,
        pattern: str,
        patch: str,
        severity: str,
        rule_id: str,
    ) -> List[GuardrailFinding]:
        findings: List[GuardrailFinding] = []
        for match in re.finditer(pattern, patch):
            line = match.group(0)[:160]
            findings.append(
                GuardrailFinding(
                    severity=severity,
                    rule_id=rule_id,
                    message=f"{severity} security guardrail matched: {rule_id}",
                    evidence=line,
                )
            )
        return findings
