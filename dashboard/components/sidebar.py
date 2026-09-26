"""CodeAuditAgent sidebar navigation."""

import streamlit as st


PAGES = {
    "WORKSPACE": [
        ("overview", "▦", "Overview"),
        ("new_scan", "＋", "New Scan"),
        ("scan_results", "◎", "Scan Results"),
        ("history", "≡", "History"),
    ],
    "SECURITY": [
        ("vulnerabilities", "⚑", "Vulnerabilities"),
        ("reports", "▤", "Security Reports"),
    ],
    "SYSTEM": [
        ("system", "◉", "System Health"),
    ],
}


def render_sidebar():

    current = st.session_state.get("page", "overview")

    with st.sidebar:

        # ============================
        # BRAND
        # ============================

        st.markdown("### ◈ CodeAuditAgent")

        st.caption("AI SECURITY PLATFORM")

        st.divider()

        # ============================
        # NAVIGATION
        # ============================

        for section, items in PAGES.items():

            st.markdown(f"**{section}**")

            for page_key, icon, label in items:

                is_active = current == page_key

                button_label = (
                    f"◆  {label}"
                    if is_active
                    else f"{icon}  {label}"
                )

                if st.button(
                    button_label,
                    key=f"nav_{page_key}",
                    use_container_width=True,
                ):
                    st.session_state["page"] = page_key
                    st.rerun()

        # ============================
        # FOOTER
        # ============================

        st.divider()

        st.caption("● SECURITY ENGINE")
        st.caption("Detect → Reason → Patch → Verify")
        st.caption("CodeAuditAgent · v0.1.0")