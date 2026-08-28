"""New Scan page — Repository ingest + scan start."""

import time
import streamlit as st
from dashboard.api_client import (
    ingest_repository,
    start_scan,
    get_scan_status,
    get_findings,
    get_report,
)


def render_new_scan():
    """New scan page render karo."""
    st.markdown("## New Security Scan")
    st.markdown("Enter a repository path to start an autonomous security audit.")

    # Form
    with st.form("scan_form"):
        repo_path = st.text_input(
            "Repository Path",
            placeholder="R:/codeauditagent/test_repo",
            help="Local path to the Python repository you want to audit",
        )
        repo_name = st.text_input(
            "Repository Name (optional)",
            placeholder="my-flask-app",
            help="Custom name for this repository",
        )
        submitted = st.form_submit_button(
            "🔍 Start Security Scan",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        if not repo_path:
            st.error("Please enter a repository path!")
            return

        _run_scan_flow(repo_path, repo_name)


def _run_scan_flow(repo_path: str, repo_name: str):
    """Complete scan flow run karo with progress updates."""

    # Progress container
    progress_container = st.container()

    with progress_container:
        # Step 1: Ingest
        st.markdown("### Scan Progress")
        progress = st.progress(0)
        status_text = st.empty()

        status_text.info("📁 Step 1/4: Ingesting repository...")
        progress.progress(10)

        result = ingest_repository(repo_path, repo_name)

        if not result["success"]:
            st.error(f"Repository ingestion failed: {result['error']}")
            return

        repo_data = result["data"]
        repo_id = repo_data["repository"]["id"]
        progress.progress(25)

        st.success(f"✅ Repository ingested: {repo_data['repository']['name']}")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Language", repo_data["repository"].get("language", "N/A"))
        with col2:
            frameworks = repo_data.get("frameworks", [])
            st.metric("Frameworks", ", ".join(frameworks) if frameworks else "None")
        with col3:
            st.metric("Files", repo_data.get("analyzable_files", 0))

        # Step 2: Start Scan
        status_text.info("🚀 Step 2/4: Starting scan agents...")
        progress.progress(35)

        scan_result = start_scan(repo_id)

        if not scan_result["success"]:
            st.error(f"Scan start failed: {scan_result['error']}")
            return

        scan_id = scan_result["data"]["id"]
        st.info(f"🆔 Scan ID: `{scan_id}`")
        st.session_state["current_scan_id"] = scan_id

        # Step 3: Poll status
        status_text.info("🤖 Step 3/4: AI agents analyzing your code...")
        progress.progress(50)

        max_wait = 180
        waited = 0
        poll_interval = 3

        status_placeholder = st.empty()

        while waited < max_wait:
            status_result = get_scan_status(scan_id)

            if not status_result["success"]:
                st.error("Failed to get scan status")
                return

            scan_status = status_result["data"]["status"]

            if scan_status == "COMPLETED":
                progress.progress(85)
                status_placeholder.success("✅ Scan completed!")
                break
            elif scan_status == "FAILED":
                error_msg = status_result["data"].get("error_message", "Unknown error")
                status_placeholder.error(f"❌ Scan failed: {error_msg}")
                return
            else:
                elapsed_pct = min(50 + int((waited / max_wait) * 35), 84)
                progress.progress(elapsed_pct)
                status_placeholder.info(
                    f"🔄 {scan_status} — {status_result['data'].get('message', '')} "
                    f"({waited}s elapsed)"
                )

            time.sleep(poll_interval)
            waited += poll_interval
        else:
            st.error("⏰ Scan timed out — please check again later")
            return

        # Step 4: Show Results
        status_text.info("📊 Step 4/4: Generating report...")
        progress.progress(95)

        risk_score = status_result["data"].get("risk_score", 0)

        progress.progress(100)
        status_text.success("🎉 Scan complete! Showing results below...")

        # Show results inline
        _render_inline_results(scan_id, risk_score)


def _render_inline_results(scan_id: str, risk_score: int):
    """Inline results render karo after scan."""
    st.markdown("---")
    st.markdown("## Scan Results")

    # Risk Score
    _render_risk_score(risk_score)

    st.markdown("---")

    # Findings
    findings_result = get_findings(scan_id)
    if findings_result["success"]:
        _render_findings(findings_result["data"])

    st.markdown("---")

    # Report summary
    report_result = get_report(scan_id)
    if report_result["success"]:
        _render_report_summary(report_result["data"])

    # Save to session for results page
    st.session_state["selected_scan_id"] = scan_id


def _render_risk_score(risk_score: int):
    """Risk score display karo."""
    if risk_score >= 75:
        color = "#ff4757"
        level = "CRITICAL"
        emoji = "🔴"
    elif risk_score >= 50:
        color = "#ff6b35"
        level = "HIGH"
        emoji = "🟠"
    elif risk_score >= 25:
        color = "#ffa502"
        level = "MEDIUM"
        emoji = "🟡"
    elif risk_score > 0:
        color = "#2ed573"
        level = "LOW"
        emoji = "🟢"
    else:
        color = "#2ed573"
        level = "SAFE"
        emoji = "✅"

    st.markdown(f"""
    <div style="
        background: #16213e;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        border: 2px solid {color};
        margin: 10px 0;
    ">
        <h2 style="color: {color}; margin: 0;">
            {emoji} RISK SCORE: {risk_score}/100
        </h2>
        <h3 style="color: {color}; margin: 5px 0;">
            {level} RISK
        </h3>
    </div>
    """, unsafe_allow_html=True)

    st.progress(risk_score / 100)


def _render_findings(findings_data: dict):
    """Findings display karo."""
    st.markdown("## Findings")

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Critical", findings_data.get("critical", 0))
    with col2:
        st.metric("High", findings_data.get("high", 0))
    with col3:
        st.metric("Medium", findings_data.get("medium", 0))
    with col4:
        st.metric("Low", findings_data.get("low", 0))

    findings = findings_data.get("findings", [])

    if not findings:
        st.success("No vulnerabilities found!")
        return

    for i, finding in enumerate(findings):
        severity = finding.get("severity", "LOW")
        severity_color = {
            "CRITICAL": "#ff4757",
            "HIGH": "#ff6b35",
            "MEDIUM": "#ffa502",
            "LOW": "#2ed573",
        }.get(severity, "#a8b2d8")

        with st.expander(
            f"Finding #{i+1} — {finding.get('vuln_type')} [{severity}] "
            f"| {finding.get('file_path')}:{finding.get('line_start')} "
            f"| Confidence: {float(finding.get('confidence', 0)):.0%}",
            expanded=i == 0,
        ):
            col_a, col_b = st.columns(2)

            with col_a:
                st.markdown(f"**Severity:** "
                           f"<span style='color:{severity_color}'>{severity}</span>",
                           unsafe_allow_html=True)
                st.markdown(f"**File:** `{finding.get('file_path')}`")
                st.markdown(f"**Line:** {finding.get('line_start')}")
                st.markdown(f"**CWE:** {finding.get('cwe_id', 'N/A')}")

            with col_b:
                st.markdown(f"**Confidence:** {float(finding.get('confidence', 0)):.0%}")
                st.markdown(f"**Status:** {finding.get('status', 'OPEN')}")
                st.markdown(f"**Type:** {finding.get('vuln_type')}")

            st.markdown("**Description:**")
            st.info(finding.get("description", "No description available"))


def _render_report_summary(report_data: dict):
    """Report summary display karo."""
    st.markdown("## Executive Summary")
    st.info(report_data.get("executive_summary", "No summary available"))

    recommendations = report_data.get("recommendations", [])
    if recommendations:
        st.markdown("## Recommendations")
        for i, rec in enumerate(recommendations, 1):
            st.markdown(f"{i}. {rec}")