"""Badge and indicator components."""
import streamlit as st
from dashboard.utils.formatting import fmt_severity_badge, fmt_status_badge


def severity_badge(severity: str) -> str:
    return fmt_severity_badge(severity)


def status_badge(status: str) -> str:
    return fmt_status_badge(status)


def health_dot(operational: bool) -> str:
    cls = "dot-green" if operational else "dot-red"
    return f'<span class="status-dot {cls}"></span>'


def render_top_bar(db_ok: bool = True, api_ok: bool = True):
    """Render sticky top bar."""
    db_dot = health_dot(db_ok)
    api_dot = health_dot(api_ok)
    st.markdown(f"""
    <div class="top-bar">
        <div class="top-bar-left">
            <span style="font-size:16px;">🔒</span>
            <div>
                <div class="top-bar-title">CodeAuditAgent</div>
                <div class="top-bar-subtitle">Autonomous AI Security Auditor</div>
            </div>
        </div>
        <div class="top-bar-right">
            <div class="health-indicator">
                {api_dot} API
            </div>
            <div class="health-indicator">
                {db_dot} Database
            </div>
            <div style="
                background:#161b22;border:1px solid #30363d;
                border-radius:6px;padding:5px 12px;
                font-size:12px;color:#8b949e;
                font-family:'JetBrains Mono',monospace;
            ">v0.1.0</div>
        </div>
    </div>
    """, unsafe_allow_html=True)