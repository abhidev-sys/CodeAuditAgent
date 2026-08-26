"""Phase 6 test — Patch Generation"""
import uuid
from app.agents.orchestrator import run_scan

scan_id = str(uuid.uuid4())
print(f"Starting scan: {scan_id}")
print("=" * 60)

result = run_scan(
    repository_path="R:/codeauditagent/test_repo",
    repository_id="test-repo-id",
    scan_id=scan_id,
)

print("\n=== VULNERABILITIES ===")
for v in result["vulnerabilities"]:
    print(f"[{v['severity']}] {v['vuln_type']} — {v['file_path']}:{v['line_start']}")
    print(f"  Confidence: {v['confidence']}")
    print(f"  Description: {v['description']}")

print("\n=== PATCHES ===")
for p in result["patches"]:
    print(f"\n{'='*50}")
    print(f"Vulnerability: {p['vuln_type']} — {p['file_path']}")
    print(f"Success: {p['success']}")
    print(f"Confidence: {p['confidence']}")
    print(f"Pattern Used: {p['pattern_used']}")
    print(f"\nExplanation:")
    print(f"  {p['explanation']}")
    print(f"\nUnified Diff:")
    print(p['unified_diff'] if p['unified_diff'] else "  No diff generated")

print("\n=== AGENT LOG ===")
for log in result["agent_log"]:
    print(f"  {log}")