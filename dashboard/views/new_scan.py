"""New Scan — God Level UI."""

import time
import streamlit as st
from dashboard.api_client import (
    ingest_repository, start_scan,
    get_scan_status, get_findings, get_report,
)


def render_new_scan():
    st.markdown("""
    <div class="section-header">
        <span class="section-title">[ NEW SECURITY SCAN ]</span>
        <div class="section-line"></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="terminal-box" style="margin-bottom: 20px;">
        <div class="terminal-line terminal-info">$ codeaudit scan --target /path/to/repo</div>
        <div class="terminal-line terminal-success">✓ Initializing AI security agents...</div>
        <div class="terminal-line terminal-warn">⚡ Model: openai/gpt-oss-120b (120B params)</div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("scan_form"):
        col1, col2 = st.columns([3, 1])
        with col1:
            repo_path = st.text_input(
                "Repository Path",
                placeholder="R:/codeauditagent/test_repo",
                label_visibility="visible",
            )
        with col2:
            repo_name = st.text_input(
                "Name (optional)",
                placeholder="my-app",
            )

        submitted = st.form_submit_button(
            "⚡  LAUNCH SECURITY SCAN",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        if not repo_path:
            st.error("[ ERROR ] Repository path is required!")
            return
        _run_scan_flow(repo_path, repo_name)


def _run_scan_flow(repo_path: str, repo_name: str):
    """Scan flow with god level UI."""

    # Steps definition
    steps = [
        ("📁", "Repository Ingestion", "Parsing files, detecting language..."),
        ("🌳", "Code Intelligence", "Building AST, tracing data flow..."),
        ("🔍", "Static Analysis", "Running Bandit + custom patterns..."),
        ("🧠", "AI Vulnerability Detection", "LLM agents analyzing code..."),
        ("🔧", "Patch Generation", "Generating secure fixes..."),
        ("📋", "Report Generation", "Building audit report..."),
    ]

    steps_placeholder = st.empty()

    def render_steps(current_step, status="running"):
        steps_html = ""
        for i, (icon, title, desc) in enumerate(steps):
            if i < current_step:
                cls = "step-done"
                prefix = "✓"
            elif i == current_step:
                cls = f"step-{status}"
                prefix = "►" if status == "running" else "✗"
            else:
                cls = "step-pending"
                prefix = "○"

            steps_html += f"""
            <div class="step-item {cls}">
                <span>{icon}</span>
                <span>{prefix} {title}</span>
                <span style="color: #333; font-size: 0.75rem; margin-left: auto;">{desc}</span>
            </div>
            """

        steps_placeholder.markdown(f"""
        <div style="background: #111; border-radius: 12px; padding: 16px; border: 1px solid #1a1a1a;">
            <div style="font-family: 'JetBrains Mono'; font-size: 0.7rem; color: #444; margin-bottom: 12px; letter-spacing: 2px;">
                [ SCAN PIPELINE ]
            </div>
            {steps_html}
        </div>
        """, unsafe_allow_html=True)

    # Step 0: Ingest
    render_steps(0)
    result = ingest_repository(repo_path, repo_name)

    if not result["success"]:
        render_steps(0, "failed")
        st.error(f"[ FAILED ] {result['error']}")
        return

    repo_data = result["data"]
    repo_id = repo_data["repository"]["id"]

    # Show repo info
    st.markdown(f"""
    <div class="terminal-box" style="margin: 12px 0;">
        <div class="terminal-line terminal-success">✓ Repository: {repo_data['repository']['name']}</div>
        <div class="terminal-line terminal-info">  Language  : {repo_data['repository'].get('language', 'N/A')}</div>
        <div class="terminal-line terminal-info">  Frameworks: {', '.join(repo_data.get('frameworks', []))}</div>
        <div class="terminal-line terminal-info">  Files     : {repo_data.get('analyzable_files', 0)} analyzable</div>
        <div class="terminal-line terminal-info">  ID        : {repo_id}</div>
    </div>
    """, unsafe_allow_html=True)

    # Step 1: Start scan
    render_steps(1)
    scan_result = start_scan(repo_id)

    if not scan_result["success"]:
        render_steps(1, "failed")
        st.error(f"[ FAILED ] {scan_result['error']}")
        return

    scan_id = scan_result["data"]["id"]
    st.session_state["current_scan_id"] = scan_id

    st.markdown(f"""
    <div class="terminal-box" style="margin: 12px 0;">
        <div class="terminal-line terminal-success">✓ Scan initiated</div>
        <div class="terminal-line terminal-info">  Scan ID: {scan_id}</div>
        <div class="terminal-line terminal-warn">  Status : RUNNING</div>
    </div>
    """, unsafe_allow_html=True)

    # Poll status
    max_wait = 180
    waited = 0
    current_step = 2

    log_placeholder = st.empty()

    while waited < max_wait:
        status_result = get_scan_status(scan_id)

        if not status_result["success"]:
            st.error("Failed to get status")
            return

        scan_status = status_result["data"]["status"]

        log_placeholder.markdown(f"""
        <div class="terminal-box">
            <div class="terminal-line terminal-warn">
                ⚡ {scan_status} — {status_result['data'].get('message', '')}
            </div>
            <div class="terminal-line terminal-info">
                ⏱  Elapsed: {waited}s
            </div>
        </div>
        """, unsafe_allow_html=True)

        if scan_status == "COMPLETED":
            render_steps(len(steps) - 1)
            log_placeholder.empty()
            break
        elif scan_status == "FAILED":
            render_steps(current_step, "failed")
            st.error(f"[ FAILED ] {status_result['data'].get('error_message')}")
            return

        # Update step visualization
        if waited > 10 and current_step < 3:
            current_step = 3
        elif waited > 20 and current_step < 4:
            current_step = 4
        elif waited > 30 and current_step < 5:
            current_step = 5

        render_steps(current_step)
        time.sleep(3)
        waited += 3
    else:
        st.error("[ TIMEOUT ] Scan exceeded time limit")
        return

    # SUCCESS
    risk_score = status_result["data"].get("risk_score", 0)
    _render_results(scan_id, risk_score)


def _render_results(scan_id: str, risk_score: int):
    """Results render karo."""

    st.markdown("---")

    # Risk score
    _render_risk_box(risk_score)

    # Findings
    findings_result = get_findings(scan_id)
    if findings_result["success"]:
        _render_findings_section(findings_result["data"])

    # Report
    report_result = get_report(scan_id)
    if report_result["success"]:
        _render_recommendations(report_result["data"])

    st.session_state["selected_scan_id"] = scan_id


def _render_risk_box(risk_score: int):
    """Risk score box."""
    if risk_score >= 75:
        color = "#ff4757"
        level = "CRITICAL RISK"
        glow = "#ff475730"
    elif risk_score >= 50:
        color = "#ff6b35"
        level = "HIGH RISK"
        glow = "#ff6b3530"
    elif risk_score >= 25:
        color = "#ffa502"
        level = "MEDIUM RISK"
        glow = "#ffa50230"
    elif risk_score > 0:
        color = "#2ed573"
        level = "LOW RISK"
        glow = "#2ed57330"
    else:
        color = "#00ff41"
        level = "SECURE"
        glow = "#00ff4130"

    st.markdown(f"""
    <div style="
        background: #111;
        border: 1px solid {color}40;
        border-radius: 16px;
        padding: 30px;
        text-align: center;
        margin: 16px 0;
        box-shadow: 0 0 40px {glow};
    ">
        <div style="
            font-size: 5rem;
            font-weight: 900;
            color: {color};
            font-family: 'JetBrains Mono', monospace;
            line-height: 1;
            text-shadow: 0 0 40px {color}60;
        ">{risk_score}<span style="font-size: 2rem; color: #333;">/100</span></div>
        <div style="
            display: inline-block;
            padding: 6px 24px;
            border-radius: 20px;
            background: {color}20;
            border: 1px solid {color}40;
            color: {color};
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.85rem;
            font-weight: 700;
            letter-spacing: 3px;
            margin-top: 12px;
        ">{level}</div>
    </div>
    """, unsafe_allow_html=True)


def _render_findings_section(findings_data: dict):
    """Findings section."""
    st.markdown("""
    <div class="section-header">
        <span class="section-title">[ VULNERABILITIES ]</span>
        <div class="section-line"></div>
    </div>
    """, unsafe_allow_html=True)

    # Counts
    counts_html = f"""
    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 16px 0;">
        <div style="background: #ff475710; border: 1px solid #ff475740; border-radius: 8px; padding: 16px; text-align: center;">
            <div style="font-size: 2rem; font-weight: 700; color: #ff4757; font-family: 'JetBrains Mono';">{findings_data.get('critical', 0)}</div>
            <div style="font-size: 0.7rem; color: #666; letter-spacing: 2px; margin-top: 4px;">CRITICAL</div>
        </div>
        <div style="background: #ff6b3510; border: 1px solid #ff6b3540; border-radius: 8px; padding: 16px; text-align: center;">
            <div style="font-size: 2rem; font-weight: 700; color: #ff6b35; font-family: 'JetBrains Mono';">{findings_data.get('high', 0)}</div>
            <div style="font-size: 0.7rem; color: #666; letter-spacing: 2px; margin-top: 4px;">HIGH</div>
        </div>
        <div style="background: #ffa50210; border: 1px solid #ffa50240; border-radius: 8px; padding: 16px; text-align: center;">
            <div style="font-size: 2rem; font-weight: 700; color: #ffa502; font-family: 'JetBrains Mono';">{findings_data.get('medium', 0)}</div>
            <div style="font-size: 0.7rem; color: #666; letter-spacing: 2px; margin-top: 4px;">MEDIUM</div>
        </div>
        <div style="background: #2ed57310; border: 1px solid #2ed57340; border-radius: 8px; padding: 16px; text-align: center;">
            <div style="font-size: 2rem; font-weight: 700; color: #2ed573; font-family: 'JetBrains Mono';">{findings_data.get('low', 0)}</div>
            <div style="font-size: 0.7rem; color: #666; letter-spacing: 2px; margin-top: 4px;">LOW</div>
        </div>
    </div>
    """
    st.markdown(counts_html, unsafe_allow_html=True)

    findings = findings_data.get("findings", [])
    if not findings:
        st.markdown("""
        <div style="text-align: center; padding: 40px; color: #00ff41; font-family: 'JetBrains Mono';">
            ✓ NO VULNERABILITIES DETECTED — CODE IS SECURE
        </div>
        """, unsafe_allow_html=True)
        return

    for i, finding in enumerate(findings):
        severity = finding.get("severity", "LOW")
        severity_colors = {
            "CRITICAL": "#ff4757",
            "HIGH": "#ff6b35",
            "MEDIUM": "#ffa502",
            "LOW": "#2ed573",
        }
        color = severity_colors.get(severity, "#666")

        with st.expander(
            f"  [{severity}] {finding.get('vuln_type')}  |  "
            f"{finding.get('file_path')}:{finding.get('line_start')}  |  "
            f"Confidence: {float(finding.get('confidence', 0)):.0%}",
            expanded=True,
        ):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"""
                <div class="terminal-box">
                    <div class="terminal-line"><span style="color:#555">TYPE      </span> <span style="color:{color}">{finding.get('vuln_type')}</span></div>
                    <div class="terminal-line"><span style="color:#555">SEVERITY  </span> <span style="color:{color}">{severity}</span></div>
                    <div class="terminal-line"><span style="color:#555">CONFIDENCE</span> <span style="color:#00ff41">{float(finding.get('confidence', 0)):.0%}</span></div>
                    <div class="terminal-line"><span style="color:#555">FILE      </span> <span style="color:#00b4d8">{finding.get('file_path')}</span></div>
                    <div class="terminal-line"><span style="color:#555">LINE      </span> <span style="color:#00b4d8">{finding.get('line_start')}</span></div>
                    <div class="terminal-line"><span style="color:#555">CWE       </span> <span style="color:#ffa502">{finding.get('cwe_id', 'N/A')}</span></div>
                    <div class="terminal-line"><span style="color:#555">STATUS    </span> <span style="color:#ff4757">{finding.get('status', 'OPEN')}</span></div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                <div style="background: #0a0a0a; border: 1px solid #1a1a1a; border-radius: 8px; padding: 16px; height: 100%;">
                    <div style="font-family: 'JetBrains Mono'; font-size: 0.7rem; color: #444; margin-bottom: 8px; letter-spacing: 2px;">[ AI ANALYSIS ]</div>
                    <div style="color: #aaa; font-size: 0.85rem; line-height: 1.6;">
                        {finding.get('description', 'No description available')}
                    </div>
                </div>
                """, unsafe_allow_html=True)


def _render_recommendations(report_data: dict):
    """Recommendations section."""
    st.markdown("""
    <div class="section-header">
        <span class="section-title">[ RECOMMENDATIONS ]</span>
        <div class="section-line"></div>
    </div>
    """, unsafe_allow_html=True)

    recs = report_data.get("recommendations", [])
    for i, rec in enumerate(recs, 1):
        st.markdown(f"""
        <div class="rec-item">
            <span class="rec-number">{i:02d}</span>
            <span>{rec}</span>
        </div>
        """, unsafe_allow_html=True)

    # Executive summary
    st.markdown("""
    <div class="section-header">
        <span class="section-title">[ EXECUTIVE SUMMARY ]</span>
        <div class="section-line"></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="
        background: #111;
        border: 1px solid #1a1a1a;
        border-radius: 8px;
        padding: 16px;
        color: #aaa;
        font-size: 0.9rem;
        line-height: 1.7;
        border-left: 3px solid #00ff41;
    ">
        {report_data.get('executive_summary', 'No summary available')}
    </div>
    """, unsafe_allow_html=True)