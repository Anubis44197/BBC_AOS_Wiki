"""Layered blast-radius analysis for production shadow planning."""

from __future__ import annotations

import ast
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


SKIP_DIRS = {
    ".bbc",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "BBC_KNOWLEDGE",
}

INFRA_NAMES = {
    "requirements.txt",
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "fastmcp.json",
    "fly.toml",
    "README.md",
}

TASK_TERMS = {
    "provider": {"provider", "client", "base", "mcp", "search"},
    "cache": {"cache", "redis", "ttl", "search", "semantic"},
    "telemetry": {"telemetry", "observability", "metric", "trace", "tracing", "token"},
    "legal": {"legal", "court", "yargitay", "danistay", "aym", "kvkk", "kik", "bddk", "search"},
    "security": {"security", "secret", "subprocess", "timeout", "validation", "url"},
    "test": {"test", "pytest", "kvkk", "bddk", "gib", "sayistay", "sigorta"},
    "semantic": {"semantic", "bm25", "embedding", "reranker", "vector", "search"},
}


@dataclass(frozen=True)
class ImpactFile:
    path: str
    reason: str
    score: float


class LayeredImpactAnalyzer:
    """Discovers affected files with direct, reverse, symbolic, semantic, and infra layers."""

    def __init__(self, full_context: dict[str, Any], workspace_root: str | Path | None = None) -> None:
        self.full_context = full_context
        root = workspace_root or full_context.get("project_skeleton", {}).get("root", ".")
        self.workspace_root = Path(str(root)).resolve()
        self.context_files = self._context_files()
        self.workspace_files = self._workspace_files()
        self.all_files = self._dedupe([*self.context_files, *self.workspace_files])
        self.imports = self._build_import_graph()
        self.reverse_imports = self._reverse_graph(self.imports)

    def analyze(
        self,
        description: str,
        target_file: str | None = None,
        target_symbols: Iterable[str] | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        query_terms = self._query_terms(description, target_symbols or [])
        normalized_target = self._normalize(target_file or "")
        primary = self._primary_files(query_terms, normalized_target)
        direct = self._direct_files(primary)
        indirect = self._indirect_files(primary, direct, query_terms)
        transitive = self._transitive_files(primary, direct, indirect, query_terms)

        matrix = {
            "PRIMARY": [item.path for item in primary],
            "DIRECT": [item.path for item in direct],
            "INDIRECT": [item.path for item in indirect],
            "TRANSITIVE": [item.path for item in transitive],
        }
        ordered = self._dedupe([path for group in matrix.values() for path in group])[:limit]
        score = self._score(ordered, matrix)
        return {
            "affected_files": ordered,
            "affected_file_count": len(ordered),
            "change_impact_matrix": matrix,
            "blast_radius_score": score,
            "blast_radius_class": self._classification(score, len(ordered)),
            "layers": {
                "direct_imports": matrix["DIRECT"],
                "reverse_imports": [p for p in matrix["INDIRECT"] if p in self.reverse_imports],
                "call_graph": matrix["INDIRECT"],
                "symbol_reference_graph": matrix["INDIRECT"],
                "semantic_dependency_graph": matrix["TRANSITIVE"],
                "shared_infrastructure": [p for p in matrix["TRANSITIVE"] if self._is_infra(p)],
            },
        }

    def _context_files(self) -> list[str]:
        files: list[str] = []
        for recipe in self.full_context.get("code_structure", []):
            if isinstance(recipe, dict):
                path = self._normalize(str(recipe.get("path") or recipe.get("file") or ""))
                if path:
                    files.append(path)
        return self._dedupe(files)

    def _workspace_files(self) -> list[str]:
        if not self.workspace_root.exists():
            return []
        files: list[str] = []
        for path in self.workspace_root.rglob("*"):
            if not path.is_file():
                continue
            rel = self._normalize(path.relative_to(self.workspace_root).as_posix())
            if any(part in SKIP_DIRS for part in rel.split("/")):
                continue
            if path.suffix.lower() in {".py", ".md", ".toml", ".txt", ".json", ".yml", ".yaml", ".ini", ".cfg"} or path.name in INFRA_NAMES:
                files.append(rel)
        return self._dedupe(files)

    def _build_import_graph(self) -> dict[str, list[str]]:
        graph: dict[str, list[str]] = {path: [] for path in self.all_files}
        module_to_file = {
            self._module_name(path): path
            for path in self.all_files
            if path.endswith(".py")
        }
        for path in self.all_files:
            if not path.endswith(".py"):
                continue
            abs_path = self.workspace_root / path
            if not abs_path.exists():
                continue
            try:
                tree = ast.parse(abs_path.read_text(encoding="utf-8", errors="ignore"))
            except SyntaxError:
                continue
            deps: set[str] = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        match = self._resolve_module(alias.name, module_to_file)
                        if match:
                            deps.add(match)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    match = self._resolve_module(node.module, module_to_file)
                    if match:
                        deps.add(match)
            graph[path] = sorted(deps)
        return graph

    def _reverse_graph(self, graph: dict[str, list[str]]) -> dict[str, list[str]]:
        reverse: dict[str, list[str]] = {path: [] for path in self.all_files}
        for src, deps in graph.items():
            for dep in deps:
                reverse.setdefault(dep, []).append(src)
        return {path: sorted(set(users)) for path, users in reverse.items()}

    def _primary_files(self, query_terms: set[str], target_file: str) -> list[ImpactFile]:
        scored: list[ImpactFile] = []
        for path in self.all_files:
            score = self._semantic_score(path, query_terms)
            if path == target_file or (target_file and path.endswith(target_file)):
                score += 3.0
            if score > 0:
                scored.append(ImpactFile(path, "semantic target", score))
        if not scored and self.context_files:
            scored.append(ImpactFile(self.context_files[0], "fallback context target", 1.0))
        return self._top(scored, 12)

    def _direct_files(self, primary: list[ImpactFile]) -> list[ImpactFile]:
        rows: list[ImpactFile] = []
        for item in primary:
            for dep in self.imports.get(item.path, []):
                rows.append(ImpactFile(dep, f"direct import of {item.path}", item.score * 0.8))
            for user in self.reverse_imports.get(item.path, []):
                rows.append(ImpactFile(user, f"reverse import of {item.path}", item.score * 0.7))
        return self._top(rows, 16, exclude={item.path for item in primary})

    def _indirect_files(self, primary: list[ImpactFile], direct: list[ImpactFile], query_terms: set[str]) -> list[ImpactFile]:
        exclude = {item.path for item in [*primary, *direct]}
        frontier = [item.path for item in [*primary, *direct]]
        rows: list[ImpactFile] = []
        for path in frontier:
            for candidate in [*self.imports.get(path, []), *self.reverse_imports.get(path, [])]:
                if candidate not in exclude:
                    rows.append(ImpactFile(candidate, f"second-order dependency of {path}", 0.55 + self._semantic_score(candidate, query_terms)))
        for path in self.all_files:
            if path not in exclude and self._shares_symbol_terms(path, query_terms):
                rows.append(ImpactFile(path, "symbol reference or domain match", 0.45 + self._semantic_score(path, query_terms)))
        return self._top(rows, 18, exclude=exclude)

    def _transitive_files(
        self,
        primary: list[ImpactFile],
        direct: list[ImpactFile],
        indirect: list[ImpactFile],
        query_terms: set[str],
    ) -> list[ImpactFile]:
        exclude = {item.path for item in [*primary, *direct, *indirect]}
        rows: list[ImpactFile] = []
        broad = self._is_broad_query(query_terms)
        for path in self.all_files:
            if path in exclude:
                continue
            if self._is_infra(path):
                rows.append(ImpactFile(path, "shared infrastructure dependency", 0.5))
            elif broad and (path.endswith(".md") or path.startswith("tests/") or "test" in path.lower()):
                rows.append(ImpactFile(path, "transitive docs/tests impact", 0.35))
            elif broad and path.endswith(".py"):
                rows.append(ImpactFile(path, "transitive module impact", 0.3 + self._semantic_score(path, query_terms)))
        return self._top(rows, 24, exclude=exclude)

    def _semantic_score(self, path: str, query_terms: set[str]) -> float:
        haystack = set(re.findall(r"[a-z0-9]+", path.lower()))
        score = len(haystack & query_terms)
        if not score and path.endswith(".py"):
            abs_path = self.workspace_root / path
            if abs_path.exists():
                try:
                    text = abs_path.read_text(encoding="utf-8", errors="ignore").lower()
                except OSError:
                    text = ""
                score += sum(1 for term in query_terms if term and term in text[:20000])
        return float(score)

    def _query_terms(self, description: str, target_symbols: Iterable[str]) -> set[str]:
        terms = set(re.findall(r"[a-z0-9]+", description.lower()))
        for symbol in target_symbols:
            terms.update(re.findall(r"[a-z0-9]+", str(symbol).lower()))
        expanded = set(terms)
        for key, aliases in TASK_TERMS.items():
            if key in terms or terms & aliases:
                expanded.update(aliases)
        return expanded

    def _shares_symbol_terms(self, path: str, query_terms: set[str]) -> bool:
        path_terms = set(re.findall(r"[a-z0-9]+", path.lower()))
        return bool(path_terms & query_terms)

    def _is_broad_query(self, query_terms: set[str]) -> bool:
        broad_terms = {"all", "unified", "architecture", "refactor", "provider", "cache", "telemetry", "observability", "security", "massive", "legal"}
        return bool(query_terms & broad_terms)

    def _is_infra(self, path: str) -> bool:
        name = Path(path).name
        return (
            name in INFRA_NAMES
            or path.startswith("tests/")
            or path.startswith("docs/")
            or "schema" in path.lower()
            or "config" in path.lower()
            or path.endswith("_report.md")
        )

    def _score(self, files: list[str], matrix: dict[str, list[str]]) -> int:
        weighted = (
            len(matrix["PRIMARY"]) * 4
            + len(matrix["DIRECT"]) * 3
            + len(matrix["INDIRECT"]) * 2
            + len(matrix["TRANSITIVE"])
        )
        breadth = min(100, int((len(files) / 50) * 85))
        depth = min(35, int(math.sqrt(max(weighted, 1)) * 7))
        return min(100, breadth + depth)

    def _classification(self, score: int, file_count: int) -> str:
        if file_count > 50 or score >= 90:
            return "MASSIVE"
        if file_count > 20 or score >= 70:
            return "LARGE"
        if file_count > 8 or score >= 40:
            return "MEDIUM"
        return "SMALL"

    def _top(self, rows: list[ImpactFile], limit: int, exclude: set[str] | None = None) -> list[ImpactFile]:
        exclude = exclude or set()
        best: dict[str, ImpactFile] = {}
        for row in rows:
            if row.path in exclude:
                continue
            current = best.get(row.path)
            if current is None or row.score > current.score:
                best[row.path] = row
        return sorted(best.values(), key=lambda item: (-item.score, item.path))[:limit]

    def _module_name(self, path: str) -> str:
        if path.endswith("/__init__.py"):
            return path[:-12].replace("/", ".")
        if path.endswith(".py"):
            return path[:-3].replace("/", ".")
        return path.replace("/", ".")

    def _resolve_module(self, module: str, module_to_file: dict[str, str]) -> str:
        if module in module_to_file:
            return module_to_file[module]
        parts = module.split(".")
        for idx in range(len(parts), 0, -1):
            candidate = ".".join(parts[:idx])
            if candidate in module_to_file:
                return module_to_file[candidate]
        return ""

    def _normalize(self, path: str) -> str:
        normalized = path.replace("\\", "/")
        if normalized.startswith("./"):
            normalized = normalized[2:]
        return normalized

    def _dedupe(self, values: Iterable[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for value in values:
            normalized = self._normalize(value)
            if normalized and normalized not in seen:
                seen.add(normalized)
                result.append(normalized)
        return result
