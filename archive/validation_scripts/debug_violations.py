import os
import sys
import json

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scratch.validate_phase11f import TestAgentOrchestratorPipeline

t = TestAgentOrchestratorPipeline()
t.setUp()

context_data = t._get_context_data()

status = t.orchestrator.execute_goal(
    goal_id="goal_debug",
    goal_description="Optimize matrix performance states",
    trace_id="tr_debug",
    replay_id="rp_debug",
    context_data=context_data,
)

print("STATUS:", status["status"])
if "verify_result" in status["outputs"]:
    print("VIOLATIONS:", status["outputs"]["verify_result"]["violations"])
else:
    print("NO verify_result found. Outputs keys:", list(status["outputs"].keys()))
