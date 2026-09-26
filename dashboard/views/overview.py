"""Security Command Center — main dashboard page."""

import streamlit as st

from dashboard.api_client import (
    list_repositories,
    list_scans,
    get_findings,
)

from dashboard.components.cards import metric_card, risk_card
from dashboard.components.states import empty_state, error_state

from dashboard.utils.formatting import (
    fmt_datetime,
    fmt_status_badge,
    fmt_risk_level,
    shorten_id,
)


# ============================================================
# MAIN PAGE
# ============================================================

def render_overview():

    st.markdown(
        """
        <div class="page-header">
            <h1>Security Command Center</h1>
            <p class="subtitle">
                Real-time visibility into repository security,
                vulnerability exposure, scan activity, and risk posture.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.container():

        st.markdown(
            '<div class="content-area">',
            unsafe_allow_html=True,
        )

        # Load data once for this page
        repos_r = list_repositories()
        scans_r = list_scans()

        repos = (
            repos_r.get("data", [])
            if repos_r.get("success")
            else []
        )

        scans = (
            scans_r.get("data", [])
            if scans_r.get("success")
            else []
        )

        # ----------------------------------------------------
        # Backend status
        # ----------------------------------------------------

        if not repos_r.get("success") and not scans_r.get("success"):

            error_state(
                "Security API is unavailable",
                "Start the FastAPI backend on port 9000 and refresh the dashboard.",
            )

            st.markdown("</div>", unsafe_allow_html=True)
            return

        # ----------------------------------------------------
        # Dashboard sections
        # ----------------------------------------------------

        _render_platform_metrics(repos, scans)

        st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

        _render_security_posture(scans)

        st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

        _render_recent_scans(scans)

        st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# PLATFORM METRICS
# ============================================================

def _render_platform_metrics(repos, scans):

    completed = [
        s for s in scans
        if s.get("status") == "COMPLETED"
    ]

    failed = [
        s for s in scans
        if s.get("status") == "FAILED"
    ]

    running = [
        s for s in scans
        if s.get("status") in ["RUNNING", "PENDING"]
    ]

    risk_scores = [
        s.get("risk_score")
        for s in completed
        if s.get("risk_score") is not None
    ]

    avg_risk = (
        int(sum(risk_scores) / len(risk_scores))
        if risk_scores
        else 0
    )

    # Latest completed scan
    latest = _latest_completed_scan(completed)

    latest_risk = (
        latest.get("risk_score")
        if latest
        else None
    )

    # Get findings for latest completed scan
    findings = []

    if latest:

        scan_id = latest.get("id")

        if scan_id:

            findings_r = get_findings(str(scan_id))

            if findings_r.get("success"):

                raw = findings_r.get("data", [])

                findings = _normalize_findings(raw)

    total_findings = len(findings)

    st.markdown(
        '<p class="section-header">Platform Overview</p>',
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        metric_card(
            "Repositories",
            len(repos),
            "Total ingested",
            "📁",
        )

    with c2:
        metric_card(
            "Total Scans",
            len(scans),
            f"{len(running)} active"
            if running
            else "All-time",
            "◎",
        )

    with c3:
        metric_card(
            "Vulnerabilities",
            total_findings,
            "Latest completed scan",
            "⚠",
        )

    with c4:
        level = fmt_risk_level(avg_risk)[0]

        metric_card(
            "Average Risk",
            f"{avg_risk}/100",
            level,
            "⚡",
        )


# ============================================================
# SECURITY POSTURE
# ============================================================

def _render_security_posture(scans):

    completed = [
        s for s in scans
        if s.get("status") == "COMPLETED"
    ]

    latest = _latest_completed_scan(completed)

    st.markdown(
        '<p class="section-header">Security Posture</p>',
        unsafe_allow_html=True,
    )

    if not latest:

        st.markdown(
            """
            <div class="caa-card" style="
                text-align:center;
                padding:40px;
            ">
                <div style="
                    font-size:28px;
                    margin-bottom:10px;
                ">
                    ◉
                </div>

                <div style="
                    font-size:15px;
                    font-weight:600;
                    color:#f4f7fb;
                ">
                    No completed scans
                </div>

                <div style="
                    margin-top:7px;
                    font-size:12px;
                    color:#687386;
                ">
                    Run a security scan to generate your security posture.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        return

    latest_risk = latest.get("risk_score")

    findings = []

    scan_id = latest.get("id")

    if scan_id:

        findings_r = get_findings(str(scan_id))

        if findings_r.get("success"):

            findings = _normalize_findings(
                findings_r.get("data", [])
            )

    critical = _count_severity(findings, "CRITICAL")
    high = _count_severity(findings, "HIGH")
    medium = _count_severity(findings, "MEDIUM")
    low = _count_severity(findings, "LOW")

    left, right = st.columns([1.15, 1])

    # --------------------------------------------------------
    # Risk card
    # --------------------------------------------------------

    with left:

        st.markdown(
            """
            <div style="
                font-size:10px;
                font-weight:700;
                color:#687386;
                text-transform:uppercase;
                letter-spacing:1px;
                margin-bottom:10px;
            ">
                Latest Scan Risk
            </div>
            """,
            unsafe_allow_html=True,
        )

        risk_card(latest_risk)

    # --------------------------------------------------------
    # Threat distribution
    # --------------------------------------------------------

    with right:

        st.markdown(
            """
            <div class="caa-card" style="
                min-height:100%;
            ">
                <div style="
                    font-size:10px;
                    font-weight:700;
                    color:#687386;
                    text-transform:uppercase;
                    letter-spacing:1px;
                    margin-bottom:18px;
                ">
                    Vulnerability Distribution
                </div>
            """,
            unsafe_allow_html=True,
        )

        _severity_row(
            "Critical",
            critical,
            "#ef4444",
            max(critical, high, medium, low, 1),
        )

        _severity_row(
            "High",
            high,
            "#f59e0b",
            max(critical, high, medium, low, 1),
        )

        _severity_row(
            "Medium",
            medium,
            "#eab308",
            max(critical, high, medium, low, 1),
        )

        _severity_row(
            "Low",
            low,
            "#22c55e",
            max(critical, high, medium, low, 1),
        )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )


# ============================================================
# SEVERITY ROW
# ============================================================

def _severity_row(label, count, color, maximum):

    percentage = (
        int((count / maximum) * 100)
        if maximum
        else 0
    )

    st.markdown(
        f"""
        <div style="
            margin-bottom:15px;
        ">

            <div style="
                display:flex;
                justify-content:space-between;
                align-items:center;
                margin-bottom:6px;
            ">

                <div style="
                    display:flex;
                    align-items:center;
                    gap:8px;
                    color:#a7b0c0;
                    font-size:11px;
                ">

                    <span style="
                        width:7px;
                        height:7px;
                        border-radius:50%;
                        background:{color};
                        box-shadow:0 0 8px {color};
                    "></span>

                    {label}

                </div>

                <div style="
                    color:#f4f7fb;
                    font-size:11px;
                    font-weight:700;
                    font-family:'JetBrains Mono',monospace;
                ">
                    {count}
                </div>

            </div>

            <div style="
                height:5px;
                width:100%;
                background:rgba(255,255,255,.055);
                border-radius:99px;
                overflow:hidden;
            ">

                <div style="
                    height:100%;
                    width:{percentage}%;
                    background:{color};
                    border-radius:99px;
                "></div>

            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# RECENT SCANS
# ============================================================

def _render_recent_scans(scans):

    st.markdown(
        '<p class="section-header">Recent Security Activity</p>',
        unsafe_allow_html=True,
    )

    if not scans:

        empty_state(
            "◎",
            "No scans yet",
            "Run your first security scan to start analyzing repositories.",
            "Start New Scan",
            "new_scan",
        )

        return

    # --------------------------------------------------------
    # Header
    # --------------------------------------------------------

    st.markdown(
        """
        <table class="caa-table">
            <thead>
                <tr>
                    <th>Repository</th>
                    <th>Scan ID</th>
                    <th>Status</th>
                    <th>Risk</th>
                    <th>Started</th>
                    <th>Completed</th>
                </tr>
            </thead>
            <tbody>
        """,
        unsafe_allow_html=True,
    )

    rows = ""

    for scan in scans[:8]:

        repository = str(
            scan.get("repository_id", "—")
        )

        scan_id = str(
            scan.get("id", "")
        )

        status = scan.get(
            "status",
            "PENDING",
        )

        risk = scan.get("risk_score")

        if risk is not None:

            level, color = fmt_risk_level(risk)

            risk_display = (
                f"""
                <span style="
                    color:{color};
                    font-weight:700;
                ">
                    {risk}
                </span>
                <span style="
                    color:#687386;
                    font-size:10px;
                ">
                    /100
                </span>
                """
            )

        else:

            risk_display = "—"

        rows += f"""
            <tr>

                <td style="
                    color:#e6edf3;
                    font-weight:600;
                ">
                    {repository[:14]}
                    {"..." if len(repository) > 14 else ""}
                </td>

                <td class="mono">
                    {shorten_id(scan_id)}
                </td>

                <td>
                    {fmt_status_badge(status)}
                </td>

                <td>
                    {risk_display}
                </td>

                <td class="mono">
                    {fmt_datetime(scan.get("started_at"))}
                </td>

                <td class="mono">
                    {fmt_datetime(scan.get("completed_at"))}
                </td>

            </tr>
        """

    st.markdown(
        rows + """
            </tbody>
        </table>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        "<div style='height:14px'></div>",
        unsafe_allow_html=True,
    )

    if st.button(
        "View Full Scan History →",
        key="overview_history",
    ):

        st.session_state["page"] = "history"

        st.rerun()


# ============================================================
# HELPERS
# ============================================================

def _latest_completed_scan(scans):

    if not scans:
        return None

    return max(
        scans,
        key=lambda x: (
            x.get("completed_at")
            or x.get("created_at")
            or ""
        ),
    )


def _normalize_findings(raw):

    if raw is None:
        return []

    # API may return a direct list
    if isinstance(raw, list):
        return raw

    # Or a wrapped response
    if isinstance(raw, dict):

        for key in [
            "findings",
            "data",
            "results",
            "items",
        ]:

            value = raw.get(key)

            if isinstance(value, list):
                return value

    return []


def _count_severity(findings, severity):

    count = 0

    for finding in findings:

        if not isinstance(finding, dict):
            continue

        value = (
            finding.get("severity")
            or finding.get("risk_level")
            or finding.get("level")
            or ""
        )

        if str(value).upper() == severity:
            count += 1

    return count