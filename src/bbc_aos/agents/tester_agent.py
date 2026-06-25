"""BBC-AOS TesterAgent - Phase 11D

Production implementation of the TesterAgent responsible for generating
deterministic validation plans and executable verification tasks based on CodeDiff.
"""

import hashlib
import json
import logging
import re
from typing import Any, Dict, List, Optional

from bbc_aos.agents.base_agent import BaseAgent
from bbc_aos.integration.validation_gateway import ValidationGateway
from bbc_aos.integration.integration_audit_log import IntegrationAuditLog, IntegrationAuditEvent

# Configure logger
logger = logging.getLogger("bbc_aos.agents.tester_agent")


# ---------------------------------------------------------------------------
# Immutable Validation Task and Plan Models
# ---------------------------------------------------------------------------

class ValidationTask:
    """Immutable representation of an executable verification task.

    Attributes:
        task_id: Unique task identifier.
        test_type: Category of validation (syntax, unit, integration, regression, replay).
        target_file: File path targeted by this verification task.
        description: Description of the verification step.
        priority: Priority value (1 is highest, 5 is lowest).
        dependencies: List of task IDs this task depends on (depth <= 5).
    """

    __slots__ = (
        "task_id",
        "test_type",
        "target_file",
        "description",
        "priority",
        "dependencies",
    )

    def __init__(
        self,
        task_id: str,
        test_type: str,
        target_file: str,
        description: str,
        priority: int,
        dependencies: List[str],
    ) -> None:
        """Initializes the ValidationTask."""
        object.__setattr__(self, "task_id", task_id)
        object.__setattr__(self, "test_type", test_type)
        object.__setattr__(self, "target_file", target_file)
        object.__setattr__(self, "description", description)
        object.__setattr__(self, "priority", priority)
        object.__setattr__(self, "dependencies", dependencies)

    def __setattr__(self, key: str, value: Any) -> None:
        raise AttributeError("ValidationTask is immutable.")

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the ValidationTask to a dictionary."""
        return {
            "task_id": self.task_id,
            "test_type": self.test_type,
            "target_file": self.target_file,
            "description": self.description,
            "priority": self.priority,
            "dependencies": self.dependencies,
        }


class ValidationPlan:
    """Immutable representation of a deterministic validation plan.

    Attributes:
        trace_id: Propagated trace identifier.
        replay_id: Propagated replay identifier.
        deterministic_hash: SHA-256 fingerprint of the plan payload.
        validation_tasks: List of executable validation task dictionaries.
        risk_level: Risk classification (LOW, MEDIUM, HIGH, CRITICAL).
        coverage_targets: Dictionary of coverage targets and active state.
    """

    __slots__ = (
        "trace_id",
        "replay_id",
        "deterministic_hash",
        "validation_tasks",
        "risk_level",
        "coverage_targets",
    )

    def __init__(
        self,
        trace_id: str,
        replay_id: str,
        deterministic_hash: str,
        validation_tasks: List[Dict[str, Any]],
        risk_level: str,
        coverage_targets: Dict[str, bool],
    ) -> None:
        """Initializes the ValidationPlan."""
        object.__setattr__(self, "trace_id", trace_id)
        object.__setattr__(self, "replay_id", replay_id)
        object.__setattr__(self, "deterministic_hash", deterministic_hash)
        object.__setattr__(self, "validation_tasks", validation_tasks)
        object.__setattr__(self, "risk_level", risk_level)
        object.__setattr__(self, "coverage_targets", coverage_targets)

    def __setattr__(self, key: str, value: Any) -> None:
        raise AttributeError("ValidationPlan is immutable.")

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the ValidationPlan to a dictionary."""
        return {
            "trace_id": self.trace_id,
            "replay_id": self.replay_id,
            "deterministic_hash": self.deterministic_hash,
            "validation_tasks": self.validation_tasks,
            "risk_level": self.risk_level,
            "coverage_targets": self.coverage_targets,
        }


# ---------------------------------------------------------------------------
# Deterministic Validation Planner (No Direct Subprocess/Execution/Filesystem)
# ---------------------------------------------------------------------------

class _DeterministicValidationPlanner:
    """Generates a deterministic validation plan based on task and CodeDiff context.

    All planning operations are stateless and seeded by a SHA-256 hash of inputs
    to ensure 100% replay determinism.
    """

    MAX_VALIDATION_TASKS: int = 50
    MAX_DEP_DEPTH: int = 5
    RISK_LEVELS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    COVERAGE_KEYS = ["syntax", "unit", "integration", "regression", "replay"]

    def plan(
        self,
        task_id: str,
        description: str,
        code_diff: Dict[str, Any],
        trace_id: str,
    ) -> Dict[str, Any]:
        """Generates a deterministic validation plan payload.

        Args:
            task_id: Unique task identifier.
            description: Natural language task description.
            code_diff: CoderAgent CodeDiff proposal dictionary.
            trace_id: Upstream trace identifier.

        Returns:
            A dictionary containing validation_tasks, risk_level, and coverage_targets.
        """
        modified_files: List[str] = code_diff.get("modified_files", [])
        added_files: List[str] = code_diff.get("added_files", [])
        removed_files: List[str] = code_diff.get("removed_files", [])

        # 1. Deterministic Risk Classification
        risk_level = self._classify_risk_level(description, modified_files, added_files, removed_files)
        logger.info(f"[PLANNER] Classified risk level: '{risk_level}' for task '{task_id}'")

        # 2. Deterministic Coverage Targets
        coverage_targets = self._generate_coverage_targets(description, risk_level, modified_files, added_files, removed_files)

        # 3. Deterministic Task Generation (DAG topology, max depth <= 5)
        tasks = self._generate_tasks(
            modified_files=modified_files,
            added_files=added_files,
            removed_files=removed_files,
            coverage_targets=coverage_targets,
        )

        # Convert to dict representation
        tasks_dicts = [t.to_dict() for t in tasks]

        # 4. Enforce stable deterministic task ordering (priority-first, task_id tie-breaker)
        sorted_tasks = sorted(
            tasks_dicts,
            key=lambda x: (x["priority"], x["task_id"])
        )

        return {
            "validation_tasks": sorted_tasks,
            "risk_level": risk_level,
            "coverage_targets": coverage_targets,
        }

    def _classify_risk_level(
        self,
        description: str,
        modified_files: List[str],
        added_files: List[str],
        removed_files: List[str],
    ) -> str:
        """Classifies risk level based on description keywords and file metrics.

        Uses regex word boundaries to prevent substring matching.
        """
        desc_lower = description.lower()
        num_files = len(modified_files) + len(added_files) + len(removed_files)

        def matches_word(keywords: List[str]) -> bool:
            for kw in keywords:
                pattern = r"\b" + re.escape(kw) + r"\b"
                if re.search(pattern, desc_lower):
                    return True
            return False

        # CRITICAL triggers
        if len(removed_files) > 0:
            return "CRITICAL"
        if matches_word(["security", "chaos", "recovery", "auth", "critical"]):
            return "CRITICAL"
        if num_files > 15:
            return "CRITICAL"

        # HIGH triggers
        if matches_word(["performance", "migration", "refactor"]):
            return "HIGH"
        if num_files > 8:
            return "HIGH"

        # MEDIUM triggers
        if matches_word(["fix", "bug", "patch"]):
            return "MEDIUM"
        if num_files > 2:
            return "MEDIUM"

        return "LOW"

    def _generate_coverage_targets(
        self,
        description: str,
        risk_level: str,
        modified_files: List[str],
        added_files: List[str],
        removed_files: List[str],
    ) -> Dict[str, bool]:
        """Generates coverage targets based on risk classification."""
        desc_lower = description.lower()
        num_files = len(modified_files) + len(added_files) + len(removed_files)

        def matches_word(keywords: List[str]) -> bool:
            for kw in keywords:
                pattern = r"\b" + re.escape(kw) + r"\b"
                if re.search(pattern, desc_lower):
                    return True
            return False

        syntax = True
        replay = True
        unit = num_files > 0
        integration = risk_level in ("HIGH", "CRITICAL") or num_files > 3
        regression = (
            risk_level in ("MEDIUM", "HIGH", "CRITICAL")
            or matches_word(["fix", "bug", "patch"])
        )

        return {
            "syntax": syntax,
            "unit": unit,
            "integration": integration,
            "regression": regression,
            "replay": replay,
        }

    def _generate_tasks(
        self,
        modified_files: List[str],
        added_files: List[str],
        removed_files: List[str],
        coverage_targets: Dict[str, bool],
    ) -> List[ValidationTask]:
        """Generates topological validation tasks per file within complexity limits."""
        all_files = sorted(list(set(modified_files + added_files + removed_files)))
        tasks: List[ValidationTask] = []
        task_count = 0

        for idx, file in enumerate(all_files):
            if task_count >= self.MAX_VALIDATION_TASKS:
                break

            is_removed = file in removed_files
            last_task_id: Optional[str] = None

            # 1. Syntax verification task (priority 1)
            if coverage_targets.get("syntax", False) and not is_removed:
                if task_count >= self.MAX_VALIDATION_TASKS:
                    break
                task_id = f"val_{idx}_syntax"
                tasks.append(
                    ValidationTask(
                        task_id=task_id,
                        test_type="syntax",
                        target_file=file,
                        description=f"Verify syntax check for {file}",
                        priority=1,
                        dependencies=[]
                    )
                )
                last_task_id = task_id
                task_count += 1

            # 2. Unit verification task (priority 2)
            if coverage_targets.get("unit", False) and not is_removed:
                if task_count >= self.MAX_VALIDATION_TASKS:
                    break
                task_id = f"val_{idx}_unit"
                deps = [last_task_id] if last_task_id else []
                tasks.append(
                    ValidationTask(
                        task_id=task_id,
                        test_type="unit",
                        target_file=file,
                        description=f"Execute unit tests for {file}",
                        priority=2,
                        dependencies=deps
                    )
                )
                last_task_id = task_id
                task_count += 1

            # 3. Integration verification task (priority 3)
            if coverage_targets.get("integration", False):
                if task_count >= self.MAX_VALIDATION_TASKS:
                    break
                task_id = f"val_{idx}_integration"
                deps = [last_task_id] if last_task_id else []
                tasks.append(
                    ValidationTask(
                        task_id=task_id,
                        test_type="integration",
                        target_file=file,
                        description=f"Run integration suite for {file}",
                        priority=3,
                        dependencies=deps
                    )
                )
                last_task_id = task_id
                task_count += 1

            # 4. Regression verification task (priority 4)
            if coverage_targets.get("regression", False):
                if task_count >= self.MAX_VALIDATION_TASKS:
                    break
                task_id = f"val_{idx}_regression"
                deps = [last_task_id] if last_task_id else []
                tasks.append(
                    ValidationTask(
                        task_id=task_id,
                        test_type="regression",
                        target_file=file,
                        description=f"Validate regression impact for {file}",
                        priority=4,
                        dependencies=deps
                    )
                )
                last_task_id = task_id
                task_count += 1

            # 5. Replay verification task (priority 5)
            if coverage_targets.get("replay", False):
                if task_count >= self.MAX_VALIDATION_TASKS:
                    break
                task_id = f"val_{idx}_replay"
                deps = [last_task_id] if last_task_id else []
                tasks.append(
                    ValidationTask(
                        task_id=task_id,
                        test_type="replay",
                        target_file=file,
                        description=f"Verify deterministic replay of {file}",
                        priority=5,
                        dependencies=deps
                    )
                )
                last_task_id = task_id
                task_count += 1

        return tasks


# ---------------------------------------------------------------------------
# TesterAgent
# ---------------------------------------------------------------------------

class TesterAgent(BaseAgent):
    """TesterAgent is responsible for planning code verification tasks.

    It receives a CoderAgent CodeDiff proposal and returns a deterministic plan
    representing the necessary validation steps.
    """

    AGENT_ID: str = "tester_agent"
    AGENT_VERSION: str = "1.0.0"
    SUPPORTED_ACTIONS: List[str] = ["generate_validation_plan", "verify_code_diff"]

    def __init__(self) -> None:
        """Initializes the TesterAgent with its deterministic planner."""
        self._planner = _DeterministicValidationPlanner()

    def initialize(self) -> None:
        """Performs setup and logs initialization telemetry."""
        logger.info("[TESTER AGENT] Initializing TesterAgent v%s.", self.AGENT_VERSION)

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

        # code_diff is mandatory
        code_diff = context.get("code_diff")
        if not isinstance(code_diff, dict):
            return False
        required_diff_fields = ["modified_files", "added_files", "removed_files", "patch"]
        if not all(f in code_diff for f in required_diff_fields):
            return False

        # metadata is mandatory
        metadata = params.get("metadata", {})
        if not isinstance(metadata, dict):
            return False
        if "trace_id" not in metadata or "replay_id" not in metadata:
            return False

        return True

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generates a deterministic validation plan from input CodeDiff.

        Args:
            params: Parameters dictionary.

        Returns:
            A dictionary conforming to the ValidationPlan schema.
        """
        context = params["context"]
        metadata = params["metadata"]

        task = context["task"]
        task_id: str = task["task_id"]
        description: str = task["description"]
        task_deps: List[str] = task.get("dependencies", [])

        code_diff: Dict[str, Any] = context["code_diff"]

        trace_id: str = metadata["trace_id"]
        replay_id: str = metadata["replay_id"]

        logger.info(
            "[TESTER AGENT] Planning validation for task '%s'. CodeDiff trace: '%s'.",
            task_id,
            code_diff.get("trace_id", "unknown"),
        )

        # 1. Enforce dependency depth limits
        if len(task_deps) > 5:
            logger.warning(
                "[TESTER AGENT] task dependencies (%d) exceeds depth limit 5.",
                len(task_deps),
            )

        # 2. Plan tasks deterministically
        plan_data = self._planner.plan(
            task_id=task_id,
            description=description,
            code_diff=code_diff,
            trace_id=trace_id,
        )

        # 3. Calculate deterministic hash (SHA-256)
        plan_payload_str = json.dumps(plan_data, sort_keys=True)
        hash_input = f"{task_id}_{trace_id}_{plan_payload_str}"
        deterministic_hash = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()

        # 4. Construct ValidationPlan
        plan = ValidationPlan(
            trace_id=trace_id,
            replay_id=replay_id,
            deterministic_hash=deterministic_hash,
            validation_tasks=plan_data["validation_tasks"],
            risk_level=plan_data["risk_level"],
            coverage_targets=plan_data["coverage_targets"],
        )

        result = plan.to_dict()

        # 5. Route through ValidationGateway check
        gateway = ValidationGateway()
        gateway.validate_output(self.AGENT_ID, result)
        logger.info("[TESTER AGENT] ValidationGateway check passed for task '%s'.", task_id)

        # 6. Emit event to IntegrationAuditLog
        audit_log = context.get("integration_log")
        if not audit_log:
            audit_log = IntegrationAuditLog()

        event = IntegrationAuditEvent(
            event_id=f"tester_{trace_id}",
            event_type="validation_plan_generated",
            trace_id=trace_id,
            replay_id=replay_id,
            deterministic_hash=deterministic_hash,
            details={
                "task_id": task_id,
                "risk_level": plan.risk_level,
                "task_count": len(plan.validation_tasks),
                "coverage_targets": plan.coverage_targets,
            },
        )
        audit_log.append(event)
        logger.info(
            "[TESTER AGENT] IntegrationAuditLog event emitted (event_id='%s').",
            event.event_id,
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
            "validation_tasks",
            "risk_level",
            "coverage_targets",
        ]
        if not all(field in result for field in required_fields):
            logger.error("[TESTER AGENT ERROR] Output missing required fields.")
            return False

        # Validate types
        if not isinstance(result["validation_tasks"], list):
            logger.error("[TESTER AGENT ERROR] validation_tasks is not a list.")
            return False

        if not isinstance(result["coverage_targets"], dict):
            logger.error("[TESTER AGENT ERROR] coverage_targets is not a dict.")
            return False

        # Validate task limits
        if len(result["validation_tasks"]) > self._planner.MAX_VALIDATION_TASKS:
            logger.error(
                "[TESTER AGENT ERROR] Validation tasks count (%d) exceeds limit %d.",
                len(result["validation_tasks"]),
                self._planner.MAX_VALIDATION_TASKS,
            )
            return False

        # Validate task dependency depths
        for task in result["validation_tasks"]:
            if not isinstance(task, dict):
                return False
            deps = task.get("dependencies", [])
            if len(deps) > 5:
                logger.error(
                    "[TESTER AGENT ERROR] Task %s dependency depth (%d) exceeds limit 5.",
                    task.get("task_id"),
                    len(deps),
                )
                return False

        # Validate risk level
        if result["risk_level"] not in self._planner.RISK_LEVELS:
            logger.error(
                "[TESTER AGENT ERROR] Invalid risk level '%s'.",
                result["risk_level"],
            )
            return False

        # Validate coverage targets keys
        if not all(k in result["coverage_targets"] for k in self._planner.COVERAGE_KEYS):
            logger.error("[TESTER AGENT ERROR] Missing keys in coverage_targets.")
            return False

        # Validate deterministic hash
        if len(result["deterministic_hash"]) != 64:
            logger.error("[TESTER AGENT ERROR] deterministic_hash is not valid SHA-256.")
            return False

        return True

    def finalize(self) -> None:
        """Performs cleanup and completes telemetry logging."""
        logger.info("[TESTER AGENT] Finalizing TesterAgent.")