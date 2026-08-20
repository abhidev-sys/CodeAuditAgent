from pathlib import Path

from app.analysis.ast_analyzer import analyze_file
from app.analysis.data_flow import analyze_data_flow
from app.analysis.code_chunker import create_chunks


file_path = "test_repo/app.py"

source = Path(file_path).read_text(encoding="utf-8")


print("\n========== AST ANALYSIS ==========")

ast_result = analyze_file(file_path)

print("Parse success:", ast_result.parse_success)
print("Functions:", [f.name for f in ast_result.functions])
print("Imports:", [i.module for i in ast_result.imports])
print("Suspicious nodes:", len(ast_result.suspicious_nodes))

for node in ast_result.suspicious_nodes:
    print(
        f"  Line {node['line']}: "
        f"{node['reason']}"
    )


print("\n========== DATA FLOW ==========")

df_result = analyze_data_flow(
    ast_result,
    source,
)

print("Tainted variables:", df_result.tainted_variables)
print("Taint flows:", len(df_result.taint_flows))

for flow in df_result.taint_flows:
    print(
        f"  {flow.vuln_type} | "
        f"{flow.tainted_variable} | "
        f"{flow.source_line} -> {flow.sink_line} | "
        f"confidence={flow.confidence}"
    )


print("\n========== CODE CHUNKS ==========")

chunks = create_chunks(
    file_path,
    ast_result,
    source,
)

print("Total chunks:", len(chunks))

for chunk in chunks:
    print(
        f"  {chunk.chunk_id} | "
        f"{chunk.chunk_type} | "
        f"lines={chunk.start_line}-{chunk.end_line} | "
        f"suspicious={chunk.is_suspicious}"
    )