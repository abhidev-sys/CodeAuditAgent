"""
CodeAuditAgent — Enterprise Security Dashboard
Run: streamlit run dashboard/app.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

st.set_page_config(
    page_title="CodeAuditAgent",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded",
)

from dashboard.styles.theme import inject_theme
from dashboard.components.sidebar import render_sidebar
from dashboard.components.badges import render_top_bar
from dashboard.api_client import check_health
from dashboard.views.overview import render_overview
from dashboard.views.new_scan import render_new_scan
from dashboard.views.scan_results import render_scan_results
from dashboard.views.history import render_history
from dashboard.views.vulnerabilities import render_vulnerabilities
from dashboard.views.reports import render_reports
from dashboard.views.system import render_system

# Inject theme
inject_theme()

# Init state
if "page" not in st.session_state:
    st.session_state["page"] = "overview"

# Render sidebar
render_sidebar()

# Top bar
health = check_health()
db_ok  = health.get("data",{}).get("database") == "connected"
api_ok = health["success"]
render_top_bar(db_ok=db_ok, api_ok=api_ok)

# Route to page
page = st.session_state.get("page", "overview")

PAGE_MAP = {
    "overview":        render_overview,
    "new_scan":        render_new_scan,
    "scan_results":    render_scan_results,
    "history":         render_history,
    "vulnerabilities": render_vulnerabilities,
    "reports":         render_reports,
    "system":          render_system,
}

renderer = PAGE_MAP.get(page, render_overview)
renderer()