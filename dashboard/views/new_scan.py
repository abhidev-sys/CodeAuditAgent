"""New Scan page — professional scan creation workflow."""
import time
import streamlit as st
from dashboard.api_client import ingest_repository, start_scan, get_scan_status
from dashboard.components.states import error_state
from dashboard.utils.formatting import fmt_datetime


def render_new_scan():
    st.markdown("""
    <div class="page-header">
        <h1>New Security Scan</h1>
        <p class="subtitle">
            Analyze a repository using CodeAuditAgent's autonomous security pipeline.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="content-area">', unsafe_allow_html=True)

    # Pipeline info card
    st.markdown("""
    <div class="caa-card" style="margin-bottom:24px;">
        <div style="font-size:12px;color:#6e7681;text-transform:uppercase;
            letter-spacing:0.8px;font-weight:600;margin-bottom:12px;">
            Analysis Pipeline
        </div>
        <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
            <span style="font-size:12px;color:#8b949e;padding:4px 10px;
                background:#21262d;border-radius:4px;">Repository Ingestion</span>
            <span style="color:#6e7681;">→</span>
            <span style="font-size:12px;color:#8b949e;padding:4px 10px;
                background:#21262d;border-radius:4px;">Static Analysis + AST</span>
            <span style="color:#6e7681;">→</span>
            <span style="font-size:12px;color:#8b949e;padding:4px 10px;
                background:#21262d;border-radius:4px;">AI Vulnerability Detection</span>
            <span style="color:#6e7681;">→</span>
            <span style="font-size:12px;color:#8b949e;padding:4px 10px;
                background:#21262d;border-radius:4px;">Patch Generation</span>
            <span style="color:#6e7681;">→</span>
            <span style="font-size:12px;color:#8b949e;padding:4px 10px;
                background:#21262d;border-radius:4px;">Security Report</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Step state
    if "scan_step" not in st.session_state:
        st.session_state["scan_step"] = 1

    step = st.session_state["scan_step"]

    # Step indicator
    _render_steps(step)
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    if step == 1:
        _step_repository()
    elif step == 2:
        _step_running()

    st.markdown('</div>', unsafe_allow_html=True)


def _render_steps(current: int):
    steps = ["Repository", "Scanning", "Results"]
    cols = st.columns(len(steps))
    for i, (col, label) in enumerate(zip(cols, steps), 1):
        with col:
            active = i == current
            done   = i < current
            color  = "#1f6feb" if active else ("#3fb950" if done else "#30363d")
            tc     = "#58a6ff" if active else ("#3fb950" if done else "#8b949e")
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:10px;">
                <div style="width:28px;height:28px;border-radius:50%;
                    background:{color};display:flex;align-items:center;
                    justify-content:center;font-size:12px;font-weight:700;
                    color:{'#fff' if active or done else '#6e7681'};
                    flex-shrink:0;">
                    {'✓' if done else i}
                </div>
                <div style="font-size:13px;font-weight:{'600' if active else '400'};
                    color:{tc};">{label}</div>
            </div>
            """, unsafe_allow_html=True)


def _step_repository():
    with st.form("repo_form"):
        st.markdown('<div class="caa-card">', unsafe_allow_html=True)
        st.markdown("""
        <div style="font-size:12px;color:#6e7681;text-transform:uppercase;
            letter-spacing:0.8px;font-weight:600;margin-bottom:16px;">
            Repository Configuration
        </div>
        """, unsafe_allow_html=True)

        repo_path = st.text_input(
            "Repository Path *",
            placeholder="R:/path/to/your/repository",
            help="Absolute local path to the Python repository",
        )
        repo_name = st.text_input(
            "Repository Name",
            placeholder="my-flask-application",
            help="Human-readable name for this repository",
        )
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

        submitted = st.form_submit_button(
            "Start Security Scan →",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        if not repo_path:
            st.error("Repository path is required.")
            return
        st.session_state["scan_repo_path"] = repo_path
        st.session_state["scan_repo_name"] = repo_name
        st.session_state["scan_step"] = 2
        st.rerun()


def _step_running():
    repo_path = st.session_state.get("scan_repo_path", "")
    repo_name = st.session_state.get("scan_repo_name", "")

    st.markdown(f"""
    <div class="caa-card" style="margin-bottom:16px;">
        <div style="font-size:11px;color:#6e7681;text-transform:uppercase;
            letter-spacing:0.8px;margin-bottom:8px;">Repository</div>
        <div style="font-family:'JetBrains Mono',monospace;
            font-size:13px;color:#e6edf3;">{repo_path}</div>
    </div>
    """, unsafe_allow_html=True)

    if "active_scan_id" not in st.session_state:
        with st.spinner("Ingesting repository..."):
            ingest_r = ingest_repository(repo_path, repo_name)

        if not ingest_r["success"]:
            error_state("Repository ingestion failed", ingest_r.get("error",""))
            if st.button("← Back"):
                st.session_state["scan_step"] = 1
                st.rerun()
            return

        repo_id = ingest_r["data"]["repository"]["id"]

        with st.spinner("Starting scan pipeline..."):
            scan_r = start_scan(repo_id)

        if not scan_r["success"]:
            error_state("Scan could not be started", scan_r.get("error",""))
            if st.button("← Back"):
                st.session_state["scan_step"] = 1
                st.rerun()
            return

        st.session_state["active_scan_id"] = scan_r["data"]["id"]
        st.session_state["active_repo_data"] = ingest_r["data"]

    scan_id = st.session_state["active_scan_id"]
    repo_data = st.session_state.get("active_repo_data", {})

    # Repo info
    repo_info = repo_data.get("repository", {})
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Language",  repo_info.get("language","N/A") or "N/A")
    with c2:
        fws = repo_data.get("frameworks",[])
        st.metric("Frameworks", ", ".join(fws) if fws else "None")
    with c3:
        st.metric("Files", repo_data.get("analyzable_files", 0))

    # Scan ID display
    st.markdown(f"""
    <div style="background:#161b22;border:1px solid #30363d;border-radius:6px;
        padding:8px 14px;margin:12px 0;font-family:'JetBrains Mono',monospace;
        font-size:12px;color:#8b949e;">
        SCAN ID: <span style="color:#58a6ff;">{scan_id}</span>
    </div>
    """, unsafe_allow_html=True)

    # Pipeline stages
    _render_pipeline(scan_id)

    # Reset button
    col1, col2 = st.columns([3,1])
    with col2:
        if st.button("New Scan", key="new_scan_reset"):
            for k in ["active_scan_id","active_repo_data","scan_step"]:
                st.session_state.pop(k, None)
            st.rerun()


def _render_pipeline(scan_id: str):
    stages = [
        ("Repository Ingestion", "✓"),
        ("Static Analysis + AST", None),
        ("AI Vulnerability Detection", None),
        ("Patch Generation", None),
        ("Security Report Generation", None),
    ]

    status_r = get_scan_status(scan_id)
    if not status_r["success"]:
        st.warning("Unable to fetch scan status")
        return

    scan_status = status_r["data"].get("status","PENDING")
    risk_score  = status_r["data"].get("risk_score")

    st.markdown('<p class="section-header">Pipeline Status</p>', unsafe_allow_html=True)

    for i, (stage, _) in enumerate(stages):
        if scan_status == "COMPLETED":
            dot = '<span class="status-dot dot-green"></span>'
            label = '<span style="color:#3fb950;font-size:12px;">Completed</span>'
        elif scan_status == "FAILED":
            dot = '<span class="status-dot dot-red"></span>'
            label = '<span style="color:#f85149;font-size:12px;">Failed</span>'
        elif scan_status == "RUNNING" and i == 0:
            dot = '<span class="status-dot dot-green"></span>'
            label = '<span style="color:#3fb950;font-size:12px;">Completed</span>'
        elif scan_status in ["RUNNING","PENDING"] and i == 1:
            dot = '<span class="status-dot dot-blue"></span>'
            label = '<span style="color:#58a6ff;font-size:12px;">Running...</span>'
        else:
            dot = '<span class="status-dot dot-gray"></span>'
            label = '<span style="color:#6e7681;font-size:12px;">Pending</span>'

        st.markdown(f"""
        <div class="pipeline-stage {'completed' if scan_status=='COMPLETED' else 'running' if (scan_status=='RUNNING' and i==1) else ''}">
            {dot}
            <span style="font-size:13px;color:#e6edf3;flex:1;">{stage}</span>
            {label}
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    if scan_status == "COMPLETED":
        st.success(f"✓ Scan complete — Risk Score: {risk_score}/100")
        if st.button("View Results →", type="primary", key="goto_results"):
            st.session_state["selected_scan_id"] = scan_id
            st.session_state["page"] = "scan_results"
            for k in ["active_scan_id","active_repo_data","scan_step"]:
                st.session_state.pop(k, None)
            st.rerun()
    elif scan_status == "FAILED":
        err = status_r["data"].get("error_message","Unknown error")
        st.error(f"Scan failed: {err}")
    else:
        st.info(f"Status: {scan_status} — Refresh to update")
        if st.button("↻ Refresh", key="refresh_scan"):
            st.rerun()