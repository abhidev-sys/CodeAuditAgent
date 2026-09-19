"""Security Reports page."""
import streamlit as st
from dashboard.api_client import list_scans, get_report
from dashboard.components.states import empty_state, error_state
from dashboard.utils.formatting import fmt_risk_level, shorten_id, fmt_datetime


def render_reports():
    st.markdown("""
    <div class="page-header">
        <h1>Security Reports</h1>
        <p class="subtitle">Evidence-based audit reports with findings, patches, and remediation guidance.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="content-area">', unsafe_allow_html=True)

    scans_r = list_scans()
    if not scans_r["success"]:
        error_state("Could not load reports")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    completed = [s for s in scans_r.get("data",[]) if s.get("status")=="COMPLETED"]

    if not completed:
        empty_state("▤", "No reports available",
                   "Reports are generated automatically after each scan.",
                   "New Scan", "new_scan")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # Report list
    for scan in completed[:10]:
        scan_id = str(scan["id"])
        risk    = scan.get("risk_score", 0)
        level, color = fmt_risk_level(risk)

        with st.expander(
            f"Report {shorten_id(scan_id)} — {fmt_datetime(scan.get('completed_at'))} — {risk}/100 {level}",
            expanded=False,
        ):
            report_r = get_report(scan_id)
            if not report_r["success"]:
                st.markdown("""
                <div style="color:#8b949e;font-size:13px;padding:8px 0;">
                    Report data not available for this scan.
                </div>
                """, unsafe_allow_html=True)
                continue

            report = report_r["data"]

            # Summary metrics
            c1,c2,c3 = st.columns(3)
            with c1: st.metric("Risk Score", f"{report.get('risk_score',0)}/100")
            with c2: st.metric("Risk Level", report.get("risk_level","N/A"))
            with c3:
                fs = report.get("findings_summary",{})
                st.metric("Findings", fs.get("total",0))

            # Summary
            st.markdown(f"""
            <div class="caa-card" style="margin-top:12px;">
                <div style="font-size:11px;color:#6e7681;text-transform:uppercase;
                    letter-spacing:0.8px;margin-bottom:8px;">Executive Summary</div>
                <div style="font-size:13px;color:#c9d1d9;line-height:1.6;">
                    {report.get('executive_summary','No summary.')}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Actions
            col1, col2 = st.columns(2)
            with col1:
                if st.button("View Full Results", key=f"rep_view_{scan_id}",
                           use_container_width=True):
                    st.session_state["selected_scan_id"] = scan_id
                    st.session_state["page"] = "scan_results"
                    st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)