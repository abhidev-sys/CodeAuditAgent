import uuid
from app.agents.orchestrator import run_scan

scan_id = str(uuid.uuid4())
print(f"Starting scan: {scan_id}")
print("=" * 50)

result = run_scan(
    repository_path="R:/codeauditagent/test_repo",
    repository_id="test-repo-id",
    scan_id=scan_id,
)

print()
print("=== SCAN RESULTS ===")
print(f"Language: {result['language']}")
print(f"Frameworks: {result['frameworks']}")
print(f"Static findings: {len(result['static_findings'])}")
print(f"Vulnerabilities confirmed: {len(result['vulnerabilities'])}")
print()

for v in result["vulnerabilities"]:
    print(f"[{v['severity']}] {v['vuln_type']}")
    print(f"  File: {v['file_path']}:{v['line_start']}")
    print(f"  Confidence: {v['confidence']}")
    print(f"  Description: {v['description']}")
    print()

print("Agent Log:")
for log in result["agent_log"]:
    print(f"  {log}")