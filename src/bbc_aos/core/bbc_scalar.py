import json
import logging
from typing import Any, Dict, Optional, Tuple, Union

# Set up structured logging for the BBC-AOS core mathematical model
logger = logging.getLogger("bbc_aos.core.bbc_scalar")

# BBC States defining the precision and reliability level of a scalar value
STABLE: str = "STABLE"
WEAK: str = "WEAK"
SLEEPING: str = "SLEEPING"
NEG_ZERO: str = "NEG_ZERO"
SATURATED: str = "SATURATED"
UNSTABLE: str = "UNSTABLE"
DEGENERATE: str = "DEGENERATE"

# State multiplication tables (Basic arithmetic)
STATE_MULT_BASIC: Dict[Tuple[str, str], str] = {
    (STABLE, STABLE): STABLE,
    (STABLE, WEAK): WEAK,
    (WEAK, STABLE): WEAK,
    (WEAK, WEAK): WEAK,
    (STABLE, SLEEPING): SLEEPING,
    (SLEEPING, STABLE): SLEEPING,
    (STABLE, NEG_ZERO): NEG_ZERO,
    (NEG_ZERO, STABLE): NEG_ZERO,
    (UNSTABLE, STABLE): UNSTABLE,
    (STABLE, UNSTABLE): UNSTABLE,
    (DEGENERATE, STABLE): DEGENERATE,
    (STABLE, DEGENERATE): DEGENERATE,
}

# State multiplication tables (Linear Algebra context)
STATE_MULT_LINALG: Dict[Tuple[str, str], str] = {
    (STABLE, STABLE): STABLE,
}

class BBCScalar:
    """
    BBCScalar represents a float value combined with a mathematical validation state.
    It tracks numerical value stability, decay, and origin metadata to prevent
    untrusted semantic data spoofing.
    """
    def __init__(
        self,
        value: Union[float, int],
        state: str = STABLE,
        heal_count: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
        origin: Optional[str] = None
    ) -> None:
        """
        Initializes a BBCScalar instance.

        Args:
            value: The underlying floating-point value.
            state: The mathematical state of the scalar. Defaults to STABLE.
            heal_count: The number of times this scalar has been healed. Defaults to 0.
            metadata: Custom metadata dictionary. Defaults to None.
            origin: The origin of the scalar ('math' or 'semantic'). Defaults to None.
        """
        self.value: float = float(value)
        self.state: str = state
        self.heal_count: int = heal_count
        self.metadata: Dict[str, Any] = metadata or {}
        if origin:
            # Persist latest semantic origin hint
            self.metadata.setdefault("origin", origin)

    @property
    def origin(self) -> str:
        """Shortcut for accessing metadata origin."""
        return self.metadata.get("origin", "unknown")

    def __repr__(self) -> str:
        meta_str = f", metadata={self.metadata}" if self.metadata else ""
        return f"BBCScalar({self.value}, state='{self.state}', heal_count={self.heal_count}{meta_str})"

    def __float__(self) -> float:
        return self.value

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, BBCScalar):
            return self.value == other.value and self.state == other.state
        try:
            return self.value == float(other)
        except (ValueError, TypeError):
            return False

    def __hash__(self) -> int:
        return hash((self.value, self.state))

    def __lt__(self, other: Any) -> bool:
        val = other.value if isinstance(other, BBCScalar) else float(other)
        return self.value < val

    def __gt__(self, other: Any) -> bool:
        val = other.value if isinstance(other, BBCScalar) else float(other)
        return self.value > val

    def __le__(self, other: Any) -> bool:
        val = other.value if isinstance(other, BBCScalar) else float(other)
        return self.value <= val

    def __ge__(self, other: Any) -> bool:
        val = other.value if isinstance(other, BBCScalar) else float(other)
        return self.value >= val

    def _determine_new_state(self, other_state: str) -> str:
        """Determines the resulting state of combining this scalar with another state."""
        if self.state == DEGENERATE or other_state == DEGENERATE:
            return DEGENERATE
        if self.state == UNSTABLE or other_state == UNSTABLE:
            return UNSTABLE
        if self.state == NEG_ZERO or other_state == NEG_ZERO:
            return NEG_ZERO
        if self.state == SATURATED or other_state == SATURATED:
            return SATURATED
        if self.state == WEAK or other_state == WEAK:
            return WEAK
        if self.state == SLEEPING or other_state == SLEEPING:
            return SLEEPING
        return STABLE

    def _merge_origin(self, other: Any) -> str:
        """Origin downgrade rule: math + semantic -> semantic; math + math -> math."""
        self_origin = self.metadata.get("origin", "unknown")
        other_origin = other.metadata.get("origin", "unknown") if isinstance(other, BBCScalar) else "unknown"
        if self_origin == "math" and other_origin == "math":
            return "math"
        if self_origin == "math" or other_origin == "math":
            return "semantic"
        return self_origin if self_origin != "unknown" else other_origin

    def _build_result_metadata(self, other: Any, new_state: str) -> Dict[str, Any]:
        """Builds metadata for arithmetic result, including security flags and logging."""
        merged_origin = self._merge_origin(other)
        meta = {"origin": merged_origin}
        
        # Security flag check: math-origin scalar hitting DEGENERATE state
        is_degenerate_flag = False
        if merged_origin == "math" and new_state == DEGENERATE:
            is_degenerate_flag = True
        else:
            self_origin = self.metadata.get("origin", "unknown")
            other_origin = other.metadata.get("origin", "unknown") if isinstance(other, BBCScalar) else "unknown"
            if new_state == DEGENERATE and (self_origin == "math" or other_origin == "math"):
                is_degenerate_flag = True

        if is_degenerate_flag:
            meta["security_flag"] = "MATH_CORE_DEGENERATION_ANOMALY"
            logger.critical(
                "[DEGENERATE STATE DETECTED] Math core degeneration anomaly triggered. "
                f"Self value: {self.value} ({self.state}), Other value: {getattr(other, 'value', other)} ({getattr(other, 'state', 'STABLE')})"
            )
        
        return meta

    def __add__(self, other: Any) -> 'BBCScalar':
        val = other.value if isinstance(other, BBCScalar) else float(other)
        other_state = other.state if isinstance(other, BBCScalar) else STABLE
        new_state = self._determine_new_state(other_state)
        new_heal_count = max(self.heal_count, getattr(other, 'heal_count', 0))
        meta = self._build_result_metadata(other, new_state)
        return BBCScalar(self.value + val, new_state, new_heal_count, metadata=meta)

    def __radd__(self, other: Any) -> 'BBCScalar':
        return self.__add__(other)

    def __sub__(self, other: Any) -> 'BBCScalar':
        val = other.value if isinstance(other, BBCScalar) else float(other)
        other_state = other.state if isinstance(other, BBCScalar) else STABLE
        new_state = self._determine_new_state(other_state)
        new_heal_count = max(self.heal_count, getattr(other, 'heal_count', 0))
        meta = self._build_result_metadata(other, new_state)
        return BBCScalar(self.value - val, new_state, new_heal_count, metadata=meta)

    def __rsub__(self, other: Any) -> 'BBCScalar':
        val = other.value if isinstance(other, BBCScalar) else float(other)
        other_state = other.state if isinstance(other, BBCScalar) else STABLE
        new_state = self._determine_new_state(other_state)
        new_heal_count = max(self.heal_count, getattr(other, 'heal_count', 0))
        meta = self._build_result_metadata(other, new_state)
        return BBCScalar(val - self.value, new_state, new_heal_count, metadata=meta)

    def __mul__(self, other: Any) -> 'BBCScalar':
        val = other.value if isinstance(other, BBCScalar) else float(other)
        other_state = other.state if isinstance(other, BBCScalar) else STABLE
        new_state = self._determine_new_state(other_state)
        new_heal_count = max(self.heal_count, getattr(other, 'heal_count', 0))
        meta = self._build_result_metadata(other, new_state)
        return BBCScalar(self.value * val, new_state, new_heal_count, metadata=meta)

    def __rmul__(self, other: Any) -> 'BBCScalar':
        return self.__mul__(other)

    def __truediv__(self, other: Any) -> 'BBCScalar':
        val = other.value if isinstance(other, BBCScalar) else float(other)
        other_state = other.state if isinstance(other, BBCScalar) else STABLE
        new_heal_count = max(self.heal_count, getattr(other, 'heal_count', 0))
        
        if val == 0:
            logger.warning("[DIVISION BY ZERO DETECTED] Transitioning to UNSTABLE state.")
            return BBCScalar(0.0, UNSTABLE, new_heal_count)
            
        new_state = self._determine_new_state(other_state)
        meta = self._build_result_metadata(other, new_state)
        return BBCScalar(self.value / val, new_state, new_heal_count, metadata=meta)

    def enter_neg_zero(self) -> None:
        """Sets the scalar value to negative zero and its state to NEG_ZERO."""
        self.value = -0.0
        self.state = NEG_ZERO
        logger.warning("[NEG ZERO ENTERED] Scalar value set to -0.0 (NEG_ZERO state).")

    def resolve_neg_zero(self) -> 'BBCScalar':
        """
        Resolves negative zero to positive zero and downgrades the state to WEAK.
        Confidence is permanently degraded.
        """
        if self.state == NEG_ZERO:
            self.value = 0.0
            self.state = WEAK
            logger.info("[NEG ZERO RESOLVED] Negative zero resolved to 0.0 with state downgraded to WEAK.")
        return self

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the BBCScalar to a dictionary representation."""
        return {
            "value": self.value, 
            "state": self.state, 
            "heal_count": self.heal_count,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BBCScalar':
        """Deserializes a dictionary representation back to a BBCScalar instance."""
        meta = dict(data.get("metadata", {}))
        meta["origin"] = "semantic"
        return cls(
            data["value"], 
            data.get("state", STABLE), 
            data.get("heal_count", 0),
            meta
        )

class OmegaOperator:
    """
    OmegaOperator defines the healing mechanism for unstable or negative zero state scalars.
    """
    @staticmethod
    def trigger(scalar: BBCScalar) -> BBCScalar:
        """
        Triggers mathematical healing for a degraded scalar (NEG_ZERO, UNSTABLE).
        The value is set to an epsilon threshold and state is set to WEAK.
        DEGENERATE scalars are not modified.
        """
        if scalar.state in [NEG_ZERO, UNSTABLE]:
            old_state = scalar.state
            old_val = scalar.value
            epsilon = 1e-6 * (1 + scalar.heal_count)
            scalar.value = epsilon
            scalar.state = WEAK
            scalar.heal_count += 1
            logger.info(
                f"[OMEGA OPERATOR TRIGGERED] Healed scalar from state={old_state} (val={old_val}) "
                f"to state={WEAK} (val={epsilon}) | new heal_count={scalar.heal_count}"
            )
        return scalar

class BBCEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle BBCScalar serialization."""
    def default(self, obj: Any) -> Any:
        if isinstance(obj, BBCScalar):
            return obj.to_dict()
        return super().default(obj)

def bbc_hook(obj: Dict[str, Any]) -> Any:
    """JSON deserialization hook to automatically reconstruct BBCScalar objects."""
    if isinstance(obj, dict) and "value" in obj and "state" in obj:
        return BBCScalar.from_dict(obj)
    return obj

def bbc_data_ingestion(data: Any, origin: Optional[str] = None) -> Any:
    """
    Recursively scans and wraps numerical values into BBCScalar instances,
    assigning the specified origin validation tag.
    """
    if isinstance(data, list):
        return [bbc_data_ingestion(x, origin=origin) for x in data]
    if isinstance(data, dict):
        return {k: bbc_data_ingestion(v, origin=origin) for k, v in data.items()}
    if isinstance(data, BBCScalar):
        if origin:
            data.metadata.setdefault("origin", origin)
        return data
    if isinstance(data, (float, int)):
        scalar = BBCScalar(data)
        if origin:
            scalar.metadata["origin"] = origin
        return scalar
    return data
