"""Metric and info card components."""
import streamlit as st
from dashboard.utils.formatting import fmt_risk_level, fmt_score_bar


def metric_card(label: str, value, sub: str = "", icon: str = ""):
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{icon} {label}</div>
        <div class="metric-value">{value}</div>
        {f'<div class="metric-sub">{sub}</div>' if sub else ''}
    </div>
    """, unsafe_allow_html=True)


def risk_card(score: int | None):
    """Professional risk score display."""
    if score is None:
        score = 0
    level, color = fmt_risk_level(score)
    bar = fmt_score_bar(score, color)

    st.markdown(f"""
    <div class="risk-meter">
        <div style="display:flex;align-items:flex-end;gap:12px;margin-bottom:4px;">
            <div class="risk-score-display" style="color:{color};">{score}</div>
            <div style="color:#6e7681;font-size:18px;margin-bottom:8px;">/100</div>
            <div style="margin-left:auto;">
                <span class="badge" style="
                    background:{'rgba(248,81,73,' if level=='CRITICAL' else 'rgba(210,153,34,' if level=='HIGH' else 'rgba(187,128,9,' if level=='MEDIUM' else 'rgba(35,134,54,'}0.15);
                    color:{color};
                    border:1px solid {color}40;
                    font-size:12px;padding:5px 14px;
                ">{level} RISK</span>
            </div>
        </div>
        {bar}
        <div style="display:flex;justify-content:space-between;
            font-size:10px;color:#6e7681;margin-top:4px;font-family:'JetBrains Mono',monospace;">
            <span>0 — SAFE</span>
            <span>20 — LOW</span>
            <span>40 — MEDIUM</span>
            <span>70 — HIGH</span>
            <span>100 — CRITICAL</span>
        </div>
    </div>
    """, unsafe_allow_html=True)