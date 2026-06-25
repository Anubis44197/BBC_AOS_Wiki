"""
BBC HMPU Polyglot Quantizer - Phase 4
Implements multi-language regex-based code extraction to build structural recipes.
"""

import re
import time
import logging
from typing import Any, Dict, List, Optional

# Set up logging namespace
logger = logging.getLogger("bbc_aos.knowledge.indexes.hmpu_quantizer")


class HMPUQuantizer:
    """
    Analyzes raw source code files to extract classes, functions, and imports
    across various programming languages using deterministic regex parsing.
    """
    
    def __init__(self) -> None:
        """Initializes the HMPUQuantizer with regex definitions for major languages."""
        self.PATTERNS: Dict[str, Dict[str, str]] = {
            "python": {
                "class": r'''^\s*class\s+([a-zA-Z0-9_]+)''',
                "function": r'''^\s*def\s+([a-zA-Z0-9_]+)''',
                "import": r'''^\s*(?:import|from)\s+([a-zA-Z0-9_\.]+)'''
            },
            "rust": {
                "class": r'''^\s*(?:pub\s+)?(?:struct|enum|trait)\s+([a-zA-Z0-9_]+)''',
                "function": r'''^\s*(?:pub\s+)?fn\s+([a-zA-Z0-9_]+)''',
                "import": r'''^\s*use\s+([a-zA-Z0-9_:]+)'''
            },
            "javascript": {
                "class": r'''^\s*(?:export\s+)?class\s+([a-zA-Z0-9_]+)''',
                "function": r'''^\s*(?:export\s+)?(?:async\s+)?function\s+([a-zA-Z0-9_]+)''',
                "variable_func": r'''^\s*(?:export\s+)?(?:const|let|var)\s+([a-zA-Z0-9_]+)\s*=\s*(?:async\s*)?(?:function|\(.*\)\s*=>)''',
                "object_method": r'''^\s{2,}([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)\s*\{''',
                "import": r'''^\s*import\s+.*\s+from\s+['"](.*?)['"]'''
            },
            "go": {
                "class": r'''^\s*type\s+([a-zA-Z0-9_]+)\s+struct''',
                "function": r'''^\s*func\s+([a-zA-Z0-9_]+)''',
                "import": r'''^\s*import\s+['"](.*?)['"]'''
            },
            "c_cpp": {
                "class": r'''^\s*(?:class|struct)\s+([a-zA-Z0-9_]+)''',
                "function": r'''^\s*(?:[a-zA-Z0-9_]+[\s\*]+)+([a-zA-Z0-9_]+)\s*\(''',
                "import": r'''^\s*#include\s+[<"](.*?)['">]'''
            },
            "java_csharp": {
                "class": r'''^\s*(?:public|private|protected|internal)?\s*(?:static\s+)?(?:class|interface|enum)\s+([a-zA-Z0-9_]+)''',
                "function": r'''^\s*(?:public|private|protected|internal)?\s*(?:static\s+)?(?:[a-zA-Z0-9_<>\[\]]+\s+)+([a-zA-Z0-9_]+)\s*\(''',
                "import": r'''^\s*(?:import|using)\s+([a-zA-Z0-9_\.]+)'''
            },
            "php": {
                "class": r'''^\s*(?:abstract\s+)?class\s+([a-zA-Z0-9_]+)''',
                "function": r'''^\s*function\s+([a-zA-Z0-9_]+)''',
                "import": r'''^\s*(?:use|require|include)\s+['"](.*?)['"]'''
            },
            "ruby": {
                "class": r'''^\s*class\s+([a-zA-Z0-9_]+)''',
                "function": r'''^\s*def\s+([a-zA-Z0-9_]+)''',
                "import": r'''^\s*require\s+['"](.*?)['"]'''
            },
            "swift": {
                "class": r'''^\s*(?:public|private)?\s*(?:class|struct|enum|protocol)\s+([a-zA-Z0-9_]+)''',
                "function": r'''^\s*(?:public|private)?\s*func\s+([a-zA-Z0-9_]+)''',
                "import": r'''^\s*import\s+([a-zA-Z0-9_]+)'''
            },
            "kotlin": {
                "class": r'''^\s*(?:open|data)?\s*class\s+([a-zA-Z0-9_]+)''',
                "function": r'''^\s*fun\s+([a-zA-Z0-9_]+)''',
                "import": r'''^\s*import\s+([a-zA-Z0-9_\.]+)'''
            },
            "sql": {
                "class": r'''^\s*CREATE\s+TABLE\s+([a-zA-Z0-9_]+)''',
                "function": r'''^\s*CREATE\s+(?:OR\s+REPLACE\s+)?(?:FUNCTION|PROCEDURE)\s+([a-zA-Z0-9_]+)''',
                "import": r'''^\s*--\s*IMPORT\s+(.*)'''
            }
        }
        
        # Apply aliases
        self.PATTERNS["typescript"] = self.PATTERNS["javascript"]
        self.PATTERNS["c"] = self.PATTERNS["c_cpp"]
        self.PATTERNS["cpp"] = self.PATTERNS["c_cpp"]
        self.PATTERNS["java"] = self.PATTERNS["java_csharp"]
        self.PATTERNS["csharp"] = self.PATTERNS["java_csharp"]
        logger.info("HMPUQuantizer initialized with multi-language patterns.")

    def detect_language(self, content: str) -> str:
        """
        Analyzes the file content structure to estimate the source language.

        Args:
            content: Document content.

        Returns:
            The matched language code string.
        """
        if "#include" in content:
            return "c_cpp"
        if "public class" in content:
            return "java"
        if "func " in content and "var " in content:
            return "go"
        if "fn " in content:
            return "rust"
        if "def " in content and ":" in content:
            return "python"
        return "python"

    def process_content(self, content: str, file_ext: Optional[str] = None) -> Dict[str, Any]:
        """
        Scans code content to extract classes, functions, imports, and metadata.

        Args:
            content: Source code text.
            file_ext: File extension string (e.g. '.py').

        Returns:
            A dictionary containing structure analysis and stats.
        """
        start_time = time.time()
        
        lang = "python"
        if file_ext:
            ext = file_ext.lower()
            if ext in ['.rs']:
                lang = "rust"
            elif ext in ['.js', '.jsx', '.ts', '.tsx']:
                lang = "javascript"
            elif ext in ['.go']:
                lang = "go"
            elif ext in ['.c', '.h', '.cpp', '.hpp']:
                lang = "c_cpp"
            elif ext in ['.java', '.cs']:
                lang = "java_csharp"
            elif ext in ['.php']:
                lang = "php"
            elif ext in ['.rb']:
                lang = "ruby"
            elif ext in ['.swift']:
                lang = "swift"
            elif ext in ['.kt', '.kts']:
                lang = "kotlin"
            elif ext in ['.sql']:
                lang = "sql"
        else:
            lang = self.detect_language(content)
            
        patterns = self.PATTERNS.get(lang, self.PATTERNS["python"])
        
        structure: Dict[str, Any] = {
            "classes": [],
            "functions": [],
            "imports": [],
            "language": lang
        }
        
        try:
            if "class" in patterns:
                for match in re.finditer(patterns["class"], content, re.MULTILINE):
                    structure["classes"].append(match.group(1))
            
            if "function" in patterns:
                for match in re.finditer(patterns["function"], content, re.MULTILINE):
                    structure["functions"].append(match.group(1))
                
            if "variable_func" in patterns:
                for match in re.finditer(patterns["variable_func"], content, re.MULTILINE):
                    structure["functions"].append(match.group(1))
            
            if "object_method" in patterns:
                for match in re.finditer(patterns["object_method"], content, re.MULTILINE):
                    method_name = match.group(1)
                    if method_name not in ['if', 'for', 'while', 'switch', 'catch', 'with']:
                        structure["functions"].append(method_name)
            
            if "import" in patterns:
                for match in re.finditer(patterns["import"], content, re.MULTILINE):
                    structure["imports"].append(match.group(1))
                
        except Exception as e:
            logger.error(f"Quantizer error parsing code content: {e}")
            
        duration = time.time() - start_time
        return {
            "structure": structure,
            "stats": {"size": len(content), "time": duration}
        }
