"""Debug: Find why static findings = 0"""
from app.security.static_analyzer import run_static_analysis
from app.analysis.ast_analyzer import analyze_file
from app.repository.indexer import index_repository
from pathlib import Path

REPO_PATH = "R:/codeauditagent/test_repo"

print("=" * 60)
print("STEP 1: Files in repo")
print("=" * 60)
index = index_repository(REPO_PATH)
print(f"Analyzable files: {index.analyzable_files}")
for f in index.analyzable_file_paths:
    print(f"  → {f}")

print("\n" + "=" * 60)
print("STEP 2: Static Analysis")
print("=" * 60)
report = run_static_analysis(REPO_PATH)
print(f"Bandit:  {report.bandit_count} findings")
print(f"Custom:  {report.custom_count} findings")
print(f"Total:   {len(report.findings)} findings")
print(f"Error:   {report.error}")

for f in report.findings:
    print(f"\n  [{f.severity}] {f.vuln_type}")
    print(f"  File: {f.file_path}:{f.line_start}")
    print(f"  Tool: {f.tool}")

print("\n" + "=" * 60)
print("STEP 3: AST Suspicious Nodes")
print("=" * 60)
for rel_path in index.analyzable_file_paths:
    abs_path = str(Path(REPO_PATH) / rel_path)
    result = analyze_file(abs_path)
    if result.suspicious_nodes:
        print(f"\n{rel_path}: {len(result.suspicious_nodes)} suspicious")
        for node in result.suspicious_nodes:
            print(f"  Line {node.get('line')}: {node.get('reason')}")