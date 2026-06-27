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
        from bbc_aos.security.prompt_firewall import PromptFirewall

        firewall_result = PromptFirewall().scan(patch, source="patch")
        for pattern in firewall_result.detected_patterns:
            findings.append(
                GuardrailFinding(
                    severity="BLOCK",
                    rule_id=f"prompt_injection_{pattern}",
                    message=f"BLOCK security guardrail matched: prompt_injection_{pattern}",
                    evidence=pattern,
                )
            )
        return findings

    def validate_patch(self, patch: str) -> Dict[str, object]:
        findings = self.scan_patch(patch)
        blocked = any(f.severity == "BLOCK" for f in findings)
        return {
            "allowed": not blocked,
            "findings": [f.to_dict() for f in findings],
        }

    def validate_prompt(self, prompt: str) -> Dict[str, object]:
        from bbc_aos.security.prompt_firewall import PromptFirewall
        from bbc_aos.security.policy_integrity_guard import PolicyIntegrityGuard
        from bbc_aos.security.system_prompt_leak_guard import SystemPromptLeakGuard
        from bbc_aos.security.tool_permission_guard import ToolPermissionGuard
        from bbc_aos.security.workspace_escape_guard import WorkspaceEscapeGuard

        firewall_result = PromptFirewall().scan(prompt, source="user_prompt")
        findings = [
            GuardrailFinding(
                severity="BLOCK",
                rule_id=f"prompt_{pattern}",
                message=f"BLOCK security guardrail matched: prompt_{pattern}",
                evidence=pattern,
            )
            for pattern in firewall_result.detected_patterns
        ]
        for guard in (
            SystemPromptLeakGuard(),
            PolicyIntegrityGuard(),
            WorkspaceEscapeGuard(),
            ToolPermissionGuard(),
        ):
            for finding in guard.scan(prompt):
                findings.append(
                    GuardrailFinding(
                        severity="BLOCK",
                        rule_id=f"prompt_{finding.rule_id}",
                        message=f"BLOCK security guardrail matched: prompt_{finding.rule_id}",
                        evidence=finding.evidence,
                    )
                )
        return {
            "allowed": not findings,
            "findings": [f.to_dict() for f in findings],
            "sanitized_text": firewall_result.sanitized_text,
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
