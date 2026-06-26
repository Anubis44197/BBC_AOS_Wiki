from abc import ABC, abstractmethod
from typing import Any, Dict, List

class BaseAgent(ABC):
    """
    Abstract base class for all BBC-AOS agents.
    Defines the standard lifecycle methods and required metadata variables.
    """
    
    # Required metadata class attributes (to be overridden by subclasses)
    AGENT_ID: str = "base_agent"
    AGENT_VERSION: str = "1.0.0"
    SUPPORTED_ACTIONS: List[str] = []

    @abstractmethod
    def initialize(self) -> None:
        """
        Performs initial setup, logs initialization telemetry, and verifies setup boundaries.
        """
        pass

    @abstractmethod
    def validate_input(self, params: Dict[str, Any]) -> bool:
        """
        Validates the incoming JSON-RPC parameters against the agent's input schema.
        """
        pass

    @abstractmethod
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the agent's core function. No direct LLM invocations or loops are permitted here.
        """
        pass

    @abstractmethod
    def validate_output(self, result: Dict[str, Any]) -> bool:
        """
        Validates the execution results against the output schema.
        """
        pass

    @abstractmethod
    def finalize(self) -> None:
        """
        Performs cleanup and completes telemetry logging.
        """
        pass
