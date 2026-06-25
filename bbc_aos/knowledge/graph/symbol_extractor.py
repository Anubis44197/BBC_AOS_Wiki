"""
BBC Symbol Extractor - Phase 2: AST and Pattern Based Symbol Extraction
Extracts class, method, function, and variable definitions in a polyglot codebase.
"""

import ast
import fnmatch
import json
import logging
import os
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple, Union

# Set up logging namespace
logger = logging.getLogger("bbc_aos.knowledge.graph.symbol_extractor")

# Configuration Limits
MAX_FILES_DEFAULT: int = 2000

# Scan Profile Exclusions
SOURCE_EXTENSIONS: Tuple[str, ...] = (
    ".py", ".md", ".json", ".js", ".jsx", ".ts", ".tsx",
    ".html", ".css", ".sql", ".rs", ".go", ".c", ".cpp",
    ".h", ".hpp", ".java", ".cs", ".php", ".rb", ".swift", ".kt",
)

EXCLUDED_DIRS: Set[str] = {
    ".bbc", ".cache", ".git", ".hg", ".idea", ".mypy_cache",
    ".next", ".nuxt", ".old", ".parcel-cache", ".pytest_cache",
    ".ruff_cache", ".svn", ".tox", ".turbo", ".venv", ".vscode",
    "__pycache__", "build", "coverage", "dist", "env",
    "generated", "node_modules", "out", "target", "tmp", "venv", "vendor",
}

EXCLUDED_FILENAMES: Set[str] = {
    "bun.lockb", "cargo.lock", "composer.lock", "package-lock.json",
    "pnpm-lock.yaml", "poetry.lock", "yarn.lock",
}

EXCLUDED_SUFFIXES: Tuple[str, ...] = (
    ".7z", ".avif", ".bmp", ".db", ".dll", ".dylib", ".exe",
    ".gif", ".gz", ".ico", ".jpeg", ".jpg", ".lock", ".log",
    ".mp3", ".mp4", ".onnx", ".pdf", ".png", ".pyc", ".sqlite",
    ".sqlite3", ".tar", ".tgz", ".ttf", ".wasm", ".webm", ".webp",
    ".whl", ".woff", ".woff2", ".zip",
)

DEFAULT_MAX_FILE_BYTES: int = 2 * 1024 * 1024


def load_bbcignore(project_root: Union[str, Path]) -> List[str]:
    """Loads glob exclusion patterns from .bbcignore file."""
    ignore_path = Path(project_root) / ".bbcignore"
    if not ignore_path.exists():
        return []
    patterns: List[str] = []
    try:
        for line in ignore_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                patterns.append(stripped.replace("\\", "/"))
    except OSError as e:
        logger.warning(f"Could not read .bbcignore at {ignore_path}: {e}")
        return []
    return patterns


def normalize_rel(path: Union[str, Path]) -> str:
    """Normalizes file path separator characters for matching."""
    return str(path).replace("\\", "/").strip("/")


def should_skip_dir_name(name: str) -> bool:
    """Evaluates if a directory should be excluded from codebase walking."""
    lower = name.lower()
    if lower in EXCLUDED_DIRS:
        return True
    if lower.startswith(".pytest-tmp"):
        return True
    if lower.endswith(".egg-info"):
        return True
    return False


def _matches_ignore(rel_path: str, patterns: Iterable[str]) -> bool:
    """Checks if path matches any glob exclusions."""
    rel = normalize_rel(rel_path)
    for raw in patterns:
        raw_pattern = str(raw).replace("\\", "/").strip()
        pattern = normalize_rel(raw_pattern)
        if not pattern:
            continue
        if raw_pattern.endswith("/"):
            prefix = pattern.rstrip("/")
            if rel == prefix or rel.startswith(prefix + "/"):
                return True
        if fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch(Path(rel).name, pattern):
            return True
    return False


def should_skip_file(
    path: Union[str, Path],
    project_root: Union[str, Path],
    ignore_patterns: Iterable[str] = (),
    output_file_abs: Optional[str] = None,
    max_file_bytes: int = DEFAULT_MAX_FILE_BYTES,
) -> bool:
    """Evaluates if a source file should be excluded based on name, size, or suffixes."""
    p = Path(path)
    if output_file_abs and os.path.abspath(str(p)) == os.path.abspath(output_file_abs):
        return True
    if p.name.lower() in EXCLUDED_FILENAMES:
        return True
    if p.suffix.lower() in EXCLUDED_SUFFIXES:
        return True
    try:
        rel = normalize_rel(p.resolve().relative_to(Path(project_root).resolve()))
    except Exception:
        rel = normalize_rel(p.name)
    if _matches_ignore(rel, ignore_patterns):
        return True
    try:
        if p.stat().st_size > max_file_bytes:
            return True
    except OSError:
        return True
    return False


class SymbolType(Enum):
    """Enumerate type categories of code symbols."""
    class CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    VARIABLE = "variable"
    CONSTANT = "constant"
    INTERFACE = "interface"
    ENUM = "enum"
    PROPERTY = "property"


@dataclass
class Symbol:
    """Represents a single parsed code definition."""
    name: str
    type: str
    line: int
    column: int = 0
    class_name: Optional[str] = None
    parent: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    signature: Optional[str] = None
    docstring: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializes the Symbol properties into a dictionary (excludes column to match legacy)."""
        result: Dict[str, Any] = {
            "name": self.name,
            "type": self.type,
            "line": self.line,
        }
        if self.class_name:
            result["class"] = self.class_name
        if self.parent and not self.class_name:
            result["parent"] = self.parent
        if self.decorators:
            result["decorators"] = self.decorators
        if self.signature:
            result["signature"] = self.signature
        return result


@dataclass
class FileSymbols:
    """Contains all definitions parsed from a single source file."""
    file: str
    language: str
    symbols: List[Symbol] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializes symbols representation to a dictionary."""
        return {
            "file": self.file,
            "language": self.language,
            "symbols": [s.to_dict() for s in self.symbols]
        }
    
    def to_json(self, indent: int = 2) -> str:
        """Serializes to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


class PythonSymbolExtractor(ast.NodeVisitor):
    """Traverses Python AST node tree to extract classes, functions, and variables."""
    
    def __init__(self, source_code: str, filename: str = "<unknown>") -> None:
        self.source_code: str = source_code
        self.filename: str = filename
        self.symbols: List[Symbol] = []
        self.current_class: Optional[str] = None
        self.lines: List[str] = source_code.split('\n')
    
    def extract(self) -> List[Symbol]:
        """Parses AST tree and triggers visitors."""
        try:
            tree = ast.parse(self.source_code)
            self.visit(tree)
        except SyntaxError as e:
            logger.warning(f"Syntax error compiling Python AST for {self.filename}: {e}")
        return self.symbols
    
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Handles class def nodes."""
        symbol = Symbol(
            name=node.name,
            type=SymbolType.CLASS.value,
            line=node.lineno,
            column=node.col_offset,
            docstring=ast.get_docstring(node),
            decorators=[self._get_decorator_name(d) for d in node.decorator_list]
        )
        self.symbols.append(symbol)
        
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Handles function def nodes."""
        self._process_function(node)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Handles async function def nodes."""
        self._process_function(node)
    
    def _process_function(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> None:
        """Generates Symbol entries for functions and class methods."""
        is_method = self.current_class is not None
        symbol_type = SymbolType.METHOD.value if is_method else SymbolType.FUNCTION.value
        
        signature = self._get_function_signature(node)
        
        symbol = Symbol(
            name=node.name,
            type=symbol_type,
            line=node.lineno,
            column=node.col_offset,
            class_name=self.current_class if is_method else None,
            parent=self.current_class,
            decorators=[self._get_decorator_name(d) for d in node.decorator_list],
            signature=signature,
            docstring=ast.get_docstring(node)
        )
        self.symbols.append(symbol)
        self._extract_variables(node)
    
    def _get_function_signature(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> str:
        """Constructs string signature parameter layouts."""
        args: List[str] = []
        for arg in node.args.args:
            arg_str = arg.arg
            if arg.annotation:
                arg_str += f": {ast.unparse(arg.annotation)}"
            args.append(arg_str)
        
        if node.args.vararg:
            args.append(f"*{node.args.vararg.arg}")
        if node.args.kwarg:
            args.append(f"**{node.args.kwarg.arg}")
        
        sig = f"({', '.join(args)})"
        if node.returns:
            sig += f" -> {ast.unparse(node.returns)}"
        
        return sig
    
    def _get_decorator_name(self, decorator: ast.expr) -> str:
        """Resolves decorator names."""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return f"{ast.unparse(decorator.value)}.{decorator.attr}"
        elif isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Name):
                return f"{decorator.func.id}()"
            elif isinstance(decorator.func, ast.Attribute):
                return f"{ast.unparse(decorator.func.value)}.{decorator.func.attr}()"
        return "<unknown>"
    
    def _extract_variables(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> None:
        """Extracts internal constants and variables assigned in functions."""
        for child in ast.walk(node):
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name):
                        is_constant = target.id.isupper() and '_' in target.id
                        symbol = Symbol(
                            name=target.id,
                            type=SymbolType.CONSTANT.value if is_constant else SymbolType.VARIABLE.value,
                            line=child.lineno,
                            column=child.col_offset,
                            class_name=self.current_class,
                            parent=node.name
                        )
                        self.symbols.append(symbol)


class RegexSymbolExtractor:
    """Regex pattern based symbol scanner for other (polyglot) source codes."""
    
    PATTERNS: Dict[str, Dict[str, str]] = {
        'javascript': {
            'class': r'class\s+(\w+)',
            'function': r'function\s+(\w+)',
            'arrow_function_const': r'const\s+(\w+)\s*=\s*(?:async\s*)?\(',
            'method': r'(?:async\s+)?(\w+)\s*\([^)]*\)\s*\{',
            'interface': r'interface\s+(\w+)',
            'enum': r'enum\s+(\w+)',
        },
        'typescript': {
            'class': r'class\s+(\w+)',
            'function': r'function\s+(\w+)',
            'interface': r'interface\s+(\w+)',
            'enum': r'enum\s+(\w+)',
            'type': r'type\s+(\w+)',
            'method': r'(?:public|private|protected|readonly)?\s*(?:async\s+)?(\w+)\s*\([^)]*\)\s*:',
        },
        'java': {
            'class': r'(?:public|private|protected)?\s*(?:abstract|final)?\s*class\s+(\w+)',
            'interface': r'interface\s+(\w+)',
            'enum': r'enum\s+(\w+)',
            'method': r'(?:public|private|protected)?\s*(?:static|final|abstract)?\s*(?:\w+)\s+(\w+)\s*\([^)]*\)\s*(?:\{|;|\w+)',
        },
        'csharp': {
            'class': r'(?:public|private|protected|internal)?\s*(?:abstract|sealed|static)?\s*class\s+(\w+)',
            'interface': r'interface\s+(\w+)',
            'enum': r'enum\s+(\w+)',
            'method': r'(?:public|private|protected|internal)?\s*(?:static|virtual|abstract|override)?\s*(?:\w+)\s+(\w+)\s*\([^)]*\)',
        },
        'go': {
            'function': r'func\s+(\w+)',
            'method': r'func\s+\([^)]*\)\s*(\w+)',
            'struct': r'type\s+(\w+)\s+struct',
            'interface': r'type\s+(\w+)\s+interface',
        },
        'rust': {
            'function': r'fn\s+(\w+)',
            'struct': r'struct\s+(\w+)',
            'enum': r'enum\s+(\w+)',
            'trait': r'trait\s+(\w+)',
            'impl': r'impl\s+(?:\w+\s+for\s+)?(\w+)',
        },
        'cpp': {
            'class': r'class\s+(\w+)',
            'struct': r'struct\s+(\w+)',
            'function': r'(?:\w+[\s*&]+)+(\w+)\s*\([^)]*\)\s*(?:\{|const)',
            'namespace': r'namespace\s+(\w+)',
        },
        'php': {
            'class': r'class\s+(\w+)',
            'function': r'function\s+(\w+)',
            'interface': r'interface\s+(\w+)',
            'trait': r'trait\s+(\w+)',
        },
        'ruby': {
            'class': r'class\s+(\w+)',
            'module': r'module\s+(\w+)',
            'method': r'def\s+(\w+)',
        },
    }
    
    def __init__(self, source_code: str, language: str, filename: str = "<unknown>") -> None:
        self.source_code: str = source_code
        self.language: str = language.lower()
        self.filename: str = filename
        self.lines: List[str] = source_code.split('\n')
    
    def extract(self) -> List[Symbol]:
        """Runs match checks against language-specific definition patterns."""
        symbols: List[Symbol] = []
        
        if self.language not in self.PATTERNS:
            return symbols
        
        patterns = self.PATTERNS[self.language]
        current_class = None
        
        for line_num, line in enumerate(self.lines, 1):
            line_stripped = line.strip()
            
            if line_stripped.startswith('//') or line_stripped.startswith('#'):
                continue
            
            # Class/Struct detection
            for pattern_type in ['class', 'struct', 'interface', 'enum', 'trait']:
                if pattern_type in patterns:
                    match = re.search(patterns[pattern_type], line)
                    if match:
                        name = match.group(1)
                        current_class = name
                        symbols.append(Symbol(
                            name=name,
                            type=pattern_type,
                            line=line_num,
                            column=line.index(name) if name in line else 0
                        ))
            
            # Function/Method detection
            for pattern_type in ['function', 'method', 'arrow_function_const']:
                if pattern_type in patterns:
                    match = re.search(patterns[pattern_type], line)
                    if match:
                        name = match.group(1)
                        if name in ['if', 'while', 'for', 'switch', 'catch']:
                            continue
                        
                        symbol_type = 'method' if current_class and pattern_type != 'function' else 'function'
                        symbols.append(Symbol(
                            name=name,
                            type=symbol_type,
                            line=line_num,
                            column=line.index(name) if name in line else 0,
                            class_name=current_class if symbol_type == 'method' else None
                        ))
        
        return symbols


class SymbolExtractor:
    """Detects languages and delegates to appropriate code scanners."""
    
    EXTENSION_MAP: Dict[str, str] = {
        '.py': 'python',
        '.pyw': 'python',
        '.js': 'javascript',
        '.jsx': 'javascript',
        '.ts': 'typescript',
        '.tsx': 'typescript',
        '.java': 'java',
        '.cs': 'csharp',
        '.go': 'go',
        '.rs': 'rust',
        '.cpp': 'cpp',
        '.cc': 'cpp',
        '.cxx': 'cpp',
        '.hpp': 'cpp',
        '.h': 'cpp',
        '.php': 'php',
        '.rb': 'ruby',
    }
    
    def __init__(self) -> None:
        self.stats: Dict[str, int] = {
            'files_processed': 0,
            'symbols_found': 0,
            'errors': 0
        }
    
    def detect_language(self, filepath: str) -> Optional[str]:
        """Detects language hint by checking suffix extensions."""
        path = Path(filepath)
        ext = path.suffix.lower()
        return self.EXTENSION_MAP.get(ext)
    
    def extract_from_file(self, filepath: str) -> Optional[FileSymbols]:
        """Extracts definitions from a single file path."""
        path = Path(filepath)
        
        if not path.exists():
            logger.warning(f"File not found during extraction: {filepath}")
            return None
        
        language = self.detect_language(filepath)
        if not language:
            logger.debug(f"Unsupported suffix for symbol extraction: {filepath}")
            return None
        
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                source_code = f.read()
            return self.extract_from_source(source_code, filepath, language)
        except Exception as e:
            logger.error(f"Error extracting symbols from {filepath}: {e}")
            self.stats['errors'] += 1
            return None
    
    def extract_from_source(self, source_code: str, filepath: str, language: str) -> FileSymbols:
        """Parses definitions directly from source string data."""
        symbols: List[Symbol] = []
        
        if language == 'python':
            extractor = PythonSymbolExtractor(source_code, filepath)
            symbols = extractor.extract()
        else:
            extractor = RegexSymbolExtractor(source_code, language, filepath)
            symbols = extractor.extract()
        
        self.stats['files_processed'] += 1
        self.stats['symbols_found'] += len(symbols)
        
        return FileSymbols(
            file=filepath,
            language=language,
            symbols=symbols
        )
    
    def extract_from_directory(self, directory: str,
                               extensions: Optional[List[str]] = None,
                               max_files: Optional[int] = None) -> List[FileSymbols]:
        """Scans folder structure and parses symbols from valid source files."""
        if max_files is None:
            max_files = MAX_FILES_DEFAULT

        if extensions is None:
            extensions = list(self.EXTENSION_MAP.keys())

        results: List[FileSymbols] = []
        files_processed = 0
        ignore_patterns = load_bbcignore(directory)

        logger.info(f"Scanning directory {directory} for symbols...")
        for root, dirs, files in os.walk(str(Path(directory))):
            dirs[:] = sorted(d for d in dirs if not should_skip_dir_name(d))

            for fname in sorted(files):
                if files_processed >= max_files:
                    break

                fpath = Path(root) / fname
                if fpath.suffix.lower() in set(extensions):
                    if should_skip_file(fpath, directory, ignore_patterns):
                        continue
                    result = self.extract_from_file(str(fpath))
                    if result and result.symbols:
                        results.append(result)
                    files_processed += 1

            if files_processed >= max_files:
                break

        logger.info(f"Extraction finished. Found symbols in {len(results)} files.")
        return results
    
    def get_stats(self) -> Dict[str, int]:
        """Returns statistics counters."""
        return self.stats.copy()
    
    def export_to_json(self, results: List[FileSymbols], output_path: str) -> None:
        """Exports parsed file symbols as a JSON database."""
        data = {
            'stats': self.stats,
            'files': [r.to_dict() for r in results]
        }
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    @staticmethod
    def get_supported_languages() -> List[str]:
        """Returns list of supported languages."""
        return list(set(SymbolExtractor.EXTENSION_MAP.values()))
