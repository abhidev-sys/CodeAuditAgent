"""
History page — All repositories and scans.
"""

import streamlit as st

from dashboard.api_client import (
    list_repositories,
    list_scans,
)


def render_history():
    """Render the scan history page."""

    st.markdown("## 📋 Scan History")

    # ============================================================
    # REPOSITORIES
    # ============================================================

    st.markdown("### 📁 Repositories")

    repos_result = list_repositories()

    if not repos_result["success"]:
        st.error(f"Failed to load repositories: {repos_result['error']}")
    else:
        repos = repos_result["data"]

        if not repos:
            st.info("No repositories have been ingested yet.")

        else:
            for repo in repos:

                repo_name = repo.get("name", "Unknown Repository")
                language = repo.get("language", "N/A")

                with st.expander(
                    f"📁 {repo_name} — {language}"
                ):

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric(
                            "Language",
                            language
                        )

                    with col2:
                        st.metric(
                            "Files",
                            repo.get("total_files", 0)
                        )

                    with col3:
                        st.metric(
                            "Lines",
                            repo.get("total_lines", 0)
                        )

                    st.markdown("**Repository Path**")
                    st.code(
                        repo.get("path", "N/A")
                    )

                    st.markdown("**Repository ID**")
                    st.code(
                        repo.get("id", "N/A")
                    )

    st.markdown("---")

    # ============================================================
    # SCAN HISTORY
    # ============================================================

    st.markdown("### 🔍 All Scans")

    scans_result = list_scans()

    if not scans_result["success"]:
        st.error(
            f"Failed to load scans: {scans_result['error']}"
        )
        return

    scans = scans_result["data"]

    if not scans:
        st.info("No scans have been performed yet.")
        return

    # ============================================================
    # SCAN SUMMARY
    # ============================================================

    completed = sum(
        1 for scan in scans
        if scan.get("status") == "COMPLETED"
    )

    running = sum(
        1 for scan in scans
        if scan.get("status") == "RUNNING"
    )

    failed = sum(
        1 for scan in scans
        if scan.get("status") == "FAILED"
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Scans",
            len(scans)
        )

    with col2:
        st.metric(
            "Completed",
            completed
        )

    with col3:
        st.metric(
            "Running",
            running
        )

    with col4:
        st.metric(
            "Failed",
            failed
        )

    st.markdown("---")

    # ============================================================
    # INDIVIDUAL SCANS
    # ============================================================

    for scan in scans:

        scan_id = scan.get("id", "")
        status = scan.get("status", "UNKNOWN")

        risk_score = scan.get("risk_score")

        if risk_score is not None:
            risk_display = f"{risk_score}/100"
        else:
            risk_display = "N/A"

        status_emoji = {
            "COMPLETED": "✅",
            "RUNNING": "🔄",
            "PENDING": "⏳",
            "FAILED": "❌",
        }.get(status, "❓")

        created_at = scan.get(
            "created_at",
            "N/A"
        )

        if created_at != "N/A":
            created_at = created_at[:19]

        # Scan row
        col1, col2, col3, col4, col5 = st.columns(
            [3, 2, 2, 2, 1]
        )

        with col1:
            st.markdown(
                f"🆔 `{scan_id[:16]}...`"
            )

        with col2:
            st.markdown(
                f"{status_emoji} **{status}**"
            )

        with col3:
            st.markdown(
                f"Risk: **{risk_display}**"
            )

        with col4:
            st.markdown(
                f"📅 {created_at}"
            )

        with col5:

            if st.button(
                "View",
                key=f"history_view_{scan_id}"
            ):
                st.session_state[
                    "selected_scan_id"
                ] = scan_id

                st.session_state[
                    "page"
                ] = "results"

                st.rerun()

        st.markdown("---")