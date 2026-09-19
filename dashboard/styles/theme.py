"""Enterprise dark theme CSS for CodeAuditAgent."""

THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Reset & Base ── */
*, *::before, *::after { box-sizing: border-box; }

.stApp {
    background: #0d1117 !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    color: #e6edf3 !important;
}

/* Hide Streamlit branding */
#MainMenu, footer, header { visibility: hidden !important; }
.stDeployButton { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
.viewerBadge_container__1QSob { display: none !important; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: #0d1117 !important;
    border-right: 1px solid #21262d !important;
    min-width: 260px !important;
    max-width: 260px !important;
}
[data-testid="stSidebar"] > div:first-child {
    padding: 0 !important;
}

/* Main content */
.main .block-container {
    padding: 0 !important;
    max-width: 100% !important;
}

/* Typography */
h1, h2, h3, h4, h5, h6 {
    font-family: 'Inter', sans-serif !important;
    color: #e6edf3 !important;
    font-weight: 600 !important;
}

/* Inputs */
.stTextInput > div > div > input {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    color: #e6edf3 !important;
    border-radius: 6px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 14px !important;
    padding: 10px 14px !important;
}
.stTextInput > div > div > input:focus {
    border-color: #388bfd !important;
    box-shadow: 0 0 0 3px rgba(56,139,253,0.15) !important;
}
.stTextInput > label {
    color: #8b949e !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}

/* Buttons */
.stButton > button {
    background: #21262d !important;
    border: 1px solid #30363d !important;
    color: #e6edf3 !important;
    border-radius: 6px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 8px 16px !important;
    transition: all 0.15s ease !important;
    cursor: pointer !important;
}
.stButton > button:hover {
    background: #30363d !important;
    border-color: #388bfd !important;
    color: #58a6ff !important;
}
.stButton > button[kind="primary"] {
    background: #1f6feb !important;
    border-color: #1f6feb !important;
    color: #ffffff !important;
}
.stButton > button[kind="primary"]:hover {
    background: #388bfd !important;
    border-color: #388bfd !important;
}

/* Select boxes */
.stSelectbox > div > div {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    color: #e6edf3 !important;
    border-radius: 6px !important;
}

/* Metrics */
[data-testid="metric-container"] {
    background: #161b22 !important;
    border: 1px solid #21262d !important;
    border-radius: 8px !important;
    padding: 16px !important;
}
[data-testid="metric-container"] label {
    color: #8b949e !important;
    font-size: 11px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.8px !important;
    font-weight: 500 !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #e6edf3 !important;
    font-size: 28px !important;
    font-weight: 700 !important;
    font-family: 'Inter', sans-serif !important;
}
[data-testid="metric-container"] [data-testid="stMetricDelta"] {
    font-size: 12px !important;
}

/* Expander */
.streamlit-expanderHeader {
    background: #161b22 !important;
    border: 1px solid #21262d !important;
    border-radius: 8px !important;
    color: #e6edf3 !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    padding: 12px 16px !important;
}
.streamlit-expanderContent {
    background: #0d1117 !important;
    border: 1px solid #21262d !important;
    border-top: none !important;
    border-radius: 0 0 8px 8px !important;
}

/* Progress */
.stProgress > div > div > div > div {
    background: #1f6feb !important;
    border-radius: 4px !important;
}
.stProgress > div > div > div {
    background: #21262d !important;
    border-radius: 4px !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid #21262d !important;
    gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #8b949e !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 10px 16px !important;
    border-bottom: 2px solid transparent !important;
}
.stTabs [aria-selected="true"] {
    color: #58a6ff !important;
    border-bottom-color: #1f6feb !important;
    background: transparent !important;
}

/* Code blocks */
.stCode, code {
    background: #161b22 !important;
    border: 1px solid #21262d !important;
    border-radius: 6px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 13px !important;
    color: #e6edf3 !important;
}

/* Divider */
hr {
    border-color: #21262d !important;
    margin: 16px 0 !important;
}

/* Spinner */
.stSpinner > div {
    border-top-color: #1f6feb !important;
}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0d1117; }
::-webkit-scrollbar-thumb { background: #30363d; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #484f58; }

/* Alert */
.stAlert {
    border-radius: 8px !important;
    border: 1px solid !important;
}

/* Custom card component */
.caa-card {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 12px;
}
.caa-card:hover {
    border-color: #30363d;
}

/* Severity badges */
.badge {
    display: inline-flex;
    align-items: center;
    padding: 3px 10px;
    border-radius: 100px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    font-family: 'Inter', sans-serif;
}
.badge-critical { background: rgba(248,81,73,0.15); color: #f85149; border: 1px solid rgba(248,81,73,0.3); }
.badge-high     { background: rgba(210,153,34,0.15); color: #d29922; border: 1px solid rgba(210,153,34,0.3); }
.badge-medium   { background: rgba(187,128,9,0.15);  color: #bb8009; border: 1px solid rgba(187,128,9,0.3); }
.badge-low      { background: rgba(35,134,54,0.15);  color: #3fb950; border: 1px solid rgba(35,134,54,0.3); }
.badge-info     { background: rgba(56,139,253,0.15); color: #58a6ff; border: 1px solid rgba(56,139,253,0.3); }
.badge-success  { background: rgba(35,134,54,0.15);  color: #3fb950; border: 1px solid rgba(35,134,54,0.3); }
.badge-running  { background: rgba(56,139,253,0.15); color: #58a6ff; border: 1px solid rgba(56,139,253,0.3); }
.badge-pending  { background: rgba(110,118,129,0.15);color: #8b949e; border: 1px solid rgba(110,118,129,0.3); }
.badge-failed   { background: rgba(248,81,73,0.15);  color: #f85149; border: 1px solid rgba(248,81,73,0.3); }

/* Metric card */
.metric-card {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 8px;
    padding: 16px 20px;
    height: 100%;
}
.metric-card .metric-label {
    color: #8b949e;
    font-size: 11px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-bottom: 8px;
}
.metric-card .metric-value {
    color: #e6edf3;
    font-size: 28px;
    font-weight: 700;
    line-height: 1;
    margin-bottom: 4px;
}
.metric-card .metric-sub {
    color: #6e7681;
    font-size: 12px;
    margin-top: 4px;
}

/* Page header */
.page-header {
    padding: 24px 32px 20px;
    border-bottom: 1px solid #21262d;
    margin-bottom: 24px;
}
.page-header h1 {
    font-size: 22px !important;
    font-weight: 600 !important;
    color: #e6edf3 !important;
    margin: 0 0 4px !important;
}
.page-header .subtitle {
    color: #8b949e;
    font-size: 13px;
    margin: 0;
}

/* Section header */
.section-header {
    font-size: 13px !important;
    font-weight: 600 !important;
    color: #8b949e !important;
    text-transform: uppercase !important;
    letter-spacing: 0.8px !important;
    margin: 20px 0 12px !important;
}

/* Table */
.caa-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
}
.caa-table th {
    background: #161b22;
    color: #8b949e;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    padding: 10px 14px;
    border-bottom: 1px solid #21262d;
    text-align: left;
}
.caa-table td {
    padding: 12px 14px;
    border-bottom: 1px solid #161b22;
    color: #e6edf3;
    vertical-align: middle;
}
.caa-table tr:hover td {
    background: #161b22;
}
.caa-table .mono {
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    color: #8b949e;
}

/* Status dot */
.status-dot {
    display: inline-block;
    width: 8px; height: 8px;
    border-radius: 50%;
    margin-right: 6px;
}
.dot-green  { background: #3fb950; box-shadow: 0 0 6px rgba(63,185,80,0.5); }
.dot-blue   { background: #58a6ff; box-shadow: 0 0 6px rgba(88,166,255,0.5); animation: blink 1.5s ease infinite; }
.dot-red    { background: #f85149; box-shadow: 0 0 6px rgba(248,81,73,0.5); }
.dot-gray   { background: #8b949e; }

@keyframes blink {
    0%,100% { opacity: 1; }
    50% { opacity: 0.4; }
}

/* Risk meter */
.risk-meter {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 8px;
    padding: 20px 24px;
}
.risk-score-display {
    font-size: 48px;
    font-weight: 700;
    line-height: 1;
    font-family: 'Inter', sans-serif;
}
.risk-bar-track {
    background: #21262d;
    height: 6px;
    border-radius: 3px;
    margin: 12px 0;
    overflow: hidden;
}
.risk-bar-fill {
    height: 100%;
    border-radius: 3px;
    transition: width 0.5s ease;
}

/* Finding card */
.finding-card {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 8px;
    margin-bottom: 8px;
    overflow: hidden;
}
.finding-header {
    padding: 14px 18px;
    display: flex;
    align-items: center;
    gap: 10px;
    cursor: pointer;
}
.finding-header:hover { background: #1c2128; }

/* Diff viewer */
.diff-removed {
    background: rgba(248,81,73,0.1);
    border-left: 3px solid #f85149;
    padding: 3px 12px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    color: #ffa198;
    display: block;
}
.diff-added {
    background: rgba(63,185,80,0.1);
    border-left: 3px solid #3fb950;
    padding: 3px 12px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    color: #7ee787;
    display: block;
}
.diff-context {
    padding: 3px 12px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    color: #6e7681;
    display: block;
}

/* Pipeline */
.pipeline-stage {
    display: flex;
    align-items: center;
    padding: 12px 16px;
    border-radius: 8px;
    margin-bottom: 4px;
    background: #161b22;
    border: 1px solid #21262d;
}
.pipeline-stage.completed { border-color: #238636; }
.pipeline-stage.running   { border-color: #1f6feb; }
.pipeline-stage.failed    { border-color: #da3633; }

/* Sidebar custom */
.sidebar-brand {
    padding: 20px 20px 16px;
    border-bottom: 1px solid #21262d;
}
.sidebar-brand-name {
    font-size: 16px;
    font-weight: 700;
    color: #e6edf3;
    letter-spacing: -0.3px;
}
.sidebar-brand-sub {
    font-size: 10px;
    color: #6e7681;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 2px;
}
.sidebar-section {
    padding: 16px 12px 8px;
    font-size: 10px;
    font-weight: 600;
    color: #6e7681;
    text-transform: uppercase;
    letter-spacing: 1.2px;
}
.sidebar-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 12px;
    margin: 1px 4px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 13px;
    font-weight: 400;
    color: #8b949e;
    text-decoration: none;
    transition: all 0.1s;
}
.sidebar-item:hover {
    background: #161b22;
    color: #e6edf3;
}
.sidebar-item.active {
    background: rgba(31,111,235,0.15);
    color: #58a6ff;
    font-weight: 500;
}
.sidebar-item.active .item-icon { color: #388bfd; }

/* Top bar */
.top-bar {
    background: #161b22;
    border-bottom: 1px solid #21262d;
    padding: 0 32px;
    height: 52px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky;
    top: 0;
    z-index: 100;
}
.top-bar-left {
    display: flex;
    align-items: center;
    gap: 8px;
}
.top-bar-title {
    font-size: 14px;
    font-weight: 600;
    color: #e6edf3;
}
.top-bar-subtitle {
    font-size: 12px;
    color: #6e7681;
}
.top-bar-right {
    display: flex;
    align-items: center;
    gap: 16px;
}
.health-indicator {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    color: #8b949e;
}

/* Content padding */
.content-area {
    padding: 0 32px 32px;
}

/* Empty state */
.empty-state {
    text-align: center;
    padding: 60px 20px;
    color: #6e7681;
}
.empty-state-icon {
    font-size: 40px;
    margin-bottom: 16px;
    opacity: 0.5;
}
.empty-state-title {
    font-size: 16px;
    font-weight: 600;
    color: #8b949e;
    margin-bottom: 8px;
}
.empty-state-body {
    font-size: 13px;
    color: #6e7681;
    margin-bottom: 20px;
    max-width: 360px;
    margin-left: auto;
    margin-right: auto;
}
</style>
"""

def inject_theme():
    """Inject enterprise theme CSS."""
    import streamlit as st
    st.markdown(THEME_CSS, unsafe_allow_html=True)