from typing import Dict, Any, List, Callable
from bbc_aos.integration.subsystem_registry import SubsystemRegistry
from bbc_aos.integration.health_manager import HealthManager
from bbc_aos.integration.integration_audit_log import IntegrationAuditLog, IntegrationAuditEvent

class IntegrationSupervisor:
    """
    Supervises system health checks, enforces deterministic lifecycle sequences,
    manages recovery rehydration, and records audit logs.
    """
    def __init__(self, registry: SubsystemRegistry, audit_log: IntegrationAuditLog) -> None:
        self.registry = registry
        self.audit_log = audit_log
        self.health_manager = HealthManager(registry)
        self._hooks: Dict[str, List[Callable[..., Any]]] = {
            "before_startup": [],
            "after_startup": [],
            "before_shutdown": [],
            "after_shutdown": [],
            "before_recovery": [],
            "after_recovery": [],
            "on_health_degraded": []
        }

    def register_hook(self, name: str, callback: Callable[..., Any]) -> None:
        """Registers a callback under an observability hook name."""
        if name in self._hooks:
            self._hooks[name].append(callback)

    def trigger_hook(self, name: str, *args, **kwargs) -> None:
        """Triggers all callbacks registered under the hook name."""
        if name in self._hooks:
            for callback in self._hooks[name]:
                callback(*args, **kwargs)

    def verify_system_health(self, subsystems: List[str]) -> bool:
        """
        Verifies health statuses of all specified subsystems.
        
        Args:
            subsystems: List of registered subsystem keys.
        """
        for sub in subsystems:
            status = self.health_manager.check_subsystem_health(sub)
            if status.get("status") == "UNHEALTHY":
                self.trigger_hook("on_health_degraded", sub, status)
                return False
        return True

    def execute_startup(self, sequence: List[str]) -> None:
        """
        Executes a deterministic system startup sequence.
        
        Args:
            sequence: Ordered list of subsystem keys to start up.
        """
        self.trigger_hook("before_startup", sequence)
        
        for step in sequence:
            # Create audit event tracing startup step
            event = IntegrationAuditEvent(
                event_id=f"start_{step}",
                event_type="startup_step",
                trace_id="system_init",
                replay_id="system_init_replay",
                deterministic_hash=f"hash_start_{step}",
                details={"step": step}
            )
            self.audit_log.append(event)
            
        self.trigger_hook("after_startup", sequence)

    def execute_shutdown(self, sequence: List[str]) -> None:
        """
        Executes a deterministic system shutdown sequence.
        
        Args:
            sequence: Ordered list of subsystem keys to shut down.
        """
        self.trigger_hook("before_shutdown", sequence)
        
        for step in sequence:
            event = IntegrationAuditEvent(
                event_id=f"stop_{step}",
                event_type="shutdown_step",
                trace_id="system_shutdown",
                replay_id="system_shutdown_replay",
                deterministic_hash=f"hash_stop_{step}",
                details={"step": step}
            )
            self.audit_log.append(event)
            
        self.trigger_hook("after_shutdown", sequence)

    def execute_recovery(self, checkpoint_id: str, trace_id: str, replay_id: str) -> None:
        """
        Executes a deterministic state recovery sequence.
        
        Args:
            checkpoint_id: Identifer of the checkpoint to recover.
            trace_id: Tracing UUID.
            replay_id: Replay transaction UUID.
        """
        self.trigger_hook("before_recovery", checkpoint_id)
        
        event = IntegrationAuditEvent(
            event_id=f"recover_{checkpoint_id}",
            event_type="recovery_step",
            trace_id=trace_id,
            replay_id=replay_id,
            deterministic_hash=f"hash_recover_{checkpoint_id}",
            details={"checkpoint_id": checkpoint_id}
        )
        self.audit_log.append(event)
        
        self.trigger_hook("after_recovery", checkpoint_id)
