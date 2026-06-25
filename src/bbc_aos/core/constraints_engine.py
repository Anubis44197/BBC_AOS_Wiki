"""
BBC HMPU Governor / Constraints Engine - Phase 5A
Implements the HMPU Governor managing matrix weights, Shannon Chaos calculations,
convergence scoring, self-healing thresholds, and gradient bending.
"""

import math
import time
import json
import os
import threading
import logging
from collections import Counter
from typing import List, Dict, Any, Optional, Tuple, Union

# Import modular components
from bbc_aos.core.bbc_scalar import (
    BBCScalar, OmegaOperator, BBCEncoder, bbc_hook, bbc_data_ingestion,
    STABLE, WEAK, NEG_ZERO, UNSTABLE, DEGENERATE
)
from bbc_aos.core.matrix_ops import MatrixOps

# Set up logging namespace
logger = logging.getLogger("bbc_aos.core.constraints_engine")


class HMPU_Governor:
    """
    HMPU Governor (v5.6+ Session & Origin Aware)
    The central controller for the Hybrid Mathematical Processing Unit.
    """

    def __init__(self, weights_path: Optional[str] = None, state_manager: Optional[Any] = None, 
                 heal_budget: int = 5, session_heal_budget: int = 5) -> None:
        """
        Initializes the HMPU Governor.

        Args:
            weights_path: Explicit path to the weights JSON file.
            state_manager: Shared state manager instance.
            heal_budget: Budget for healing operations.
            session_heal_budget: Session specific healing limit.
        """
        if weights_path is None:
            from bbc_aos.config import BBCConfig
            bbc_dir = BBCConfig.get_bbc_dir()
            weights_path = os.path.join(bbc_dir, 'hmpu_weights.json')
        
        self.weights_path: str = weights_path
        try:
            os.makedirs(os.path.dirname(self.weights_path), exist_ok=True)
        except Exception as e:
            logger.warning(f"Failed to create weights directory: {e}")
            
        self.lock: threading.RLock = threading.RLock()

        # StateManager integration
        if state_manager is not None:
            self.state_manager = state_manager
        else:
            from bbc_aos.memory.working.state_manager import StateManager
            self.state_manager = StateManager(heal_budget=heal_budget, session_heal_budget=session_heal_budget)

        # Aura Field Base Matrix (The Core Geometry) - Wrapped in BBCScalar
        self._Aura_Base: List[List[BBCScalar]] = bbc_data_ingestion([
            [1.00, 0.00, 0.00], # S (Structural Anchor)
            [0.75, 0.15, 0.10], # C (Chaos Density)
            [0.70, 0.10, 0.20]  # P (Pulse Alpha)
        ], origin="math")

        # Aura Gradient Weights (Persistent)
        self._Aura_Weights: List[List[BBCScalar]] = self._load_weights()
        self._iterations: int = 5
        self.heal_limit: int = self.state_manager.session_heal_budget

    def _origin_from_scalar(self, scalar: Any, default: str = "unknown") -> str:
        """Extracts origin metadata from a BBCScalar."""
        if isinstance(scalar, BBCScalar):
            return scalar.metadata.get("origin", default)
        return default

    def _load_weights(self) -> List[List[BBCScalar]]:
        """Loads weights from disk or initializes to zero."""
        if os.path.exists(self.weights_path):
            try:
                with open(self.weights_path, 'r', encoding='utf-8') as f:
                    data = json.load(f, object_hook=bbc_hook)
                    return bbc_data_ingestion(data, origin="math")
            except Exception as e:
                logger.warning(f"Failed to load weights file, using fallback zero weights: {e}")
        return bbc_data_ingestion([[0.0] * 3 for _ in range(3)], origin="math")

    def _save_weights(self) -> None:
        """Saves current weights to disk."""
        try:
            with open(self.weights_path, 'w', encoding='utf-8') as f:
                json.dump(self._Aura_Weights, f, cls=BBCEncoder)
        except Exception as e:
            logger.error(f"Failed to save weights file to '{self.weights_path}': {e}")

    def get_field_stability(self) -> float:
        """
        Calculates the mathematical stability (condition number) of the Aura Field matrix.
        Returns a score where lower is more stable (1.0 is ideal).
        If the matrix is singular, returns infinity.
        """
        with self.lock:
            # Combine Base and Weights
            M = [[self._Aura_Base[i][j] + self._Aura_Weights[i][j] for j in range(3)] for i in range(3)]
        
        try:
            # Calculate condition number of matrix M
            cond = MatrixOps.condition_number(M)
            
            # Add a very tiny micro-entropy for dynamic tracking, but scale it to not break the primary state
            micro_entropy = (time.time() % 3600) / 3600000.0  # even smaller fluctuation 
            
            normalized_cond = float(cond) / 2.5 + micro_entropy
            return normalized_cond
        except Exception as e:
            logger.debug(f"Stability solver failed, returning infinity: {e}")
            return float('inf')

    def _calculate_chaos(self, text: str) -> float:
        """Calculates Shannon Chaos Density of a signal."""
        if not text or not isinstance(text, str):
            return 0.0
        cnt = Counter(text)
        ln = len(text)
        entropy = sum(-(v / ln) * math.log2(v / ln) for v in cnt.values())
        return entropy if not math.isnan(entropy) else 0.0

    def chaos_derivative_filter(self, stream: List[str], threshold: float = 0.4) -> List[str]:
        """
        Operator 1: Chaos Derivative (dC/dt)
        Filters noise by detecting phase shifts in information density.
        """
        signals = []
        prev_chaos = 0.0
        for chunk in stream:
            curr_chaos = self._calculate_chaos(chunk)
            dc_dt = abs(curr_chaos - prev_chaos)
            if dc_dt > threshold:
                signals.append(chunk)
            prev_chaos = curr_chaos
        return signals

    def aura_field_score(self, s: float, c: float, p: float) -> float:
        """
        Calculates the convergence score within the Aura Field.
        STRICT MODE: Raises RuntimeError if DEGENERATE state is detected.
        """
        s_bbc, c_bbc, p_bbc = bbc_data_ingestion([s, c, p], origin="semantic")

        # DEGENERATE girdi kontrolü — Origin bilgisiyle
        degenerate_inputs = [x for x in [s_bbc, c_bbc, p_bbc] if x.state == DEGENERATE]
        if degenerate_inputs:
            origin = self._origin_from_scalar(degenerate_inputs[0])
            if self.state_manager:
                self.state_manager.record_degenerate(origin)
            raise RuntimeError(f"DEGENERATE state detected. OMEGA TRIGGER activated. Origin: {origin}")

        v = [s_bbc, c_bbc, p_bbc]

        with self.lock:
            M = [[self._Aura_Base[i][j] + self._Aura_Weights[i][j] for j in range(3)] for i in range(3)]

        try:
            for _ in range(self._iterations):
                v_new = []
                for i in range(3):
                    val = BBCScalar(0.0)
                    for j in range(3):
                        val = val + (M[i][j] * v[j])
                    v_new.append(val)

                # İterasyon sırasında DEGENERATE kontrolü
                if any(x.state == DEGENERATE for x in v_new):
                    if self.state_manager:
                        self.state_manager.record_degenerate("math")
                    raise RuntimeError("DEGENERATE state mutation during field iteration (math corruption)")

                # Normalize
                max_val_scalar = v_new[0]
                for x in v_new[1:]:
                    if float(x) > float(max_val_scalar):
                        max_val_scalar = x
                mx = float(max_val_scalar) if float(max_val_scalar) > 0 else 1.0
                v = [x / mx for x in v_new]

        except RuntimeError:
            raise
        except Exception as e:
            logger.error(f"Error during aura field score iteration: {e}")
            return 0.0

        # Proprietary Weighted Synthesis
        score_scalar = (v[0] * 0.6) + (v[1] * 0.2) + (v[2] * 0.2)

        if score_scalar.state == DEGENERATE:
            if self.state_manager:
                self.state_manager.record_degenerate("math")
            raise RuntimeError("DEGENERATE state in final score calculation")

        return float(score_scalar)

    def self_heal_protocol(self) -> int:
        """
        Ω trigger: Heals weights in neg_zero or unstable states.
        Enforces session budget and heal limits.
        Result kodları: 1 (heal uygulandı), 0 (hiç gerekmedi), -1 (DEGENERATE), -2 (bütçe bitti)
        """
        healed_count = 0
        with self.lock:
            for i in range(3):
                for j in range(3):
                    w = self._Aura_Weights[i][j]
                    if w.state in [NEG_ZERO, UNSTABLE, DEGENERATE]:
                        # Session bütçe kontrolü
                        budget_left = self.state_manager.consume_heal_budget() if self.state_manager else 1
                        if budget_left == -2:
                            logger.critical("CRITICAL: Session healing budget exhausted.")
                            return -2

                        if w.heal_count > self.heal_limit:
                            if w.state != DEGENERATE:
                                w.state = DEGENERATE
                            if self.state_manager:
                                self.state_manager.record_degenerate("math")
                            logger.critical(f"CRITICAL: Pipeline stop due to DEGENERATE state persistence at [{i},{j}].")
                            return -1
                        else:
                            self._Aura_Weights[i][j] = OmegaOperator.trigger(w)
                            healed_count += 1
            self._save_weights()

        if healed_count > 0:
            return 1
        return 0

    def aura_gradient_bend(self, delta: float, stability: bool) -> None:
        """
        Operator 2: Aura Gradient (nabla A)
        Bends the decision hyperplane based on feedback error.
        """
        lr = 0.001

        with self.lock:
            for i in range(3):
                if stability:
                    adjustment = delta * lr
                    self._Aura_Weights[i][i] += adjustment
                else:
                    current = self._Aura_Weights[i][i]
                    if current.state == STABLE:
                        current.state = WEAK
                    elif current.state == WEAK:
                        current.state = UNSTABLE
                    elif current.state == UNSTABLE:
                        current.enter_neg_zero()

            self.self_heal_protocol()
            self._save_weights()

    def pulse_perturbation_sim(self, current_aura: float, intent_magnitude: float, op_type: str) -> Dict[str, Any]:
        """
        Operator 3: Pulse Perturbation (P_t+1)
        Predicts chaotic collapse before execution.
        """
        impact_map = {"Refactor": 0.25, "Patch": 0.08, "Feature": 0.15}
        impact = impact_map.get(op_type, 0.1)
        predicted_pulse = current_aura * (1 - (impact * intent_magnitude))
        is_stable = predicted_pulse > 0.65

        return {
            "predicted_pulse": round(predicted_pulse, 4),
            "is_stable": is_stable,
            "risk_level": "HIGH" if not is_stable else "LOW",
            "timestamp": time.time()
        }

    def focus_projection(self, query_vec: List[float], target_vecs: List[Dict[str, Any]]) -> List[str]:
        """
        Operator 4: Focus Projection (F_perp)
        Eliminates orthogonal noise vectors to maximize semantic density.
        """
        focused_targets = []
        q = bbc_data_ingestion(query_vec, origin="semantic")
        threshold = BBCScalar(0.80)
        threshold_sq = threshold * threshold

        q_norm_sq = BBCScalar(0.0)
        for x in q:
            q_norm_sq = q_norm_sq + (x * x)

        for target in target_vecs:
            t = bbc_data_ingestion(target.get("vec", []), origin="semantic")
            if len(t) != len(q) or len(t) == 0:
                continue

            dot = BBCScalar(0.0)
            t_norm_sq = BBCScalar(0.0)
            for a, b in zip(q, t):
                dot = dot + (a * b)
                t_norm_sq = t_norm_sq + (b * b)

            denom_sq = q_norm_sq * t_norm_sq
            if float(denom_sq) <= 0:
                continue

            # cos²(θ) > threshold² karşılaştırması (sqrt-free)
            lhs = dot * dot
            rhs = threshold_sq * denom_sq
            if float(lhs) > float(rhs):
                focused_targets.append(target["name"])

        return focused_targets