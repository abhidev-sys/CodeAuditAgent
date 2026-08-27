"""
Phase 8 test — Complete API flow test

Flow:
1. Repository ingest karo
2. Scan start karo
3. Status poll karo
4. Findings fetch karo
5. Report fetch karo
"""

import time
import httpx

BASE_URL = "http://127.0.0.1:9000/api/v1"


def test_complete_api_flow():
    print("=" * 60)
    print("PHASE 8 — API FLOW TEST")
    print("=" * 60)

    # Step 1: Repository ingest karo
    print("\n[1] Ingesting repository...")
    resp = httpx.post(
        f"{BASE_URL}/repositories/",
        json={
            "path": "R:/codeauditagent/test_repo",
            "name": "test-vulnerable-app",
        }
    )
    print(f"Status: {resp.status_code}")

    if resp.status_code == 201:
        repo_data = resp.json()
        repo_id = repo_data["repository"]["id"]
        print(f"Repository ID: {repo_id}")
        print(f"Language: {repo_data['repository']['language']}")
        print(f"Frameworks: {repo_data['frameworks']}")
    else:
        # Repository already exists — list karo
        print("Repository may already exist, fetching list...")
        list_resp = httpx.get(f"{BASE_URL}/repositories/")
        repos = list_resp.json()
        if repos:
            repo_id = repos[0]["id"]
            print(f"Using existing repository: {repo_id}")
        else:
            print("ERROR: No repositories found!")
            return

    # Step 2: Scan start karo
    print(f"\n[2] Starting scan for repository: {repo_id}")
    scan_resp = httpx.post(
        f"{BASE_URL}/scans/",
        json={"repository_id": repo_id},
    )
    print(f"Status: {scan_resp.status_code}")

    if scan_resp.status_code not in [200, 202]:
        print(f"ERROR: {scan_resp.text}")
        return

    scan_data = scan_resp.json()
    scan_id = scan_data["id"]
    print(f"Scan ID: {scan_id}")
    print(f"Initial Status: {scan_data['status']}")

    # Step 3: Status poll karo
    print(f"\n[3] Polling scan status...")
    max_wait = 120  # 2 minutes max
    waited = 0
    poll_interval = 5

    while waited < max_wait:
        status_resp = httpx.get(f"{BASE_URL}/scans/{scan_id}")
        status_data = status_resp.json()
        current_status = status_data["status"]

        print(f"  [{waited}s] Status: {current_status} — {status_data['message']}")

        if current_status == "COMPLETED":
            print(f"\n  SCAN COMPLETE!")
            print(f"  Risk Score: {status_data.get('risk_score', 'N/A')}/100")
            break
        elif current_status == "FAILED":
            print(f"\n  SCAN FAILED: {status_data.get('error_message')}")
            return

        time.sleep(poll_interval)
        waited += poll_interval
    else:
        print("  TIMEOUT — scan took too long!")
        return

    # Step 4: Findings fetch karo
    print(f"\n[4] Fetching findings...")
    findings_resp = httpx.get(f"{BASE_URL}/findings/{scan_id}")
    print(f"Status: {findings_resp.status_code}")

    if findings_resp.status_code == 200:
        findings_data = findings_resp.json()
        print(f"Total Findings: {findings_data['total']}")
        print(f"Critical: {findings_data['critical']}")
        print(f"High:     {findings_data['high']}")
        print(f"Medium:   {findings_data['medium']}")
        print(f"Low:      {findings_data['low']}")

        for f in findings_data["findings"]:
            print(f"\n  [{f['severity']}] {f['vuln_type']}")
            print(f"  File: {f['file_path']}:{f['line_start']}")
            print(f"  Confidence: {f['confidence']}")
            print(f"  {f['description'][:80]}...")

    # Step 5: Report fetch karo
    print(f"\n[5] Fetching report...")
    report_resp = httpx.get(f"{BASE_URL}/reports/{scan_id}")
    print(f"Status: {report_resp.status_code}")

    if report_resp.status_code == 200:
        report_data = report_resp.json()
        print(f"\nREPORT SUMMARY:")
        print(f"  Report ID:   {report_data['report_id']}")
        print(f"  Repository:  {report_data['repository_name']}")
        print(f"  Risk Score:  {report_data['risk_score']}/100 ({report_data['risk_level']})")
        print(f"\n  Executive Summary:")
        print(f"  {report_data['executive_summary']}")
        print(f"\n  Recommendations:")
        for i, rec in enumerate(report_data['recommendations'][:3], 1):
            print(f"  {i}. {rec}")

    print("\n" + "=" * 60)
    print("PHASE 8 TEST COMPLETE!")
    print("=" * 60)


if __name__ == "__main__":
    test_complete_api_flow()