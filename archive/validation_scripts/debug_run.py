import os
import sys
import json
import shutil
import copy

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scratch.run_repository_pilot import RepositoryPilot

pilot = RepositoryPilot()
pilot.prepare_sandbox()
memory_manager = pilot.setup_memory_manager()

from bbc_aos.agents.agent_orchestrator import AgentOrchestrator
from bbc_aos.memory.working.state_manager import StateManager
from bbc_aos.integration import IntegrationAuditLog
from bbc_aos.commit.commit_manager import CommitManager
from bbc_aos.commit.commit_audit_log import CommitAuditLog
from bbc_aos.approval.approval_manager import ApprovalManager
from bbc_aos.approval.approval_audit_log import ApprovalAuditLog

state_manager = StateManager(heal_budget=1000, session_heal_budget=1000)
orchestrator = AgentOrchestrator(state_manager=state_manager)
integration_log = IntegrationAuditLog()
approval_audit = ApprovalAuditLog(project_root=pilot.sandbox_dir)
approval_manager = ApprovalManager(audit_log=approval_audit)
commit_audit = CommitAuditLog(project_root=pilot.sandbox_dir)
commit_manager = CommitManager(audit_log=commit_audit, approval_manager=approval_manager)

trace_id = "tr_debug_0"
replay_id = "rp_debug_0"
context_data = {
    "memory_manager": memory_manager,
    "integration_log": integration_log,
}

status = orchestrator.execute_goal(
    goal_id="goal_debug",
    goal_description="Fix bug in scalar matrix calculations",
    trace_id=trace_id,
    replay_id=replay_id,
    context_data=context_data,
)

print("STATUS:", status["status"])
if "outputs" in status:
    coder_res = status["outputs"]["coder_result"]
    print("CODER RESULT:", json.dumps(coder_res, indent=2))
    verify_res = status["outputs"]["verify_result"]
    print("VERIFY RESULT:", json.dumps(verify_res, indent=2))
