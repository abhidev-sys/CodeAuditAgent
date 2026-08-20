from pathlib import Path

from app.analysis.ast_analyzer import analyze_file
from app.analysis.data_flow import _analyze_function_flow


file_path = "test_repo/app.py"

source = Path(file_path).read_text(
    encoding="utf-8"
)

lines = source.splitlines()

ast_result = analyze_file(file_path)

print("========== DEBUG FLOW ==========")

print("Functions:")
for func in ast_result.functions:
    print(
        f"  {func.name}: "
        f"lines {func.start_line}-{func.end_line}"
    )

print("\nCalling _analyze_function_flow()...")

func = ast_result.functions[0]

flows = _analyze_function_flow(
    func,
    lines,
    ast_result,
)

print("\nFlows:")
print("Count:", len(flows))

for flow in flows:
    print()
    print("Vulnerability:", flow.vuln_type)
    print("Variable:", flow.tainted_variable)
    print("Source line:", flow.source_line)
    print("Sink line:", flow.sink_line)
    print("Confidence:", flow.confidence)
    print("Evidence:")

    for evidence in flow.evidence:
        print("  ", evidence)