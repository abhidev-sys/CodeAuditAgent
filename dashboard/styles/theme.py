"""Premium Cybersecurity SOC theme for CodeAuditAgent."""

import streamlit as st

THEME_CSS = """
<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
    --bg-root: #070910;
    --bg-primary: #0a0d14;
    --bg-secondary: #0e121b;
    --bg-card: #111622;

    --border: rgba(148,163,184,.10);

    --text-primary: #f4f7fb;
    --text-secondary: #a7b0c0;
    --text-muted: #687386;

    --accent: #8b5cf6;
    --accent-light: #a78bfa;
    --accent-blue: #6366f1;

    --success: #22c55e;
    --warning: #f59e0b;
    --danger: #ef4444;

    --mono: 'JetBrains Mono', Consolas, monospace;
    --sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}


/* ================================
   GLOBAL
   ================================ */

html,
body {
    background: var(--bg-root) !important;
}

.stApp {
    background:
        radial-gradient(
            circle at 80% 0%,
            rgba(99,102,241,.08),
            transparent 30%
        ),
        var(--bg-root) !important;

    color: var(--text-primary) !important;
    font-family: var(--sans) !important;
}


/* ================================
   STREAMLIT CLEANUP
   ================================ */

#MainMenu,
footer,
header,
.stDeployButton,
[data-testid="stToolbar"],
[data-testid="stDecoration"] {
    visibility: hidden !important;
}


/* ================================
   MAIN CONTENT
   ================================ */

.main .block-container {
    max-width: 1600px !important;
    padding: 0 36px 48px !important;
}


/* ================================
   TYPOGRAPHY
   ================================ */

h1,
h2,
h3,
h4,
h5,
h6 {
    font-family: var(--sans) !important;
    color: var(--text-primary) !important;
}

p {
    color: var(--text-secondary);
}

.mono,
code,
pre {
    font-family: var(--mono) !important;
}


/* ================================
   SIDEBAR
   ================================ */

[data-testid="stSidebar"] {
    background: linear-gradient(
        180deg,
        #090c13 0%,
        #080b11 55%,
        #070910 100%
    ) !important;

    border-right: 1px solid var(--border) !important;

    min-width: 272px !important;
    max-width: 272px !important;
}

[data-testid="stSidebar"] > div:first-child {
    padding: 0 !important;
}


/* Sidebar brand */

.sidebar-brand {
    padding: 24px 20px 20px;
    border-bottom: 1px solid var(--border);

    background:
        radial-gradient(
            circle at 20% 0%,
            rgba(139,92,246,.14),
            transparent 55%
        );
}

.sidebar-brand-name {
    font-size: 16px;
    font-weight: 700;
    color: var(--text-primary);
}

.sidebar-brand-sub {
    font-size: 9px;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 1.4px;
    margin-top: 3px;
}


/* Sidebar section */

.sidebar-section {
    padding: 18px 14px 7px;

    color: #596477;

    font-size: 9px;
    font-weight: 700;

    text-transform: uppercase;
    letter-spacing: 1.5px;
}


/* Sidebar buttons */

[data-testid="stSidebar"] .stButton {
    margin: 0 !important;
}

[data-testid="stSidebar"] .stButton > button {
    width: calc(100% - 14px) !important;

    margin: 2px 7px !important;

    min-height: 40px !important;

    justify-content: flex-start !important;

    background: transparent !important;

    border: 1px solid transparent !important;

    border-radius: 8px !important;

    color: var(--text-secondary) !important;

    font-family: var(--sans) !important;
    font-size: 13px !important;
    font-weight: 500 !important;

    text-align: left !important;

    padding: 9px 12px !important;
}

[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(139,92,246,.08) !important;

    border-color: rgba(139,92,246,.18) !important;

    color: var(--text-primary) !important;
}


/* ================================
   TOP BAR
   ================================ */

.top-bar {
    height: 62px;

    display: flex;
    align-items: center;
    justify-content: space-between;

    padding: 0 36px;

    background: rgba(8,11,17,.92);

    border-bottom: 1px solid rgba(148,163,184,.08);
}

.top-bar-left {
    display: flex;
    align-items: center;
    gap: 11px;
}

.top-bar-title {
    color: var(--text-primary);

    font-size: 14px;
    font-weight: 700;
}

.top-bar-subtitle {
    color: var(--text-muted);

    font-size: 10px;

    margin-top: 1px;
}

.top-bar-right {
    display: flex;
    align-items: center;
    gap: 10px;
}

.health-indicator {
    display: inline-flex;
    align-items: center;
    gap: 6px;

    padding: 6px 9px;

    border: 1px solid rgba(148,163,184,.08);

    border-radius: 999px;

    background: rgba(255,255,255,.025);

    color: var(--text-muted);

    font-size: 10px;
    font-weight: 600;
}


/* ================================
   STATUS DOT
   ================================ */

.status-dot {
    display: inline-block;

    width: 7px;
    height: 7px;

    border-radius: 50%;
}

.dot-green {
    background: var(--success);
    box-shadow: 0 0 10px rgba(34,197,94,.55);
}

.dot-red {
    background: var(--danger);
    box-shadow: 0 0 10px rgba(239,68,68,.55);
}


/* ================================
   PAGE HEADER
   ================================ */

.page-header {
    padding: 34px 36px 26px;

    border-bottom: 1px solid rgba(148,163,184,.08);

    background:
        radial-gradient(
            circle at 72% 0%,
            rgba(99,102,241,.08),
            transparent 38%
        );
}

.page-header h1 {
    margin: 0 0 7px !important;

    font-size: 25px !important;
    font-weight: 750 !important;
}

.page-header .subtitle {
    margin: 0;

    color: var(--text-muted);

    font-size: 12px;
}


/* ================================
   CONTENT
   ================================ */

.content-area {
    padding: 0 36px 40px;
}

.section-header {
    margin: 26px 0 13px !important;

    color: #8e9aae !important;

    font-size: 10px !important;
    font-weight: 700 !important;

    text-transform: uppercase !important;
    letter-spacing: 1.25px !important;
}


/* ================================
   CARDS
   ================================ */

.caa-card,
.metric-card,
.finding-card,
.pipeline-stage,
.risk-meter {
    background: linear-gradient(
        145deg,
        rgba(18,24,37,.92),
        rgba(11,15,23,.95)
    );

    border: 1px solid var(--border);

    border-radius: 11px;

    box-shadow: 0 8px 25px rgba(0,0,0,.18);
}


/* Metric */

.metric-card {
    min-height: 125px;

    padding: 18px 20px;

    height: 100%;
}

.metric-card .metric-label {
    color: var(--text-muted);

    font-size: 9px;
    font-weight: 700;

    text-transform: uppercase;
    letter-spacing: 1.1px;

    margin-bottom: 13px;
}

.metric-card .metric-value {
    color: var(--text-primary);

    font-size: 29px;
    font-weight: 750;

    line-height: 1;

    margin-bottom: 7px;
}

.metric-card .metric-sub {
    color: var(--text-muted);

    font-size: 11px;
}


/* ================================
   RISK
   ================================ */

.risk-meter {
    padding: 24px 26px;
}

.risk-score-display {
    font-size: 52px;

    font-weight: 800;

    line-height: 1;
}

.risk-bar-track {
    background: rgba(255,255,255,.055);

    height: 8px;

    border-radius: 99px;

    margin: 15px 0;

    overflow: hidden;
}

.risk-bar-fill {
    height: 100%;

    border-radius: 99px;
}


/* ================================
   BADGES
   ================================ */

.badge {
    display: inline-flex;

    align-items: center;
    justify-content: center;

    padding: 4px 9px;

    border-radius: 999px;

    font-size: 9px;

    font-weight: 700;

    letter-spacing: .75px;

    text-transform: uppercase;
}

.badge-critical {
    background: rgba(239,68,68,.10);
    color: #f87171;
    border: 1px solid rgba(239,68,68,.22);
}

.badge-high {
    background: rgba(245,158,11,.10);
    color: #fbbf24;
    border: 1px solid rgba(245,158,11,.22);
}

.badge-medium {
    background: rgba(234,179,8,.09);
    color: #facc15;
    border: 1px solid rgba(234,179,8,.20);
}

.badge-low,
.badge-success {
    background: rgba(34,197,94,.09);
    color: #4ade80;
    border: 1px solid rgba(34,197,94,.20);
}

.badge-running {
    background: rgba(99,102,241,.10);
    color: #a5b4fc;
    border: 1px solid rgba(99,102,241,.23);
}

.badge-pending {
    background: rgba(100,116,139,.10);
    color: #94a3b8;
    border: 1px solid rgba(100,116,139,.20);
}

.badge-failed {
    background: rgba(239,68,68,.10);
    color: #f87171;
    border: 1px solid rgba(239,68,68,.22);
}


/* ================================
   TABLE
   ================================ */

.caa-table {
    width: 100%;

    border-collapse: separate;

    border-spacing: 0;

    overflow: hidden;

    border: 1px solid var(--border);

    border-radius: 12px;

    font-size: 12px;

    background: rgba(12,16,25,.72);
}

.caa-table th {
    background: rgba(255,255,255,.025);

    color: #748096;

    font-size: 9px;
    font-weight: 700;

    text-transform: uppercase;
    letter-spacing: 1px;

    padding: 12px 14px;

    border-bottom: 1px solid var(--border);

    text-align: left;
}

.caa-table td {
    padding: 13px 14px;

    border-bottom: 1px solid rgba(148,163,184,.055);

    color: #dce3ed;
}

.caa-table tr:last-child td {
    border-bottom: none;
}

.caa-table tr:hover td {
    background: rgba(139,92,246,.035);
}

.caa-table .mono {
    font-family: var(--mono);
    font-size: 10px;
    color: #7f8ca3;
}


/* ================================
   INPUTS
   ================================ */

.stTextInput input,
.stTextArea textarea,
.stSelectbox > div > div {
    background: rgba(14,18,27,.90) !important;

    border: 1px solid rgba(148,163,184,.12) !important;

    color: var(--text-primary) !important;

    border-radius: 9px !important;

    font-family: var(--sans) !important;
}


/* ================================
   BUTTONS
   ================================ */

.stButton > button {
    background: rgba(20,26,39,.92) !important;

    border: 1px solid rgba(148,163,184,.13) !important;

    color: #dce4ef !important;

    border-radius: 8px !important;

    font-family: var(--sans) !important;

    font-size: 12px !important;

    font-weight: 600 !important;

    min-height: 38px !important;
}

.stButton > button:hover {
    background: rgba(139,92,246,.10) !important;

    border-color: rgba(139,92,246,.35) !important;

    color: #c4b5fd !important;
}

.stButton > button[kind="primary"] {
    background: linear-gradient(
        135deg,
        #7c3aed,
        #4f46e5
    ) !important;

    color: white !important;
}


/* ================================
   TABS
   ================================ */

.stTabs [data-baseweb="tab-list"] {
    background: rgba(10,13,20,.65) !important;

    border-bottom: 1px solid var(--border) !important;
}

.stTabs [data-baseweb="tab"] {
    color: var(--text-muted) !important;

    font-size: 11px !important;
}

.stTabs [aria-selected="true"] {
    color: #c4b5fd !important;

    background: rgba(139,92,246,.09) !important;
}


/* ================================
   ALERTS
   ================================ */

.stAlert {
    border-radius: 10px !important;

    border: 1px solid rgba(148,163,184,.12) !important;

    background: rgba(17,22,34,.72) !important;
}


/* ================================
   DIVIDER
   ================================ */

hr {
    border: none !important;

    border-top: 1px solid rgba(148,163,184,.075) !important;
}


/* ================================
   EMPTY STATE
   ================================ */

.empty-state {
    text-align: center;

    padding: 72px 20px;

    background: rgba(139,92,246,.025);

    border: 1px dashed rgba(148,163,184,.12);

    border-radius: 15px;
}

.empty-state-icon {
    font-size: 25px;

    color: #a78bfa;

    margin-bottom: 17px;
}

.empty-state-title {
    font-size: 17px;

    font-weight: 650;

    color: var(--text-primary);

    margin-bottom: 7px;
}

.empty-state-body {
    font-size: 12px;

    color: var(--text-muted);

    margin-bottom: 20px;
}


/* ================================
   CODE
   ================================ */

.stCode,
pre,
code {
    background: #090d15 !important;

    border: 1px solid rgba(148,163,184,.10) !important;

    border-radius: 9px !important;

    font-family: var(--mono) !important;
}


/* ================================
   SCROLLBAR
   ================================ */

::-webkit-scrollbar {
    width: 7px;
    height: 7px;
}

::-webkit-scrollbar-track {
    background: var(--bg-root);
}

::-webkit-scrollbar-thumb {
    background: #293244;
    border-radius: 99px;
}

</style>
"""


def inject_theme():
    """Inject the CodeAuditAgent theme."""
    st.markdown(
        THEME_CSS,
        unsafe_allow_html=True
    )