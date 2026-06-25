"""Deterministic reflection agent for BBC-AOS executions."""

import hashlib
import json
from typing import Any, Dict, List

from bbc_aos.agents.base_agent import BaseAgent


class ReflectionAgent(BaseAgent):
    """Generates replayable structured reflections after an execution."""

    AGENT_ID = "reflection_agent"
    AGENT_VERSION = "1.0.0"
    SUPPORTED_ACTIONS = ["reflect"]

    def initialize(self) -> None:
        pass

    def validate_input(self, params: Dict[str, Any]) -> bool:
        return isinstance(params, dict) and isinstance(params.get("context", {}), dict)

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        context = params.get("context", {})
        goal = context.get("goal") or context.get("goal_description") or ""
        outputs = context.get("outputs", {})
        failures = context.get("failures", [])
        retries = int(context.get("retries", 0) or 0)
        rollback = context.get("rollback", {})

        verify = outputs.get("verify_result", {})
        coder = outputs.get("coder_result", {})
        tester = outputs.get("tester_result", {})
        violations = verify.get("violations", []) or failures
        affected_files = (
            coder.get("modified_files", [])
            + coder.get("added_files", [])
            + coder.get("removed_files", [])
        )

        success_patterns = self._success_patterns(verify, coder, tester)
        failure_patterns = self._failure_patterns(violations, rollback)
        lessons = self._lessons(goal, success_patterns, failure_patterns, affected_files)
        recommendations = self._recommendations(failure_patterns, affected_files)
        future_risks = self._future_risks(tester, retries, affected_files)

        payload = {
            "goal": goal,
            "success_patterns": success_patterns,
            "failure_patterns": failure_patterns,
            "lessons_learned": lessons,
            "recommendations": recommendations,
            "future_risks": future_risks,
            "reusable": bool(lessons or recommendations),
        }
        stable = json.dumps(payload, sort_keys=True, default=str)
        payload["deterministic_hash"] = hashlib.sha256(stable.encode("utf-8")).hexdigest()
        return payload

    def validate_output(self, result: Dict[str, Any]) -> bool:
        required = [
            "success_patterns",
            "failure_patterns",
            "lessons_learned",
            "recommendations",
            "future_risks",
            "deterministic_hash",
        ]
        return isinstance(result, dict) and all(key in result for key in required)

    def finalize(self) -> None:
        pass

    def _success_patterns(
        self,
        verify: Dict[str, Any],
        coder: Dict[str, Any],
        tester: Dict[str, Any],
    ) -> List[str]:
        patterns: List[str] = []
        if verify.get("verdict") == "APPROVED":
            patterns.append("verification_approved")
        if coder.get("patch"):
            patterns.append("deterministic_patch_generated")
        if tester.get("validation_tasks") is not None:
            patterns.append("validation_plan_generated")
        return patterns

    def _failure_patterns(self, violations: List[Any], rollback: Dict[str, Any]) -> List[str]:
        patterns: List[str] = []
        for violation in violations:
            text = str(violation).upper()
            if "IMPORT" in text:
                patterns.append("MISSING_IMPORT")
            elif "SYMBOL" in text:
                patterns.append("INVALID_SYMBOL")
            elif "BLAST" in text:
                patterns.append("BLAST_RADIUS_VIOLATION")
            elif "PERMISSION" in text:
                patterns.append("PERMISSION_VIOLATION")
            elif "SECURITY" in text:
                patterns.append("SECURITY_GUARDRAIL")
            else:
                patterns.append("VERIFICATION_REJECTION")
        if rollback:
            patterns.append("ROLLBACK_OCCURRED")
        return sorted(set(patterns))

    def _lessons(
        self,
        goal: str,
        success_patterns: List[str],
        failure_patterns: List[str],
        affected_files: List[str],
    ) -> List[str]:
        if failure_patterns:
            return [f"{goal or 'Task'} exposed {', '.join(failure_patterns)}."]
        if affected_files:
            return [f"{goal or 'Task'} safely targeted {len(affected_files)} file(s)."]
        if success_patterns:
            return ["Read-only or shadow execution completed without patching."]
        return []

    def _recommendations(self, failure_patterns: List[str], affected_files: List[str]) -> List[str]:
        recommendations: List[str] = []
        if "MISSING_IMPORT" in failure_patterns:
            recommendations.append("Verify imports before patch generation.")
        if "BLAST_RADIUS_VIOLATION" in failure_patterns:
            recommendations.append("Re-run context selection before generating a patch.")
        if "SECURITY_GUARDRAIL" in failure_patterns:
            recommendations.append("Remove dangerous operations from the proposed patch.")
        if affected_files:
            recommendations.append("Review affected files before approving commit.")
        return recommendations

    def _future_risks(
        self,
        tester: Dict[str, Any],
        retries: int,
        affected_files: List[str],
    ) -> List[str]:
        risks: List[str] = []
        risk_level = tester.get("risk_level")
        if risk_level in ("HIGH", "CRITICAL"):
            risks.append(f"{risk_level}_risk_requires_manual_review")
        if retries:
            risks.append("recurring_retry_pressure")
        if len(affected_files) > 5:
            risks.append("large_blast_radius")
        return risks
