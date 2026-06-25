import sys
import os
import traceback
import py_compile

WIKI_ROOT = "C:/Users/90535/.gemini/antigravity/scratch/BBC_AOS_Wiki"
sys.path.insert(0, WIKI_ROOT)

print("[*] Phase 7B Validation Script Initialized.")

success = True

# 1. Syntax Validation
print("[*] Step 1: Performing Syntax Verification...")
try:
    agents_dir = os.path.join(WIKI_ROOT, "bbc_aos", "agents")
    files_to_compile = [
        "base_agent.py", "agent_message.py", "agent_result.py", "agent_context.py",
        "agent_exceptions.py", "agent_registry.py", "agent_orchestrator.py",
        "planner_agent.py", "context_agent.py", "resolver_agent.py",
        "compression_agent.py", "verification_agent.py", "documentation_agent.py", "execution_agent.py"
    ]
    
    for f in files_to_compile:
        f_path = os.path.join(agents_dir, f)
        py_compile.compile(f_path, doraise=True)
    print("[+] Syntax Verification: SUCCESS")
except Exception as e:
    print(f"[-] Syntax Verification: FAILED\n{traceback.format_exc()}")
    success = False

# 2 & 3. Import & Inheritance Validation
print("[*] Step 2 & 3: Performing Import & Inheritance Verification...")
try:
    from bbc_aos.agents.base_agent import BaseAgent
    from bbc_aos.agents.agent_message import AgentMessage
    from bbc_aos.agents.agent_result import AgentResult
    from bbc_aos.agents.agent_context import AgentContext
    from bbc_aos.agents.agent_exceptions import AgentException
    from bbc_aos.agents.agent_registry import AgentRegistry
    from bbc_aos.agents.agent_orchestrator import AgentOrchestrator
    
    from bbc_aos.agents.planner_agent import PlannerAgent
    from bbc_aos.agents.context_agent import ContextAgent
    from bbc_aos.agents.resolver_agent import ResolverAgent
    from bbc_aos.agents.compression_agent import CompressionAgent
    from bbc_aos.agents.verification_agent import VerificationAgent
    from bbc_aos.agents.documentation_agent import DocumentationAgent
    from bbc_aos.agents.execution_agent import ExecutionAgent
    
    agent_classes = [
        PlannerAgent, ContextAgent, ResolverAgent, CompressionAgent,
        VerificationAgent, DocumentationAgent, ExecutionAgent
    ]
    
    inheritance_ok = True
    for cls in agent_classes:
        if not issubclass(cls, BaseAgent):
            print(f"[-] Class '{cls.__name__}' does not inherit from BaseAgent")
            inheritance_ok = False
            
    if inheritance_ok:
        print("[+] Import & Inheritance Verification: SUCCESS")
    else:
        success = False
except Exception as e:
    print(f"[-] Import & Inheritance Verification: FAILED\n{traceback.format_exc()}")
    success = False

# 4. Registry & Orchestration Routing Validation
print("[*] Step 4: Performing Registry & Orchestration Verification...")
try:
    # Set up registry
    registry = AgentRegistry()
    registry.reset()
    
    for cls in agent_classes:
        registry.register(cls)
        
    # Verify lookup
    reg_lookup_ok = True
    for cls in agent_classes:
        resolved = registry.get_agent_cls(cls.AGENT_ID)
        if resolved != cls:
            print(f"[-] Registry lookup mismatch for agent '{cls.AGENT_ID}'")
            reg_lookup_ok = False
            
    # Orchestrator Dispatch Test
    orch = AgentOrchestrator()
    
    # Run Planner plan dispatch
    mock_request = {
        "jsonrpc": "2.0",
        "id": "test_id_123",
        "method": "planner_agent.create_plan",
        "params": {
            "task_id": "task_456",
            "context": {
                "task_description": "Analyze repository and apply modular patch",
                "rules": []
            },
            "constraints": {},
            "metadata": {
                "originating_agent": "UserRequest",
                "trace_id": "trace_789"
            }
        }
    }
    
    response = orch.dispatch(mock_request)
    
    dispatch_ok = (
        response.get("jsonrpc") == "2.0" and
        response.get("id") == "test_id_123" and
        "result" in response and
        "steps" in response["result"]
    )
    
    # Safety sandbox path check test
    mock_unsafe_request = {
        "jsonrpc": "2.0",
        "id": "test_unsafe",
        "method": "planner_agent.create_plan",
        "params": {
            "task_id": "task_456",
            "context": {
                "task_description": "Unsafe test",
                "project_path": "/etc/shadow"
            }
        }
    }
    unsafe_response = orch.dispatch(mock_unsafe_request)
    unsafe_ok = (
        "error" in unsafe_response and
        unsafe_response["error"].get("code") == -32002  # Safety Boundary Breach
    )
    
    if reg_lookup_ok and dispatch_ok and unsafe_ok:
        print("[+] Registry & Orchestration Verification: SUCCESS")
    else:
        print(f"[-] Registry & Orchestration Verification Mismatch (reg={reg_lookup_ok}, dispatch={dispatch_ok}, safety={unsafe_ok})")
        success = False
        
except Exception as e:
    print(f"[-] Registry & Orchestration Verification: FAILED\n{traceback.format_exc()}")
    success = False

if success:
    print("[+] Phase 7B Validation: ALL PASSED")
    sys.exit(0)
else:
    sys.exit(1)
