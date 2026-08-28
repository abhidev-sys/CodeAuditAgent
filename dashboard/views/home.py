"""Home page — Dashboard overview."""

import streamlit as st
from dashboard.api_client import list_repositories, list_scans


def render_home():
    """Home page render karo."""

    st.markdown("## Welcome to CodeAuditAgent")
    st.markdown("""
    An autonomous AI-powered security auditing platform that:
    - **Detects** vulnerabilities using static analysis + AST
    - **Reasons** about exploitability using LLM agents
    - **Patches** vulnerabilities with secure code
    - **Verifies** fixes automatically
    """)

    st.markdown("---")

    # Stats
    col1, col2, col3, col4 = st.columns(4)

    # Fetch data
    repos_result = list_repositories()
    scans_result = list_scans()

    repos = repos_result.get("data", []) if repos_result["success"] else []
    scans = scans_result.get("data", []) if scans_result["success"] else []

    completed = [s for s in scans if s.get("status") == "COMPLETED"]
    failed = [s for s in scans if s.get("status") == "FAILED"]

    with col1:
        st.metric(
            label="Repositories",
            value=len(repos),
            help="Total repositories ingested"
        )

    with col2:
        st.metric(
            label="Total Scans",
            value=len(scans),
            help="Total security scans run"
        )

    with col3:
        st.metric(
            label="Completed",
            value=len(completed),
            delta=f"{len(failed)} failed",
            help="Successfully completed scans"
        )

    with col4:
        avg_risk = 0
        if completed:
            risk_scores = [s.get("risk_score", 0) for s in completed if s.get("risk_score")]
            avg_risk = int(sum(risk_scores) / len(risk_scores)) if risk_scores else 0
        st.metric(
            label="Avg Risk Score",
            value=f"{avg_risk}/100",
            help="Average risk score across completed scans"
        )

    st.markdown("---")

    # Quick start
    st.markdown("## Quick Start")

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("### 1. Ingest Repository")
        st.code("POST /api/v1/repositories/\n{\n  'path': '/path/to/repo'\n}", language="json")

    with col_b:
        st.markdown("### 2. Start Scan")
        st.code("POST /api/v1/scans/\n{\n  'repository_id': 'uuid'\n}", language="json")

    st.markdown("### 3. Get Results")
    col_c, col_d = st.columns(2)
    with col_c:
        st.code("GET /api/v1/findings/{scan_id}", language="bash")
    with col_d:
        st.code("GET /api/v1/reports/{scan_id}", language="bash")

    st.markdown("---")

    # Recent scans
    if scans:
        st.markdown("## Recent Scans")
        for scan in scans[:5]:
            status_emoji = {
                "COMPLETED": "✅",
                "RUNNING": "🔄",
                "PENDING": "⏳",
                "FAILED": "❌",
            }.get(scan.get("status", ""), "❓")

            col_s1, col_s2, col_s3, col_s4 = st.columns([3, 2, 2, 2])
            with col_s1:
                st.text(f"Scan: {scan['id'][:8]}...")
            with col_s2:
                st.text(f"{status_emoji} {scan.get('status', 'N/A')}")
            with col_s3:
                risk = scan.get("risk_score")
                st.text(f"Risk: {risk}/100" if risk else "Risk: N/A")
            with col_s4:
                if st.button("View", key=f"view_{scan['id']}"):
                    st.session_state["selected_scan_id"] = scan["id"]
                    st.session_state["page"] = "results"
                    st.rerun()