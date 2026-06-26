from bbc_aos.agents.agent_registry import AgentRegistry
from bbc_aos.agents.planner_agent import PlannerAgent
from bbc_aos.agents.context_agent import ContextAgent
from bbc_aos.agents.resolver_agent import ResolverAgent
from bbc_aos.agents.compression_agent import CompressionAgent
from bbc_aos.agents.verification_agent import VerificationAgent
from bbc_aos.agents.documentation_agent import DocumentationAgent
from bbc_aos.agents.execution_agent import ExecutionAgent
from bbc_aos.agents.coder_agent import CoderAgent
from bbc_aos.agents.tester_agent import TesterAgent

# Auto-register all core agents on package import
_registry = AgentRegistry()
_registry.register(PlannerAgent)
_registry.register(ContextAgent)
_registry.register(ResolverAgent)
_registry.register(CompressionAgent)
_registry.register(VerificationAgent)
_registry.register(DocumentationAgent)
_registry.register(ExecutionAgent)
_registry.register(CoderAgent)
_registry.register(TesterAgent)

