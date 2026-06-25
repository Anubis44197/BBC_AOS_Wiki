"""BBC-AOS AgentOrchestrator - Phase 11F

Production coordinator coordinating the E2E agent execution pipeline:
PlannerAgent -> ContextAgent -> CoderAgent -> TesterAgent -> VerificationAgent.
"""

import logging
import copy
import json
import traceback
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

    def __init__(self, state_manager: Optional[Any] = None) -> None:
        """Initializes AgentOrchestrator.

        Args:
            state_manager: Optional telemetry state manager.
        """
        self.state_manager: Optional[Any] = state_manager
        self.registry: AgentRegistry = AgentRegistry()
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
        return self._run_execution_loop(trace_id, replay_id)

    def resume_execution(self, trace_id: str, replay_id: str) -> Dict[str, Any]:
        """Resumes execution for the trace/replay ID from the next uncompleted stage.

        Args:
            trace_id: Trace ID.
            replay_id: Replay ID.

        Returns:
            The final execution status dictionary.
        """
        key = (trace_id, replay_id)
        execution = self.active_executions.get(key)
        if not execution:
            raise KeyError(f"No active execution found for trace '{trace_id}' and replay '{replay_id}'")
        
        logger.info(f"[ORCHESTRATOR] Resuming execution from stage '{execution['current_stage']}'")
        return self._run_execution_loop(trace_id, replay_id)

    def rollback_execution(self, trace_id: str, replay_id: str, target_stage: str) -> Dict[str, Any]:
        """Rolls back to the target stage checkpoint and resumes execution immediately.

        Args:
            trace_id: Trace ID.
            replay_id: Replay ID.
            target_stage: Stage name to roll back to.

        Returns:
            The final execution status dictionary.
        """
        logger.info(f"[ORCHESTRATOR] Rolling back and resuming execution to stage '{target_stage}'")
        self.rollback_to_checkpoint(trace_id, replay_id, target_stage)
        return self.resume_execution(trace_id, replay_id)

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
        
        return {
            "goal_id": execution["goal_id"],
            "goal_description": execution["goal_description"],
            "trace_id": execution["trace_id"],
            "replay_id": execution["replay_id"],
            "current_stage": execution["current_stage"],
            "status": execution["status"],
            "checkpoints": list(execution["checkpoints"].keys()),
            "outputs": execution["outputs"],
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
                    agent = agent_cls()
                    agent.initialize()
                    
                    if not agent.validate_input(params):
                        raise InvalidParamsException(f"Input validation failed for agent '{agent_id}' at stage '{stage}'")
                        
                    result = agent.execute(params)
                    
                    if not agent.validate_output(result):
                        raise InvalidParamsException(f"Output validation failed for agent '{agent_id}' at stage '{stage}'")
                        
                    agent.finalize()
                    
                    execution["outputs"][f"{stage}_result"] = result
                    success = True
                    break
                except Exception as e:
                    logger.error(f"[ORCHESTRATOR] Attempt {retries + 1} at stage '{stage}' failed: {e}")
                    retries += 1
                    execution["retry_counts"][stage] = retries
                    last_exception = e
                    
            if not success:
                execution["status"] = "FAILED"
                self._save_checkpoint(stage, execution)
                raise last_exception or RuntimeError(f"Stage '{stage}' failed after maximum retries")

            # Update active stage to current
            execution["current_stage"] = stage

            # Handle VerificationAgent rejection immediately
            if stage == "verify":
                verdict = execution["outputs"]["verify_result"].get("verdict")
                if verdict == "REJECTED":
                    execution["status"] = "REJECTED"
                    self._save_checkpoint(stage, execution)
                    logger.warning("[ORCHESTRATOR] Verification rejected payload. Pipeline terminated.")
                    return self.get_execution_status(trace_id, replay_id)

            # Save checkpoint
            self._save_checkpoint(stage, execution)

            # Update Telemetry & StateManager
            self._update_state_manager(stage, execution["outputs"][f"{stage}_result"])

        execution["status"] = "COMPLETED"
        return self.get_execution_status(trace_id, replay_id)

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
