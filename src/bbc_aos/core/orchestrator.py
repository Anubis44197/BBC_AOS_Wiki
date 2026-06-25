"""
BBC HMPU Orchestrator - Phase 5B
Implements the main orchestrator engine, recipe structures, and segment execution pipelines.
Splits orchestration concerns into internal services: RecipeValidator, ContentSegmenter, and DynamicAuraCalibrator.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

# Import modular components
from bbc_aos.memory.working.state_manager import StateManager
from bbc_aos.core.constraints_engine import HMPU_Governor

# Set up logging namespace
logger = logging.getLogger("bbc_aos.core.orchestrator")


@dataclass
class RecipeConstraint:
    """
    BBC CONSTRAINT CONSTITUTION (v1.0)
    Only visible and enforced by BBC Core.
    """
    max_tokens: int              # 1. LLM upper token limit
    output_format: str           # 2. JSON schema / markdown contract
    allowed_fields: List[str]    # 3. Whitelist fields
    forbidden_content: List[str] # 4. Speculative / commentary words forbidden
    determinism_level: str       # 5. hard / soft
    context_scope: str           # 6. only_structure / headers_only etc.
    compression_ratio_target: float # 7. Target compression ratio
    execution_budget: Dict[str, Any] # 8. max_calls / nesting limits
    visibility_policy: str       # 9. internal_only / audit_log


# ==========================================
# Internal Orchestration Services
# ==========================================

class RecipeValidator:
    """Internal service to validate recipe outputs against sealed constitutions (CVP v1.0)."""

    @staticmethod
    def trigger_cvp(recipe_name: str, determinism_level: str, constraint_name: str, phase: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Triggers the Constraint Violation Protocol."""
        severity = "hard" if determinism_level == "hard" else "soft"
        cvp_error = {
            "status": "error",
            "error_type": "CONSTRAINT_VIOLATION",
            "constraint_name": constraint_name,
            "recipe_id": recipe_name,
            "phase": phase,
            "severity": severity,
            "decision": "abort" if severity == "hard" else "discard",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "details": details or {}
        }
        logger.warning(f"CVP Triggered: {cvp_error}")
        return cvp_error

    @staticmethod
    async def validate(recipe_name: str, constraints: RecipeConstraint, result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Validates output against recipe constraints."""
        # 1. Output Format & Allowed Fields Check
        data = result.get("data", {})
        if isinstance(data, dict):
            for field in list(data.keys()):
                if field not in constraints.allowed_fields:
                    return RecipeValidator.trigger_cvp(recipe_name, constraints.determinism_level, "allowed_fields", "post_execution", {"offending_field": field})

        # 2. Forbidden Content Check
        result_str = json.dumps(result).lower()
        for forbidden in constraints.forbidden_content:
            if forbidden.lower() in result_str:
                return RecipeValidator.trigger_cvp(recipe_name, constraints.determinism_level, "forbidden_content", "post_execution", {"forbidden_term": forbidden})

        # 3. Max Tokens Check (Approx for baseline)
        recipe_size = len(result_str)
        if recipe_size > constraints.max_tokens:
            return RecipeValidator.trigger_cvp(recipe_name, constraints.determinism_level, "max_tokens", "post_execution", {"actual": recipe_size, "limit": constraints.max_tokens})

        return None


class ContentSegmenter:
    """Internal service to split content into code or documentation segments."""

    @staticmethod
    def segment(content: str) -> List[tuple]:
        """Segments mixed code and documentation files."""
        import re
        segments = []
        
        # 1. File-based splitting (Phase 10 Native Adapter standard)
        file_blocks = list(re.finditer(r'--- FILE: (.*?) ---\s*[\r\n]+([\s\S]*?)(?=[\r\n]+--- FILE:|$)', content))
        
        if file_blocks:
            for match in file_blocks:
                filename = match.group(1).lower()
                body = match.group(2).strip()
                start = match.start()
                
                if filename.endswith(('.py', '.js', '.ts', '.sql')):
                    segments.append(("code", body, start))
                else:
                    segments.append(("documentation", body, start))
            return segments

        # 2. Find script blocks (legacy logic for HTML/Mixed content)
        matches = list(re.finditer(r'<script.*?>([\s\S]*?)</script>', content, re.IGNORECASE))
        
        last_idx = 0
        for match in matches:
            start, end = match.span()
            pre_text = content[last_idx:start].strip()
            if len(pre_text) > 20:
                segments.append(("documentation", pre_text, last_idx))
            
            script_body = match.group(1).strip()
            if len(script_body) > 10:
                segments.append(("code", script_body, start))
            last_idx = end
            
        remaining = content[last_idx:].strip()
        if len(remaining) > 20 or not segments:
            segments.append(("documentation", remaining, last_idx))
            
        return segments


class DynamicAuraCalibrator:
    """Internal service to dynamically adjust recipe constraints based on Governor chaos levels."""

    @staticmethod
    def calibrate(governor: Optional[HMPU_Governor], content: str, recipe: 'BaseRecipe') -> None:
        """Tunes recipe constraints using Governor complexity calculations."""
        if not governor:
            return

        try:
            # Calculate Chaos (Mathematical complexity)
            chaos = governor._calculate_chaos(content)
            
            # Determine target aura field metrics
            if chaos > 4.5: # High entropy/complexity
                recipe.constraints.compression_ratio_target = 0.65 
                recipe.constraints.determinism_level = "soft"
            elif chaos < 2.5: # Repetitive/Simple content
                recipe.constraints.compression_ratio_target = 0.95
                recipe.constraints.determinism_level = "hard"

            logger.info(f"Aura Adjustment: Chaos={chaos:.2f} -> Compression Target={recipe.constraints.compression_ratio_target}")
        except Exception as e:
            logger.debug(f"Aura adjustment failed: {e}")


# ==========================================
# Core Orchestrator Classes
# ==========================================

class BaseRecipe:
    """Base class for all BBC recipes."""
    
    def __init__(self, name: str, constraints: RecipeConstraint) -> None:
        self.name: str = name
        self.constraints: RecipeConstraint = constraints

    def _trigger_cvp(self, constraint_name: str, phase: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """BBC Constraint Violation Protocol (CVP v1.0) Trigger"""
        return RecipeValidator.trigger_cvp(self.name, self.constraints.determinism_level, constraint_name, phase, details)

    async def validate_output(self, result: Dict[str, Any], raw_content: str) -> Optional[Dict[str, Any]]:
        """Validates output against sealed constitution."""
        return await RecipeValidator.validate(self.name, self.constraints, result)

    def filter_output(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Visibility Policy (v1.0): Filters data for LLM/IDE."""
        if self.constraints.visibility_policy == "internal_only":
            return result.get("data", {})
        return result

    async def execute(self, data: Any) -> Dict[str, Any]:
        raise NotImplementedError("Recipes must implement execute()")


class CodeStructureRecipe(BaseRecipe):
    """
    REFERENCE RECIPE: Code Structure
    Analyzes code files and extracts structural summary.
    """
    
    def __init__(self) -> None:
        super().__init__(
            name="code_structure",
            constraints=RecipeConstraint(
                max_tokens=1000000,
                output_format="json",
                allowed_fields=["classes", "functions", "imports"],
                forbidden_content=["speculative", "commentary", "guess"],
                determinism_level="hard",
                context_scope="only_structure",
                compression_ratio_target=0.8,
                execution_budget={"max_llm_calls": 0, "no_recursive_calls": True},
                visibility_policy="internal_only"
            )
        )

    async def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        content = data.get("content", "")
        lines = content.splitlines()
        structure = {
            "classes": [line.strip() for line in lines if "class " in line],
            "functions": [line.strip() for line in lines if "def " in line],
            "imports": [line.strip() for line in lines if "import " in line or "from " in line]
        }
        
        raw_size = len(content)
        recipe_json = json.dumps(structure, ensure_ascii=False)
        recipe_size = len(recipe_json)
        savings = (1 - (recipe_size / raw_size)) * 100 if raw_size > 0 else 0

        return {
            "recipe_name": self.name,
            "data": structure,
            "metrics": {
                "raw_bytes": raw_size,
                "recipe_bytes": recipe_size,
                "savings_ratio": f"{savings:.2f}%"
            }
        }


class LogTelemetryRecipe(BaseRecipe):
    """
    BBC RECIPE: Log / Telemetry
    Summarizes log data semantically and statistically.
    """
    
    def __init__(self) -> None:
        super().__init__(
            name="log_telemetry",
            constraints=RecipeConstraint(
                max_tokens=1000000,
                output_format="json",
                allowed_fields=["counts", "patterns", "anomalies", "severity_summary"],
                forbidden_content=["comment", "cause-effect", "suggestion", "probably", "guess"],
                determinism_level="hard",
                context_scope="log_summary",
                compression_ratio_target=0.9,
                execution_budget={"max_llm_calls": 0, "no_recursive_calls": True},
                visibility_policy="internal_only"
            )
        )

    async def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        content = data.get("content", "")
        lines = content.splitlines()
        
        counts = {"INFO": 0, "ERROR": 0, "WARNING": 0, "DEBUG": 0}
        anomalies = []
        
        for line in lines:
            l_up = line.upper()
            if "INFO" in l_up: counts["INFO"] += 1
            elif "ERROR" in l_up: counts["ERROR"] += 1
            elif "WARN" in l_up: counts["WARNING"] += 1
            elif "DEBUG" in l_up: counts["DEBUG"] += 1
            
            if any(x in l_up for x in ["EXCEPTION", "CRITICAL", "FATAL", "TIMEOUT"]):
                anomalies.append(line[:120].strip())

        structure = {
            "counts": counts,
            "patterns": [],
            "anomalies": anomalies[:15],
            "severity_summary": f"Total {len(lines)} lines. Errors: {counts['ERROR']}, Warnings: {counts['WARNING']}"
        }

        raw_size = len(content)
        recipe_json = json.dumps(structure, ensure_ascii=False)
        recipe_size = len(recipe_json)
        savings = (1 - (recipe_size / raw_size)) * 100 if raw_size > 0 else 0

        return {
            "recipe_name": self.name,
            "data": structure,
            "metrics": {
                "raw_bytes": raw_size,
                "recipe_bytes": recipe_size,
                "savings_ratio": f"{savings:.2f}%"
            }
        }


class ConfigJsonRecipe(BaseRecipe):
    """
    BBC RECIPE: Configuration / JSON
    Summarizes complex config files hierarchically and structurally.
    """
    
    def __init__(self) -> None:
        super().__init__(
            name="config_json",
            constraints=RecipeConstraint(
                max_tokens=1000000,
                output_format="json",
                allowed_fields=["sections", "keys", "types", "defaults", "overrides"],
                forbidden_content=["suggestion", "comment", "reason", "how", "probably", "guess"],
                determinism_level="hard",
                context_scope="structural_config",
                compression_ratio_target=0.90,
                execution_budget={"max_llm_calls": 0, "no_recursive_calls": True},
                visibility_policy="internal_only"
            )
        )

    async def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        content = data.get("content", "").strip()
        
        try:
            parsed = json.loads(content)
        except Exception:
            return self._trigger_cvp("output_format", "pre_execution", {"error": "Invalid JSON input"})

        def extract_structure(obj, depth=0):
            if depth > 3: return "..."
            if isinstance(obj, dict):
                keys = list(obj.keys())
                limited_keys = keys[:5]
                res = {k: {"type": type(obj[k]).__name__, "val": extract_structure(obj[k], depth + 1)} for k in limited_keys}
                if len(keys) > 5: res["_etc"] = f"{len(keys) - 5} keys"
                return res
            elif isinstance(obj, list):
                if not obj: return []
                types_in_list = list(set([type(v).__name__ for v in obj]))
                return {"list_of": types_in_list, "len": len(obj), "sample": extract_structure(obj[0], depth + 1) if obj else None}
            else:
                return str(type(obj).__name__)

        parsed_keys = list(parsed.keys()) if isinstance(parsed, dict) else []
        structure = {
            "sections": parsed_keys[:50] + (["..."] if len(parsed_keys) > 50 else []),
            "keys": len(parsed) if isinstance(parsed, (dict, list)) else 0,
            "types": extract_structure(parsed),
            "defaults": {},
            "overrides": {}
        }

        raw_size = len(content)
        recipe_json = json.dumps(structure, ensure_ascii=False)
        recipe_size = len(recipe_json)
        savings = (1 - (recipe_size / raw_size)) * 100 if raw_size > 0 else 0

        return {
            "recipe_name": self.name,
            "data": structure,
            "metrics": {
                "raw_bytes": raw_size,
                "recipe_bytes": recipe_size,
                "savings_ratio": f"{savings:.2f}%"
            }
        }


class DocumentationRecipe(BaseRecipe):
    """
    BBC RECIPE: Documentation
    Hierarchically summarizes large text and document files.
    """
    
    def __init__(self) -> None:
        super().__init__(
            name="documentation",
            constraints=RecipeConstraint(
                max_tokens=1000000,
                output_format="json",
                allowed_fields=["headers", "summary", "keywords", "links"],
                forbidden_content=["comment", "probably", "opinion"],
                determinism_level="hard",
                context_scope="doc_structure",
                compression_ratio_target=0.95,
                execution_budget={"max_llm_calls": 0, "no_recursive_calls": True},
                visibility_policy="internal_only"
            )
        )

    async def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        content = data.get("content", "")
        lines = content.splitlines()
        
        headers = []
        keywords = []
        
        for line in lines:
            trimmed = line.strip()
            if trimmed.startswith("#"):
                headers.append(trimmed)
            elif trimmed.lower().startswith("<h") and ">" in trimmed:
                headers.append(trimmed)
            
            if len(trimmed) > 20 and any(c.isupper() for c in trimmed):
                words = trimmed.split()
                for w in words:
                    if len(w) > 5 and w[0].isupper() and w.isalnum():
                        if w not in keywords: keywords.append(w)

        structure = {
            "headers": headers[:20],
            "summary": f"Document length: {len(lines)} lines.",
            "keywords": keywords[:15],
            "links": [line.strip() for line in lines if "http" in line and ("href" in line or "src" in line)][:10]
        }

        raw_size = len(content)
        recipe_json = json.dumps(structure, ensure_ascii=False)
        recipe_size = len(recipe_json)
        savings = (1 - (recipe_size / raw_size)) * 100 if raw_size > 0 else 0

        return {
            "recipe_name": self.name,
            "data": structure,
            "metrics": {
                "raw_bytes": raw_size,
                "recipe_bytes": recipe_size,
                "savings_ratio": f"{savings:.2f}%"
            }
        }


class MultiRecipePipeline:
    """
    BBC PLATFORM CORE: Multi-Recipe Pipeline (v1.1)
    Industrial-grade hybrid context management.
    """
    
    def __init__(self, engine: 'HMPUEngine') -> None:
        self.engine: HMPUEngine = engine

    async def process(self, content: str) -> Dict[str, Any]:
        """Splits input into segments, manages each independently."""
        segments = self._segment_content(content)
        if not segments:
            return {"status": "error", "message": "No valid segments found"}

        results = []
        total_raw_bytes = len(content)
        total_recipe_bytes = 0
        execution_errors = []

        for seg_type, seg_content, start_idx in segments:
            try:
                recipe = self.engine.recipes.get(seg_type)
                if recipe:
                    res = await recipe.execute({"content": seg_content})
                    cvp_error = await recipe.validate_output(res, seg_content)
                    
                    if cvp_error:
                        results.append({
                            "segment_type": seg_type,
                            "status": "degraded",
                            "reason": "CONSTRAINT_VIOLATION",
                            "details": cvp_error.get("constraint_name")
                        })
                        execution_errors.append(f"Segment at {start_idx} violated {cvp_error.get('constraint_name')}")
                    else:
                        data = recipe.filter_output(res)
                        results.append({
                            "segment_type": seg_type,
                            "status": "ok",
                            "recipe_used": recipe.name,
                            "content": data
                        })
                        total_recipe_bytes += res.get("metrics", {}).get("recipe_bytes", 0)
                else:
                    results.append({
                        "segment_type": seg_type,
                        "status": "raw",
                        "content": seg_content[:150] + "..."
                    })
                    total_recipe_bytes += 150
            except Exception as e:
                execution_errors.append(f"Error in segment at {start_idx}: {str(e)}")
                results.append({"segment_type": seg_type, "status": "failed", "error": str(e)})

        savings = (1 - (total_recipe_bytes / total_raw_bytes)) * 100 if total_raw_bytes > 0 else 0

        return {
            "recipe_name": "multi_recipe_pipeline",
            "data": {
                "hybrid_context": results,
                "platform_status": "stable" if not execution_errors else "degraded",
                "execution_log": execution_errors
            },
            "metrics": {
                "raw_bytes": total_raw_bytes,
                "recipe_bytes": total_recipe_bytes,
                "savings_ratio": f"{savings:.2f}%",
                "segments_total": len(segments),
                "segments_ok": len([r for r in results if r["status"] == "ok"])
            }
        }

    def _segment_content(self, content: str) -> List[tuple]:
        """Delegates segment detection to ContentSegmenter service."""
        return ContentSegmenter.segment(content)


class HMPUEngine:
    """BBC HMPU main engine (Aura-Enhanced v5.6)"""
    
    def __init__(self, state_manager: StateManager) -> None:
        self.state_manager: StateManager = state_manager
        self.initialized: bool = False
        self.ready: bool = False 
        self.governor: Optional[HMPU_Governor] = None
        
        # Tools (Legacy compatibility placeholders)
        self.analyze_file_tool: Optional[Any] = None
        self.create_recipe_tool: Optional[Any] = None
        self.get_stats_tool: Optional[Any] = None
        
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize engine and register recipes"""
        try:
            self.recipes: Dict[str, BaseRecipe] = {
                "code": CodeStructureRecipe(),
                "log": LogTelemetryRecipe(),
                "config": ConfigJsonRecipe(),
                "documentation": DocumentationRecipe()
            }
            
            # HMPU Governor Integration
            try:
                from bbc_aos.config import BBCConfig
                bbc_dir = Path(BBCConfig.get_bbc_dir())
                bbc_dir.mkdir(parents=True, exist_ok=True)
                weights_path = str(bbc_dir / "hmpu_weights.json")
                self.governor = HMPU_Governor(
                    weights_path=weights_path,
                    state_manager=self.state_manager
                )
                logger.info("BBC HMPU Governor (v5.6+) integrated successfully.")
            except Exception as e:
                logger.warning(f"BBC HMPU Governor could not be loaded: {e}")

            # Platform pipeline setup
            self.pipeline: MultiRecipePipeline = MultiRecipePipeline(self)
            
            logger.info(f"BBC HMPU Platform Engine started. Registered recipes: {len(self.recipes)}")
            self.initialized = True
            self.ready = True
            
        except Exception as e:
            logger.error(f"BBC Engine initialization error: {e}")
            raise
    
    def _adjust_constraints_by_aura(self, content: str, recipe: BaseRecipe) -> None:
        """Delegates dynamic recipe constraint tuning to DynamicAuraCalibrator."""
        DynamicAuraCalibrator.calibrate(self.governor, content, recipe)

    def get_aura_confidence(self) -> float:
        """Calculates confidence using Governor stability."""
        if not self.governor:
            return 0.95

        try:
            import math
            stability = self.governor.get_field_stability()
            if math.isinf(stability) or stability <= 0:
                return 0.0
            
            confidence = 1.0 / (1.0 + math.log10(stability))
            return round(min(max(confidence, 0.0), 1.0), 3)
        except Exception:
            return 0.85

    async def analyze_file(self, file_path: str, analysis_type: str = "auto") -> Dict[str, Any]:
        """Analyze file - passes through Recipe Engine."""
        if not self.initialized:
            raise RuntimeError("Engine not initialized")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            result = await self.create_recipe(content)
            
            if self.state_manager:
                self.state_manager.increment_files_analyzed()
                
            return {"success": True, "result": result, "file_path": file_path}
        except Exception as e:
            logger.error(f"File analysis error: {e}")
            raise
    
    async def create_recipe(self, content: str, max_recipe_size: int = 5000) -> Dict[str, Any]:
        """Selects and executes recipe(s) based on input context."""
        if not self.initialized:
            raise RuntimeError("Engine not initialized")
        
        # 1. Multi-Recipe Pipeline Split Check
        segments = self.pipeline._segment_content(content)
        seg_types = set(s[0] for s in segments) if segments else set()
        is_hybrid = len(segments) > 1 and len(seg_types) > 1
        if is_hybrid:
            logger.info(f"BBC Platform Decision: Hybrid Content Detected. Pipeline activated. Segments: {len(segments)}")
            result = await self.pipeline.process(content)
            return await self._finalize_recipe_execution(result, content, None)

        # 2. Standalone Single Recipe Selection
        c_strip = content.strip()
        c_up = content.upper()
        is_json_structured = (c_strip.startswith("{") and c_strip.endswith("}")) or (c_strip.startswith("[") and c_strip.endswith("]"))
        has_log_keywords = any(x in c_up for x in ["INFO", "ERROR", "WARN", "DEBUG", "TIMESTAMP", "EXCEPTION"])
        is_html_doc = "<HTML" in c_up or "<!DOCTYPE" in c_up or "# " in c_strip[:10]
        
        if is_json_structured and not has_log_keywords:
            target_recipe = "config"
        elif has_log_keywords:
            target_recipe = "log"
        elif is_html_doc:
            target_recipe = "documentation"
        else:
            target_recipe = "code"
        
        recipe = self.recipes.get(target_recipe)
        if not recipe:
            logger.error(f"Recipe not found: {target_recipe}")
            return {"success": False, "error": "No suitable recipe found"}

        try:
            # 3. Dynamic Aura Adjustment
            self._adjust_constraints_by_aura(content, recipe)

            # 4. Standalone Execution
            logger.info(f"BBC Decision: Using Standalone Recipe '{recipe.name}'")
            result = await recipe.execute({"content": content})
            return await self._finalize_recipe_execution(result, content, recipe)
            
        except Exception as e:
            logger.error(f"Recipe execution error ({recipe.name}): {e}")
            raise

    async def _finalize_recipe_execution(self, result: Dict[str, Any], raw_content: str, recipe: Optional[BaseRecipe]) -> Dict[str, Any]:
        """Seals CVP validation, metrics updates, and data filtering."""
        # 1. CVP Validation
        if recipe:
            cvp_result = await recipe.validate_output(result, raw_content)
            if cvp_result:
                return cvp_result

        # 2. Telemetry Metrics Accumulation
        metrics = result.get("metrics", {})
        if self.state_manager and metrics:
            self.state_manager.increment_recipes_created()
            self.state_manager.add_data_processed(metrics.get("raw_bytes", 0))
            saved_bytes = int(metrics.get("raw_bytes", 0)) - int(metrics.get("recipe_bytes", 0))
            self.state_manager.add_token_savings(float(saved_bytes / 4))

        # 3. Visibility Filtering
        response_data = result.get("data", result)
        if recipe:
            response_data = recipe.filter_output(result)
        
        return {
            "success": True, 
            "data": response_data,
            "metrics": metrics
        }
    
    async def get_stats(self) -> Dict[str, Any]:
        """Exposes engine statistics using the registered stats tool callback."""
        if not self.initialized:
            raise RuntimeError("Engine not initialized")
        
        try:
            if self.get_stats_tool:
                result = await self.get_stats_tool(self.state_manager.stats)
            else:
                result = self.state_manager.stats
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"Statistics error: {e}")
            raise