"""
BBC Attribution Tracer - Phase 2: Static Analysis Call Attribution
Traces definitions and references polyglot-style across project directories
to determine modification impact and blast radius metrics.
"""

import logging
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Set, Tuple, Union

# Set up logging namespace
logger = logging.getLogger("bbc_aos.audit.attribution_tracer")


def iter_source_files(
    project_root: Union[str, Path],
    extensions: Tuple[str, ...]
) -> Iterator[Path]:
    """
    Iterates through the directory tree, skipping standard excluded folders,
    and yields files matching the specified extensions.
    """
    exts = {ext.lower() for ext in extensions}
    for root, dirs, files in os.walk(str(project_root)):
        # Skip common excluded folders during scan to save resources
        dirs[:] = sorted(d for d in dirs if d not in {
            "node_modules", ".venv", "venv", "dist", "build", ".git",
            "__pycache__", "target", ".bbc", ".old", "env",
        })
        for fname in sorted(files):
            path = Path(root) / fname
            if path.suffix.lower() in exts:
                yield path


class AttributionTracer:
    """
    AttributionTracer tracks definitions and usage references across a polyglot project structure,
    estimating file dependency blast radius for changes and potential code faults.
    """
    
    def __init__(self, project_root: str) -> None:
        """
        Initializes an AttributionTracer instance.

        Args:
            project_root: The root directory path of the codebase to analyze.
        """
        self.project_root: str = project_root
        self.symbol_map: Dict[str, List[str]] = {}  # symbol_name -> [defined_in_file1, ...]
        self.reference_map: Dict[str, List[str]] = defaultdict(list)  # symbol_name -> [used_in_file1, ...]
        
    def scan_project(self, target_extensions: Optional[Tuple[str, ...]] = None) -> None:
        """
        Performs definition and reference passes on all source files matching extensions.

        Args:
            target_extensions: Tuple of suffixes to scan (e.g. ('.py', '.js')). Defaults to a polyglot list.
        """
        if not target_extensions:
            target_extensions = ('.py', '.js', '.ts', '.c', '.cpp', '.h', '.java', '.go', '.rs')
            
        logger.info(f"Scanning dependency network in project root: {self.project_root}")
        
        # Pass 1: Extract Definitions
        for path in iter_source_files(self.project_root, extensions=target_extensions):
            rel_path = os.path.relpath(str(path), self.project_root).replace("\\", "/")
            self._extract_definitions(str(path), rel_path)
                    
        logger.info(f"Attribution Knowledge Base: Loaded {len(self.symbol_map)} global symbols.")

        # Pass 2: Extract References
        file_count = 0
        for path in iter_source_files(self.project_root, extensions=target_extensions):
            rel_path = os.path.relpath(str(path), self.project_root).replace("\\", "/")
            self._find_references(str(path), rel_path)
            file_count += 1
        
        logger.info(f"Attribution scan complete. Mapped {len(self.reference_map)} references in {file_count} files.")

    def _extract_definitions(self, file_path: str, rel_path: str) -> None:
        """Scans a file using regex to record defined symbols."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            patterns = [
                r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)',        # Python function
                r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)',      # Python or JS class
                r'function\s+([a-zA-Z_][a-zA-Z0-9_]*)',   # JS/TS function
                r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',       # C-style generic function
            ]
            
            for pat in patterns:
                matches = re.finditer(pat, content)
                for m in matches:
                    symbol = m.group(1)
                    if len(symbol) > 3:  # Skip keywords like if, for, def
                        if symbol not in self.symbol_map:
                            self.symbol_map[symbol] = []
                        if rel_path not in self.symbol_map[symbol]:
                            self.symbol_map[symbol].append(rel_path)
        except Exception as e:
            logger.warning(f"Error extracting definitions from {file_path}: {e}")

    def _find_references(self, file_path: str, rel_path: str) -> None:
        """Checks if known symbols are referenced in file content."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            for symbol in self.symbol_map:
                if symbol in content:
                    # Exclude self-references (calling a symbol inside its definition file)
                    if rel_path not in self.symbol_map[symbol]:
                        if rel_path not in self.reference_map[symbol]:
                            self.reference_map[symbol].append(rel_path)
        except Exception as e:
            logger.warning(f"Error resolving references in {file_path}: {e}")

    def trace_impact(self, faulty_file: str) -> List[str]:
        """
        Traces which files might be impacted if the target file has errors (Blast Radius).

        Args:
            faulty_file: Relative path to the modified or faulty file.

        Returns:
            A list of relative paths representing impacted dependent files.
        """
        impacted_files: Set[str] = set()
        
        # 1. Find symbols defined in the faulty file
        defined_symbols = [sym for sym, files in self.symbol_map.items() if faulty_file in files]
        
        # 2. Add files that reference any of these symbols
        for sym in defined_symbols:
            users = self.reference_map.get(sym, [])
            impacted_files.update(users)
            
        logger.info(f"Attribution trace for {faulty_file} completed. Impacted files: {len(impacted_files)}")
        return list(impacted_files)
