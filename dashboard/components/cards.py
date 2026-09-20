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
    pct = max(0, min(100, score))

    st.markdown(f"""
    <div style="background:#161b22;border:1px solid #21262d;
        border-radius:8px;padding:20px 24px;">
        <div style="display:flex;align-items:flex-end;
            gap:12px;margin-bottom:8px;">
            <div style="font-size:48px;font-weight:700;
                color:{color};line-height:1;">{score}</div>
            <div style="color:#6e7681;font-size:18px;
                margin-bottom:8px;">/100</div>
            <div style="margin-left:auto;">
                <span style="background:{'rgba(248,81,73,.15)' if level=='CRITICAL' else 'rgba(210,153,34,.15)' if level=='HIGH' else 'rgba(187,128,9,.15)' if level=='MEDIUM' else 'rgba(35,134,54,.15)'};
                color:{color};border:1px solid {color}40;
                border-radius:100px;padding:5px 14px;
                font-size:12px;font-weight:600;
                letter-spacing:.5px;">{level} RISK</span>
            </div>
        </div>
        <div style="background:#21262d;height:6px;
            border-radius:3px;overflow:hidden;margin:8px 0;">
            <div style="width:{pct}%;height:100%;
                background:{color};border-radius:3px;"></div>
        </div>
        <div style="display:flex;justify-content:space-between;
            font-size:10px;color:#6e7681;margin-top:4px;
            font-family:'JetBrains Mono',monospace;">
            <span>0 SAFE</span>
            <span>20 LOW</span>
            <span>40 MEDIUM</span>
            <span>70 HIGH</span>
            <span>100 CRITICAL</span>
        </div>
    </div>
    """, unsafe_allow_html=True)