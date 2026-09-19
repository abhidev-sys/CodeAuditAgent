"""Debug script to find why static findings = 0"""
from app.security.static_analyzer import run_static_analysis
from app.analysis.ast_analyzer import analyze_file
from app.repository.indexer import index_repository
import sys

# Apna repo path daalo
REPO_PATH = "R:/codeauditagent/test_repo"

print("=" * 60)
print("STEP 1: Repository Index")
print("=" * 60)
index = index_repository(REPO_PATH)
print(f"Total files: {index.total_files}")
print(f"Analyzable files: {index.analyzable_files}")
for f in index.analyzable_file_paths:
    print(f"  → {f}")

print("\n" + "=" * 60)
print("STEP 2: Static Analysis")
print("=" * 60)
report = run_static_analysis(REPO_PATH)
print(f"Bandit findings:  {report.bandit_count}")
print(f"Semgrep findings: {report.semgrep_count}")
print(f"Custom findings:  {report.custom_count}")
print(f"Total findings:   {len(report.findings)}")
print(f"Bandit success:   {report.bandit_success}")
print(f"Semgrep success:  {report.semgrep_success}")

for f in report.findings:
    print(f"\n  [{f.severity}] {f.vuln_type}")
    print(f"  File: {f.file_path}:{f.line_start}")
    print(f"  Tool: {f.tool}")
    print(f"  Description: {f.description[:80]}")

print("\n" + "=" * 60)
print("STEP 3: AST Analysis per file")
print("=" * 60)
from pathlib import Path
for rel_path in index.analyzable_file_paths:
    abs_path = str(Path(REPO_PATH) / rel_path)
    result = analyze_file(abs_path)
    if result.suspicious_nodes:
        print(f"\n{rel_path}:")
        print(f"  Suspicious nodes: {len(result.suspicious_nodes)}")
        for node in result.suspicious_nodes:
            print(f"    Line {node.get('line')}: {node.get('reason')}")