"""BBC-AOS AgentOrchestrator - Phase 11F

Production coordinator coordinating the E2E agent execution pipeline:
PlannerAgent -> ContextAgent -> CoderAgent -> TesterAgent -> VerificationAgent.
"""

import logging
import copy
import json
import traceback
import hashlib
from typing import Any, Dict, List, Optional
from bbc_aos.agents.agent_registry import AgentRegistry
from bbc_aos.agents.agent_message import AgentMessage
from bbc_aos.agents.agent_result import AgentResult
from bbc_aos.agents.agent_exceptions import MethodNotFoundException, InvalidParamsException, SafetyBreachException

# Configure logger
logger = logging.getLogger("bbc_aos.agents.agent_orchestrator")


class AgentOrchestrator:
    """Central dispatcher coordinating agent executions and workflows.

    Coordinates sequential agent execution chains, checkpoints, rollbacks,
    resumes, retries, and telemetry integration.
    """

    STAGES: List[str] = ["planner", "context", "coder", "tester", "verify"]
    MAX_RETRIES: int = 3

    def __init__(
        self,
        state_manager: Optional[Any] = None,
        agent_registry: Optional[Any] = None,
        memory_manager: Optional[Any] = None,
        audit_log: Optional[Any] = None,
        **kwargs: Any,
    ) -> None:
        """Initializes AgentOrchestrator.

        Args:
            state_manager: Optional telemetry state manager.
            agent_registry: Optional agent registry.
            memory_manager: Optional memory manager.
            audit_log: Optional audit log.
        """
        self.state_manager: Optional[Any] = state_manager
        self.registry: AgentRegistry = agent_registry or AgentRegistry()
        self.memory_manager: Optional[Any] = memory_manager
        self.audit_log: Optional[Any] = audit_log
        self.active_executions: Dict[tuple, Dict[str, Any]] = {}

    def dispatch(self, message_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Ingests a JSON-RPC request and routes to the target agent class.

        Args:
            message_dict: JSON-RPC request dictionary.

        Returns:
            JSON-RPC response dictionary.
        """
        try:
            # 1. Parse and validate message
            msg = AgentMessage.from_dict(message_dict)
            
            # 2. Extract metadata validation signature
            params = msg.params
            metadata = params.get("metadata", {})
            trace_id = metadata.get("trace_id", "")
            
            # Enforce path sandboxes in params check
            context = params.get("context", {})
            for key, val in context.items():
                if "path" in key and isinstance(val, str):
                    if ".." in val or val.startswith("/") or val.startswith("\\"):
                        logger.error(f"[SAFETY BREACH] Sandbox violation on path: {val}")
                        raise SafetyBreachException("Paths must reside inside target workspace root")
            
            # 3. Lookup target agent ID from method name format
            method = msg.method
            if "." not in method:
                raise MethodNotFoundException("Method format must be 'agent_id.action'")
            
            agent_id, action = method.split(".", 1)
            agent_cls = self.registry.get_agent_cls(agent_id)
            
            if action not in agent_cls.SUPPORTED_ACTIONS:
                raise MethodNotFoundException(f"Action '{action}' is not supported by agent '{agent_id}'")
            
            # 4. Instantiate agent and run through lifecycle
            agent = agent_cls()
            agent.initialize()
            
            if not agent.validate_input(params):
                raise InvalidParamsException("Parameters failed input schema verification")
                
            logger.info(f"[ORCHESTRATOR] Routing {agent_id}.{action} (Trace: {trace_id}) through BBC Core Validator")
            
            exec_result = agent.execute(params)
            
            if not agent.validate_output(exec_result):
                raise InvalidParamsException("Output result failed validation schema verification")
                
            agent.finalize()
            
            # 5. Pack response result
            res = AgentResult(message_id=msg.id, result=exec_result)
            return res.to_dict()
            
        except Exception as e:
            logger.error(f"[ORCHESTRATOR ERROR] Execution failed: {e}")
            error_code = getattr(e, "error_code", -32603)
            error_msg = str(e)
            res = AgentResult(
                message_id=message_dict.get("id", "null"),
                error={
                    "code": error_code,
                    "message": error_msg,
                    "data": {"traceback": traceback.format_exc() if not isinstance(e, (MethodNotFoundException, SafetyBreachException)) else ""}
                }
            )
            return res.to_dict()

    # -----------------------------------------------------------------------
    # E2E Execution Flow Pipeline (Phase 11F)
    # -----------------------------------------------------------------------

    def execute_goal(
        self,
        goal_id: str,
        goal_description: str,
        trace_id: str,
        replay_id: str,
        context_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Starts the sequential agent execution pipeline for a goal from scratch.

        Args:
            goal_id: Unique goal identifier.
            goal_description: Natural language task goal.
            trace_id: Trace ID for tracking.
            replay_id: Replay ID for auditing.
            context_data: Optional starting context envelope.

        Returns:
            The final execution status dictionary.
        """
        key = (trace_id, replay_id)
        self.active_executions[key] = {
            "goal_id": goal_id,
            "goal_description": goal_description,
            "trace_id": trace_id,
            "replay_id": replay_id,
            "current_stage": "start",
            "status": "IN_PROGRESS",
            "retry_counts": {s: 0 for s in self.STAGES},
            "checkpoints": {},
            "outputs": {},
            "context_data": context_data or {},
        }
        logger.info(f"[ORCHESTRATOR] Starting goal execution: '{goal_id}'")
        self._run_security_validation(goal_description, trace_id, replay_id)
        return self._run_execution_loop(trace_id, replay_id)

    def resume_execution(
        self,
        trace_id: str,
        replay_id: str,
        context_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Resumes execution for the trace/replay ID from the next uncompleted stage.

        Args:
            trace_id: Trace ID.
            replay_id: Replay ID.
            context_data: Optional context data to update/merge.

        Returns:
            The final execution status dictionary.
        """
        key = (trace_id, replay_id)
        execution = self.active_executions.get(key)
        if not execution:
            raise KeyError(f"No active execution found for trace '{trace_id}' and replay '{replay_id}'")

        if context_data:
            execution["context_data"].update(context_data)

        logger.info(f"[ORCHESTRATOR] Resuming execution from stage '{execution['current_stage']}'")
        return self._run_execution_loop(trace_id, replay_id)

    def rollback_execution(self, trace_id: str, replay_id: str, target_stage: str) -> Dict[str, Any]:
        """Rolls back to the target stage checkpoint and suspends execution.

        Args:
            trace_id: Trace ID.
            replay_id: Replay ID.
            target_stage: Stage name to roll back to.

        Returns:
            The rolled back execution status summary dictionary.
        """
        logger.info(f"[ORCHESTRATOR] Rolling back execution to stage '{target_stage}'")
        self.rollback_to_checkpoint(trace_id, replay_id, target_stage)
        key = (trace_id, replay_id)
        self.active_executions[key]["status"] = "SUSPENDED"
        return self.get_execution_status(trace_id, replay_id)

    def get_execution_status(self, trace_id: str, replay_id: str) -> Dict[str, Any]:
        """Compiles the status envelope of the goal execution.

        Args:
            trace_id: Trace ID.
            replay_id: Replay ID.

        Returns:
            Status summary dictionary.
        """
        key = (trace_id, replay_id)
        execution = self.active_executions.get(key)
        if not execution:
            raise KeyError(f"No execution found for trace '{trace_id}' and replay '{replay_id}'")

        # Calculate a deterministic hash of the execution outputs if not already present
        outputs = execution.get("outputs", {})
        verify_res = outputs.get("verify_result", {})
        det_hash = verify_res.get("deterministic_hash")
        if not det_hash:
            import hashlib
            payload_str = json.dumps(outputs, sort_keys=True)
            hash_input = f"{execution['trace_id']}_{execution['replay_id']}_{payload_str}"
            det_hash = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()

        return {
            "goal_id": execution["goal_id"],
            "goal_description": execution["goal_description"],
            "trace_id": execution["trace_id"],
            "replay_id": execution["replay_id"],
            "current_stage": execution["current_stage"],
            "status": execution["status"],
            "checkpoints": list(execution["checkpoints"].keys()),
            "outputs": execution["outputs"],
            "deterministic_hash": det_hash,
        }

    def resume_from_checkpoint(self, checkpoint: Dict[str, Any]) -> Dict[str, Any]:
        """Registers execution state directly from a serialized checkpoint and resumes.

        Args:
            checkpoint: Serialized checkpoint dictionary.

        Returns:
            The final execution status dictionary.
        """
        trace_id = checkpoint["trace_id"]
        replay_id = checkpoint["replay_id"]
        key = (trace_id, replay_id)
        
        self.active_executions[key] = {
            "goal_id": checkpoint["goal_id"],
            "goal_description": checkpoint["goal_description"],
            "trace_id": trace_id,
            "replay_id": replay_id,
            "current_stage": checkpoint["current_stage"],
            "status": checkpoint["status"],
            "retry_counts": copy.deepcopy(checkpoint["retry_counts"]),
            "checkpoints": {checkpoint["current_stage"]: checkpoint},
            "outputs": copy.deepcopy(checkpoint["outputs"]),
            "context_data": copy.deepcopy(checkpoint.get("context_data", {})),
        }
        logger.info(f"[ORCHESTRATOR] Loaded checkpoint from storage. Resuming trace '{trace_id}'")
        return self._run_execution_loop(trace_id, replay_id)

    def rollback_to_checkpoint(self, trace_id: str, replay_id: str, target_stage: str) -> Dict[str, Any]:
        """Resets execution state to the target stage checkpoint, clearing later states.

        Args:
            trace_id: Trace ID.
            replay_id: Replay ID.
            target_stage: Stage to roll back to.

        Returns:
            The rolled back execution status summary dictionary.
        """
        key = (trace_id, replay_id)
        execution = self.active_executions.get(key)
        if not execution:
            raise KeyError(f"No execution found for trace '{trace_id}' and replay '{replay_id}'")
        
        checkpoints = execution["checkpoints"]
        if target_stage not in checkpoints:
            raise KeyError(f"No checkpoint found for stage '{target_stage}'")
            
        target_cp = checkpoints[target_stage]
        
        # Revert execution state properties
        execution["current_stage"] = target_stage
        execution["status"] = "IN_PROGRESS"
        execution["outputs"] = copy.deepcopy(target_cp["outputs"])
        execution["retry_counts"] = copy.deepcopy(target_cp["retry_counts"])
        execution["context_data"] = copy.deepcopy(target_cp.get("context_data", {}))
        
        # Remove subsequent checkpoints
        target_idx = self.STAGES.index(target_stage)
        for idx in range(target_idx + 1, len(self.STAGES)):
            stage_to_del = self.STAGES[idx]
            if stage_to_del in checkpoints:
                del checkpoints[stage_to_del]
                
        logger.info(f"[ORCHESTRATOR] State rolled back successfully to stage '{target_stage}'")
        return self.get_execution_status(trace_id, replay_id)

    # -----------------------------------------------------------------------
    # Helper Private Methods
    # -----------------------------------------------------------------------

    def _run_execution_loop(self, trace_id: str, replay_id: str) -> Dict[str, Any]:
        """Internal execution loop advancing stages topologically."""
        key = (trace_id, replay_id)
        execution = self.active_executions[key]
        
        current_stage = execution["current_stage"]
        if current_stage == "start":
            start_idx = 0
        else:
            start_idx = self.STAGES.index(current_stage) + 1

        execution["status"] = "IN_PROGRESS"

        for idx in range(start_idx, len(self.STAGES)):
            stage = self.STAGES[idx]
            agent_id = self._get_agent_id_for_stage(stage)
            agent_cls = self.registry.get_agent_cls(agent_id)
            
            params = self._build_params_for_stage(stage, execution)
            
            retries = execution["retry_counts"].get(stage, 0)
            success = False
            last_exception = None
            
            # Execute with retries (max retries = 3)
            while retries <= self.MAX_RETRIES:
                try:
                    logger.info(f"[ORCHESTRATOR] Running stage '{stage}' (Attempt {retries + 1})...")
                    self._audit_stage(stage, "started", trace_id, replay_id, {"attempt": retries + 1})
                    agent = agent_cls()
                    agent.initialize()
                    
                    if not agent.validate_input(params):
                        raise InvalidParamsException(f"Input validation failed for agent '{agent_id}' at stage '{stage}'")
                        
                    result = agent.execute(params)
                    
                    if not agent.validate_output(result):
                        raise InvalidParamsException(f"Output validation failed for agent '{agent_id}' at stage '{stage}'")
                        
                    agent.finalize()
                    
                    execution["outputs"][f"{stage}_result"] = result
                    self._audit_stage(stage, "completed", trace_id, replay_id, {"attempt": retries + 1, "result": result})
                    success = True
                    break
                except Exception as e:
                    logger.error(f"[ORCHESTRATOR] Attempt {retries + 1} at stage '{stage}' failed: {e}")
                    self._audit_stage(stage, "failed", trace_id, replay_id, {"attempt": retries + 1, "error": str(e)})
                    retries += 1
                    execution["retry_counts"][stage] = retries
                    last_exception = e
                    
            if not success:
                execution["status"] = "FAILED"
                self._save_checkpoint(stage, execution)
                self._audit_event("execution_failed", trace_id, replay_id, "orchestrator", "FAILED", {"stage": stage})
                raise last_exception or RuntimeError(f"Stage '{stage}' failed after maximum retries")

            # Update active stage to current
            execution["current_stage"] = stage

            # Handle VerificationAgent rejection immediately
            if stage == "verify":
                verdict = execution["outputs"]["verify_result"].get("verdict")
                if verdict == "REJECTED":
                    execution["status"] = "SUSPENDED"
                    self._save_checkpoint(stage, execution)
                    self._audit_event("execution_failed", trace_id, replay_id, "orchestrator", "SUSPENDED", {"reason": "verification_rejected"})
                    logger.warning("[ORCHESTRATOR] Verification rejected payload. Pipeline terminated.")
                    return self.get_execution_status(trace_id, replay_id)

            # Save checkpoint
            self._save_checkpoint(stage, execution)

            # Update Telemetry & StateManager
            self._update_state_manager(stage, execution["outputs"][f"{stage}_result"])

        execution["status"] = "COMPLETED"
        self._audit_event("execution_completed", trace_id, replay_id, "orchestrator", "COMPLETED")
        return self.get_execution_status(trace_id, replay_id)

    def _run_security_validation(self, goal_description: str, trace_id: str, replay_id: str) -> None:
        self._audit_event("security_started", trace_id, replay_id, "security", "STARTED")
        self._audit_event("security_validation_started", trace_id, replay_id, "security", "STARTED")
        from bbc_aos.security.prompt_firewall import PromptFirewall
        from bbc_aos.security.instruction_hierarchy import InstructionHierarchy
        from bbc_aos.security.guardrails import SecurityGuardrails

        firewall_result = PromptFirewall().scan(goal_description, source="user_prompt")
        boundary_result = InstructionHierarchy().validate_boundary(goal_description, source="external_text")
        guardrail_result = SecurityGuardrails().validate_prompt(goal_description)
        violations: List[str] = []
        violations.extend(firewall_result.detected_patterns)
        violations.extend(boundary_result.detected_patterns)
        violations.extend([str(item.get("rule_id", "")) for item in guardrail_result.get("findings", [])])
        unique_violations = sorted({v for v in violations if v})
        details = {
            "violations": unique_violations,
            "firewall": firewall_result.to_dict(),
            "instruction_hierarchy": boundary_result.to_dict(),
            "guardrails": guardrail_result,
        }
        if firewall_result.blocked or not boundary_result.allowed or not guardrail_result.get("allowed", True):
            self._audit_event("security_validation_blocked", trace_id, replay_id, "security", "BLOCKED", details)
            self._audit_event("security_completed", trace_id, replay_id, "security", "BLOCKED", details)
            raise SafetyBreachException("Security validation blocked prompt before agent execution: " + ", ".join(unique_violations))
        self._audit_event("security_validation_passed", trace_id, replay_id, "security", "PASSED", details)
        self._audit_event("security_completed", trace_id, replay_id, "security", "COMPLETED", details)

    def _get_agent_id_for_stage(self, stage: str) -> str:
        """Maps stage name to registry agent identifier."""
        mapping = {
            "planner": "planner_agent",
            "context": "context_agent",
            "coder": "coder_agent",
            "tester": "tester_agent",
            "verify": "verification_agent",
        }
        return mapping[stage]

    def _event_stage_name(self, stage: str) -> str:
        return "verification" if stage == "verify" else stage

    def _audit_stage(
        self,
        stage: str,
        status: str,
        trace_id: str,
        replay_id: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        event_stage = self._event_stage_name(stage)
        agent_name = self._get_agent_id_for_stage(stage)
        self._audit_event(f"{event_stage}_{status}", trace_id, replay_id, agent_name, status.upper(), details)

    def _audit_event(
        self,
        event_type: str,
        trace_id: str,
        replay_id: str,
        agent_name: str,
        status: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not self.audit_log:
            return
        if hasattr(self.audit_log, "append_event"):
            self.audit_log.append_event(
                event_type=event_type,
                trace_id=trace_id,
                replay_id=replay_id,
                agent_name=agent_name,
                status=status,
                details=details or {},
            )
            return
        payload = json.dumps(details or {}, sort_keys=True, default=str)
        deterministic_hash = hashlib.sha256(f"{event_type}:{trace_id}:{replay_id}:{payload}".encode("utf-8")).hexdigest()
        from bbc_aos.integration.integration_audit_log import IntegrationAuditEvent

        self.audit_log.append(
            IntegrationAuditEvent(
                event_id=deterministic_hash,
                event_type=event_type,
                trace_id=trace_id,
                replay_id=replay_id,
                deterministic_hash=deterministic_hash,
                agent_name=agent_name,
                status=status,
                details=details or {},
            )
        )

    def _save_checkpoint(self, stage_name: str, execution: Dict[str, Any]) -> None:
        """Saves an immutable snapshot copy of current progress."""
        checkpoint = {
            "goal_id": execution["goal_id"],
            "goal_description": execution["goal_description"],
            "trace_id": execution["trace_id"],
            "replay_id": execution["replay_id"],
            "current_stage": stage_name,
            "status": execution["status"],
            "retry_counts": copy.deepcopy(execution["retry_counts"]),
            "outputs": copy.deepcopy(execution["outputs"]),
            "context_data": copy.deepcopy(execution.get("context_data", {})),
        }
        execution["checkpoints"][stage_name] = checkpoint
        logger.info(f"[ORCHESTRATOR] Checkpoint created for stage '{stage_name}'. Status: {execution['status']}")

    def _update_state_manager(self, stage: str, result: Dict[str, Any]) -> None:
        """Records telemetry and processing metrics to StateManager."""
        from bbc_aos.memory.working.state_manager import StateManager
        try:
            state_manager = StateManager()
            payload_str = json.dumps(result)
            state_manager.add_data_processed(len(payload_str))
            
            if stage == "coder":
                state_manager.increment_files_analyzed()
            elif stage == "verify":
                state_manager.increment_recipes_created()
        except Exception as e:
            logger.warning(f"StateManager telemetry write failed: {e}")

    def _build_params_for_stage(self, stage: str, execution: Dict[str, Any]) -> Dict[str, Any]:
        """Prepares input parameters dynamically for the target stage."""
        trace_id = execution["trace_id"]
        replay_id = execution["replay_id"]
        outputs = execution["outputs"]
        goal_description = execution["goal_description"]
        goal_id = execution["goal_id"]
        context_data = execution.get("context_data", {})

        # Start base context dictionary
        ctx: Dict[str, Any] = {}
        if "memory_manager" in context_data:
            ctx["memory_manager"] = context_data["memory_manager"]
        if "integration_log" in context_data:
            ctx["integration_log"] = context_data["integration_log"]

        if stage == "planner":
            ctx["goal"] = goal_description
            ctx["goal_id"] = goal_id
            return {
                "context": ctx,
                "metadata": {
                    "trace_id": trace_id,
                    "replay_id": replay_id,
                }
            }
        elif stage == "context":
            plan_res = outputs["planner_result"]
            task = plan_res["tasks"][0] if plan_res.get("tasks") else {
                "task_id": "task_default",
                "description": goal_description,
                "dependencies": [],
            }
            task = {**task, "description": f"{goal_description} | {task.get('description', '')}".strip(" |")}
            ctx["task"] = task
            return {
                "context": ctx,
                "metadata": {
                    "trace_id": trace_id,
                    "replay_id": replay_id,
                }
            }
        elif stage == "coder":
            plan_res = outputs["planner_result"]
            task = plan_res["tasks"][0] if plan_res.get("tasks") else {
                "task_id": "task_default",
                "description": goal_description,
                "dependencies": [],
            }
            task = {**task, "description": f"{goal_description} | {task.get('description', '')}".strip(" |")}
            ctx_res = outputs["context_result"]
            ctx["task"] = task
            ctx["selected_files"] = ctx_res.get("selected_files", [])
            ctx["packed_context"] = ctx_res.get("packed_context", {})
            return {
                "context": ctx,
                "metadata": {
                    "trace_id": trace_id,
                    "replay_id": replay_id,
                }
            }
        elif stage == "tester":
            plan_res = outputs["planner_result"]
            task = plan_res["tasks"][0] if plan_res.get("tasks") else {
                "task_id": "task_default",
                "description": goal_description,
                "dependencies": [],
            }
            task = {**task, "description": f"{goal_description} | {task.get('description', '')}".strip(" |")}
            coder_res = outputs["coder_result"]
            ctx["task"] = task
            ctx["code_diff"] = coder_res
            return {
                "context": ctx,
                "metadata": {
                    "trace_id": trace_id,
                    "replay_id": replay_id,
                }
            }
        elif stage == "verify":
            plan_res = outputs["planner_result"]
            task = plan_res["tasks"][0] if plan_res.get("tasks") else {
                "task_id": "task_default",
                "description": goal_description,
                "dependencies": [],
            }
            task = {**task, "description": f"{goal_description} | {task.get('description', '')}".strip(" |")}
            ctx_res = outputs["context_result"]
            coder_res = outputs["coder_result"]
            tester_res = outputs["tester_result"]
            ctx["task"] = task
            ctx["code_diff"] = coder_res
            ctx["validation_plan"] = tester_res
            ctx["packed_context"] = ctx_res
            return {
                "context": ctx,
                "metadata": {
                    "trace_id": trace_id,
                    "replay_id": replay_id,
                }
            }
        else:
            raise ValueError(f"Unknown stage '{stage}'")
