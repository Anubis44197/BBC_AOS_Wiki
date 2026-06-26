from typing import List, Set
from bbc_aos.integration.integration_audit_log import IntegrationAuditLog, IntegrationAuditEvent

class ReplayEngine:
    """
    Reconstructs historical subsystem execution states using immutable audit logs.
    """
    def __init__(self) -> None:
        pass

    def reconstruct_execution(self, replay_id: str, audit_log: IntegrationAuditLog) -> List[IntegrationAuditEvent]:
        """
        Gathers matching audit events and aligns them to reconstruct execution chronologically.
        
        Args:
            replay_id: Unique replay transaction ID.
            audit_log: Append-only audit logger instance.
            
        Returns:
            Sorted list of events matching the replay_id.
        """
        events = audit_log.get_events()
        matching_events = [evt for evt in events if evt.replay_id == replay_id]
        # Sort chronologically by timestamp
        matching_events.sort(key=lambda x: x.timestamp)
        return matching_events

    def fidelity_score(self, replay_id: str, audit_log: IntegrationAuditLog) -> float:
        events = self.reconstruct_execution(replay_id, audit_log)
        if not events:
            return 0.0
        observed = {event.event_type for event in events}
        terminal_events = {
            "execution_completed",
            "execution_failed",
            "security_validation_blocked",
        }
        if "security_validation_blocked" in observed:
            required = {
                "security_started",
                "security_validation_started",
                "security_validation_blocked",
                "security_completed",
            }
            return self._coverage(required, observed)
        required = {
            "security_started",
            "security_completed",
            "planner_started",
            "planner_completed",
            "context_started",
            "context_completed",
            "coder_started",
            "coder_completed",
            "tester_started",
            "tester_completed",
            "verification_started",
            "verification_completed",
        }
        return self._coverage(required, observed) if observed & terminal_events else 0.0

    def _coverage(self, required: Set[str], observed: Set[str]) -> float:
        return len(required & observed) / len(required)
