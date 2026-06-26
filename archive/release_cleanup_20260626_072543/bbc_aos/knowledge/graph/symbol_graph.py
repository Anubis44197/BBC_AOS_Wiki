"""
BBC Symbol Graph - Phase 2: AST Based Call Graph Construction
Analyzes symbol references and call networks to build a dependency graph of the codebase.
"""

import ast
import json
import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

# Set up logging namespace
logger = logging.getLogger("bbc_aos.knowledge.graph.symbol_graph")

class CallType(Enum):
    """Enumerates call relation types."""
    INTERNAL = "internal"      # Call targets defined in the project
    EXTERNAL = "external"      # Call targets from external or standard libraries
    RECURSIVE = "recursive"    # Self recursive calls
    UNKNOWN = "unknown"        # Unresolved call targets


@dataclass
class Call:
    """Represents a call relation from a caller to a callee symbol."""
    symbol: str
    call_type: str
    line: int
    column: int = 0
    raw_call: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializes Call properties to a dictionary."""
        result: Dict[str, Any] = {
            "symbol": self.symbol,
            "type": self.call_type,
            "line": self.line,
        }
        if self.column:
            result["column"] = self.column
        if self.raw_call:
            result["raw_call"] = self.raw_call
        return result


@dataclass
class SymbolNode:
    """Represents a node in the symbol graph."""
    name: str
    full_name: str
    symbol_type: str
    file: str
    line: int
    column: int = 0
    class_name: Optional[str] = None
    module: Optional[str] = None
    calls: List[Call] = field(default_factory=list)
    called_by: List[Call] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializes the SymbolNode and its edges to a dictionary (excludes column to match legacy)."""
        result: Dict[str, Any] = {
            "symbol": self.full_name,
            "type": self.symbol_type,
            "file": self.file,
            "line": self.line,
        }
        if self.class_name:
            result["class"] = self.class_name
        if self.module:
            result["module"] = self.module
        if self.calls:
            result["calls"] = [c.to_dict() for c in self.calls]
        if self.called_by:
            result["called_by"] = [c.to_dict() for c in self.called_by]
        return result


class ImportResolver:
    """
    Parses AST import nodes to map shorthand aliases to fully qualified module paths.
    """
    def __init__(self) -> None:
        self.import_map: Dict[str, str] = {}
        self.module_imports: Set[str] = set()
        self.from_imports: Dict[str, str] = {}
        
    def resolve_imports(self, tree: ast.AST) -> Dict[str, str]:
        """Parses imports from AST tree."""
        self.import_map = {}
        self.module_imports = set()
        self.from_imports = {}
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                self._handle_import(node)
            elif isinstance(node, ast.ImportFrom):
                self._handle_import_from(node)
        
        return self.import_map
    
    def _handle_import(self, node: ast.Import) -> None:
        """Processes import alias statements."""
        for alias in node.names:
            if alias.asname:
                self.import_map[alias.asname] = alias.name
            else:
                self.import_map[alias.name] = alias.name
            self.module_imports.add(alias.name)
    
    def _handle_import_from(self, node: ast.ImportFrom) -> None:
        """Processes from import statements."""
        module = node.module or ""
        level = node.level
        
        prefix = ""
        if level > 0:
            prefix = "." * level
            if module:
                module = prefix + module
            else:
                module = prefix
        
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            if alias.name == "*":
                self.from_imports["*"] = module
            else:
                fully_qualified = f"{module}.{alias.name}" if module else alias.name
                self.import_map[name] = fully_qualified
                self.from_imports[name] = module
    
    def resolve_symbol(self, name: str) -> Optional[str]:
        """Resolves alias string back to qualified module path."""
        return self.import_map.get(name)
    
    def is_module_imported(self, module: str) -> bool:
        """Checks if a module name has been imported."""
        return module in self.module_imports or module in self.import_map


class ASTCallExtractor(ast.NodeVisitor):
    """Traverses Python AST nodes to identify method and function calls."""
    
    def __init__(self, source_code: str, filename: str = "<unknown>") -> None:
        self.source_code: str = source_code
        self.filename: str = filename
        self.lines: List[str] = source_code.split('\n')
        self.import_resolver: ImportResolver = ImportResolver()
        self.symbol_stack: List[str] = []
        self.current_class: Optional[str] = None
        self.current_function: Optional[str] = None
        self.calls: List[Dict[str, Any]] = []
        
    def extract(self) -> List[Dict[str, Any]]:
        """Compiles AST tree and extracts call statements."""
        try:
            tree = ast.parse(self.source_code)
            self.import_resolver.resolve_imports(tree)
            self.visit(tree)
        except SyntaxError as e:
            logger.warning(f"Syntax error compiling AST call extractor for {self.filename}: {e}")
        return self.calls
    
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Zips class scopes to visitor stacks."""
        old_class = self.current_class
        self.current_class = node.name
        self.symbol_stack.append(node.name)
        
        self.generic_visit(node)
        
        self.symbol_stack.pop()
        self.current_class = old_class
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visits standard function definitions."""
        self._enter_function(node.name, node)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visits async function definitions."""
        self._enter_function(node.name, node)
    
    def _enter_function(self, name: str, node: ast.AST) -> None:
        """Pushes function context to walker stack."""
        old_function = self.current_function
        self.current_function = name
        self.symbol_stack.append(name)
        
        self.generic_visit(node)
        
        self.symbol_stack.pop()
        self.current_function = old_function
    
    def visit_Call(self, node: ast.Call) -> None:
        """Zips function call node to output dictionary."""
        call_info = self._analyze_call(node)
        if call_info:
            self.calls.append(call_info)
        self.generic_visit(node)
    
    def _get_current_caller(self) -> Optional[str]:
        """Resolves full path of current caller scope."""
        if not self.symbol_stack:
            return None
        return ".".join(self.symbol_stack)
    
    def _get_raw_call(self, node: ast.Call) -> str:
        """Retrieves raw unparsed code string representation of a call."""
        try:
            return ast.unparse(node)
        except Exception:
            try:
                return ast.unparse(node.func)
            except Exception:
                return "<unparseable>"
    
    def _analyze_call(self, node: ast.Call) -> Optional[Dict[str, Any]]:
        """Resolves target and type parameters for a Call node."""
        caller = self._get_current_caller()
        if not caller:
            return None
        
        line = node.lineno
        column = node.col_offset
        raw_call = self._get_raw_call(node)
        
        func = node.func
        callee, call_type = self._resolve_callee(func)
        
        return {
            "caller": caller,
            "callee": callee,
            "call_type": call_type,
            "line": line,
            "column": column,
            "raw_call": raw_call,
            "file": self.filename
        }
    
    def _resolve_callee(self, func: ast.expr) -> Tuple[str, str]:
        """Resolves callee name and call type class."""
        if isinstance(func, ast.Name):
            return self._resolve_simple_call(func.id)
        elif isinstance(func, ast.Attribute):
            return self._resolve_attribute_call(func)
        elif isinstance(func, ast.Subscript):
            return ("UNKNOWN", CallType.UNKNOWN.value)
        elif isinstance(func, ast.Lambda):
            return ("<lambda>", CallType.EXTERNAL.value)
        return ("UNKNOWN", CallType.UNKNOWN.value)
    
    def _resolve_simple_call(self, name: str) -> Tuple[str, str]:
        """Resolves a direct identifier call."""
        current_caller = self._get_current_caller()
        if current_caller:
            caller_parts = current_caller.split('.')
            if name == caller_parts[-1]:
                return (current_caller, CallType.RECURSIVE.value)
        
        resolved = self.import_resolver.resolve_symbol(name)
        if resolved:
            return (resolved, CallType.EXTERNAL.value)
        
        builtins = {'print', 'len', 'range', 'enumerate', 'zip', 'map', 'filter',
                    'open', 'input', 'int', 'str', 'list', 'dict', 'set', 'tuple',
                    'isinstance', 'hasattr', 'getattr', 'setattr', 'super',
                    'classmethod', 'staticmethod', 'property', 'type', 'id',
                    'iter', 'next', 'sum', 'min', 'max', 'abs', 'round',
                    'divmod', 'pow', 'callable', 'repr', 'dir', 'vars',
                    'globals', 'locals', 'eval', 'exec', 'compile',
                    'breakpoint', 'help', 'exit', 'quit'}
        
        if name in builtins:
            return (f"builtins.{name}", CallType.EXTERNAL.value)
        
        if self.current_class:
            return (f"{self.current_class}.{name}", CallType.INTERNAL.value)
        
        return (name, CallType.UNKNOWN.value)
    
    def _resolve_attribute_call(self, func: ast.Attribute) -> Tuple[str, str]:
        """Resolves method call chains."""
        obj = self._get_object_chain(func.value)
        method = func.attr
        
        if not obj:
            return (f"<unknown>.{method}", CallType.UNKNOWN.value)
        
        if obj == "self":
            if self.current_class:
                return (f"{self.current_class}.{method}", CallType.INTERNAL.value)
            return (method, CallType.UNKNOWN.value)
        
        if obj == "cls" and self.current_class:
            return (f"{self.current_class}.{method}", CallType.INTERNAL.value)
            
        if obj == "super":
            if self.current_class:
                return (f"{self.current_class}.{method}", CallType.EXTERNAL.value)
            return (f"super.{method}", CallType.EXTERNAL.value)
            
        resolved_obj = self.import_resolver.resolve_symbol(obj)
        if resolved_obj:
            return (f"{resolved_obj}.{method}", CallType.EXTERNAL.value)
            
        if self.import_resolver.is_module_imported(obj):
            return (f"{obj}.{method}", CallType.EXTERNAL.value)
            
        if '.' in obj:
            parts = obj.split('.')
            first_part = parts[0]
            resolved_first = self.import_resolver.resolve_symbol(first_part)
            if resolved_first:
                full_path = f"{resolved_first}.{'.'.join(parts[1:])}.{method}"
                return (full_path, CallType.EXTERNAL.value)
                
        return (f"{obj}.{method}", CallType.EXTERNAL.value)

    def _get_object_chain(self, node: ast.expr) -> Optional[str]:
        """Resolves attribute target naming string chains."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            val = self._get_object_chain(node.value)
            if val:
                return f"{val}.{node.attr}"
            return node.attr
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                return node.func.id
        elif isinstance(node, ast.Subscript):
            return self._get_object_chain(node.value)
        return None


class SymbolGraph:
    """Assembles individual file symbol dictionaries into a unified dependency graph."""
    
    def __init__(self) -> None:
        self.nodes: Dict[str, SymbolNode] = {}
        self.file_symbols: Dict[str, List[SymbolNode]] = {}
        self.unresolved_calls: List[Dict[str, Any]] = []
        self.stats: Dict[str, Any] = {
            "total_symbols": 0,
            "total_calls": 0,
            "internal_calls": 0,
            "external_calls": 0,
            "recursive_calls": 0,
            "unknown_calls": 0,
            "unresolved_calls": []
        }
        
    def build_from_symbols(self, symbols_data: List[Dict[str, Any]], 
                           source_files: Optional[Dict[str, str]] = None) -> None:
        """Builds symbol graph nodes and dependency call links."""
        # 1. Add all symbol nodes
        for file_data in symbols_data:
            filepath = file_data.get('file', '')
            symbols = file_data.get('symbols', [])
            for sym in symbols:
                self._add_symbol_node(sym, filepath)
                
        # 2. Analyze calls using AST if source content is present
        if source_files:
            self._analyze_calls_ast(source_files)
            
        # 3. Connect reverse edges (called_by)
        self._build_reverse_edges()
        
        # 4. Compile statistics
        self._update_stats()
        
    def build_from_extractor_output(self, extractor_output: Dict[str, Any],
                                    source_files: Optional[Dict[str, str]] = None) -> None:
        """Builds graph directly from serialized JSON output of SymbolExtractor."""
        files = extractor_output.get('files', [])
        self.build_from_symbols(files, source_files)
        
    def _add_symbol_node(self, symbol: Dict[str, Any], filepath: str) -> None:
        """Converts raw dict symbol representation to a registered SymbolNode."""
        name = symbol.get('name', '')
        sym_type = symbol.get('type', 'unknown')
        line = symbol.get('line', 0)
        column = symbol.get('column', 0)
        class_name = symbol.get('class')
        module = symbol.get('module')
        
        if class_name:
            full_name = f"{class_name}.{name}"
        else:
            full_name = name
            
        node = SymbolNode(
            name=name,
            full_name=full_name,
            symbol_type=sym_type,
            file=filepath,
            line=line,
            column=column,
            class_name=class_name,
            module=module
        )
        
        self.nodes[full_name] = node
        
        if filepath not in self.file_symbols:
            self.file_symbols[filepath] = []
        self.file_symbols[filepath].append(node)
        
    def _analyze_calls_ast(self, source_files: Dict[str, str]) -> None:
        """Runs call extraction on files that are registered in our graph."""
        for filepath, source_code in source_files.items():
            # Match both raw relative/absolute path variants
            matched_key = None
            for key in self.file_symbols.keys():
                if filepath == key or Path(filepath).name == Path(key).name:
                    matched_key = key
                    break
                    
            if not matched_key:
                continue
                
            extractor = ASTCallExtractor(source_code=source_code, filename=matched_key)
            calls = extractor.extract()
            for call_info in calls:
                self._process_call(call_info)
                
    def _process_call(self, call_info: Dict[str, Any]) -> None:
        """Saves calls and traces unresolved references."""
        caller = call_info['caller']
        callee = call_info['callee']
        call_type = call_info['call_type']
        line = call_info['line']
        column = call_info['column']
        raw_call = call_info['raw_call']
        
        caller_node = self.nodes.get(caller)
        if not caller_node:
            return
            
        # Resolve class context
        if call_type == CallType.INTERNAL.value:
            if callee not in self.nodes:
                # E.g. self.other_method()
                callee_full = f"{caller_node.class_name}.{callee.split('.')[-1]}" if caller_node.class_name else callee
                if callee_full in self.nodes:
                    callee = callee_full
                else:
                    call_type = CallType.UNKNOWN.value
                    self.unresolved_calls.append({
                        "caller": caller,
                        "callee": callee,
                        "line": line,
                        "raw_call": raw_call,
                        "reason": "callee_not_in_graph"
                    })
                    
        call = Call(
            symbol=callee,
            call_type=call_type,
            line=line,
            column=column,
            raw_call=raw_call
        )
        caller_node.calls.append(call)
        
    def _build_reverse_edges(self) -> None:
        """Populates called_by arrays for reverse referencing."""
        for node in self.nodes.values():
            for call in node.calls:
                called_symbol = call.symbol
                if called_symbol in self.nodes:
                    reverse_call = Call(
                        symbol=node.full_name,
                        call_type=call.call_type,
                        line=call.line,
                        column=call.column,
                        raw_call=call.raw_call
                    )
                    self.nodes[called_symbol].called_by.append(reverse_call)
                    
    def _update_stats(self) -> None:
        """Aggregates graph statistics."""
        self.stats['total_symbols'] = len(self.nodes)
        
        total_calls = 0
        internal = 0
        external = 0
        recursive = 0
        unknown = 0
        
        for node in self.nodes.values():
            for call in node.calls:
                total_calls += 1
                if call.call_type == CallType.INTERNAL.value:
                    internal += 1
                elif call.call_type == CallType.EXTERNAL.value:
                    external += 1
                elif call.call_type == CallType.RECURSIVE.value:
                    recursive += 1
                elif call.call_type == CallType.UNKNOWN.value:
                    unknown += 1
                    
        self.stats['total_calls'] = total_calls
        self.stats['internal_calls'] = internal
        self.stats['external_calls'] = external
        self.stats['recursive_calls'] = recursive
        self.stats['unknown_calls'] = unknown
        self.stats['unresolved_calls'] = self.unresolved_calls
        
    def get_node(self, full_name: str) -> Optional[SymbolNode]:
        """Queries registered node by name."""
        return self.nodes.get(full_name)
        
    def get_dependents(self, full_name: str) -> List[str]:
        """Returns recursive list of dependent symbol names (calling full_name)."""
        node = self.nodes.get(full_name)
        if not node:
            return []
            
        dependents: Set[str] = set()
        visited: Set[str] = set()
        
        def collect(sym_name: str) -> None:
            if sym_name in visited:
                return
            visited.add(sym_name)
            
            sym_node = self.nodes.get(sym_name)
            if sym_node:
                for call in sym_node.called_by:
                    if call.symbol != full_name:
                        dependents.add(call.symbol)
                        collect(call.symbol)
                        
        collect(full_name)
        return list(dependents)
        
    def get_dependencies(self, full_name: str) -> List[str]:
        """Returns direct dependency targets called by full_name."""
        node = self.nodes.get(full_name)
        if not node:
            return []
        return [c.symbol for c in node.calls if c.call_type in [CallType.INTERNAL.value, CallType.RECURSIVE.value]]
        
    def get_blast_radius(self, full_name: str) -> Dict[str, Any]:
        """Calculates direct and total dependents count statistics."""
        dependents = self.get_dependents(full_name)
        node = self.nodes.get(full_name, SymbolNode("", "", "", "", 0))
        return {
            "symbol": full_name,
            "direct_dependents": [call.symbol for call in node.called_by],
            "total_dependents": len(dependents),
            "all_dependents": dependents,
            "impact_score": len(dependents)
        }
        
    def to_dict(self) -> Dict[str, Any]:
        """Serializes current graph configuration into a dictionary."""
        return {
            "symbols": [node.to_dict() for node in self.nodes.values()],
            "graph_stats": self.stats
        }
        
    def to_json(self, indent: int = 2) -> str:
        """Encodes graph dictionary to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
        
    def export_to_json(self, output_path: str) -> None:
        """Saves graph to file path."""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(self.to_json())


class SymbolGraphBuilder:
    """Helper orchestrator to build SymbolGraph instances from extraction databases."""
    
    def __init__(self) -> None:
        self.graph: SymbolGraph = SymbolGraph()
        
    def build_from_directory(self, symbols_json_path: str, source_dir: str) -> SymbolGraph:
        """Reads JSON definitions and loads source file codes to run call graph walks."""
        with open(symbols_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        source_files = {}
        files = data.get('files', [])
        
        for file_data in files:
            filepath = file_data.get('file', '')
            full_path = Path(source_dir) / filepath
            if not full_path.exists():
                # Fallback: check exact name matching
                for root, dirs, folder_files in os.walk(source_dir):
                    for folder_file in folder_files:
                        if folder_file == Path(filepath).name:
                            full_path = Path(root) / folder_file
                            break
                            
            if full_path.exists():
                try:
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as sf:
                        source_files[filepath] = sf.read()
                except Exception:
                    pass
                    
        self.graph.build_from_extractor_output(data, source_files)
        return self.graph
        
    def build_simple(self, symbols_data: List[Dict[str, Any]]) -> SymbolGraph:
        """Constructs a raw graph nodes list without examining source calls."""
        self.graph.build_from_symbols(symbols_data)
        return self.graph
        
    def build_with_source_mapping(self, symbols_data: List[Dict[str, Any]],
                                  source_mapping: Dict[str, str]) -> SymbolGraph:
        """Constructs graph and traces calls using direct mapping source dictionary."""
        self.graph.build_from_symbols(symbols_data, source_mapping)
        return self.graph
