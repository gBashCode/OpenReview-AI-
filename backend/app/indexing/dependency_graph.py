"""Dependency Graph Analysis Engine: Imports, Call Graphs, Class Hierarchies, and Test Mappings."""

from collections import defaultdict
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from app.indexing.ast_parser import ParsedImport, ParsedSymbol
from app.indexing.file_discovery import DiscoveredFile, FileCategory


class DependencyGraph:
    """Represents cross-file and symbol relationships across an entire codebase."""

    def __init__(self):
        # File-to-file relationships
        self.file_imports: Dict[str, Set[str]] = defaultdict(set)  # file -> imported module/file paths
        self.reverse_file_imports: Dict[str, Set[str]] = defaultdict(set)  # file -> files that import it
        
        # Symbol definitions and locations
        self.symbol_to_file: Dict[str, str] = {}  # symbol_name -> file_path
        self.symbol_to_kind: Dict[str, str] = {}  # symbol_name -> kind
        self.file_to_symbols: Dict[str, List[str]] = defaultdict(list)  # file_path -> [symbol_names]

        # Call Graph: callee -> callers
        self.symbol_callers: Dict[str, Set[str]] = defaultdict(set)  # function_name -> set of calling function_names
        self.symbol_calls: Dict[str, Set[str]] = defaultdict(set)  # function_name -> set of called function_names

        # Class Inheritance
        self.class_hierarchy: Dict[str, List[str]] = defaultdict(list)  # class_name -> [base_class_names]

        # Test Mappings: source_file -> related_test_files
        self.test_mappings: Dict[str, Set[str]] = defaultdict(set)

    def add_symbols(self, file_path: str, symbols: List[ParsedSymbol]):
        """Indexes symbols, calls, and class inheritances from a parsed file."""
        for sym in symbols:
            self.symbol_to_file[sym.name] = file_path
            self.symbol_to_kind[sym.name] = sym.kind
            self.file_to_symbols[file_path].append(sym.name)

            if sym.bases:
                self.class_hierarchy[sym.name].extend(sym.bases)

            # Record call relationships
            caller_ident = f"{sym.parent_symbol}.{sym.name}" if sym.parent_symbol else sym.name
            for callee in sym.calls:
                self.symbol_calls[caller_ident].add(callee)
                self.symbol_callers[callee].add(caller_ident)

    def add_imports(self, file_path: str, imports: List[ParsedImport]):
        """Records file import statements."""
        for imp in imports:
            self.file_imports[file_path].add(imp.module)

    def resolve_relationships(self, all_files: List[DiscoveredFile]):
        """Resolves module imports to actual file paths and associates test files."""
        known_files = {f.relative_path for f in all_files}
        path_stems = {Path(f).stem: f for f in known_files}

        # 1. Resolve file imports
        for file_path, imported_modules in list(self.file_imports.items()):
            file_dir = os.path.dirname(file_path).replace("\\", "/")

            for mod in imported_modules:
                resolved_target: Optional[str] = None

                # Relative import (JS/TS/Python: ./utils, ../config)
                if mod.startswith("."):
                    candidate = os.path.normpath(os.path.join(file_dir, mod)).replace("\\", "/")
                    for ext in ("", ".ts", ".js", ".tsx", ".jsx", ".py"):
                        test_path = candidate + ext
                        if test_path in known_files:
                            resolved_target = test_path
                            break
                        # index file in folder
                        idx_path = f"{candidate}/index{ext}"
                        if idx_path in known_files:
                            resolved_target = idx_path
                            break

                # Python dotted import or Go/Java package
                else:
                    dotted_path = mod.replace(".", "/")
                    for ext in (".py", ".ts", ".js", ".java", ".go"):
                        if (dotted_path + ext) in known_files:
                            resolved_target = dotted_path + ext
                            break
                        elif f"backend/{dotted_path}{ext}" in known_files:
                            resolved_target = f"backend/{dotted_path}{ext}"
                            break
                        elif f"src/{dotted_path}{ext}" in known_files:
                            resolved_target = f"src/{dotted_path}{ext}"
                            break

                # Fallback to file stem match
                if not resolved_target and mod in path_stems:
                    resolved_target = path_stems[mod]

                if resolved_target and resolved_target != file_path:
                    self.reverse_file_imports[resolved_target].add(file_path)

        # 2. Build Test Mappings
        test_files = [f for f in all_files if f.category == FileCategory.TEST]
        source_files = [f for f in all_files if f.category == FileCategory.SOURCE_CODE]

        for s_file in source_files:
            s_stem = Path(s_file.relative_path).stem
            for t_file in test_files:
                t_rel = t_file.relative_path
                t_stem = Path(t_rel).stem

                # Naming heuristics:
                # test_auth.py -> auth.py
                # auth_test.go -> auth.go
                # auth.test.ts -> auth.ts
                # OrderServiceTest.java -> OrderService.java
                if (
                    t_stem == f"test_{s_stem}"
                    or t_stem == f"{s_stem}_test"
                    or t_stem == f"{s_stem}.test"
                    or t_stem == f"{s_stem}.spec"
                    or t_stem.lower() == f"{s_stem.lower()}test"
                    or s_file.relative_path in self.file_imports.get(t_rel, set())
                ):
                    self.test_mappings[s_file.relative_path].add(t_rel)

    def get_callers(self, symbol_name: str) -> List[str]:
        """Returns all functions or methods that call the specified symbol."""
        callers = set()
        # Direct match
        callers.update(self.symbol_callers.get(symbol_name, set()))
        # Check unqualified name if passed Class.method
        if "." in symbol_name:
            short = symbol_name.split(".")[-1]
            callers.update(self.symbol_callers.get(short, set()))
        return sorted(list(callers))

    def get_related_tests(self, file_path: str) -> List[str]:
        """Returns test files associated with a source file."""
        return sorted(list(self.test_mappings.get(file_path, set())))

    def get_dependencies(self, file_path: str) -> List[str]:
        """Returns modules/files directly imported by the given file."""
        return sorted(list(self.file_imports.get(file_path, set())))

    def get_dependents(self, file_path: str) -> List[str]:
        """Returns files in the repository that import or depend on the given file."""
        return sorted(list(self.reverse_file_imports.get(file_path, set())))

    def to_dict(self) -> Dict[str, Any]:
        """Serializes graph to a JSON-compatible dictionary."""
        return {
            "file_imports": {k: sorted(list(v)) for k, v in self.file_imports.items()},
            "reverse_file_imports": {k: sorted(list(v)) for k, v in self.reverse_file_imports.items()},
            "symbol_callers": {k: sorted(list(v)) for k, v in self.symbol_callers.items()},
            "class_hierarchy": dict(self.class_hierarchy),
            "test_mappings": {k: sorted(list(v)) for k, v in self.test_mappings.items()},
        }

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "DependencyGraph":
        """Reconstructs graph from serialized dictionary."""
        graph = cls()
        if not data:
            return graph

        for k, vals in data.get("file_imports", {}).items():
            graph.file_imports[k] = set(vals)
        for k, vals in data.get("reverse_file_imports", {}).items():
            graph.reverse_file_imports[k] = set(vals)
        for k, vals in data.get("symbol_callers", {}).items():
            graph.symbol_callers[k] = set(vals)
        for k, vals in data.get("class_hierarchy", {}).items():
            graph.class_hierarchy[k] = list(vals)
        for k, vals in data.get("test_mappings", {}).items():
            graph.test_mappings[k] = set(vals)

        return graph
