"""
AST Analyzer — Tree-sitter se Python code parse karta hai

Kya karta hai:
- Python files ka Abstract Syntax Tree banata hai
- Functions, classes, imports extract karta hai
- Exact line numbers track karta hai
- Suspicious patterns identify karta hai

Kyun Tree-sitter?
- Python ke built-in ast module se fast hai
- Multiple languages support karta hai
- Exact byte positions deta hai
- Production-grade tool hai (GitHub use karta hai)
"""

import tree_sitter_python as tspython
from tree_sitter import Language, Parser, Node
from dataclasses import dataclass, field
from pathlib import Path
from app.core.logger import get_logger

logger = get_logger("ast_analyzer")

# Tree-sitter Python language initialize karo
PY_LANGUAGE = Language(tspython.language())
parser = Parser(PY_LANGUAGE)


@dataclass
class FunctionInfo:
    """Ek function ke baare mein saari info."""
    name: str
    start_line: int
    end_line: int
    parameters: list[str]
    # Kya yeh function user input accept karta hai?
    has_request_param: bool = False
    # Function ka poora source code
    source: str = ""


@dataclass
class ImportInfo:
    """Import statement ki info."""
    module: str
    names: list[str]
    line: int
    # Kya yeh security-sensitive module hai?
    is_sensitive: bool = False


@dataclass
class ASTAnalysisResult:
    """Ek file ke AST analysis ka complete result."""
    file_path: str
    functions: list[FunctionInfo] = field(default_factory=list)
    imports: list[ImportInfo] = field(default_factory=list)
    # Suspicious code patterns — jahan vulnerability ho sakti hai
    suspicious_nodes: list[dict] = field(default_factory=list)
    # Saari string literals
    string_literals: list[dict] = field(default_factory=list)
    # File ke total lines
    total_lines: int = 0
    # Parse successful raha?
    parse_success: bool = True
    error: str = ""


# Yeh modules security-sensitive hain
SENSITIVE_MODULES = {
    "sqlite3", "psycopg2", "pymysql", "sqlalchemy",  # SQL
    "subprocess", "os", "shlex",                       # Command execution
    "pickle", "shelve", "marshal",                     # Deserialization
    "requests", "urllib", "httpx", "aiohttp",          # HTTP (SSRF)
    "flask", "django", "fastapi",                      # Web frameworks
    "eval", "exec", "compile",                         # Code execution
}

# Yeh function names suspicious hain
SUSPICIOUS_FUNCTIONS = {
    "execute",
    "executemany",
    "raw",
    "system",
    "popen",
    "loads",
    "load",
    "unpickle",
    "post",
    "request",
    "eval",
    "exec",
    "render_template_string",
}

def analyze_file(file_path: str) -> ASTAnalysisResult:
    """
    Ek Python file ka complete AST analysis karo.

    Args:
        file_path: Python file ka path

    Returns:
        ASTAnalysisResult with all extracted information
    """
    result = ASTAnalysisResult(file_path=file_path)

    try:
        # File padho
        source_code = Path(file_path).read_text(encoding="utf-8", errors="ignore")
        result.total_lines = len(source_code.splitlines())

        # Tree-sitter se parse karo
        # encode() isliye kyunki tree-sitter bytes expect karta hai
        tree = parser.parse(source_code.encode("utf-8"))
        root_node = tree.root_node

        # Saari information extract karo
        result.functions = _extract_functions(root_node, source_code)
        result.imports = _extract_imports(root_node, source_code)
        result.suspicious_nodes = _find_suspicious_nodes(root_node, source_code)
        result.string_literals = _extract_string_literals(root_node, source_code)

        logger.info(
            "AST analysis complete",
            file=file_path,
            functions=len(result.functions),
            imports=len(result.imports),
            suspicious=len(result.suspicious_nodes),
        )

    except Exception as e:
        result.parse_success = False
        result.error = str(e)
        logger.error("AST analysis failed", file=file_path, error=str(e))

    return result


def _extract_functions(root: Node, source: str) -> list[FunctionInfo]:
    """
    File mein saare functions dhundho.

    Tree-sitter nodes traverse karke function_definition nodes nikalo.
    """
    functions = []
    lines = source.splitlines()

    def traverse(node: Node):
        # Agar yeh node function definition hai
        if node.type == "function_definition":
            func_info = _parse_function_node(node, source, lines)
            if func_info:
                functions.append(func_info)

        # Recursively children traverse karo
        for child in node.children:
            traverse(child)

    traverse(root)
    return functions


def _parse_function_node(node: Node, source: str, lines: list) -> FunctionInfo | None:
    """Ek function node se FunctionInfo banao."""
    try:
        # Function naam dhundho
        name_node = node.child_by_field_name("name")
        if not name_node:
            return None

        name = source[name_node.start_byte:name_node.end_byte]

        # Line numbers (0-indexed to 1-indexed)
        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1

        # Parameters extract karo
        params = _extract_parameters(node, source)

        # Request parameter check karo
        # Flask/Django mein 'request' parameter common hai
        has_request = any(
            p in ["request", "req"] or "request" in p.lower()
            for p in params
        )

        # Function ka source code
        func_source = source[node.start_byte:node.end_byte]

        return FunctionInfo(
            name=name,
            start_line=start_line,
            end_line=end_line,
            parameters=params,
            has_request_param=has_request,
            source=func_source[:500],  # First 500 chars
        )

    except Exception:
        return None


def _extract_parameters(func_node: Node, source: str) -> list[str]:
    """Function ke parameters extract karo."""
    params = []

    params_node = func_node.child_by_field_name("parameters")
    if not params_node:
        return params

    for child in params_node.children:
        # identifier = simple parameter jaise 'user_id'
        if child.type == "identifier":
            param_name = source[child.start_byte:child.end_byte]
            if param_name != "self":
                params.append(param_name)
        # typed_parameter = type hint wala parameter
        elif child.type in ["typed_parameter", "default_parameter"]:
            for subchild in child.children:
                if subchild.type == "identifier":
                    param_name = source[subchild.start_byte:subchild.end_byte]
                    if param_name != "self":
                        params.append(param_name)
                    break

    return params


def _extract_imports(root: Node, source: str) -> list[ImportInfo]:
    """File mein saare import statements dhundho."""
    imports = []

    def traverse(node: Node):
        if node.type == "import_statement":
            imp = _parse_import_node(node, source)
            if imp:
                imports.append(imp)

        elif node.type == "import_from_statement":
            imp = _parse_from_import_node(node, source)
            if imp:
                imports.append(imp)

        for child in node.children:
            traverse(child)

    traverse(root)
    return imports


def _parse_import_node(node: Node, source: str) -> ImportInfo | None:
    """Simple import statement parse karo."""
    try:
        line = node.start_point[0] + 1
        names = []

        for child in node.children:
            if child.type == "dotted_name":
                module = source[child.start_byte:child.end_byte]
                names.append(module)

        if not names:
            return None

        module = names[0]
        is_sensitive = any(s in module.lower() for s in SENSITIVE_MODULES)

        return ImportInfo(
            module=module,
            names=names,
            line=line,
            is_sensitive=is_sensitive,
        )
    except Exception:
        return None


def _parse_from_import_node(node: Node, source: str) -> ImportInfo | None:
    """from X import Y statement parse karo."""
    try:
        line = node.start_point[0] + 1
        module = ""
        names = []

        for child in node.children:
            if child.type == "dotted_name" and not module:
                module = source[child.start_byte:child.end_byte]
            elif child.type == "import_from_statement":
                pass

        # Names extract karo
        for child in node.children:
            if child.type == "import_from_statement":
                for subchild in child.children:
                    if subchild.type == "identifier":
                        names.append(source[subchild.start_byte:subchild.end_byte])

        if not module:
            return None

        is_sensitive = any(s in module.lower() for s in SENSITIVE_MODULES)

        return ImportInfo(
            module=module,
            names=names,
            line=line,
            is_sensitive=is_sensitive,
        )
    except Exception:
        return None


def _find_suspicious_nodes(root: Node, source: str) -> list[dict]:
    """
    Suspicious code patterns dhundho.

    Yeh woh jagah hain jahan vulnerability ho sakti hai:
    - String concatenation with variables (SQL injection)
    - Function calls with user input
    - Dangerous function calls (eval, exec, pickle.loads)
    """
    suspicious = []

    def traverse(node: Node):
        # Call expressions check karo — jaise db.execute(query)
        if node.type == "call":
            susp = _check_call_node(node, source)
            if susp:
                suspicious.append(susp)

        # String concatenation check karo — jaise "SELECT " + user_input
        elif node.type == "binary_operator":
            susp = _check_string_concat(node, source)
            if susp:
                suspicious.append(susp)

        for child in node.children:
            traverse(child)

    traverse(root)
    return suspicious


def _check_call_node(node: Node, source: str) -> dict | None:
    """Check whether a function call represents a suspicious operation."""
    try:
        # Get the function/method being called.
        func_node = node.child_by_field_name("function")

        if not func_node:
            return None

        # Example:
        #   conn.execute(...)      -> "conn.execute"
        #   request.args.get(...)  -> "request.args.get"
        #   eval(...)              -> "eval"
        func_name = source[
            func_node.start_byte:func_node.end_byte
        ].strip()

        if not func_name:
            return None

        func_name_lower = func_name.lower()

        # Extract only the actual method/function name.
        #
        # Examples:
        #   "conn.execute"       -> "execute"
        #   "request.args.get"   -> "get"
        #   "subprocess.run"     -> "run"
        #   "eval"               -> "eval"
        base_name = func_name_lower.split(".")[-1]

        # IMPORTANT:
        # Do exact matching instead of substring matching.
        #
        # BAD:
        #   "request.args.get" contains "get"
        #   "app.run" contains "run"
        #
        # This creates false positives.
        #
        # GOOD:
        #   "conn.execute" -> execute is explicitly suspicious
        is_suspicious = base_name in SUSPICIOUS_FUNCTIONS

        if not is_suspicious:
            return None

        # Tree-sitter uses zero-based line numbers.
        # Convert to normal human-readable 1-based line numbers.
        line = node.start_point[0] + 1

        # Extract the actual source code for evidence.
        code = source[
            node.start_byte:node.end_byte
        ].strip()[:200]

        return {
            "type": "suspicious_call",
            "function": func_name,
            "base_name": base_name,
            "line": line,
            "code": code,
            "reason": f"Suspicious function call: {func_name}",
        }

    except Exception as e:
        # AST analysis should never crash the complete repository scan.
        # If one malformed node causes an issue, simply ignore that node.
        return None



def _check_string_concat(node: Node, source: str) -> dict | None:
    """String concatenation suspicious hai kya check karo."""
    try:
        operator_node = None
        for child in node.children:
            if child.type == "+" and child.is_named is False:
                operator_node = child
                break

        if not operator_node:
            return None

        code = source[node.start_byte:node.end_byte][:200]
        line = node.start_point[0] + 1

        # Kya ek side string literal hai?
        children = [c for c in node.children if c.type not in ["+", " "]]
        has_string = any(c.type == "string" for c in children)
        has_variable = any(c.type in ["identifier", "attribute", "call"] for c in children)

        if has_string and has_variable:
            return {
                "type": "string_concatenation",
                "line": line,
                "code": code,
                "reason": "String concatenation with variable — potential injection",
            }

        return None

    except Exception:
        return None


def _extract_string_literals(root: Node, source: str) -> list[dict]:
    """
    SQL queries aur URLs jaise important strings dhundho.
    """
    strings = []
    sql_keywords = {"select", "insert", "update", "delete", "drop", "where"}

    def traverse(node: Node):
        if node.type == "string":
            value = source[node.start_byte:node.end_byte].lower()
            # Kya SQL keywords hain?
            if any(kw in value for kw in sql_keywords):
                strings.append({
                    "value": source[node.start_byte:node.end_byte][:200],
                    "line": node.start_point[0] + 1,
                    "type": "sql_string",
                })

        for child in node.children:
            traverse(child)

    traverse(root)
    return strings