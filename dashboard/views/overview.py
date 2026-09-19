"""Security Overview — main dashboard page."""
import streamlit as st
from dashboard.api_client import list_repositories, list_scans, get_findings
from dashboard.components.cards import metric_card, risk_card
from dashboard.components.states import empty_state, error_state
from dashboard.utils.formatting import (
    fmt_datetime, fmt_severity_badge, fmt_status_badge,
    fmt_risk_level, shorten_id
)


def render_overview():
    # Page header
    st.markdown("""
    <div class="page-header">
        <h1>Security Overview</h1>
        <p class="subtitle">Monitor repository security, vulnerabilities, scans, and remediation activity.</p>
    </div>
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="content-area">', unsafe_allow_html=True)
        _render_metrics()
        st.markdown("<hr>", unsafe_allow_html=True)
        _render_recent_scans()
        st.markdown("</div>", unsafe_allow_html=True)


def _render_metrics():
    repos_r  = list_repositories()
    scans_r  = list_scans()

    repos = repos_r.get("data", []) if repos_r["success"] else []
    scans = scans_r.get("data", []) if scans_r["success"] else []

    completed = [s for s in scans if s.get("status") == "COMPLETED"]
    failed    = [s for s in scans if s.get("status") == "FAILED"]
    running   = [s for s in scans if s.get("status") in ["RUNNING","PENDING"]]

    risk_scores = [s.get("risk_score",0) for s in completed if s.get("risk_score") is not None]
    avg_risk = int(sum(risk_scores)/len(risk_scores)) if risk_scores else 0

    # Row 1 — scan metrics
    st.markdown('<p class="section-header">Platform Overview</p>', unsafe_allow_html=True)
    c1,c2,c3,c4 = st.columns(4)
    with c1: metric_card("Repositories", len(repos), "Total ingested", "📁")
    with c2: metric_card("Total Scans",  len(scans),
                         f"+{len(running)} active" if running else "All-time", "⊙")
    with c3: metric_card("Completed",    len(completed),
                         f"{len(failed)} failed", "✓")
    with c4: metric_card("Avg Risk Score", f"{avg_risk}/100",
                         fmt_risk_level(avg_risk)[0], "⚡")

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # Risk overview
    if completed:
        latest = max(completed, key=lambda x: x.get("created_at",""))
        latest_risk = latest.get("risk_score", 0)
    else:
        latest_risk = None

    st.markdown('<p class="section-header">Latest Risk Score</p>', unsafe_allow_html=True)
    risk_card(latest_risk)


def _render_recent_scans():
    scans_r = list_scans()

    st.markdown('<p class="section-header">Recent Scans</p>', unsafe_allow_html=True)

    if not scans_r["success"]:
        error_state("Could not load scans", scans_r.get("error",""))
        return

    scans = scans_r.get("data", [])

    if not scans:
        empty_state("⊙", "No scans yet",
                   "Run your first security scan to start analyzing repositories.",
                   "Start New Scan", "new_scan")
        return

    # Table header
    st.markdown("""
    <table class="caa-table">
    <thead><tr>
        <th>Repository</th>
        <th>Scan ID</th>
        <th>Status</th>
        <th>Risk Score</th>
        <th>Started</th>
        <th>Completed</th>
    </tr></thead>
    <tbody>
    """, unsafe_allow_html=True)

    rows = ""
    for s in scans[:10]:
        risk = s.get("risk_score")
        level, color = fmt_risk_level(risk)
        risk_display = (
            f'<span style="color:{color};font-weight:600;">{risk}/100</span> '
            f'<span style="color:#6e7681;font-size:11px;">{level}</span>'
            if risk is not None else "—"
        )
        rows += f"""
        <tr>
            <td style="color:#e6edf3;font-weight:500;">
                {s.get('repository_id','—')[:8]}...
            </td>
            <td class="mono">{shorten_id(str(s.get('id','')))}...</td>
            <td>{fmt_status_badge(s.get('status','PENDING'))}</td>
            <td>{risk_display}</td>
            <td class="mono">{fmt_datetime(s.get('started_at'))}</td>
            <td class="mono">{fmt_datetime(s.get('completed_at'))}</td>
        </tr>
        """

    st.markdown(rows + "</tbody></table>", unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    if st.button("View Full History →", key="overview_history"):
        st.session_state["page"] = "history"
        st.rerun()