"""Formatting utilities for CodeAuditAgent dashboard."""

from datetime import datetime


def fmt_datetime(dt_str: str | None, fmt: str = "%b %d, %Y %H:%M") -> str:
    if not dt_str:
        return "—"
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return dt.strftime(fmt)
    except Exception:
        return dt_str[:16] if dt_str else "—"


def fmt_date(dt_str: str | None) -> str:
    return fmt_datetime(dt_str, "%b %d, %Y")


def fmt_confidence(conf) -> str:
    if conf is None:
        return "N/A"
    try:
        return f"{float(conf):.0%}"
    except Exception:
        return str(conf)


def fmt_risk_level(score: int | None) -> tuple[str, str]:
    """Returns (level_label, css_color)."""
    if score is None:
        return "N/A", "#8b949e"
    if score >= 71:
        return "CRITICAL", "#f85149"
    if score >= 41:
        return "HIGH", "#d29922"
    if score >= 21:
        return "MEDIUM", "#bb8009"
    if score > 0:
        return "LOW", "#3fb950"
    return "SAFE", "#3fb950"


def fmt_severity_color(severity: str) -> str:
    colors = {
        "CRITICAL": "#f85149",
        "HIGH":     "#d29922",
        "MEDIUM":   "#bb8009",
        "LOW":      "#3fb950",
        "INFO":     "#58a6ff",
    }
    return colors.get(severity.upper(), "#8b949e")


def fmt_status_badge(status: str) -> str:
    cls = {
        "COMPLETED": "badge-success",
        "RUNNING":   "badge-running",
        "PENDING":   "badge-pending",
        "FAILED":    "badge-failed",
        "OPEN":      "badge-high",
        "RESOLVED":  "badge-success",
    }.get(status.upper(), "badge-info")
    return f'<span class="badge {cls}">{status}</span>'


def fmt_severity_badge(severity: str) -> str:
    cls = {
        "CRITICAL": "badge-critical",
        "HIGH":     "badge-high",
        "MEDIUM":   "badge-medium",
        "LOW":      "badge-low",
        "INFO":     "badge-info",
    }.get(severity.upper(), "badge-info")
    return f'<span class="badge {cls}">{severity}</span>'


def shorten_id(uid: str, length: int = 8) -> str:
    return str(uid)[:length].upper() if uid else "—"


def fmt_score_bar(score: int, color: str) -> str:
    pct = max(0, min(100, score))
    return f"""
    <div class="risk-bar-track">
      <div class="risk-bar-fill" style="width:{pct}%;background:{color};"></div>
    </div>
    """