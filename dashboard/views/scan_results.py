"""Scan Results — detailed vulnerability analysis workspace."""
import streamlit as st
from dashboard.api_client import get_scan_status, get_findings, get_report, list_scans
from dashboard.components.cards import risk_card
from dashboard.components.states import empty_state, error_state
from dashboard.utils.formatting import (
    fmt_severity_badge, fmt_status_badge, fmt_confidence,
    fmt_datetime, shorten_id, fmt_severity_color
)


def render_scan_results():
    st.markdown("""
    <div class="page-header">
        <h1>Scan Results</h1>
        <p class="subtitle">Vulnerability analysis workspace — findings, patches, and AI reasoning.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="content-area">', unsafe_allow_html=True)

    # Scan selector
    scan_id = st.session_state.get("selected_scan_id", "")

    col1, col2 = st.columns([4, 1])
    with col1:
        scan_id_input = st.text_input(
            "Scan ID",
            value=scan_id,
            placeholder="Enter scan UUID to load results...",
            label_visibility="collapsed",
        )
    with col2:
        load = st.button("Load", type="primary", use_container_width=True)

    if scan_id_input:
        scan_id = scan_id_input
        st.session_state["selected_scan_id"] = scan_id

    if not scan_id:
        _render_scan_selector()
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # Load scan
    status_r = get_scan_status(scan_id)
    if not status_r["success"]:
        error_state("Scan not found", f"ID: {scan_id}")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    scan_data = status_r["data"]
    _render_scan_header(scan_id, scan_data)

    if scan_data.get("status") != "COMPLETED":
        st.info(f"Scan is {scan_data.get('status')} — results available after completion.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # Tabs
    tab1, tab2, tab3 = st.tabs(["Findings", "Report", "Raw Data"])
    with tab1:
        _render_findings_tab(scan_id)
    with tab2:
        _render_report_tab(scan_id)
    with tab3:
        _render_raw_tab(scan_data)

    st.markdown('</div>', unsafe_allow_html=True)


def _render_scan_selector():
    scans_r = list_scans()
    scans = scans_r.get("data", []) if scans_r["success"] else []
    completed = [s for s in scans if s.get("status") == "COMPLETED"]

    if not completed:
        empty_state("◎", "No completed scans",
                   "Start a new scan to analyze your repositories.",
                   "New Scan", "new_scan")
        return

    st.markdown('<p class="section-header">Recent Completed Scans</p>',
               unsafe_allow_html=True)

    for s in completed[:8]:
        risk = s.get("risk_score", 0)
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
        with col1:
            st.markdown(f"""
            <span style="font-family:'JetBrains Mono',monospace;
                font-size:12px;color:#58a6ff;">
                {shorten_id(str(s.get('id','')))}...
            </span>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(
                fmt_status_badge(s.get("status","N/A")),
                unsafe_allow_html=True
            )
        with col3:
            st.markdown(f"""
            <span style="color:#e6edf3;font-size:13px;font-weight:600;">
                {risk}/100
            </span>
            """, unsafe_allow_html=True)
        with col4:
            if st.button("Load", key=f"load_{s['id']}", use_container_width=True):
                st.session_state["selected_scan_id"] = s["id"]
                st.rerun()
        st.markdown("<hr>", unsafe_allow_html=True)


def _render_scan_header(scan_id: str, scan_data: dict):
    risk = scan_data.get("risk_score", 0)

    # Summary bar
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Scan ID", shorten_id(scan_id) + "...")
    with c2:
        st.metric("Status", scan_data.get("status","N/A"))
    with c3:
        st.metric("Risk Score", f"{risk}/100" if risk is not None else "N/A")
    with c4:
        completed = fmt_datetime(scan_data.get("completed_at"))
        st.metric("Completed", completed)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    risk_card(risk)
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)


def _render_findings_tab(scan_id: str):
    findings_r = get_findings(scan_id)

    if not findings_r["success"]:
        error_state("Could not load findings", findings_r.get("error",""))
        return

    data = findings_r["data"]
    findings = data.get("findings", [])

    # Severity summary
    st.markdown('<p class="section-header">Severity Summary</p>',
               unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: st.metric("Total",    data.get("total",0))
    with c2: st.metric("Critical", data.get("critical",0))
    with c3: st.metric("High",     data.get("high",0))
    with c4: st.metric("Medium",   data.get("medium",0))
    with c5: st.metric("Low",      data.get("low",0))

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    if not findings:
        empty_state("✓", "No vulnerabilities detected",
                   "This repository passed all security checks.")
        return

    st.markdown('<p class="section-header">Findings</p>', unsafe_allow_html=True)

    for i, f in enumerate(findings):
        _render_finding_card(f, i)


def _render_finding_card(f: dict, idx: int):
    severity  = f.get("severity", "LOW")
    vuln_type = f.get("vuln_type", "UNKNOWN")
    file_path = f.get("file_path", "")
    line      = f.get("line_start", "")
    conf      = fmt_confidence(f.get("confidence"))
    color     = fmt_severity_color(severity)

    with st.expander(
        f"  {severity}  ·  {vuln_type}  ·  {file_path}:{line}  ·  {conf} confidence",
        expanded=(idx == 0),
    ):
        c1, c2 = st.columns(2)

        with c1:
            st.markdown(f"""
            <div class="caa-card">
                <div style="font-size:11px;color:#6e7681;text-transform:uppercase;
                    letter-spacing:0.8px;font-weight:600;margin-bottom:14px;">
                    Vulnerability Details
                </div>
                <table style="width:100%;font-size:13px;border-collapse:collapse;">
                    <tr>
                        <td style="color:#8b949e;padding:5px 0;width:40%;">Type</td>
                        <td style="color:#e6edf3;font-family:'JetBrains Mono',monospace;">
                            {vuln_type}
                        </td>
                    </tr>
                    <tr>
                        <td style="color:#8b949e;padding:5px 0;">Severity</td>
                        <td>{fmt_severity_badge(severity)}</td>
                    </tr>
                    <tr>
                        <td style="color:#8b949e;padding:5px 0;">Confidence</td>
                        <td style="color:{color};font-weight:600;">{conf}</td>
                    </tr>
                    <tr>
                        <td style="color:#8b949e;padding:5px 0;">CWE</td>
                        <td style="color:#58a6ff;font-family:'JetBrains Mono',monospace;">
                            {f.get('cwe_id','N/A')}
                        </td>
                    </tr>
                    <tr>
                        <td style="color:#8b949e;padding:5px 0;">File</td>
                        <td style="font-family:'JetBrains Mono',monospace;color:#e6edf3;">
                            {file_path}
                        </td>
                    </tr>
                    <tr>
                        <td style="color:#8b949e;padding:5px 0;">Line</td>
                        <td style="font-family:'JetBrains Mono',monospace;color:#e6edf3;">
                            {line}
                        </td>
                    </tr>
                    <tr>
                        <td style="color:#8b949e;padding:5px 0;">Status</td>
                        <td>{fmt_status_badge(f.get('status','OPEN'))}</td>
                    </tr>
                </table>
            </div>
            """, unsafe_allow_html=True)

        with c2:
            st.markdown("""
            <div class="caa-card" style="height:100%;">
                <div style="font-size:11px;color:#6e7681;text-transform:uppercase;
                    letter-spacing:0.8px;font-weight:600;margin-bottom:14px;">
                    AI Security Analysis
                </div>
            """, unsafe_allow_html=True)
            desc = f.get("description", "No description available.")
            st.markdown(f"""
                <div style="font-size:13px;color:#c9d1d9;line-height:1.6;">
                    {desc}
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Code snippet
        if f.get("code_snippet"):
            st.markdown("""
            <div style="font-size:11px;color:#6e7681;text-transform:uppercase;
                letter-spacing:0.8px;font-weight:600;margin:14px 0 8px;">
                Vulnerable Code
            </div>
            """, unsafe_allow_html=True)
            st.code(f.get("code_snippet",""), language="python")


def _render_report_tab(scan_id: str):
    report_r = get_report(scan_id)

    if not report_r["success"]:
        error_state("Report not available", report_r.get("error",""))
        return

    report = report_r["data"]

    # Header
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("Report ID",   report.get("report_id","N/A"))
    with c2: st.metric("Risk Score",  f"{report.get('risk_score',0)}/100")
    with c3: st.metric("Risk Level",  report.get("risk_level","N/A"))

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # Executive Summary
    st.markdown("""
    <div style="font-size:11px;color:#6e7681;text-transform:uppercase;
        letter-spacing:0.8px;font-weight:600;margin-bottom:10px;">
        Executive Summary
    </div>
    """, unsafe_allow_html=True)
    st.markdown(f"""
    <div class="caa-card">
        <div style="font-size:13px;color:#c9d1d9;line-height:1.7;">
            {report.get('executive_summary','No summary available.')}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Findings with patches
    findings = report.get("findings", [])
    if findings:
        st.markdown("""
        <div style="font-size:11px;color:#6e7681;text-transform:uppercase;
            letter-spacing:0.8px;font-weight:600;margin:20px 0 10px;">
            Findings & Patches
        </div>
        """, unsafe_allow_html=True)

        for finding in findings:
            with st.expander(
                f"{finding.get('vuln_type')} — {finding.get('file_path')}:{finding.get('line_start')}",
                expanded=False,
            ):
                st.markdown(f"""
                <div style="font-size:13px;color:#c9d1d9;margin-bottom:12px;">
                    {finding.get('description','')}
                </div>
                <div style="font-size:12px;color:#6e7681;margin-bottom:6px;">
                    <b style="color:#8b949e;">CWE:</b> {finding.get('cwe_id','N/A')}
                    &nbsp;·&nbsp;
                    <b style="color:#8b949e;">Confidence:</b>
                    {fmt_confidence(finding.get('confidence'))}
                </div>
                """, unsafe_allow_html=True)

                if finding.get("patch_available"):
                    st.markdown("""
                    <div style="display:inline-flex;align-items:center;gap:6px;
                        background:rgba(35,134,54,0.1);border:1px solid rgba(35,134,54,0.3);
                        border-radius:6px;padding:5px 12px;font-size:12px;color:#3fb950;
                        margin-bottom:10px;">
                        ✓ Patch Available
                    </div>
                    """, unsafe_allow_html=True)

                    diff = finding.get("unified_diff","")
                    if diff:
                        _render_diff(diff)

    # Recommendations
    recs = report.get("recommendations", [])
    if recs:
        st.markdown("""
        <div style="font-size:11px;color:#6e7681;text-transform:uppercase;
            letter-spacing:0.8px;font-weight:600;margin:20px 0 10px;">
            Recommendations
        </div>
        """, unsafe_allow_html=True)
        for i, rec in enumerate(recs, 1):
            st.markdown(f"""
            <div style="display:flex;gap:12px;padding:10px 0;
                border-bottom:1px solid #21262d;font-size:13px;">
                <span style="color:#6e7681;font-family:'JetBrains Mono',monospace;
                    font-size:11px;padding-top:2px;min-width:24px;">P{i-1}</span>
                <span style="color:#c9d1d9;">{rec}</span>
            </div>
            """, unsafe_allow_html=True)


def _render_diff(diff: str):
    lines = diff.splitlines()
    html = '<div style="background:#0d1117;border:1px solid #21262d;border-radius:6px;padding:12px;overflow-x:auto;">'
    for line in lines:
        if line.startswith("---") or line.startswith("+++"):
            html += f'<span style="color:#6e7681;font-family:JetBrains Mono,monospace;font-size:12px;display:block;">{line}</span>'
        elif line.startswith("-"):
            html += f'<span class="diff-removed">{line}</span>'
        elif line.startswith("+"):
            html += f'<span class="diff-added">{line}</span>'
        elif line.startswith("@@"):
            html += f'<span style="color:#58a6ff;font-family:JetBrains Mono,monospace;font-size:12px;display:block;padding:2px 12px;">{line}</span>'
        else:
            html += f'<span class="diff-context">{line}</span>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def _render_raw_tab(scan_data: dict):
    st.json(scan_data)