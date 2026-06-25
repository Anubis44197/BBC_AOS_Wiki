"""BBC-AOS VerificationAgent - Phase 11E

Production implementation of the VerificationAgent responsible for verifying
schemas, dependencies, blast radius, replay IDs, risk levels, and contract constraints.
"""

import hashlib
import json
import logging
import re
from typing import Any, Dict, List, Set

from bbc_aos.agents.base_agent import BaseAgent
from bbc_aos.integration.validation_gateway import ValidationGateway
from bbc_aos.integration.integration_audit_log import IntegrationAuditLog, IntegrationAuditEvent

# Configure logger
logger = logging.getLogger("bbc_aos.agents.verification_agent")


# ---------------------------------------------------------------------------
# Verification Engine (Stateless, Stateless Checks)
# ---------------------------------------------------------------------------

class _VerificationEngine:
    """Performs deterministic verification on CodeDiff, ValidationPlan, and Context."""

    SUPPORTED_RISKS: List[str] = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

    def verify(
        self,
        task_id: str,
        description: str,
        code_diff: Dict[str, Any],
        validation_plan: Dict[str, Any],
        packed_context: Dict[str, Any],
        trace_id: str,
        replay_id: str,
    ) -> List[str]:
        """Runs all contract verification rules.

        Args:
            task_id: Unique task identifier.
            description: Task description.
            code_diff: CoderAgent CodeDiff dictionary.
            validation_plan: TesterAgent ValidationPlan dictionary.
            packed_context: ContextAgent packed context package.
            trace_id: Current execution trace ID.
            replay_id: Current execution replay ID.

        Returns:
            A list of violation strings. If empty, the verification has passed.
        """
        violations: List[str] = []

        # 1. Schema Validation
        self._verify_schemas(code_diff, validation_plan, packed_context, violations)
        if violations:
            # Short-circuit if basic schemas are corrupted
            return violations

        # 2. Replay Validation
        self._verify_replay(code_diff, validation_plan, trace_id, replay_id, violations)

        # 3. Blast Radius Validation
        self._verify_blast_radius(code_diff, packed_context, violations)

        # 4. Risk Validation
        self._verify_risk(description, code_diff, validation_plan, violations)

        # 5. Dependency Validation
        self._verify_dependencies(validation_plan, violations)

        # 6. Contract Validation
        self._verify_contracts(code_diff, validation_plan, violations)

        return violations

    def _verify_schemas(
        self,
        code_diff: Dict[str, Any],
        validation_plan: Dict[str, Any],
        packed_context: Dict[str, Any],
        violations: List[str],
    ) -> None:
        """Verifies structure and types of the inputs."""
        # CodeDiff schema
        for field in ("modified_files", "added_files", "removed_files", "patch", "deterministic_hash"):
            if field not in code_diff:
                violations.append(f"Schema violation: CodeDiff is missing field '{field}'")
        
        if not isinstance(code_diff.get("modified_files"), list):
            violations.append("Schema violation: CodeDiff modified_files is not a list")
        if not isinstance(code_diff.get("added_files"), list):
            violations.append("Schema violation: CodeDiff added_files is not a list")
        if not isinstance(code_diff.get("removed_files"), list):
            violations.append("Schema violation: CodeDiff removed_files is not a list")
        if not isinstance(code_diff.get("patch"), str):
            violations.append("Schema violation: CodeDiff patch is not a string")

        # ValidationPlan schema
        for field in ("validation_tasks", "risk_level", "coverage_targets", "deterministic_hash"):
            if field not in validation_plan:
                violations.append(f"Schema violation: ValidationPlan is missing field '{field}'")
        
        if not isinstance(validation_plan.get("validation_tasks"), list):
            violations.append("Schema violation: ValidationPlan validation_tasks is not a list")
        if not isinstance(validation_plan.get("coverage_targets"), dict):
            violations.append("Schema violation: ValidationPlan coverage_targets is not a dictionary")

        # Context schema
        if "selected_files" not in packed_context:
            violations.append("Schema violation: packed_context is missing 'selected_files'")
        elif not isinstance(packed_context["selected_files"], list):
            violations.append("Schema violation: packed_context selected_files is not a list")

    def _verify_replay(
        self,
        code_diff: Dict[str, Any],
        validation_plan: Dict[str, Any],
        trace_id: str,
        replay_id: str,
        violations: List[str],
    ) -> None:
        """Checks trace/replay propagation consistency."""
        diff_trace = code_diff.get("trace_id")
        diff_replay = code_diff.get("replay_id")
        plan_trace = validation_plan.get("trace_id")
        plan_replay = validation_plan.get("replay_id")

        if diff_trace and diff_trace != trace_id:
            violations.append(f"Replay violation: CodeDiff trace_id '{diff_trace}' does not match context trace_id '{trace_id}'")
        if diff_replay and diff_replay != replay_id:
            violations.append(f"Replay violation: CodeDiff replay_id '{diff_replay}' does not match context replay_id '{replay_id}'")
        if plan_trace and plan_trace != trace_id:
            violations.append(f"Replay violation: ValidationPlan trace_id '{plan_trace}' does not match context trace_id '{trace_id}'")
        if plan_replay and plan_replay != replay_id:
            violations.append(f"Replay violation: ValidationPlan replay_id '{plan_replay}' does not match context replay_id '{replay_id}'")

    def _verify_blast_radius(
        self,
        code_diff: Dict[str, Any],
        packed_context: Dict[str, Any],
        violations: List[str],
    ) -> None:
        """Enforces that affected files strictly reside inside context selected_files."""
        selected_files = set(packed_context.get("selected_files", []))
        modified_files = code_diff.get("modified_files", [])
        added_files = code_diff.get("added_files", [])
        removed_files = code_diff.get("removed_files", [])

        # Check modified and removed files strictly
        for file in modified_files + removed_files:
            if file not in selected_files:
                violations.append(
                    f"Blast radius violation: file '{file}' is modified/added/removed in CodeDiff but was not selected in packed_context"
                )

        # Check added files (allow hash suffix for derived additions)
        for file in added_files:
            if file in selected_files:
                continue
            
            # Clean hash suffix like _a1b2c3.py or .py_a1b2c3.py
            cleaned_file = re.sub(r"_[a-f0-9]{6}\.py$", ".py", file)
            if cleaned_file in selected_files:
                continue
            cleaned_file_no_py = re.sub(r"_[a-f0-9]{6}\.py$", "", file)
            if cleaned_file_no_py in selected_files:
                continue

            violations.append(
                f"Blast radius violation: file '{file}' is modified/added/removed in CodeDiff but was not selected in packed_context"
            )

    def _verify_risk(
        self,
        description: str,
        code_diff: Dict[str, Any],
        validation_plan: Dict[str, Any],
        violations: List[str],
    ) -> None:
        """Verifies risk classification matches calculation."""
        plan_risk = validation_plan.get("risk_level")
        if plan_risk not in self.SUPPORTED_RISKS:
            violations.append(f"Risk violation: ValidationPlan risk_level '{plan_risk}' is invalid")
            return

        # Calculated risk classification logic (identical to TesterAgent)
        desc_lower = description.lower()
        modified_files = code_diff.get("modified_files", [])
        added_files = code_diff.get("added_files", [])
        removed_files = code_diff.get("removed_files", [])
        num_files = len(modified_files) + len(added_files) + len(removed_files)

        def matches_word(keywords: List[str]) -> bool:
            for kw in keywords:
                pattern = r"\b" + re.escape(kw) + r"\b"
                if re.search(pattern, desc_lower):
                    return True
            return False

        # CRITICAL triggers
        if len(removed_files) > 0:
            calc_risk = "CRITICAL"
        elif matches_word(["security", "chaos", "recovery", "auth", "critical"]):
            calc_risk = "CRITICAL"
        elif num_files > 15:
            calc_risk = "CRITICAL"
        # HIGH triggers
        elif matches_word(["performance", "migration", "refactor"]):
            calc_risk = "HIGH"
        elif num_files > 8:
            calc_risk = "HIGH"
        # MEDIUM triggers
        elif matches_word(["fix", "bug", "patch"]):
            calc_risk = "MEDIUM"
        elif num_files > 2:
            calc_risk = "MEDIUM"
        else:
            calc_risk = "LOW"

        if plan_risk != calc_risk:
            violations.append(
                f"Risk violation: ValidationPlan risk_level claims '{plan_risk}' but verification engine calculates '{calc_risk}'"
            )

    def _verify_dependencies(
        self,
        validation_plan: Dict[str, Any],
        violations: List[str],
    ) -> None:
        """Validates that tasks DAG has no cycles, valid references, and depth <= 5."""
        tasks = validation_plan.get("validation_tasks", [])
        task_map = {t.get("task_id"): t for t in tasks if isinstance(t, dict)}

        depths: Dict[str, int] = {}

        def get_depth(task_id: str, visited: Set[str]) -> int:
            if task_id in visited:
                raise ValueError(f"Cyclic dependency detected on task '{task_id}'")
            if task_id in depths:
                return depths[task_id]

            task = task_map.get(task_id)
            if not task:
                raise ValueError(f"Dependency task '{task_id}' not found in validation plan")

            deps = task.get("dependencies", [])
            if not deps:
                depths[task_id] = 1
                return 1

            visited.add(task_id)
            max_dep_depth = max(get_depth(d, visited) for d in deps)
            visited.remove(task_id)

            depths[task_id] = 1 + max_dep_depth
            return depths[task_id]

        for t in tasks:
            if not isinstance(t, dict):
                continue
            task_id = t.get("task_id")
            if not task_id:
                violations.append("Dependency violation: Validation task is missing 'task_id'")
                continue

            try:
                task_depth = get_depth(task_id, set())
                if task_depth > 5:
                    violations.append(
                        f"Dependency violation: Task '{task_id}' dependency depth {task_depth} exceeds limit of 5"
                    )
            except ValueError as e:
                violations.append(f"Dependency violation: {str(e)}")

    def _verify_contracts(
        self,
        code_diff: Dict[str, Any],
        validation_plan: Dict[str, Any],
        violations: List[str],
    ) -> None:
        """Verifies hex hash formats and stable tasks sorting."""
        diff_hash = code_diff.get("deterministic_hash", "")
        plan_hash = validation_plan.get("deterministic_hash", "")

        if len(diff_hash) != 64:
            violations.append("Contract violation: CodeDiff deterministic_hash is not a valid 64-character SHA-256 hash")
        if len(plan_hash) != 64:
            violations.append("Contract violation: ValidationPlan deterministic_hash is not a valid 64-character SHA-256 hash")

        # Verify stable task ordering
        tasks = validation_plan.get("validation_tasks", [])
        if not all(isinstance(t, dict) for t in tasks):
            return

        sorted_tasks = sorted(
            tasks,
            key=lambda x: (x.get("priority", 9), x.get("task_id", ""))
        )

        # Assert task order match
        actual_ids = [t.get("task_id") for t in tasks]
        expected_ids = [t.get("task_id") for t in sorted_tasks]
        if actual_ids != expected_ids:
            violations.append("Contract violation: Validation tasks are not ordered deterministically by priority and task_id")


# ---------------------------------------------------------------------------
# VerificationAgent
# ---------------------------------------------------------------------------

class VerificationAgent(BaseAgent):
    """VerificationAgent is the final gate validating schemas, dependencies, and blast radius.

    It returns a verdict of APPROVED or REJECTED alongside a list of violations.
    """

    AGENT_ID: str = "verification_agent"
    AGENT_VERSION: str = "1.0.0"
    SUPPORTED_ACTIONS: List[str] = ["verify_contracts", "verify_gate"]

    def __init__(self) -> None:
        """Initializes the VerificationAgent."""
        self._engine = _VerificationEngine()

    def initialize(self) -> None:
        """Logs initialization telemetry."""
        logger.info("[VERIFICATION AGENT] Initializing VerificationAgent v%s.", self.AGENT_VERSION)

    def validate_input(self, params: Dict[str, Any]) -> bool:
        """Validates incoming JSON-RPC parameters.

        Args:
            params: Parameters dictionary.

        Returns:
            True if valid, False otherwise.
        """
        if not params or not isinstance(params, dict):
            return False

        context = params.get("context", {})
        if not isinstance(context, dict):
            return False

        # task is mandatory
        task = context.get("task")
        if not isinstance(task, dict):
            return False
        if "task_id" not in task or "description" not in task:
            return False

        # code_diff, validation_plan, packed_context are mandatory
        if "code_diff" not in context or "validation_plan" not in context or "packed_context" not in context:
            return False

        if not isinstance(context["code_diff"], dict):
            return False
        if not isinstance(context["validation_plan"], dict):
            return False
        if not isinstance(context["packed_context"], dict):
            return False

        # metadata is mandatory
        metadata = params.get("metadata", {})
        if not isinstance(metadata, dict):
            return False
        if "trace_id" not in metadata or "replay_id" not in metadata:
            return False

        return True

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Runs the verification engine checks to resolve approval or rejection.

        Args:
            params: Input parameters.

        Returns:
            A dictionary conforming to the output schema.
        """
        context = params["context"]
        metadata = params["metadata"]

        task = context["task"]
        task_id: str = task["task_id"]
        description: str = task["description"]

        code_diff: Dict[str, Any] = context["code_diff"]
        validation_plan: Dict[str, Any] = context["validation_plan"]
        packed_context: Dict[str, Any] = context["packed_context"]

        trace_id: str = metadata["trace_id"]
        replay_id: str = metadata["replay_id"]

        logger.info(
            "[VERIFICATION AGENT] Auditing contracts for task '%s'. Trace: '%s'.",
            task_id,
            trace_id,
        )

        # 1. Run all checks through the verification engine
        violations = self._engine.verify(
            task_id=task_id,
            description=description,
            code_diff=code_diff,
            validation_plan=validation_plan,
            packed_context=packed_context,
            trace_id=trace_id,
            replay_id=replay_id,
        )

        # 2. Build verdict status
        verdict = "REJECTED" if violations else "APPROVED"
        risk_level = validation_plan.get("risk_level", "LOW")

        validation_summary = {
            "files_checked": len(packed_context.get("selected_files", [])),
            "tasks_checked": len(validation_plan.get("validation_tasks", [])),
            "violations_count": len(violations),
            "risk_level": risk_level,
        }

        # 3. Calculate deterministic hash (SHA-256)
        payload = {
            "verdict": verdict,
            "violations": violations,
            "risk_level": risk_level,
            "validation_summary": validation_summary,
        }
        payload_str = json.dumps(payload, sort_keys=True)
        hash_input = f"{task_id}_{trace_id}_{payload_str}"
        deterministic_hash = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()

        result = {
            "trace_id": trace_id,
            "replay_id": replay_id,
            "deterministic_hash": deterministic_hash,
            "verdict": verdict,
            "violations": violations,
            "risk_level": risk_level,
            "validation_summary": validation_summary,
        }

        # 4. Route through ValidationGateway check
        gateway = ValidationGateway()
        gateway.validate_output(self.AGENT_ID, result)
        logger.info("[VERIFICATION AGENT] ValidationGateway check passed for task '%s'.", task_id)

        # 5. Emit event to IntegrationAuditLog
        audit_log = context.get("integration_log")
        if not audit_log:
            audit_log = IntegrationAuditLog()

        event = IntegrationAuditEvent(
            event_id=f"verify_{trace_id}",
            event_type="contract_verified",
            trace_id=trace_id,
            replay_id=replay_id,
            deterministic_hash=deterministic_hash,
            details={
                "task_id": task_id,
                "verdict": verdict,
                "risk_level": risk_level,
                "violations_count": len(violations),
            },
        )
        audit_log.append(event)
        logger.info(
            "[VERIFICATION AGENT] IntegrationAuditLog event emitted (event_id='%s'). Verdict: %s",
            event.event_id,
            verdict,
        )

        return result

    def validate_output(self, result: Dict[str, Any]) -> bool:
        """Validates output schema conformity.

        Args:
            result: Outputs generated by execute().

        Returns:
            True if valid, False otherwise.
        """
        if not result or not isinstance(result, dict):
            return False

        required_fields = [
            "trace_id",
            "replay_id",
            "deterministic_hash",
            "verdict",
            "violations",
            "risk_level",
            "validation_summary",
        ]
        if not all(field in result for field in required_fields):
            logger.error("[VERIFICATION AGENT ERROR] Output missing required fields.")
            return False

        # Validate types
        if not isinstance(result["violations"], list):
            logger.error("[VERIFICATION AGENT ERROR] violations is not a list.")
            return False

        if not isinstance(result["validation_summary"], dict):
            logger.error("[VERIFICATION AGENT ERROR] validation_summary is not a dict.")
            return False

        if result["verdict"] not in ("APPROVED", "REJECTED"):
            logger.error("[VERIFICATION AGENT ERROR] Invalid verdict '%s'.", result["verdict"])
            return False

        if result["risk_level"] not in self._engine.SUPPORTED_RISKS:
            logger.error("[VERIFICATION AGENT ERROR] Invalid risk level '%s'.", result["risk_level"])
            return False

        if len(result["deterministic_hash"]) != 64:
            logger.error("[VERIFICATION AGENT ERROR] deterministic_hash is not valid SHA-256.")
            return False

        return True

    def finalize(self) -> None:
        """Logs finalizing telemetry."""
        logger.info("[VERIFICATION AGENT] Finalizing VerificationAgent.")
