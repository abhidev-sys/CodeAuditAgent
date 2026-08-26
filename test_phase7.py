"""Phase 7 test — Complete Audit Report"""
import uuid
from pathlib import Path
from app.agents.orchestrator import run_scan

scan_id = str(uuid.uuid4())
print(f"Starting complete scan: {scan_id}")
print("=" * 60)

result = run_scan(
    repository_path="R:/codeauditagent/test_repo",
    repository_id="test-repo-id",
    scan_id=scan_id,
)

print("\n" + "=" * 60)
print("         SCAN COMPLETE")
print("=" * 60)
print(f"Risk Score:      {result.get('risk_score', 0)}/100")
print(f"Vulnerabilities: {len(result.get('vulnerabilities', []))}")
print(f"Patches:         {len(result.get('patches', []))}")
print()

# Report file padhke print karo
report_id = scan_id[:8]
txt_report = Path(f"reports/report_{report_id}.txt")
json_report = Path(f"reports/report_{report_id}.json")

if txt_report.exists():
    print("\n" + "=" * 60)
    print("FULL AUDIT REPORT:")
    print("=" * 60)
    print(txt_report.read_text())
else:
    print("Report file not found!")
    print("\nAgent Log:")
    for log in result.get("agent_log", []):
        print(f"  {log}")