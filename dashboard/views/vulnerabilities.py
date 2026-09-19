"""Vulnerability Management page."""
import streamlit as st
from dashboard.api_client import list_scans, get_findings
from dashboard.components.states import empty_state, error_state
from dashboard.utils.formatting import (
    fmt_severity_badge, fmt_confidence, fmt_datetime, shorten_id
)


def render_vulnerabilities():
    st.markdown("""
    <div class="page-header">
        <h1>Vulnerability Management</h1>
        <p class="subtitle">Centralized view of all detected security vulnerabilities across repositories.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="content-area">', unsafe_allow_html=True)

    # Load all findings from completed scans
    scans_r = list_scans()
    if not scans_r["success"]:
        error_state("Could not load data", scans_r.get("error",""))
        st.markdown('</div>', unsafe_allow_html=True)
        return

    scans = scans_r.get("data", [])
    completed = [s for s in scans if s.get("status") == "COMPLETED"]

    if not completed:
        empty_state("⚑", "No vulnerability data",
                   "Complete a security scan to populate this view.",
                   "New Scan", "new_scan")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    all_findings = []
    for scan in completed[:5]:  # Last 5 scans
        findings_r = get_findings(str(scan["id"]))
        if findings_r["success"]:
            for f in findings_r["data"].get("findings", []):
                f["_scan_id"] = str(scan["id"])
                all_findings.append(f)

    if not all_findings:
        empty_state("✓", "No vulnerabilities found",
                   "All scanned repositories appear clean.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # Counts
    critical = sum(1 for f in all_findings if f.get("severity")=="CRITICAL")
    high     = sum(1 for f in all_findings if f.get("severity")=="HIGH")
    medium   = sum(1 for f in all_findings if f.get("severity")=="MEDIUM")
    low      = sum(1 for f in all_findings if f.get("severity")=="LOW")

    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: st.metric("Total",    len(all_findings))
    with c2: st.metric("Critical", critical)
    with c3: st.metric("High",     high)
    with c4: st.metric("Medium",   medium)
    with c5: st.metric("Low",      low)

    # Filters
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        sev_filter = st.selectbox(
            "Severity",
            ["All Severities","CRITICAL","HIGH","MEDIUM","LOW"],
            label_visibility="collapsed",
        )
    with col2:
        type_filter = st.selectbox(
            "Type",
            ["All Types"] + list({f.get("vuln_type","") for f in all_findings}),
            label_visibility="collapsed",
        )

    filtered = all_findings
    if sev_filter != "All Severities":
        filtered = [f for f in filtered if f.get("severity") == sev_filter]
    if type_filter != "All Types":
        filtered = [f for f in filtered if f.get("vuln_type") == type_filter]

    st.markdown(f"""
    <div style="font-size:12px;color:#6e7681;margin:12px 0;">
        {len(filtered)} vulnerabilities
    </div>
    """, unsafe_allow_html=True)

    # Table
    st.markdown("""
    <table class="caa-table">
    <thead><tr>
        <th>Severity</th>
        <th>Type</th>
        <th>File</th>
        <th>Line</th>
        <th>CWE</th>
        <th>Confidence</th>
        <th>Status</th>
    </tr></thead>
    <tbody>
    """, unsafe_allow_html=True)

    for f in filtered:
        st.markdown(f"""
        <tr>
            <td>{fmt_severity_badge(f.get('severity','LOW'))}</td>
            <td style="font-family:'JetBrains Mono',monospace;font-size:12px;
                color:#e6edf3;">{f.get('vuln_type','N/A')}</td>
            <td style="font-family:'JetBrains Mono',monospace;font-size:12px;
                color:#8b949e;">{f.get('file_path','N/A')}</td>
            <td style="font-family:'JetBrains Mono',monospace;font-size:12px;
                color:#6e7681;">{f.get('line_start','—')}</td>
            <td style="font-family:'JetBrains Mono',monospace;font-size:12px;
                color:#58a6ff;">{f.get('cwe_id','N/A')}</td>
            <td style="color:#e6edf3;">{fmt_confidence(f.get('confidence'))}</td>
            <td><span class="badge badge-high">{f.get('status','OPEN')}</span></td>
        </tr>
        """, unsafe_allow_html=True)

    st.markdown("</tbody></table>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)