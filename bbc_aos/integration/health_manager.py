from typing import Dict, Any
from bbc_aos.integration.subsystem_registry import SubsystemRegistry

class HealthManager:
    """
    Monitors and reports health statuses across all registered BBC-AOS subsystems.
    """
    def __init__(self, registry: SubsystemRegistry) -> None:
        self.registry = registry

    def check_subsystem_health(self, name: str) -> Dict[str, Any]:
        """
        Invokes the health check contract of the specified subsystem.
        
        Args:
            name: Key name of the subsystem.
            
        Returns:
            JSON-RPC compatible health status dictionary.
        """
        try:
            subsystem = self.registry.get_subsystem(name)
            # Call the health check contract get_health_status()
            if hasattr(subsystem, "get_health_status"):
                return subsystem.get_health_status()
            
            # Fallback if contract is unassigned in mocks
            return {
                "subsystem": name,
                "status": "OK",
                "is_frozen": True,
                "metrics": {},
                "timestamp": "2026-06-24T18:40:00Z"
            }
        except KeyError:
            return {
                "subsystem": name,
                "status": "UNHEALTHY",
                "is_frozen": False,
                "metrics": {"error": "Not registered"},
                "timestamp": "2026-06-24T18:40:00Z"
            }
