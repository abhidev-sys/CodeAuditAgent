from app.agents.orchestrator import run_scan

REPO_PATH = "R:/codeauditagent/test_repo"

result = run_scan(
    repository_path=REPO_PATH,
    repository_id="debug-repo",
    scan_id="debug-scan",
)

print("\n" + "=" * 70)
print("FINAL PIPELINE RESULT")
print("=" * 70)

print("Current step      :", result.get("current_step"))
print("Static findings   :", len(result.get("static_findings", [])))
print("Vulnerabilities   :", len(result.get("vulnerabilities", [])))
print("Patches           :", len(result.get("patches", [])))
print("Risk score        :", result.get("risk_score"))
print("Errors            :", result.get("errors", []))

print("\n" + "=" * 70)
print("AGENT LOG")
print("=" * 70)

for log in result.get("agent_log", []):
    print(log)