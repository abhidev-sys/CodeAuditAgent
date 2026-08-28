"""Scan Results page — Detailed view of a specific scan."""

import streamlit as st
from dashboard.api_client import (
    get_scan_status,
    get_findings,
    get_report,
    list_scans,
)


def render_scan_results():
    """Scan results page render karo."""
    st.markdown("## Scan Results")

    # Scan ID input
    scan_id = st.session_state.get("selected_scan_id", "")

    col1, col2 = st.columns([4, 1])
    with col1:
        scan_id_input = st.text_input(
            "Scan ID",
            value=scan_id,
            placeholder="Enter scan UUID...",
        )
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        load_btn = st.button("Load Results", type="primary", use_container_width=True)

    if scan_id_input:
        scan_id = scan_id_input

    if not scan_id:
        st.info("Enter a Scan ID or run a new scan from the 'New Scan' page.")

        # Show recent scans
        st.markdown("### Recent Scans")
        scans_result = list_scans()
        if scans_result["success"]:
            scans = scans_result["data"]
            for scan in scans[:10]:
                col_a, col_b, col_c = st.columns([3, 2, 2])
                with col_a:
                    st.text(f"ID: {scan['id'][:16]}...")
                with col_b:
                    status = scan.get("status", "N/A")
                    emoji = {"COMPLETED": "✅", "RUNNING": "🔄", "PENDING": "⏳", "FAILED": "❌"}.get(status, "❓")
                    st.text(f"{emoji} {status}")
                with col_c:
                    if st.button("Load", key=f"load_{scan['id']}"):
                        st.session_state["selected_scan_id"] = scan["id"]
                        st.rerun()
        return

    # Load scan data
    with st.spinner("Loading scan data..."):
        status_result = get_scan_status(scan_id)

    if not status_result["success"]:
        st.error(f"Scan not found: {scan_id}")
        return

    scan_data = status_result["data"]
    status = scan_data.get("status")

    # Status header
    _render_status_header(scan_id, scan_data)

    if status != "COMPLETED":
        if status == "RUNNING":
            st.warning("🔄 Scan is still running — refresh to check progress")
            if st.button("Refresh"):
                st.rerun()
        elif status == "FAILED":
            st.error(f"❌ Scan failed: {scan_data.get('error_message', 'Unknown error')}")
        else:
            st.info(f"⏳ Scan status: {status}")
        return

    # Tabs for detailed view
    tab1, tab2, tab3 = st.tabs(["🔍 Findings", "📄 Report", "📊 Summary"])

    with tab1:
        _render_detailed_findings(scan_id)

    with tab2:
        _render_full_report(scan_id)

    with tab3:
        _render_summary(scan_id, scan_data)


def _render_status_header(scan_id: str, scan_data: dict):
    """Scan status header render karo."""
    status = scan_data.get("status")
    risk_score = scan_data.get("risk_score", 0)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Scan ID", f"{scan_id[:8]}...")

    with col2:
        status_display = {
            "COMPLETED": "✅ Completed",
            "RUNNING": "🔄 Running",
            "PENDING": "⏳ Pending",
            "FAILED": "❌ Failed",
        }.get(status, status)
        st.metric("Status", status_display)

    with col3:
        if risk_score is not None:
            st.metric("Risk Score", f"{risk_score}/100")
        else:
            st.metric("Risk Score", "N/A")

    with col4:
        completed_at = scan_data.get("completed_at")
        if completed_at:
            st.metric("Completed", completed_at[:10])


def _render_detailed_findings(scan_id: str):
    """Detailed findings render karo."""
    findings_result = get_findings(scan_id)

    if not findings_result["success"]:
        st.error(f"Could not load findings: {findings_result['error']}")
        return

    findings_data = findings_result["data"]
    findings = findings_data.get("findings", [])

    # Counts
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total", findings_data.get("total", 0))
    with col2:
        st.metric("Critical 🔴", findings_data.get("critical", 0))
    with col3:
        st.metric("High 🟠", findings_data.get("high", 0))
    with col4:
        st.metric("Medium 🟡", findings_data.get("medium", 0))
    with col5:
        st.metric("Low 🟢", findings_data.get("low", 0))

    if not findings:
        st.success("🎉 No vulnerabilities found! Your code is clean.")
        return

    st.markdown("---")

    for i, finding in enumerate(findings):
        severity = finding.get("severity", "LOW")
        vuln_type = finding.get("vuln_type", "UNKNOWN")
        confidence = float(finding.get("confidence", 0))
        file_path = finding.get("file_path", "")
        line = finding.get("line_start", 0)

        severity_emoji = {
            "CRITICAL": "🔴",
            "HIGH": "🟠",
            "MEDIUM": "🟡",
            "LOW": "🟢",
        }.get(severity, "⚪")

        with st.expander(
            f"{severity_emoji} Finding #{i+1} — **{vuln_type}** [{severity}] "
            f"| `{file_path}:{line}` | {confidence:.0%} confidence",
            expanded=True,
        ):
            col_left, col_right = st.columns(2)

            with col_left:
                st.markdown("#### Vulnerability Details")
                st.markdown(f"- **Type:** `{vuln_type}`")
                st.markdown(f"- **Severity:** {severity_emoji} {severity}")
                st.markdown(f"- **Confidence:** {confidence:.0%}")
                st.markdown(f"- **File:** `{file_path}`")
                st.markdown(f"- **Line:** {line}")
                st.markdown(f"- **CWE:** `{finding.get('cwe_id', 'N/A')}`")
                st.markdown(f"- **Status:** {finding.get('status', 'OPEN')}")

            with col_right:
                st.markdown("#### AI Analysis")
                st.info(finding.get("description", "No description"))

            # Code snippet
            if finding.get("code_snippet"):
                st.markdown("#### Vulnerable Code")
                st.code(finding.get("code_snippet", ""), language="python")


def _render_full_report(scan_id: str):
    """Full report render karo."""
    report_result = get_report(scan_id)

    if not report_result["success"]:
        st.error(f"Could not load report: {report_result['error']}")
        return

    report = report_result["data"]

    # Report header
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Report ID", report.get("report_id", "N/A"))
    with col2:
        st.metric("Risk Score", f"{report.get('risk_score', 0)}/100")
    with col3:
        st.metric("Risk Level", report.get("risk_level", "N/A"))

    st.markdown("---")

    # Executive Summary
    st.markdown("### Executive Summary")
    st.info(report.get("executive_summary", "No summary"))

    st.markdown("---")

    # Findings with patches
    findings = report.get("findings", [])
    if findings:
        st.markdown("### Detailed Findings with Patches")

        for finding in findings:
            severity = finding.get("severity", "LOW")
            severity_emoji = {
                "CRITICAL": "🔴", "HIGH": "🟠",
                "MEDIUM": "🟡", "LOW": "🟢"
            }.get(severity, "⚪")

            with st.expander(
                f"{severity_emoji} {finding.get('vuln_type')} — "
                f"{finding.get('file_path')}:{finding.get('line_start')}",
                expanded=True,
            ):
                st.markdown(f"**Description:** {finding.get('description', '')}")
                st.markdown(f"**CWE:** {finding.get('cwe_id', 'N/A')} — "
                           f"{finding.get('cwe_description', '')}")

                if finding.get("patch_available"):
                    st.success("✅ Patch Available")
                    diff = finding.get("unified_diff", "")
                    if diff:
                        st.markdown("**Unified Diff:**")
                        st.code(diff, language="diff")
                else:
                    st.warning("⚠️ No automated patch available")

    st.markdown("---")

    # Recommendations
    recs = report.get("recommendations", [])
    if recs:
        st.markdown("### Recommendations")
        for i, rec in enumerate(recs, 1):
            st.markdown(f"{i}. {rec}")


def _render_summary(scan_id: str, scan_data: dict):
    """Summary charts render karo."""
    report_result = get_report(scan_id)

    if not report_result["success"]:
        st.error("Could not load report data")
        return

    report = report_result["data"]
    findings_summary = report.get("findings_summary", {})
    patch_summary = report.get("patch_summary", {})

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Findings Breakdown")
        import pandas as pd

        severity_data = {
            "Severity": ["Critical", "High", "Medium", "Low"],
            "Count": [
                findings_summary.get("critical", 0),
                findings_summary.get("high", 0),
                findings_summary.get("medium", 0),
                findings_summary.get("low", 0),
            ]
        }
        df = pd.DataFrame(severity_data)
        st.bar_chart(df.set_index("Severity"))

    with col2:
        st.markdown("### Patch Statistics")
        total_patches = patch_summary.get("total", 0)
        successful = patch_summary.get("successful", 0)
        success_rate = patch_summary.get("success_rate", 0)

        st.metric("Total Patches", total_patches)
        st.metric("Successful", successful)
        st.metric("Success Rate", f"{success_rate:.0%}")

        if total_patches > 0:
            st.progress(success_rate)