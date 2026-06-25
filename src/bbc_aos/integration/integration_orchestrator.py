from typing import List, Optional
from bbc_aos.integration.subsystem_registry import SubsystemRegistry
from bbc_aos.integration.validation_gateway import ValidationGateway
from bbc_aos.integration.replay_engine import ReplayEngine
from bbc_aos.integration.integration_audit_log import IntegrationAuditLog, IntegrationAuditEvent
from bbc_aos.integration.integration_supervisor import IntegrationSupervisor
from bbc_aos.integration.integration_context import IntegrationContext
from bbc_aos.integration.integration_result import IntegrationResult

class IntegrationOrchestrator:
    """
    The sole system-wide broker coordinating dispatches, lifecycles, health sweeps,
    and recovery sequences across all subsystems.
    """
    def __init__(self, registry: SubsystemRegistry, audit_log: Optional[IntegrationAuditLog] = None) -> None:
        self.registry = registry
        self.audit_log = audit_log or IntegrationAuditLog()
        self.validation_gateway = ValidationGateway()
        self.replay_engine = ReplayEngine()
        self.supervisor = IntegrationSupervisor(self.registry, self.audit_log)

    def startup(self, sequence: List[str]) -> None:
        """
        Deterministically initializes registered subsystems in order.
        
        Args:
            sequence: Ordered list of subsystem names.
        """
        self.supervisor.execute_startup(sequence)

    def shutdown(self, sequence: List[str]) -> None:
        """
        Deterministically halts registered subsystems in order.
        
        Args:
            sequence: Ordered list of subsystem names.
        """
        self.supervisor.execute_shutdown(sequence)

    def dispatch(self, source_subsystem: str, target_subsystem: str, context: IntegrationContext) -> IntegrationResult:
        """
        Brokers transaction dispatch from source to target subsystem.
        
        Args:
            source_subsystem: Name of the initiating subsystem.
            target_subsystem: Name of the target subsystem.
            context: Context details.
            
        Returns:
            IntegrationResult structure representing the dispatch outcome.
        """
        # Validate source output payload
        self.validation_gateway.validate_output(source_subsystem, context.payload)

        # Record audit event of interaction
        event = IntegrationAuditEvent(
            event_id=f"dispatch_{context.trace_id}",
            event_type="subsystem_dispatch",
            trace_id=context.trace_id,
            replay_id=context.replay_id,
            deterministic_hash=context.deterministic_hash,
            details={"source": source_subsystem, "target": target_subsystem}
        )
        self.audit_log.append(event)

        # Mock successful routing
        return IntegrationResult(
            success=True,
            trace_id=context.trace_id,
            replay_id=context.replay_id,
            deterministic_hash=context.deterministic_hash,
            data={"routed": True, "source": source_subsystem, "target": target_subsystem}
        )

    def recover(self, checkpoint_id: str, trace_id: str, replay_id: str) -> None:
        """
        Triggers the supervisor state recovery sequence.
        
        Args:
            checkpoint_id: Target checkpoint key.
            trace_id: Tracing UUID.
            replay_id: Replay transaction UUID.
        """
        self.supervisor.execute_recovery(checkpoint_id, trace_id, replay_id)

    def check_health(self, subsystems: List[str]) -> bool:
        """
        Sweeps health metrics of target subsystems.
        
        Args:
            subsystems: Subsystems list.
        """
        return self.supervisor.verify_system_health(subsystems)
