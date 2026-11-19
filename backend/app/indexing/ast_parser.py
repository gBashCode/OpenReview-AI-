"""Tree-sitter AST Parser for Multi-Language Symbol, Method, Class, and Import Extraction.

Supported Languages:
- Python
- JavaScript
- TypeScript / TSX
- Java
- Go
"""

from dataclasses import dataclass, field
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from tree_sitter import Language, Node, Parser
import tree_sitter_go as tsgo
import tree_sitter_java as tsjava
import tree_sitter_javascript as tsjs
import tree_sitter_python as tspython
import tree_sitter_typescript as tsts

from app.core.logging import get_logger
from app.indexing.file_discovery import Language as LangEnum

logger = get_logger("openreview.indexing.ast")


@dataclass
class ParsedSymbol:
    """Represents an extracted code symbol (function, method, class, interface, struct)."""

    name: str
    kind: str  # function, method, class, interface, struct
    file_path: str
    line_number: int  # 1-indexed
    end_line_number: int  # 1-indexed
    signature: Optional[str] = None
    docstring: Optional[str] = None
    parameters: List[str] = field(default_factory=list)
    return_type: Optional[str] = None
    parent_symbol: Optional[str] = None  # Enclosing class name
    bases: List[str] = field(default_factory=list)  # Base classes or implemented interfaces
    calls: List[str] = field(default_factory=list)  # Function/method names invoked in body


@dataclass
class ParsedImport:
    """Represents an extracted import statement and its imported identifiers."""

    module: str
    imported_names: List[str] = field(default_factory=list)
    alias: Optional[str] = None
    line_number: int = 1


class TreeSitterASTParser:
    """Universal AST parser powered by tree-sitter language grammars."""

    _parsers: Dict[str, Parser] = {}

    def __init__(self):
        self._initialize_parsers()

    @classmethod
    def _initialize_parsers(cls):
        """Initializes tree-sitter parsers once per process."""
        if cls._parsers:
            return

        try:
            cls._parsers["python"] = Parser(Language(tspython.language()))
            cls._parsers["javascript"] = Parser(Language(tsjs.language()))
            cls._parsers["typescript"] = Parser(Language(tsts.language_typescript()))
            cls._parsers["tsx"] = Parser(Language(tsts.language_tsx()))
            cls._parsers["java"] = Parser(Language(tsjava.language()))
            cls._parsers["go"] = Parser(Language(tsgo.language()))
        except Exception as exc:
            logger.error(f"Failed to initialize tree-sitter grammars: {exc}")

    def parse_file(
        self,
        file_path: str,
        content: str,
        language: LangEnum,
    ) -> Tuple[List[ParsedSymbol], List[ParsedImport]]:
        """Parses source code into symbols and imports."""
        if not content.strip():
            return [], []

        lang_key = self._get_grammar_key(file_path, language)
        parser = self._parsers.get(lang_key)
        if not parser:
            # Fallback regex extraction for unknown dialects
            return self._fallback_regex_parse(file_path, content, language)

        content_bytes = content.encode("utf-8")
        try:
            tree = parser.parse(content_bytes)
            root = tree.root_node
        except Exception as exc:
            logger.warning(f"Tree-sitter parse error in {file_path}: {exc}")
            return self._fallback_regex_parse(file_path, content, language)

        symbols: List[ParsedSymbol] = []
        imports: List[ParsedImport] = []

        if language == LangEnum.PYTHON:
            self._extract_python(root, file_path, content_bytes, symbols, imports)
        elif language in (LangEnum.JAVASCRIPT, LangEnum.TYPESCRIPT):
            self._extract_javascript_typescript(root, file_path, content_bytes, symbols, imports)
        elif language == LangEnum.JAVA:
            self._extract_java(root, file_path, content_bytes, symbols, imports)
        elif language == LangEnum.GO:
            self._extract_go(root, file_path, content_bytes, symbols, imports)

        return symbols, imports

    def _get_grammar_key(self, file_path: str, language: LangEnum) -> str:
        lower = file_path.lower()
        if language == LangEnum.PYTHON:
            return "python"
        if language == LangEnum.JAVASCRIPT:
            return "javascript"
        if language == LangEnum.TYPESCRIPT:
            return "tsx" if lower.endswith(".tsx") else "typescript"
        if language == LangEnum.JAVA:
            return "java"
        if language == LangEnum.GO:
            return "go"
        return ""

    # =========================================================================
    # PYTHON EXTRACTOR
    # =========================================================================
    def _extract_python(
        self,
        node: Node,
        file_path: str,
        content_bytes: bytes,
        symbols: List[ParsedSymbol],
        imports: List[ParsedImport],
        parent_class: Optional[str] = None,
    ):
        for child in node.children:
            node_type = child.type

            # Imports: `import foo` or `from foo import bar`
            if node_type == "import_statement":
                for name_node in child.children_by_field_name("name"):
                    imports.append(
                        ParsedImport(
                            module=name_node.text.decode("utf-8"),
                            line_number=child.start_point.row + 1,
                        )
                    )
            elif node_type == "import_from_statement":
                module_node = child.child_by_field_name("module_name")
                mod_str = module_node.text.decode("utf-8") if module_node else ""
                imported_names = []
                for imp_child in child.children_by_field_name("name"):
                    imported_names.append(imp_child.text.decode("utf-8"))
                imports.append(
                    ParsedImport(
                        module=mod_str,
                        imported_names=imported_names,
                        line_number=child.start_point.row + 1,
                    )
                )

            # Class Definition
            elif node_type == "class_definition":
                name_node = child.child_by_field_name("name")
                if name_node:
                    class_name = name_node.text.decode("utf-8")
                    bases = []
                    superclasses = child.child_by_field_name("superclasses")
                    if superclasses:
                        for b in superclasses.children:
                            if b.type == "identifier":
                                bases.append(b.text.decode("utf-8"))

                    docstring = self._extract_python_docstring(child)
                    first_line = content_bytes[child.start_byte : child.end_byte].split(b"\n")[0].decode("utf-8", "ignore")

                    symbols.append(
                        ParsedSymbol(
                            name=class_name,
                            kind="class",
                            file_path=file_path,
                            line_number=child.start_point.row + 1,
                            end_line_number=child.end_point.row + 1,
                            signature=first_line.strip(),
                            docstring=docstring,
                            bases=bases,
                        )
                    )

                    body = child.child_by_field_name("body")
                    if body:
                        self._extract_python(body, file_path, content_bytes, symbols, imports, parent_class=class_name)

            # Function / Method Definition
            elif node_type == "function_definition":
                name_node = child.child_by_field_name("name")
                if name_node:
                    func_name = name_node.text.decode("utf-8")
                    params = []
                    params_node = child.child_by_field_name("parameters")
                    if params_node:
                        for p in params_node.children:
                            if p.type in ("identifier", "typed_parameter", "default_parameter"):
                                p_id = p.child_by_field_name("name") or p
                                params.append(p_id.text.decode("utf-8"))

                    return_type = None
                    ret_node = child.child_by_field_name("return_type")
                    if ret_node:
                        return_type = ret_node.text.decode("utf-8")

                    docstring = self._extract_python_docstring(child)
                    calls = self._extract_calls(child)
                    first_line = content_bytes[child.start_byte : child.end_byte].split(b"\n")[0].decode("utf-8", "ignore")

                    symbols.append(
                        ParsedSymbol(
                            name=func_name,
                            kind="method" if parent_class else "function",
                            file_path=file_path,
                            line_number=child.start_point.row + 1,
                            end_line_number=child.end_point.row + 1,
                            signature=first_line.strip(),
                            docstring=docstring,
                            parameters=params,
                            return_type=return_type,
                            parent_symbol=parent_class,
                            calls=calls,
                        )
                    )

            # Decorated Definition (`@decorator def foo()`)
            elif node_type == "decorated_definition":
                def_child = child.child_by_field_name("definition")
                if def_child:
                    self._extract_python(
                        def_child.parent,  # inspect full decorated node
                        file_path,
                        content_bytes,
                        symbols,
                        imports,
                        parent_class=parent_class,
                    )

    def _extract_python_docstring(self, func_or_class_node: Node) -> Optional[str]:
        body = func_or_class_node.child_by_field_name("body")
        if body and body.children:
            first_stmt = body.children[0]
            if first_stmt.type == "expression_statement":
                expr = first_stmt.children[0] if first_stmt.children else None
                if expr and expr.type == "string":
                    text = expr.text.decode("utf-8", "ignore")
                    return text.strip(" '\"\t\r\n")
        return None

    # =========================================================================
    # JAVASCRIPT / TYPESCRIPT EXTRACTOR
    # =========================================================================
    def _extract_javascript_typescript(
        self,
        node: Node,
        file_path: str,
        content_bytes: bytes,
        symbols: List[ParsedSymbol],
        imports: List[ParsedImport],
        parent_class: Optional[str] = None,
    ):
        for child in node.children:
            node_type = child.type

            # Imports: `import { a, b } from './module'`
            if node_type == "import_statement":
                source_node = child.child_by_field_name("source")
                mod_path = source_node.text.decode("utf-8").strip("'\"") if source_node else ""
                imported_names = []
                clause = child.child_by_field_name("clause") or child
                for sub in self._find_nodes_of_type(clause, ["import_specifier", "identifier"]):
                    imported_names.append(sub.text.decode("utf-8"))
                imports.append(
                    ParsedImport(
                        module=mod_path,
                        imported_names=imported_names,
                        line_number=child.start_point.row + 1,
                    )
                )

            # Class or Interface
            elif node_type in ("class_declaration", "interface_declaration"):
                name_node = child.child_by_field_name("name")
                if name_node:
                    name = name_node.text.decode("utf-8")
                    kind = "interface" if "interface" in node_type else "class"
                    first_line = content_bytes[child.start_byte : child.end_byte].split(b"\n")[0].decode("utf-8", "ignore")

                    bases = []
                    heritage = child.child_by_field_name("heritage") or child.child_by_field_name("extends")
                    if heritage:
                        for id_node in self._find_nodes_of_type(heritage, ["identifier"]):
                            bases.append(id_node.text.decode("utf-8"))

                    symbols.append(
                        ParsedSymbol(
                            name=name,
                            kind=kind,
                            file_path=file_path,
                            line_number=child.start_point.row + 1,
                            end_line_number=child.end_point.row + 1,
                            signature=first_line.strip(),
                            bases=bases,
                        )
                    )

                    body = child.child_by_field_name("body")
                    if body:
                        self._extract_javascript_typescript(
                            body, file_path, content_bytes, symbols, imports, parent_class=name
                        )

            # Function Declaration
            elif node_type in ("function_declaration", "method_definition", "function_signature"):
                name_node = child.child_by_field_name("name")
                if name_node:
                    func_name = name_node.text.decode("utf-8")
                    calls = self._extract_calls(child)
                    first_line = content_bytes[child.start_byte : child.end_byte].split(b"\n")[0].decode("utf-8", "ignore")
                    symbols.append(
                        ParsedSymbol(
                            name=func_name,
                            kind="method" if parent_class else "function",
                            file_path=file_path,
                            line_number=child.start_point.row + 1,
                            end_line_number=child.end_point.row + 1,
                            signature=first_line.strip(),
                            parent_symbol=parent_class,
                            calls=calls,
                        )
                    )

            # Variable Declarations (const foo = () => {})
            elif node_type in ("lexical_declaration", "variable_declaration"):
                for decl in child.children:
                    if decl.type == "variable_declarator":
                        name_node = decl.child_by_field_name("name")
                        val_node = decl.child_by_field_name("value")
                        if name_node and val_node and val_node.type in ("arrow_function", "function_expression"):
                            func_name = name_node.text.decode("utf-8")
                            calls = self._extract_calls(val_node)
                            first_line = content_bytes[decl.start_byte : decl.end_byte].split(b"\n")[0].decode("utf-8", "ignore")
                            symbols.append(
                                ParsedSymbol(
                                    name=func_name,
                                    kind="function",
                                    file_path=file_path,
                                    line_number=decl.start_point.row + 1,
                                    end_line_number=decl.end_point.row + 1,
                                    signature=first_line.strip(),
                                    calls=calls,
                                )
                            )

            # Export Statement (`export const ...` or `export default ...`)
            elif node_type == "export_statement":
                decl = child.child_by_field_name("declaration")
                if decl:
                    self._extract_javascript_typescript(
                        decl.parent, file_path, content_bytes, symbols, imports, parent_class=parent_class
                    )

    # =========================================================================
    # JAVA EXTRACTOR
    # =========================================================================
    def _extract_java(
        self,
        node: Node,
        file_path: str,
        content_bytes: bytes,
        symbols: List[ParsedSymbol],
        imports: List[ParsedImport],
        parent_class: Optional[str] = None,
    ):
        for child in node.children:
            node_type = child.type

            # Import: `import com.foo.bar;`
            if node_type == "import_declaration":
                pkg_text = child.text.decode("utf-8").replace("import", "").replace(";", "").strip()
                imports.append(
                    ParsedImport(
                        module=pkg_text,
                        line_number=child.start_point.row + 1,
                    )
                )

            # Class or Interface
            elif node_type in ("class_declaration", "interface_declaration", "enum_declaration", "record_declaration"):
                name_node = child.child_by_field_name("name")
                if name_node:
                    class_name = name_node.text.decode("utf-8")
                    kind = "interface" if "interface" in node_type else "class"
                    first_line = content_bytes[child.start_byte : child.end_byte].split(b"\n")[0].decode("utf-8", "ignore")

                    bases = []
                    superclasses = child.child_by_field_name("superclass")
                    if superclasses:
                        bases.append(superclasses.text.decode("utf-8"))
                    interfaces = child.child_by_field_name("interfaces")
                    if interfaces:
                        for iface in self._find_nodes_of_type(interfaces, ["type_identifier"]):
                            bases.append(iface.text.decode("utf-8"))

                    symbols.append(
                        ParsedSymbol(
                            name=class_name,
                            kind=kind,
                            file_path=file_path,
                            line_number=child.start_point.row + 1,
                            end_line_number=child.end_point.row + 1,
                            signature=first_line.strip(),
                            bases=bases,
                        )
                    )

                    body = child.child_by_field_name("body")
                    if body:
                        self._extract_java(body, file_path, content_bytes, symbols, imports, parent_class=class_name)

            # Method Declaration or Constructor
            elif node_type in ("method_declaration", "constructor_declaration"):
                name_node = child.child_by_field_name("name")
                if name_node:
                    method_name = name_node.text.decode("utf-8")
                    calls = self._extract_calls(child)
                    first_line = content_bytes[child.start_byte : child.end_byte].split(b"\n")[0].decode("utf-8", "ignore")
                    symbols.append(
                        ParsedSymbol(
                            name=method_name,
                            kind="method",
                            file_path=file_path,
                            line_number=child.start_point.row + 1,
                            end_line_number=child.end_point.row + 1,
                            signature=first_line.strip(),
                            parent_symbol=parent_class,
                            calls=calls,
                        )
                    )

    # =========================================================================
    # GO EXTRACTOR
    # =========================================================================
    def _extract_go(
        self,
        node: Node,
        file_path: str,
        content_bytes: bytes,
        symbols: List[ParsedSymbol],
        imports: List[ParsedImport],
    ):
        for child in node.children:
            node_type = child.type

            # Imports: `import "fmt"` or `import ( "os" \n "net/http" )`
            if node_type == "import_declaration":
                for spec in self._find_nodes_of_type(child, ["import_spec"]):
                    path_node = spec.child_by_field_name("path")
                    if path_node:
                        imports.append(
                            ParsedImport(
                                module=path_node.text.decode("utf-8").strip('"'),
                                line_number=spec.start_point.row + 1,
                            )
                        )

            # Type Declaration (`type User struct { ... }` or `type Reader interface { ... }`)
            elif node_type == "type_declaration":
                for spec in child.children:
                    if spec.type == "type_spec":
                        name_node = spec.child_by_field_name("name")
                        type_node = spec.child_by_field_name("type")
                        if name_node:
                            name = name_node.text.decode("utf-8")
                            kind = "struct" if type_node and type_node.type == "struct_type" else "interface"
                            first_line = content_bytes[child.start_byte : child.end_byte].split(b"\n")[0].decode("utf-8", "ignore")
                            symbols.append(
                                ParsedSymbol(
                                    name=name,
                                    kind=kind,
                                    file_path=file_path,
                                    line_number=child.start_point.row + 1,
                                    end_line_number=child.end_point.row + 1,
                                    signature=first_line.strip(),
                                )
                            )

            # Function Declaration (`func Add(a, b int) int`)
            elif node_type == "function_declaration":
                name_node = child.child_by_field_name("name")
                if name_node:
                    func_name = name_node.text.decode("utf-8")
                    calls = self._extract_calls(child)
                    first_line = content_bytes[child.start_byte : child.end_byte].split(b"\n")[0].decode("utf-8", "ignore")
                    symbols.append(
                        ParsedSymbol(
                            name=func_name,
                            kind="function",
                            file_path=file_path,
                            line_number=child.start_point.row + 1,
                            end_line_number=child.end_point.row + 1,
                            signature=first_line.strip(),
                            calls=calls,
                        )
                    )

            # Method Declaration (`func (s *Server) Start() error`)
            elif node_type == "method_declaration":
                name_node = child.child_by_field_name("name")
                receiver_node = child.child_by_field_name("receiver")
                receiver_name = None
                if receiver_node:
                    for t_id in self._find_nodes_of_type(receiver_node, ["type_identifier", "identifier"]):
                        receiver_name = t_id.text.decode("utf-8")

                if name_node:
                    method_name = name_node.text.decode("utf-8")
                    calls = self._extract_calls(child)
                    first_line = content_bytes[child.start_byte : child.end_byte].split(b"\n")[0].decode("utf-8", "ignore")
                    symbols.append(
                        ParsedSymbol(
                            name=method_name,
                            kind="method",
                            file_path=file_path,
                            line_number=child.start_point.row + 1,
                            end_line_number=child.end_point.row + 1,
                            signature=first_line.strip(),
                            parent_symbol=receiver_name,
                            calls=calls,
                        )
                    )

    # =========================================================================
    # HELPERS
    # =========================================================================
    def _extract_calls(self, node: Node) -> List[str]:
        """Extracts invoked function or method names inside an AST subtree."""
        calls: Set[str] = set()
        call_types = {"call", "call_expression", "method_invocation"}

        def visit(n: Node):
            if n.type in call_types:
                func_node = n.child_by_field_name("function") or n.child_by_field_name("name")
                if func_node:
                    ident = func_node.text.decode("utf-8", "ignore")
                    # Handle obj.method() -> extract method name
                    if "." in ident:
                        ident = ident.split(".")[-1]
                    if ident and ident.isidentifier():
                        calls.add(ident)
            for ch in n.children:
                visit(ch)

        visit(node)
        return sorted(list(calls))

    def _find_nodes_of_type(self, node: Node, types: List[str]) -> List[Node]:
        """Recursively gathers all child nodes matching any of the given types."""
        results: List[Node] = []

        def visit(n: Node):
            if n.type in types:
                results.append(n)
            for ch in n.children:
                visit(ch)

        visit(node)
        return results

    def _fallback_regex_parse(
        self,
        file_path: str,
        content: str,
        language: LangEnum,
    ) -> Tuple[List[ParsedSymbol], List[ParsedImport]]:
        """Fallback regex parser for non-AST languages or degraded environments."""
        symbols: List[ParsedSymbol] = []
        imports: List[ParsedImport] = []
        lines = content.splitlines()

        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            # Generic function matching
            fn_match = re.search(r"^\s*(def|function|func|public\s+\w+)\s+([a-zA-Z_]\w*)", stripped)
            if fn_match:
                symbols.append(
                    ParsedSymbol(
                        name=fn_match.group(2),
                        kind="function",
                        file_path=file_path,
                        line_number=idx,
                        end_line_number=idx,
                        signature=stripped,
                    )
                )
            # Generic class matching
            cls_match = re.search(r"^\s*(class|interface|type)\s+([a-zA-Z_]\w*)", stripped)
            if cls_match:
                symbols.append(
                    ParsedSymbol(
                        name=cls_match.group(2),
                        kind="class",
                        file_path=file_path,
                        line_number=idx,
                        end_line_number=idx,
                        signature=stripped,
                    )
                )

        return symbols, imports
