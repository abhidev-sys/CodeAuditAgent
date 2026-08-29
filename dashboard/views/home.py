"""Home page — God level UI."""

import streamlit as st
from dashboard.api_client import list_repositories, list_scans


def render_home():
    repos_result = list_repositories()
    scans_result = list_scans()

    repos = repos_result.get("data", []) if repos_result["success"] else []
    scans = scans_result.get("data", []) if scans_result["success"] else []
    completed = [s for s in scans if s.get("status") == "COMPLETED"]
    failed = [s for s in scans if s.get("status") == "FAILED"]
    risk_scores = [s.get("risk_score", 0) for s in completed if s.get("risk_score")]
    avg_risk = int(sum(risk_scores) / len(risk_scores)) if risk_scores else 0

    # Stats Grid
    st.markdown(f"""
    <div class="metric-grid">
        <div class="metric-card">
            <div class="metric-value">{len(repos)}</div>
            <div class="metric-label">Repositories</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{len(scans)}</div>
            <div class="metric-label">Total Scans</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{len(completed)}</div>
            <div class="metric-label">Completed</div>
        </div>
        <div class="metric-card">
            <div class="metric-value" style="color: {'#ff4757' if avg_risk >= 75 else '#ffa502' if avg_risk >= 25 else '#00ff41'}">
                {avg_risk}
            </div>
            <div class="metric-label">Avg Risk Score</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Pipeline visualization
    st.markdown("""
    <div class="section-header">
        <span class="section-title">[ HOW IT WORKS ]</span>
        <div class="section-line"></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="display: flex; gap: 8px; align-items: center; padding: 20px; background: #111; border-radius: 12px; border: 1px solid #1a1a1a; overflow-x: auto; margin: 16px 0;">
        <div style="text-align: center; min-width: 100px;">
            <div style="font-size: 2rem; margin-bottom: 6px;">📁</div>
            <div style="font-family: 'JetBrains Mono'; font-size: 0.7rem; color: #00ff41;">INGEST</div>
            <div style="font-size: 0.65rem; color: #444; margin-top: 4px;">Repository</div>
        </div>
        <div style="color: #00ff41; font-size: 1.5rem; font-family: monospace;">→</div>
        <div style="text-align: center; min-width: 100px;">
            <div style="font-size: 2rem; margin-bottom: 6px;">🌳</div>
            <div style="font-family: 'JetBrains Mono'; font-size: 0.7rem; color: #00ff41;">ANALYZE</div>
            <div style="font-size: 0.65rem; color: #444; margin-top: 4px;">AST + DataFlow</div>
        </div>
        <div style="color: #00ff41; font-size: 1.5rem; font-family: monospace;">→</div>
        <div style="text-align: center; min-width: 100px;">
            <div style="font-size: 2rem; margin-bottom: 6px;">🔍</div>
            <div style="font-family: 'JetBrains Mono'; font-size: 0.7rem; color: #00ff41;">DETECT</div>
            <div style="font-size: 0.65rem; color: #444; margin-top: 4px;">Static + LLM</div>
        </div>
        <div style="color: #00ff41; font-size: 1.5rem; font-family: monospace;">→</div>
        <div style="text-align: center; min-width: 100px;">
            <div style="font-size: 2rem; margin-bottom: 6px;">🧠</div>
            <div style="font-family: 'JetBrains Mono'; font-size: 0.7rem; color: #00ff41;">REASON</div>
            <div style="font-size: 0.65rem; color: #444; margin-top: 4px;">AI Agents</div>
        </div>
        <div style="color: #00ff41; font-size: 1.5rem; font-family: monospace;">→</div>
        <div style="text-align: center; min-width: 100px;">
            <div style="font-size: 2rem; margin-bottom: 6px;">🔧</div>
            <div style="font-family: 'JetBrains Mono'; font-size: 0.7rem; color: #00ff41;">PATCH</div>
            <div style="font-size: 0.65rem; color: #444; margin-top: 4px;">Secure Fix</div>
        </div>
        <div style="color: #00ff41; font-size: 1.5rem; font-family: monospace;">→</div>
        <div style="text-align: center; min-width: 100px;">
            <div style="font-size: 2rem; margin-bottom: 6px;">📋</div>
            <div style="font-family: 'JetBrains Mono'; font-size: 0.7rem; color: #00ff41;">REPORT</div>
            <div style="font-size: 0.65rem; color: #444; margin-top: 4px;">Audit PDF</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Quick start
    st.markdown("""
    <div class="section-header">
        <span class="section-title">[ QUICK START ]</span>
        <div class="section-line"></div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔍  Start New Scan", type="primary", use_container_width=True):
            st.session_state["current_page"] = "new_scan"
            st.rerun()
    with col2:
        if st.button("📋  View History", use_container_width=True):
            st.session_state["current_page"] = "history"
            st.rerun()

    # Recent scans
    if scans:
        st.markdown("""
        <div class="section-header">
            <span class="section-title">[ RECENT SCANS ]</span>
            <div class="section-line"></div>
        </div>
        """, unsafe_allow_html=True)

        for scan in scans[:5]:
            status = scan.get("status", "N/A")
            risk = scan.get("risk_score", 0) or 0

            status_color = {
                "COMPLETED": "#00ff41",
                "RUNNING": "#ffa502",
                "PENDING": "#666",
                "FAILED": "#ff4757",
            }.get(status, "#666")

            risk_color = "#ff4757" if risk >= 75 else "#ffa502" if risk >= 25 else "#00ff41"

            st.markdown(f"""
            <div class="finding-card" style="border-left: 4px solid {status_color};">
                <div class="finding-header">
                    <div>
                        <div class="finding-type">
                            SCAN_{scan['id'][:8].upper()}
                        </div>
                        <div class="finding-meta">
                            <div class="meta-item">Status: <span style="color:{status_color}">{status}</span></div>
                            <div class="meta-item">Risk: <span style="color:{risk_color}">{risk}/100</span></div>
                            <div class="meta-item">Date: <span>{scan.get('created_at', '')[:10]}</span></div>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)