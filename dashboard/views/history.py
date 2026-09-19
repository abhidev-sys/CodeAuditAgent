"""Scan History page."""
import streamlit as st
from dashboard.api_client import list_scans, list_repositories
from dashboard.components.states import empty_state, error_state
from dashboard.utils.formatting import (
    fmt_datetime, fmt_status_badge, fmt_risk_level,
    fmt_severity_badge, shorten_id
)


def render_history():
    st.markdown("""
    <div class="page-header">
        <h1>Scan History</h1>
        <p class="subtitle">Review previous security scans and repository security posture.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="content-area">', unsafe_allow_html=True)

    scans_r = list_scans()
    repos_r = list_repositories()

    if not scans_r["success"]:
        error_state("Could not load scan history", scans_r.get("error",""))
        st.markdown('</div>', unsafe_allow_html=True)
        return

    scans = scans_r.get("data", [])

    if not scans:
        empty_state("≡", "No scan history",
                   "Run your first security scan to build your audit trail.",
                   "New Scan", "new_scan")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # Filter bar
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox(
            "Status",
            ["All", "COMPLETED", "RUNNING", "PENDING", "FAILED"],
            label_visibility="collapsed",
        )
    with col2:
        risk_filter = st.selectbox(
            "Risk Level",
            ["All Risk Levels", "CRITICAL", "HIGH", "MEDIUM", "LOW", "SAFE"],
            label_visibility="collapsed",
        )
    with col3:
        search = st.text_input(
            "Search",
            placeholder="Search scan ID...",
            label_visibility="collapsed",
        )

    # Apply filters
    filtered = scans
    if status_filter != "All":
        filtered = [s for s in filtered if s.get("status") == status_filter]
    if risk_filter != "All Risk Levels":
        filtered = [
            s for s in filtered
            if fmt_risk_level(s.get("risk_score",0))[0] == risk_filter
        ]
    if search:
        filtered = [s for s in filtered if search.lower() in str(s.get("id","")).lower()]

    st.markdown(f"""
    <div style="font-size:12px;color:#6e7681;margin:12px 0;">
        Showing {len(filtered)} of {len(scans)} scans
    </div>
    """, unsafe_allow_html=True)

    # Table
    st.markdown("""
    <table class="caa-table">
    <thead><tr>
        <th>Scan ID</th>
        <th>Status</th>
        <th>Risk Score</th>
        <th>Risk Level</th>
        <th>Started</th>
        <th>Completed</th>
        <th>Action</th>
    </tr></thead>
    <tbody>
    """, unsafe_allow_html=True)

    for s in filtered:
        risk = s.get("risk_score")
        level, color = fmt_risk_level(risk)
        risk_display = (
            f'<span style="color:{color};font-weight:600;">{risk}</span>'
            if risk is not None else "—"
        )
        st.markdown(f"""
        <tr>
            <td class="mono">{shorten_id(str(s.get('id','')))}...</td>
            <td>{fmt_status_badge(s.get('status','PENDING'))}</td>
            <td>{risk_display}</td>
            <td><span style="color:{color};font-size:12px;font-weight:500;">{level}</span></td>
            <td class="mono">{fmt_datetime(s.get('started_at'))}</td>
            <td class="mono">{fmt_datetime(s.get('completed_at'))}</td>
            <td>—</td>
        </tr>
        """, unsafe_allow_html=True)

    st.markdown("</tbody></table>", unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # Click to load scan
    st.markdown('<p class="section-header">Load a Scan</p>', unsafe_allow_html=True)
    for s in filtered[:5]:
        if s.get("status") == "COMPLETED":
            col1, col2 = st.columns([5,1])
            with col1:
                risk = s.get("risk_score",0)
                level, color = fmt_risk_level(risk)
                st.markdown(f"""
                <span style="font-family:'JetBrains Mono',monospace;font-size:12px;color:#58a6ff;">
                    {str(s.get('id',''))[:16]}...
                </span>
                &nbsp;
                <span style="color:{color};font-size:12px;">{risk}/100 {level}</span>
                """, unsafe_allow_html=True)
            with col2:
                if st.button("View", key=f"hist_view_{s['id']}", use_container_width=True):
                    st.session_state["selected_scan_id"] = s["id"]
                    st.session_state["page"] = "scan_results"
                    st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)