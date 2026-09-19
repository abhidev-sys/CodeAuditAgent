"""Enterprise sidebar navigation."""
import streamlit as st

PAGES = {
    "WORKSPACE": [
        ("overview",         "▦",  "Overview"),
        ("new_scan",         "＋", "New Scan"),
        ("scan_results",     "◎",  "Scan Results"),
        ("history",          "≡",  "History"),
    ],
    "SECURITY": [
        ("vulnerabilities",  "⚑",  "Vulnerabilities"),
        ("reports",          "▤",  "Security Reports"),
    ],
    "SYSTEM": [
        ("system",           "◉",  "System Health"),
    ],
}


def render_sidebar():
    current = st.session_state.get("page", "overview")

    with st.sidebar:
        # Brand
        st.markdown("""
        <div class="sidebar-brand">
            <div style="display:flex;align-items:center;gap:10px;">
                <span style="font-size:22px;">🔒</span>
                <div>
                    <div class="sidebar-brand-name">CodeAuditAgent</div>
                    <div class="sidebar-brand-sub">AI Security Platform</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

        # Nav items
        for section, items in PAGES.items():
            st.markdown(f'<div class="sidebar-section">{section}</div>',
                       unsafe_allow_html=True)
            for page_key, icon, label in items:
                is_active = current == page_key
                active_cls = "active" if is_active else ""
                if st.button(
                    f"{icon}  {label}",
                    key=f"nav_{page_key}",
                    use_container_width=True,
                ):
                    st.session_state["page"] = page_key
                    st.rerun()

        # Bottom info
        st.markdown("""
        <div style="position:absolute;bottom:20px;left:0;right:0;
            padding:0 16px;font-size:11px;color:#6e7681;">
            <div style="border-top:1px solid #21262d;padding-top:12px;">
                <div>Detect → Reason → Patch → Verify</div>
                <div style="margin-top:4px;color:#484f58;">CodeAuditAgent v0.1.0</div>
            </div>
        </div>
        """, unsafe_allow_html=True)