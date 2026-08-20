"""
Data Flow Analyzer — User input kahan jaata hai track karta hai

Concept: Taint Analysis
- SOURCE = user-controlled input (request.args, request.form, etc.)
- SINK = dangerous function (db.execute, subprocess.run, etc.)
- Agar source se sink tak path hai = vulnerability!

Example:
    user_id = request.args.get('id')   ← SOURCE
    query = "SELECT * FROM users WHERE id=" + user_id  ← PROPAGATION
    db.execute(query)                  ← SINK = SQL INJECTION!
"""

from dataclasses import dataclass, field
from app.analysis.ast_analyzer import ASTAnalysisResult, FunctionInfo
from app.core.logger import get_logger
import re
logger = get_logger("data_flow")

# User input ke sources
TAINT_SOURCES = {
    "request.args",
    "request.form",
    "request.json",
    "request.data",
    "request.values",
    "request.get_json",
    "request.cookies",
    "request.headers",
    "input(",
    "sys.argv",
}

# Dangerous sinks — jahan tainted data pahunche toh vulnerability hai
TAINT_SINKS = {
    "execute": "SQL_INJECTION",
    "executemany": "SQL_INJECTION",
    "raw": "SQL_INJECTION",

    "system": "COMMAND_INJECTION",
    "popen": "COMMAND_INJECTION",
    "call": "COMMAND_INJECTION",

    "loads": "DESERIALIZATION",
    "load": "DESERIALIZATION",

    "eval": "CODE_INJECTION",
    "exec": "CODE_INJECTION",

    "render_template_string": "TEMPLATE_INJECTION",
}

@dataclass
class TaintFlow:
    """
    Ek taint flow — source se sink tak ka path.
    Yeh ek potential vulnerability hai.
    """
    # Vulnerability type
    vuln_type: str
    # Source — user input kahan se aaya
    source: str
    source_line: int
    # Variable jo tainted hai
    tainted_variable: str
    # Sink — dangerous function
    sink: str
    sink_line: int
    # Confidence — kitna sure hain hum
    confidence: float
    # Evidence — code snippets
    evidence: list[str] = field(default_factory=list)


@dataclass
class DataFlowResult:
    """Ek file ka complete data flow analysis result."""
    file_path: str
    taint_flows: list[TaintFlow] = field(default_factory=list)
    # Saare tainted variables
    tainted_variables: set[str] = field(default_factory=set)


def analyze_data_flow(
    ast_result: ASTAnalysisResult,
    source_code: str,
) -> DataFlowResult:
    """
    AST analysis result se data flow analyze karo.

    Approach:
    1. Sources dhundho (request.args, etc.)
    2. Tainted variables track karo
    3. Sinks check karo (db.execute, etc.)
    4. Source-to-sink path report karo

    Args:
        ast_result: Pehle ka AST analysis result
        source_code: File ka source code

    Returns:
        DataFlowResult with all taint flows
    """
    result = DataFlowResult(file_path=ast_result.file_path)
    lines = source_code.splitlines()

    # Har function ke liye analysis karo
    for func in ast_result.functions:
        flows = _analyze_function_flow(func, lines, ast_result)
        result.taint_flows.extend(flows)

    # Tainted variables collect karo
    for flow in result.taint_flows:
        result.tainted_variables.add(flow.tainted_variable)

    logger.info(
        "Data flow analysis complete",
        file=ast_result.file_path,
        taint_flows=len(result.taint_flows),
        tainted_vars=len(result.tainted_variables),
    )

    return result

def _analyze_function_flow(
    func: FunctionInfo,
    all_lines: list[str],
    ast_result: ASTAnalysisResult,
) -> list[TaintFlow]:
    """
    Analyze taint propagation inside a single function.

    Tracks:

        SOURCE
          ↓
        TAINTED VARIABLE
          ↓
        PROPAGATION
          ↓
        TAINTED VARIABLE
          ↓
        SINK

    Example:

        user_id = request.args.get("id")
        query = "SELECT * FROM users WHERE id=" + user_id
        conn.execute(query)

    Flow detected:

        request.args
            ↓
        user_id
            ↓
        query
            ↓
        conn.execute()

    Returns:
        List of detected TaintFlow objects.
    """

    flows: list[TaintFlow] = []

    # ---------------------------------------------------------
    # 1. Extract function lines
    # ---------------------------------------------------------

    function_start_index = func.start_line - 1
    function_end_index = min(
        func.end_line,
        len(all_lines),
    )

    func_lines = all_lines[
        function_start_index:function_end_index
    ]

    if not func_lines:
        return flows

    # ---------------------------------------------------------
    # 2. Find initial tainted variables
    # ---------------------------------------------------------

    tainted_vars = _find_tainted_variables(
        func_lines,
        func.start_line,
    )

    if not tainted_vars:
        return flows

    # ---------------------------------------------------------
    # 3. Track taint state
    #
    # variable -> source information
    #
    # Example:
    #
    # user_id -> (8, source line)
    # query   -> (8, source line)
    # ---------------------------------------------------------

    taint_state: dict[str, tuple[int, str]] = dict(
        tainted_vars
    )

    # ---------------------------------------------------------
    # 4. Track already reported flows
    # ---------------------------------------------------------

    seen_flows: set[tuple] = set()

    # ---------------------------------------------------------
    # 5. Scan function sequentially
    # ---------------------------------------------------------

    for line_offset, raw_line in enumerate(func_lines):

        actual_line = func.start_line + line_offset

        # Remove comments.
        line = raw_line.split("#", 1)[0].strip()

        if not line:
            continue

        # -----------------------------------------------------
        # Skip source assignment itself.
        # -----------------------------------------------------

        source_assignment = any(
            actual_line == source_line
            for source_line, _ in taint_state.values()
        )

        # -----------------------------------------------------
        # 6. Detect assignment propagation
        #
        # Example:
        #
        # query = "SELECT..." + user_id
        #
        # If user_id is tainted,
        # query becomes tainted.
        # -----------------------------------------------------

        if "=" in line:

            left_side, right_side = line.split("=", 1)

            target = left_side.strip()
            expression = right_side.strip()

            # Only simple variable assignments.
            if target.isidentifier() and target != "self":

                # Check whether any currently tainted variable
                # appears in the RHS.
                for tainted_var in list(taint_state.keys()):

                    variable_pattern = (
                        rf"\b{re.escape(tainted_var)}\b"
                    )

                    if re.search(
                        variable_pattern,
                        expression,
                    ):

                        # Don't overwrite the original source
                        # information.
                        if target not in taint_state:

                            original_source = taint_state[
                                tainted_var
                            ]

                            taint_state[target] = (
                                original_source[0],
                                original_source[1],
                            )

                        break

        # -----------------------------------------------------
        # 7. Check sinks
        # -----------------------------------------------------

        for sink_func, vuln_type in TAINT_SINKS.items():

            sink_func = sink_func.strip().lower()

            if not sink_func:
                continue

            # Exact function-call pattern.
            #
            # Matches:
            #   execute(query)
            #   conn.execute(query)
            #
            # Does NOT match:
            #   execute_something()
            #   myexecute()
            #

            sink_pattern = (
                rf"(?<![\w.])"
                rf"(?:[\w]+\.)*"
                rf"{re.escape(sink_func)}"
                rf"\s*\("
            )

            sink_match = re.search(
                sink_pattern,
                line,
                flags=re.IGNORECASE,
            )

            if not sink_match:
                continue

            # -------------------------------------------------
            # Get only the function call.
            # -------------------------------------------------

            call_text = line[
                sink_match.start():
            ]

            # -------------------------------------------------
            # Check whether ANY tainted variable reaches
            # this sink.
            # -------------------------------------------------

            for tainted_var, (
                source_line,
                source_text,
            ) in taint_state.items():

                variable_pattern = (
                    rf"\b{re.escape(tainted_var)}\b"
                )

                if not re.search(
                    variable_pattern,
                    call_text,
                ):
                    continue

                # -------------------------------------------------
                # Avoid reporting source line itself as sink.
                # -------------------------------------------------

                if actual_line <= source_line:
                    continue

                # -------------------------------------------------
                # Create unique flow identifier.
                # -------------------------------------------------

                flow_key = (
                    vuln_type,
                    tainted_var,
                    source_line,
                    actual_line,
                    sink_func,
                )

                if flow_key in seen_flows:
                    continue

                seen_flows.add(flow_key)

                # -------------------------------------------------
                # Calculate confidence.
                # -------------------------------------------------

                confidence = _calculate_confidence(
                    source_text,
                    line,
                    tainted_var,
                    vuln_type,
                )

                # -------------------------------------------------
                # Create evidence.
                # -------------------------------------------------

                evidence = [
                    (
                        f"Line {source_line}: "
                        f"{source_text.strip()}"
                    ),
                    (
                        f"Line {actual_line}: "
                        f"{line.strip()}"
                    ),
                ]

                # -------------------------------------------------
                # Create TaintFlow.
                # -------------------------------------------------

                flow = TaintFlow(
                    vuln_type=vuln_type,
                    source=source_text.strip(),
                    source_line=source_line,
                    tainted_variable=tainted_var,
                    sink=line.strip(),
                    sink_line=actual_line,
                    confidence=confidence,
                    evidence=evidence,
                )

                flows.append(flow)

    return flows


def _find_tainted_variables(
    func_lines: list[str],
    start_line: int,
) -> dict[str, tuple[int, str]]:
    """
    Find variables that receive user-controlled input.

    Example:
        user_id = request.args.get("id")

    Result:
        {
            "user_id": (
                8,
                "    user_id = request.args.get('id')"
            )
        }
    """

    tainted: dict[str, tuple[int, str]] = {}

    for offset, raw_line in enumerate(func_lines):

        actual_line = start_line + offset

        # Remove comments.
        code_line = raw_line.split("#", 1)[0].strip()

        if not code_line:
            continue

        # We only analyse assignments.
        if "=" not in code_line:
            continue

        # Split only at the first "=".
        left_side, right_side = code_line.split("=", 1)

        variable = left_side.strip()
        expression = right_side.strip()

        # Only simple variable assignments.
        #
        # Valid:
        #   user_id = ...
        #
        # Ignore:
        #   obj.user_id = ...
        #   data["id"] = ...
        #   a, b = ...
        if not variable.isidentifier():
            continue

        if variable == "self":
            continue

        # ---------------------------------------------------------
        # Check user-controlled sources.
        # ---------------------------------------------------------

        source_found = False

        for source in TAINT_SOURCES:

            source = source.strip()

            if not source:
                continue

            # Function source:
            #
            # input(...)
            # sys.argv is handled below as an attribute/source.
            if source.endswith("("):

                function_name = source[:-1].strip()

                if (
                    expression.startswith(function_name + "(")
                    or f" {function_name}(" in expression
                    or f"({function_name}(" in expression
                ):
                    source_found = True
                    break

            else:
                # Direct source detection.
                #
                # This intentionally allows:
                #
                # request.args.get(...)
                # request.form.get(...)
                # request.json.get(...)
                #
                # because request.args itself is the taint source.
                if source in expression:
                    source_found = True
                    break

        if not source_found:
            continue

        # ---------------------------------------------------------
        # User-controlled value found.
        # ---------------------------------------------------------

        tainted[variable] = (
            actual_line,
            raw_line,
        )

    return tainted

def _calculate_confidence(
    source: str,
    sink: str,
    variable: str,
    vuln_type: str,
) -> float:
    """
    Confidence score calculate karo — 0.0 to 1.0

    Factors:
    - Source clearly user-controlled hai?
    - Sink clearly dangerous hai?
    - Variable directly use ho raha hai?
    - String concatenation hai?
    """
    confidence = 0.5  # Base confidence

    # Direct string concatenation — high confidence SQL injection
    if "+" in sink and variable in sink:
        confidence += 0.3

    # f-string mein variable — high confidence
    if f"{{{variable}}}" in sink or f"'{variable}'" in sink:
        confidence += 0.2

    # Request.args direct use — very suspicious
    if "request.args" in source:
        confidence += 0.1

    # Cap at 0.95 — hum 100% sure kabhi nahi
    return min(confidence, 0.95)