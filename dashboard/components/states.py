"""Empty, loading, and error states."""
import streamlit as st


def empty_state(icon: str, title: str, body: str, cta_label: str = None, cta_page: str = None):
    st.markdown(f"""
    <div class="empty-state">
        <div class="empty-state-icon">{icon}</div>
        <div class="empty-state-title">{title}</div>
        <div class="empty-state-body">{body}</div>
    </div>
    """, unsafe_allow_html=True)
    if cta_label and cta_page:
        col = st.columns([1, 2, 1])[1]
        with col:
            if st.button(cta_label, type="primary", use_container_width=True):
                st.session_state["page"] = cta_page
                st.rerun()


def error_state(message: str, detail: str = None):
    st.markdown(f"""
    <div style="background:rgba(248,81,73,0.08);border:1px solid rgba(248,81,73,0.3);
    border-radius:8px;padding:20px 24px;margin:16px 0;">
        <div style="color:#f85149;font-weight:600;font-size:14px;margin-bottom:6px;">
            ⚠ Error
        </div>
        <div style="color:#e6edf3;font-size:13px;">{message}</div>
        {f'<div style="color:#8b949e;font-size:12px;margin-top:8px;">{detail}</div>' if detail else ''}
    </div>
    """, unsafe_allow_html=True)


def loading_state(message: str = "Loading..."):
    st.markdown(f"""
    <div style="text-align:center;padding:40px;color:#8b949e;font-size:13px;">
        <div style="margin-bottom:12px;font-size:20px;">⟳</div>
        {message}
    </div>
    """, unsafe_allow_html=True)