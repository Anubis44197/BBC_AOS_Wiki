"""
BBC Context Optimizer - Phase 3: Context Optimizer Guardrails
Analyzes the symbol graph and blast radius metrics to generate task-focused context decisions for AI.
"""

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Set up logging namespace
logger = logging.getLogger("bbc_aos.core.context_optimizer")


class ImpactLevel(Enum):
    """Enumerates impact levels for codebase symbols."""
    PRIMARY = "primary"      # %40 Importance - The target symbol itself
    DIRECT = "direct"        # %30 Importance - Directly calling or calling target (level 1)
    INDIRECT = "indirect"    # %20 Importance - Transitive dependents (level 2+)
    DISTANT = "distant"      # %10 Importance - Distant dependents (level 3+)
    IGNORE = "ignore"        # %0 Importance - External, unknown, or noise


class ContextOptimizerError(Exception):
    """Base exception class for Context Optimizer errors."""
    pass


class ContextReductionError(ContextOptimizerError):
    """Raised when the context reduction ratio is below safe thresholds."""
    pass


@dataclass
class SymbolResolutionResult:
    """Represents the outcome of a symbol name resolution query."""
    primary: Optional[str]
    candidates: List[str]
    resolution_type: str            # "exact", "unique_short", "graph_scored", "ambiguous", "not_found"
    warnings: List[str]
    scores: Dict[str, float]
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializes result properties to a dictionary."""
        return {
            "primary": self.primary,
            "candidates": self.candidates,
            "resolution_type": self.resolution_type,
            "warnings": self.warnings,
            "scores": {k: round(v, 3) for k, v in self.scores.items()}
        }


class SymbolResolver:
    """
    Resolves shorthand user-provided symbols to fully qualified graph symbol names.
    Employs a strict deterministic hierarchy (exact match, unique short, scored graph metrics).
    """
    
    def __init__(self, symbol_graph: Dict[str, Any]) -> None:
        """
        Initializes the SymbolResolver.

        Args:
            symbol_graph: The parsed JSON graph data from SymbolGraph.
        """
        # Ensure deterministic iteration by sorting the incoming symbol array keys
        symbols_list = symbol_graph.get("symbols", [])
        self.symbols: Dict[str, Dict[str, Any]] = {
            s["symbol"]: s for s in sorted(symbols_list, key=lambda x: x["symbol"])
        }
        
        self.short_name_map: Dict[str, List[str]] = {}
        self.symbol_metrics: Dict[str, Dict[str, Any]] = {}
        
        self._build_short_name_index()
        self._build_graph_metrics()
    
    def _build_short_name_index(self) -> None:
        """Builds lookup index from short-name components to fully qualified names."""
        self.short_name_map = {}
        for full_name in sorted(self.symbols.keys()):
            short_name = full_name.split('.')[-1]
            if short_name not in self.short_name_map:
                self.short_name_map[short_name] = []
            self.short_name_map[short_name].append(full_name)
        
        # Sort each candidate list to keep resolution deterministic
        for short_name in self.short_name_map:
            self.short_name_map[short_name] = sorted(self.short_name_map[short_name])
    
    def _build_graph_metrics(self) -> None:
        """Computes structural call network statistics for all symbols."""
        self.symbol_metrics = {}
        for full_name in sorted(self.symbols.keys()):
            sym_data = self.symbols[full_name]
            
            # Indegree (number of callers)
            called_by = sym_data.get("called_by", [])
            indegree = len(called_by)
            
            # Outdegree (number of callees)
            calls = sym_data.get("calls", [])
            outdegree = len(calls)
            
            total_calls = indegree + outdegree
            file_path = sym_data.get("file", "")
            
            self.symbol_metrics[full_name] = {
                "indegree": indegree,
                "outdegree": outdegree,
                "total_calls": total_calls,
                "file": file_path,
                "short_name": full_name.split('.')[-1]
            }
    
    def resolve(self, target: str, context_file: Optional[str] = None) -> SymbolResolutionResult:
        """
        Attempts to resolve the target symbol name.

        Args:
            target: Shorthand or full symbol identifier.
            context_file: Optional file path constraint hint.

        Returns:
            A SymbolResolutionResult instance.
        """
        logger.info(f"Resolving symbol query: '{target}' (Context File: {context_file})")
        
        # Step 1: Exact match
        if target in self.symbols:
            logger.debug(f"Exact match found for symbol: {target}")
            return SymbolResolutionResult(
                primary=target,
                candidates=[target],
                resolution_type="exact",
                warnings=[],
                scores={target: 1.0}
            )
        
        # Step 2: Short-name alias lookup
        if target in self.short_name_map:
            candidates = self.short_name_map[target]
            if len(candidates) == 1:
                full_name = candidates[0]
                logger.debug(f"Unique short-name match found: '{target}' -> '{full_name}'")
                return SymbolResolutionResult(
                    primary=full_name,
                    candidates=candidates,
                    resolution_type="unique_short",
                    warnings=[],
                    scores={full_name: 1.0}
                )
            else:
                logger.info(f"Ambiguous short name '{target}' matched {len(candidates)} candidates. Scoring...")
                return self._resolve_by_graph_score(target, candidates, context_file)
        
        # Fallback: No matches found
        logger.warning(f"Symbol '{target}' not found in registered symbol map.")
        return SymbolResolutionResult(
            primary=None,
            candidates=[],
            resolution_type="not_found",
            warnings=[f"'{target}' sembolü graph'ta bulunamadı"],
            scores={}
        )
    
    def _resolve_by_graph_score(self, short_name: str, candidates: List[str], 
                                 context_file: Optional[str]) -> SymbolResolutionResult:
        """Scores candidates based on call graph centrality metrics and file proximity."""
        scores: Dict[str, float] = {}
        for full_name in sorted(candidates):
            metrics = self.symbol_metrics[full_name]
            score = metrics["indegree"] * 2.0
            score += metrics["total_calls"] * 0.5
            
            # File proximity bonus
            if context_file and metrics["file"]:
                if context_file in metrics["file"] or metrics["file"] in context_file:
                    score += 3.0
            scores[full_name] = score
            
        # Sort candidates descending by score, ascending by name on tie
        sorted_candidates = sorted(scores.keys(), key=lambda x: (-scores[x], x))
        best_candidate = sorted_candidates[0]
        best_score = scores[best_candidate]
        second_best_score = scores[sorted_candidates[1]] if len(sorted_candidates) > 1 else 0.0
        
        # Check for ambiguity threshold
        if second_best_score > 0 and (best_score - second_best_score) < 1.0:
            warnings = [
                f"'{short_name}' için birden fazla eşleşme bulundu: {candidates}",
                f"En iyi aday: {best_candidate} (score: {best_score:.1f})",
                f"İkinci aday: {sorted_candidates[1]} (score: {second_best_score:.1f})",
                "Lütfen tam sembol adını (full_name) kullanın"
            ]
            logger.warning(f"Ambiguity threshold breached for '{short_name}' best candidates.")
            return SymbolResolutionResult(
                primary=None,
                candidates=sorted_candidates,
                resolution_type="ambiguous",
                warnings=warnings,
                scores=scores
            )
            
        return SymbolResolutionResult(
            primary=best_candidate,
            candidates=sorted_candidates,
            resolution_type="graph_scored",
            warnings=[],
            scores=scores
        )
    
    def get_all_short_names(self) -> Dict[str, List[str]]:
        """Returns a copy of the short name candidate registry."""
        return self.short_name_map.copy()


@dataclass
class SymbolImpact:
    """Represents calculated blast-radius statistics for a symbol."""
    symbol: str
    level: ImpactLevel
    score: float
    depth: int
    call_paths: List[List[str]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializes SymbolImpact state to a dictionary."""
        return {
            "symbol": self.symbol,
            "level": self.level.value,
            "score": round(self.score, 3),
            "depth": self.depth,
            "call_paths": self.call_paths[:3]
        }


@dataclass  
class ContextDecision:
    """Encapsulates context prioritization selections generated by ContextOptimizer."""
    target: str
    primary: List[str]
    direct: List[str]
    indirect: List[str]
    ignored: List[str]
    safety: List[str]
    impact_scores: Dict[str, float]
    stats: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializes ContextDecision properties to a sorted deterministic dictionary representation."""
        return {
            "target": self.target,
            "primary": sorted(self.primary),
            "direct": sorted(self.direct),
            "indirect": sorted(self.indirect),
            "ignored": sorted(self.ignored),
            "safety": self.safety,
            "impact_scores": {k: round(v, 3) for k, v in sorted(self.impact_scores.items())},
            "stats": self.stats
        }


class BlastRadiusAnalyzer:
    """
    Traces reverse dependency flows (callers) starting from a target symbol
    to compute etki (impact) score rankings.
    """
    
    def __init__(self, symbol_graph: Dict[str, Any]) -> None:
        """
        Initializes BlastRadiusAnalyzer.

        Args:
            symbol_graph: The parsed JSON graph data.
        """
        symbols_list = symbol_graph.get("symbols", [])
        self.symbols: Dict[str, Dict[str, Any]] = {
            s["symbol"]: s for s in sorted(symbols_list, key=lambda x: x["symbol"])
        }
        self.graph_stats: Dict[str, Any] = symbol_graph.get("graph_stats", {})
        self.called_by_index: Dict[str, List[str]] = {}
        self._build_called_by_index()
    
    def _build_called_by_index(self) -> None:
        """Index caller definitions, filtering out external and recursive links."""
        for sym_name in sorted(self.symbols.keys()):
            sym_data = self.symbols[sym_name]
            self.called_by_index[sym_name] = []
            called_by = sym_data.get("called_by", [])
            
            for call in called_by:
                caller = call.get("symbol") if isinstance(call, dict) else call
                call_type = call.get("type", "internal") if isinstance(call, dict) else "internal"
                
                if caller and caller != sym_name and call_type == "internal":
                    self.called_by_index[sym_name].append(caller)
            
            self.called_by_index[sym_name] = sorted(self.called_by_index[sym_name])
            
    def analyze(self, target: str, max_depth: int = 5) -> Tuple[List[SymbolImpact], List[str], List[str]]:
        """
        Traces reverse dependency network (called_by) up to max_depth.

        Args:
            target: The fully resolved symbol name to analyze.
            max_depth: Maximum recursion level.

        Returns:
            A tuple of (sorted_impacts, ignored_externals, safety_warnings).
        """
        logger.info(f"Analyzing blast radius traversal for target: '{target}' (Max Depth: {max_depth})")
        if target not in self.symbols:
            return [], [], [f"Target '{target}' not found in graph"]
            
        impacts: Dict[str, SymbolImpact] = {}
        visited: Set[str] = set()
        ignored_external_calls: List[str] = []
        safety_warnings: List[str] = []
        
        # Parse initial call properties defined inside target symbol
        target_sym = self.symbols[target]
        target_calls = target_sym.get("calls", [])
        for call in target_calls:
            call_type = call.get("type", "internal") if isinstance(call, dict) else "internal"
            call_symbol = call.get("symbol") if isinstance(call, dict) else call
            
            if call_type == "external" and call_symbol:
                ignored_external_calls.append(call_symbol)
            elif call_type == "unknown" and call_symbol:
                safety_warnings.append(f"Unknown call '{call_symbol}' detected in target")
                
        # Run BFS traversal using a sorted queue list
        queue: List[Tuple[str, int, List[str]]] = [(target, 0, [target])]
        
        while queue:
            current, depth, path = queue.pop(0)
            if current in visited or depth > max_depth:
                continue
            visited.add(current)
            
            score = self._calculate_impact_score(depth, current)
            level = self._depth_to_level(depth)
            
            if current not in impacts:
                impacts[current] = SymbolImpact(
                    symbol=current,
                    level=level,
                    score=score,
                    depth=depth,
                    call_paths=[]
                )
                
            if len(impacts[current].call_paths) < 3:
                impacts[current].call_paths.append(path.copy())
                
            if depth < max_depth:
                current_sym = self.symbols.get(current, {})
                callers_data = current_sym.get("called_by", [])
                
                for call in callers_data:
                    caller = call.get("symbol") if isinstance(call, dict) else call
                    call_type = call.get("type", "internal") if isinstance(call, dict) else "internal"
                    
                    if call_type == "external":
                        if caller and caller not in ignored_external_calls:
                            ignored_external_calls.append(caller)
                        continue
                        
                    if call_type == "unknown":
                        if caller and caller not in safety_warnings:
                            safety_warnings.append(f"Unknown call '{caller}' detected in graph traversal")
                        continue
                        
                    if caller and caller not in path:
                        new_path = path + [caller]
                        queue.append((caller, depth + 1, new_path))
                        
                # Re-sort BFS queue for exact deterministic consistency
                queue = sorted(queue, key=lambda x: x[0])
                
        sorted_impacts = sorted(impacts.values(), key=lambda x: (-x.score, x.depth, x.symbol))
        return sorted_impacts, sorted(ignored_external_calls), safety_warnings
        
    def _calculate_impact_score(self, depth: int, symbol: str) -> float:
        """Determines impact score values matching legacy weights."""
        base_scores = {
            0: 1.0,
            1: 0.75,
            2: 0.50,
            3: 0.25,
        }
        base = base_scores.get(min(depth, 3), 0.1)
        
        caller_count = len(self.called_by_index.get(symbol, []))
        if caller_count > 5:
            base *= 1.1
        elif caller_count == 0 and depth > 0:
            base *= 0.9
            
        return min(base, 1.0)
        
    def _depth_to_level(self, depth: int) -> ImpactLevel:
        """Resolves depth integer to standard ImpactLevel enum value."""
        if depth == 0:
            return ImpactLevel.PRIMARY
        elif depth == 1:
            return ImpactLevel.DIRECT
        elif depth == 2:
            return ImpactLevel.INDIRECT
        else:
            return ImpactLevel.DISTANT


class ContextOptimizer:
    """
    ContextOptimizer prioritizes symbols by importance categories,
    verifies context reduction safety thresholds, and outputs deterministic ContextDecisions.
    """
    DEFAULT_PRIMARY_THRESHOLD: float = 0.85
    DEFAULT_DIRECT_THRESHOLD: float = 0.60
    DEFAULT_INDIRECT_THRESHOLD: float = 0.35
    DEFAULT_MAX_CONTEXT_SYMBOLS: int = 50
    DEFAULT_MIN_REDUCTION_RATIO: float = 0.6
    
    def __init__(self, symbol_graph: Dict[str, Any],
                 primary_threshold: float = DEFAULT_PRIMARY_THRESHOLD,
                 direct_threshold: float = DEFAULT_DIRECT_THRESHOLD,
                 indirect_threshold: float = DEFAULT_INDIRECT_THRESHOLD,
                 max_symbols: int = DEFAULT_MAX_CONTEXT_SYMBOLS,
                 min_reduction_ratio: float = DEFAULT_MIN_REDUCTION_RATIO) -> None:
        """
        Initializes ContextOptimizer.

        Args:
            symbol_graph: The parsed JSON graph data.
            primary_threshold: Threshold for primary classification.
            direct_threshold: Threshold for direct classification.
            indirect_threshold: Threshold for indirect classification.
            max_symbols: Maximum allowed context symbols.
            min_reduction_ratio: Minimum allowed reduction ratio.
        """
        self.symbol_graph = symbol_graph
        self.analyzer: BlastRadiusAnalyzer = BlastRadiusAnalyzer(symbol_graph)
        self.resolver: SymbolResolver = SymbolResolver(symbol_graph)
        
        self.primary_threshold = primary_threshold
        self.direct_threshold = direct_threshold
        self.indirect_threshold = indirect_threshold
        self.max_symbols = max_symbols
        self.min_reduction_ratio = min_reduction_ratio

    def optimize(self, target: str, context_file: Optional[str] = None) -> ContextDecision:
        """
        Generates ContextDecision output prioritizing dependent symbols.

        Args:
            target: Symbol name to optimize.
            context_file: Optional path constraint.

        Returns:
            A ContextDecision instance.
        """
        logger.info(f"Running context optimization for target: '{target}'")
        resolution = self.resolver.resolve(target, context_file)
        
        if resolution.resolution_type == "not_found":
            logger.warning(f"Optimization target '{target}' resolved as not_found.")
            return self._unresolved_decision(target, resolution)
            
        if resolution.resolution_type == "ambiguous":
            logger.warning(f"Optimization target '{target}' resolved as ambiguous.")
            return self._ambiguous_decision(target, resolution)
            
        resolved_target = resolution.primary
        if not resolved_target or resolved_target not in self.analyzer.symbols:
            logger.warning(f"Resolved target '{resolved_target}' not found in analyzer map.")
            return self._unresolved_decision(target, resolution)
            
        impacts, ignored_external, safety_warnings = self.analyzer.analyze(resolved_target)
        if not impacts:
            logger.warning("Empty impact results returned for target.")
            return self._empty_decision(resolved_target)
            
        primary: List[str] = []
        direct: List[str] = []
        indirect: List[str] = []
        ignored: List[str] = []
        impact_scores: Dict[str, float] = {}
        
        for imp in impacts:
            impact_scores[imp.symbol] = imp.score
            if imp.score >= self.primary_threshold:
                primary.append(imp.symbol)
            elif imp.score >= self.direct_threshold:
                direct.append(imp.symbol)
            elif imp.score >= self.indirect_threshold:
                indirect.append(imp.symbol)
            else:
                ignored.append(imp.symbol)
                
        # Enforce singular primary target symbol
        if len(primary) > 1:
            logger.debug(f"Multiple primary symbols detected: {primary}. Collapsing to single target.")
            sorted_primary = sorted(primary, key=lambda x: -impact_scores[x])
            primary = [sorted_primary[0]]
            direct = sorted_primary[1:] + direct
            
        ignored.extend(ignored_external)
        
        # Enforce maximum context size constraints
        total_selected = len(primary) + len(direct) + len(indirect)
        if total_selected > self.max_symbols:
            logger.info(f"Target selections ({total_selected}) exceed max limit ({self.max_symbols}). Trimming...")
            indirect = self._limit_category(indirect, max(0, self.max_symbols - len(primary) - len(direct)))
            if len(primary) + len(direct) > self.max_symbols:
                direct = self._limit_category(direct, max(0, self.max_symbols - len(primary)))
                
        safety_rules = self._generate_safety_rules(resolved_target, impacts)
        if resolution.resolution_type in ("unique_short", "graph_scored"):
            safety_rules.insert(0, f"'{target}' -> '{resolved_target}' olarak çözümlendi")
        safety_rules.extend(safety_warnings)
        
        # Enforce reduction ratio guardrails
        total_analyzed = len(impacts)
        selected_count = len(primary) + len(direct) + len(indirect)
        reduction_ratio = self._calculate_reduction_ratio(total_analyzed, selected_count)
        
        if reduction_ratio < self.min_reduction_ratio:
            msg = (
                f"Context reduction ratio ({reduction_ratio:.2f}) is below minimum threshold "
                f"({self.min_reduction_ratio}). This indicates potential context explosion. "
                f"Analyzed: {total_analyzed}, Selected: {selected_count}"
            )
            logger.error(msg)
            raise ContextReductionError(msg)
            
        stats = {
            "total_symbols": len(self.analyzer.symbols),
            "analyzed_symbols": len(impacts),
            "primary_count": len(primary),
            "direct_count": len(direct),
            "indirect_count": len(indirect),
            "ignored_count": len(ignored),
            "context_reduction": f"{reduction_ratio * 100:.1f}%",
            "resolution": {
                "original_target": target,
                "resolved_target": resolved_target,
                "resolution_type": resolution.resolution_type
            }
        }
        
        return ContextDecision(
            target=target,
            primary=primary,
            direct=direct,
            indirect=indirect,
            ignored=ignored,
            safety=safety_rules,
            impact_scores=impact_scores,
            stats=stats
        )

    def _limit_category(self, symbols: List[str], limit: int) -> List[str]:
        """Limits the size of a symbol list in a deterministic alphabetical sorting."""
        if len(symbols) <= limit:
            return sorted(symbols)
        return sorted(symbols)[:limit]
        
    def _generate_safety_rules(self, target: str, impacts: List[SymbolImpact]) -> List[str]:
        """Generates contextual verification rules to guide coding agents."""
        rules = []
        target_sym = self.analyzer.symbols.get(target, {})
        sym_type = target_sym.get("type", "unknown")
        
        rules.append(f"'{target}' sembolünün imzası korunmalı")
        if sym_type == "function":
            rules.append("Fonksiyon dönüş tipi değişirse çağıranlar etkilenir")
        elif sym_type == "method":
            rules.append("self/cls parametre imzası korunmalı")
        elif sym_type == "class":
            rules.append("Sınıf constructor'ı değişirse instantiation noktaları etkilenir")
            
        high_impact = [i for i in impacts if i.score > 0.5 and i.symbol != target]
        if high_impact:
            rules.append(f"{len(high_impact)} yüksek etkili sembol var - dikkatli refactor")
            
        cycles = self._detect_cycles(target, impacts)
        if cycles:
            rules.append("Çevrimsel bağımlılık tespit edildi: kontrollü değişim yap")
            
        return rules
        
    def _detect_cycles(self, target: str, impacts: List[SymbolImpact]) -> List[List[str]]:
        """Identifies circular call dependency sequences in trace paths."""
        cycles = []
        for imp in impacts:
            for path in imp.call_paths:
                if len(path) > 2 and path[0] == path[-1]:
                    cycles.append(path)
        return cycles
        
    def _calculate_reduction_ratio(self, total: int, selected: int) -> float:
        """Computes the compression ratio."""
        if total == 0:
            return 1.0
        return (total - selected) / total
        
    def _empty_decision(self, target: str) -> ContextDecision:
        """Returns standard decision representation for empty targets."""
        return ContextDecision(
            target=target,
            primary=[],
            direct=[],
            indirect=[],
            ignored=[],
            safety=[f"Hedef sembol '{target}' graph'ta bulunamadı"],
            impact_scores={},
            stats={"error": "Target not found"}
        )
        
    def _unresolved_decision(self, target: str, resolution: SymbolResolutionResult) -> ContextDecision:
        """Returns empty decisions for unresolved queries."""
        return ContextDecision(
            target=target,
            primary=[],
            direct=[],
            indirect=[],
            ignored=[],
            safety=resolution.warnings,
            impact_scores={},
            stats={
                "error": "Symbol not found",
                "resolution_type": resolution.resolution_type,
                "candidates": resolution.candidates
            }
        )
        
    def _ambiguous_decision(self, target: str, resolution: SymbolResolutionResult) -> ContextDecision:
        """Returns empty decisions for ambiguous queries."""
        return ContextDecision(
            target=target,
            primary=[],
            direct=[],
            indirect=[],
            ignored=sorted(resolution.candidates),
            safety=resolution.warnings,
            impact_scores=resolution.scores,
            stats={
                "error": "Ambiguous symbol resolution",
                "resolution_type": resolution.resolution_type,
                "candidates_count": len(resolution.candidates),
                "candidates": sorted(resolution.candidates)
            }
        )
        
    def compare_targets(self, targets: List[str]) -> Dict[str, ContextDecision]:
        """Compares multiple targets side-by-side."""
        decisions = {}
        for target in sorted(targets):
            decisions[target] = self.optimize(target)
        return decisions
        
    def export_decision(self, decision: ContextDecision, output_path: str, format: str = "json") -> None:
        """Exports decision structure to standard formats."""
        path = Path(output_path)
        if format == "json":
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(decision.to_dict(), f, indent=2, ensure_ascii=False)
        else:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(self._format_decision_text(decision))
                
    def _format_decision_text(self, decision: ContextDecision) -> str:
        """Formats ContextDecision properties to a clean string representation."""
        lines = [
            "=" * 60,
            "BBC CONTEXT OPTIMIZER - KARAR RAPORU",
            "=" * 60,
            "",
            f"Hedef Sembol: {decision.target}",
            "",
            "[PRIMARY - %40 Önem]",
        ]
        
        for sym in sorted(decision.primary):
            score = decision.impact_scores.get(sym, 0.0)
            lines.append(f"  • {sym} (score: {score:.2f})")
            
        lines.extend(["", "[DIRECT - %30 Önem]"])
        for sym in sorted(decision.direct):
            score = decision.impact_scores.get(sym, 0.0)
            lines.append(f"  • {sym} (score: {score:.2f})")
            
        lines.extend(["", "[INDIRECT - %20 Önem]"])
        for sym in sorted(decision.indirect):
            score = decision.impact_scores.get(sym, 0.0)
            lines.append(f"  • {sym} (score: {score:.2f})")
            
        lines.extend(["", "[IGNORED - External/Unknown]"])
        for sym in sorted(decision.ignored):
            lines.append(f"  • {sym}")
            
        lines.extend(["", "[SAFETY - Güvenlik Kuralları]"])
        for rule in decision.safety:
            lines.append(f"  ⚠ {rule}")
            
        lines.extend(["", "[İSTATİSTİKLER]"])
        for key, value in decision.stats.items():
            lines.append(f"  {key}: {value}")
            
        lines.extend(["", "=" * 60])
        return "\n".join(lines)


def main() -> None:
    """Command-line execution helper."""
    import argparse
    parser = argparse.ArgumentParser(description='BBC Context Optimizer - CLI')
    parser.add_argument('graph_json', help='SymbolGraph JSON file')
    parser.add_argument('target', help='Target symbol to optimize')
    parser.add_argument('--out', '-o', help='Output file path', default=None)
    parser.add_argument('--format', '-f', choices=['json', 'txt'], default='json')
    parser.add_argument('--max-symbols', '-m', type=int, default=50)
    args = parser.parse_args()
    
    with open(args.graph_json, 'r', encoding='utf-8') as f:
        graph_data = json.load(f)
        
    optimizer = ContextOptimizer(symbol_graph=graph_data, max_symbols=args.max_symbols)
    decision = optimizer.optimize(args.target)
    
    if args.out:
        optimizer.export_decision(decision, args.out, args.format)
        print(f"Decision saved: {args.out}")
    else:
        if args.format == 'json':
            print(json.dumps(decision.to_dict(), indent=2, ensure_ascii=False))
        else:
            print(optimizer._format_decision_text(decision))


if __name__ == "__main__":
    main()
