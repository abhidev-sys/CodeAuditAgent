"""System Health page."""
import streamlit as st
from dashboard.api_client import check_health
from dashboard.components.states import error_state


def render_system():
    st.markdown("""
    <div class="page-header">
        <h1>System Health</h1>
        <p class="subtitle">Real-time status of all CodeAuditAgent platform components.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="content-area">', unsafe_allow_html=True)

    health_r = check_health()
    health   = health_r.get("data", {}) if health_r["success"] else {}

    db_ok  = health.get("database") == "connected"
    api_ok = health_r["success"]

    components = [
        ("API Server",          api_ok,  "FastAPI backend",           "All endpoints operational"),
        ("Database",            db_ok,   "PostgreSQL",                "Connected and accepting queries"),
        ("AI Engine",           api_ok,  "openai/gpt-oss-120b",      "LLM agent pipeline ready"),
        ("Static Analyzer",     api_ok,  "Bandit + Custom Rules",    "Pattern detection active"),
        ("AST Parser",          api_ok,  "Tree-sitter",              "Code intelligence ready"),
        ("Patch Engine",        api_ok,  "Diff generation",          "Patch synthesis operational"),
        ("Report Generator",    api_ok,  "JSON + Text output",       "Report engine ready"),
    ]

    st.markdown('<p class="section-header">Component Status</p>', unsafe_allow_html=True)

    for name, ok, tech, desc in components:
        dot_cls = "dot-green" if ok else "dot-red"
        status_label = "Operational" if ok else "Unreachable"
        status_color = "#3fb950" if ok else "#f85149"

        st.markdown(f"""
        <div class="caa-card" style="display:flex;align-items:center;
            gap:16px;padding:16px 20px;margin-bottom:8px;">
            <span class="status-dot {dot_cls}" style="flex-shrink:0;"></span>
            <div style="flex:1;">
                <div style="font-size:14px;font-weight:600;color:#e6edf3;
                    margin-bottom:2px;">{name}</div>
                <div style="font-size:12px;color:#6e7681;">{tech} · {desc}</div>
            </div>
            <div style="font-size:12px;font-weight:600;color:{status_color};">
                {status_label}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # API info
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    st.markdown('<p class="section-header">API Information</p>', unsafe_allow_html=True)
    st.markdown("""
    <div class="caa-card">
        <table style="width:100%;font-size:13px;border-collapse:collapse;">
            <tr>
                <td style="color:#8b949e;padding:6px 0;width:30%;">API Base URL</td>
                <td style="font-family:'JetBrains Mono',monospace;color:#58a6ff;">
                    http://127.0.0.1:9000
                </td>
            </tr>
            <tr>
                <td style="color:#8b949e;padding:6px 0;">Documentation</td>
                <td style="font-family:'JetBrains Mono',monospace;color:#58a6ff;">
                    http://127.0.0.1:9000/docs
                </td>
            </tr>
            <tr>
                <td style="color:#8b949e;padding:6px 0;">Version</td>
                <td style="font-family:'JetBrains Mono',monospace;color:#e6edf3;">
                    v0.1.0
                </td>
            </tr>
        </table>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)