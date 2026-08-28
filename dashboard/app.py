"""
CodeAuditAgent — Streamlit Dashboard

Main entry point for the dashboard.
Run with: streamlit run dashboard/app.py
"""

import streamlit as st

# Page config — MUST be first Streamlit call
st.set_page_config(
    page_title="CodeAuditAgent",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded",
)

from dashboard.views.home import render_home
from dashboard.views.new_scan import render_new_scan
from dashboard.views.scan_results import render_scan_results
from dashboard.views.history import render_history


def main():
    """Main dashboard application."""

    # Custom CSS
    st.markdown("""
    <style>
        /* Main header */
        .main-header {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        }
        .main-header h1 {
            color: #e94560;
            font-size: 2.5rem;
            margin: 0;
        }
        .main-header p {
            color: #a8b2d8;
            margin: 5px 0 0 0;
        }

        /* Risk score cards */
        .metric-card {
            background: #16213e;
            border-radius: 10px;
            padding: 15px;
            text-align: center;
            border: 1px solid #0f3460;
        }

        /* Severity badges */
        .badge-critical { color: #ff4757; font-weight: bold; }
        .badge-high     { color: #ff6b35; font-weight: bold; }
        .badge-medium   { color: #ffa502; font-weight: bold; }
        .badge-low      { color: #2ed573; font-weight: bold; }

        /* Finding cards */
        .finding-card {
            background: #16213e;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            border-left: 4px solid #e94560;
        }

        /* Status badges */
        .status-running  { color: #ffa502; }
        .status-complete { color: #2ed573; }
        .status-failed   { color: #ff4757; }

        /* Hide streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🔒 CodeAuditAgent</h1>
        <p>Autonomous AI Security Auditor — Detect → Reason → Patch → Verify</p>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar navigation
    with st.sidebar:
        st.markdown("## Navigation")
        page = st.radio(
            "Go to",
            ["🏠 Home", "🔍 New Scan", "📊 Scan Results", "📋 History"],
            label_visibility="collapsed",
        )
        st.markdown("---")
        st.markdown("### About")
        st.markdown("""
        **CodeAuditAgent** uses AI agents to:
        - 🔍 Detect vulnerabilities
        - 🧠 Reason about exploitability
        - 🔧 Generate secure patches
        - ✅ Verify fixes
        """)
        st.markdown("---")
        st.markdown("**API:** `http://localhost:9000`")
        st.markdown("**Docs:** `http://localhost:9000/docs`")

    # Route to page
    if page == "🏠 Home":
        render_home()
    elif page == "🔍 New Scan":
        render_new_scan()
    elif page == "📊 Scan Results":
        render_scan_results()
    elif page == "📋 History":
        render_history()


if __name__ == "__main__":
    main()