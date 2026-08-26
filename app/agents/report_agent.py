"""
Audit Report Engine — Final Agent

Responsibility:
- Scan ke saare results collect karna
- Risk score calculate karna
- Professional security report banana
- JSON + Human-readable format mein output dena
- Database mein save karna
"""

import json
from datetime import datetime
from dataclasses import dataclass, field
from pathlib import Path
from app.agents.state import ScanState
from app.core.logger import get_logger

logger = get_logger("report_agent")

SEVERITY_WEIGHTS = {
    "CRITICAL": 40,
    "HIGH": 25,
    "MEDIUM": 10,
    "LOW": 5,
    "INFO": 1,
}

CWE_DESCRIPTIONS = {
    "CWE-89": "SQL Injection — Improper Neutralization of Special Elements in SQL Commands",
    "CWE-79": "Cross-site Scripting (XSS) — Improper Neutralization of Input During Web Page Generation",
    "CWE-798": "Use of Hard-coded Credentials",
    "CWE-918": "Server-Side Request Forgery (SSRF)",
    "CWE-502": "Deserialization of Untrusted Data",
    "CWE-78": "OS Command Injection",
    "CWE-22": "Path Traversal",
}

RECOMMENDATIONS = {
    "SQLI": [
        "Use parameterized queries or prepared statements for all SQL operations",
        "Implement an ORM (SQLAlchemy) to abstract direct SQL execution",
        "Apply input validation and whitelist acceptable characters",
        "Use least-privilege database accounts",
        "Enable SQL query logging for monitoring",
    ],
    "XSS": [
        "Use template engines with auto-escaping enabled (Jinja2, etc.)",
        "Implement Content Security Policy (CSP) headers",
        "Sanitize all user input before rendering in HTML",
        "Use HTTPOnly and Secure flags for cookies",
        "Validate and encode output based on context",
    ],
    "SECRETS": [
        "Move all secrets to environment variables immediately",
        "Use a secrets manager (HashiCorp Vault, AWS Secrets Manager)",
        "Rotate all exposed credentials immediately",
        "Add pre-commit hooks to prevent secret commits",
        "Audit git history for previously committed secrets",
    ],
    "SSRF": [
        "Implement URL allowlist for all outbound HTTP requests",
        "Validate and sanitize user-supplied URLs",
        "Use a network firewall to restrict outbound connections",
        "Disable unnecessary URL schemes (file://, gopher://, etc.)",
        "Implement response validation before processing",
    ],
    "DESERIALIZATION": [
        "Replace pickle with JSON for data serialization",
        "Never deserialize untrusted data",
        "Implement integrity checks before deserialization",
        "Use language-agnostic data formats (JSON, MessagePack)",
        "Apply allowlisting for acceptable classes during deserialization",
    ],
}


@dataclass
class AuditReport:
    """Complete security audit report."""
    report_id: str
    scan_id: str
    repository_name: str
    repository_path: str
    generated_at: str
    scan_duration_seconds: float
    risk_score: int
    risk_level: str
    risk_summary: str
    total_findings: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    total_patches: int
    successful_patches: int
    patch_success_rate: float
    findings: list[dict] = field(default_factory=list)
    patches: list[dict] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    executive_summary: str = ""
    frameworks_detected: list[str] = field(default_factory=list)
    language: str = ""
    files_analyzed: int = 0


def report_node(state: ScanState) -> dict:
    """LangGraph node — Audit Report Generation."""
    scan_id = state["scan_id"]
    logger.info("Report Agent starting", scan_id=scan_id)

    try:
        vulnerabilities = state.get("vulnerabilities", [])
        patches = state.get("patches", [])
        repo_summary = state.get("repo_summary", {})

        risk_score = _calculate_risk_score(vulnerabilities)
        risk_level = _get_risk_level(risk_score)

        critical = sum(1 for v in vulnerabilities if v.get("severity") == "CRITICAL")
        high = sum(1 for v in vulnerabilities if v.get("severity") == "HIGH")
        medium = sum(1 for v in vulnerabilities if v.get("severity") == "MEDIUM")
        low = sum(1 for v in vulnerabilities if v.get("severity") == "LOW")

        successful_patches = sum(1 for p in patches if p.get("success"))
        patch_rate = successful_patches / len(patches) if patches else 0.0

        all_recommendations = []
        seen_types = set()
        for vuln in vulnerabilities:
            vtype = vuln.get("vuln_type", "")
            if vtype not in seen_types:
                recs = RECOMMENDATIONS.get(vtype, [])
                all_recommendations.extend(recs[:3])
                seen_types.add(vtype)

        formatted_findings = _format_findings(vulnerabilities, patches)

        executive_summary = _generate_executive_summary(
            risk_score=risk_score,
            risk_level=risk_level,
            total_findings=len(vulnerabilities),
            critical=critical,
            high=high,
            medium=medium,
            low=low,
            successful_patches=successful_patches,
            total_patches=len(patches),
            repo_name=state["repository_path"].split("/")[-1],
        )

        report = AuditReport(
            report_id=f"RPT-{scan_id[:8].upper()}",
            scan_id=scan_id,
            repository_name=state["repository_path"].split("/")[-1],
            repository_path=state["repository_path"],
            generated_at=datetime.now().isoformat(),
            scan_duration_seconds=0.0,
            risk_score=risk_score,
            risk_level=risk_level,
            risk_summary=_get_risk_summary(risk_score, len(vulnerabilities)),
            total_findings=len(vulnerabilities),
            critical_count=critical,
            high_count=high,
            medium_count=medium,
            low_count=low,
            total_patches=len(patches),
            successful_patches=successful_patches,
            patch_success_rate=patch_rate,
            findings=formatted_findings,
            patches=patches,
            recommendations=all_recommendations,
            executive_summary=executive_summary,
            frameworks_detected=state.get("frameworks", []),
            language=state.get("language", ""),
            files_analyzed=repo_summary.get("analyzable_files", 0),
        )

        report_path = _save_report(report, scan_id)

        logger.info(
            "Report Agent complete",
            scan_id=scan_id,
            risk_score=risk_score,
            risk_level=risk_level,
            findings=len(vulnerabilities),
            report_path=report_path,
        )

        return {
            "current_step": "report_complete",
            "risk_score": risk_score,
            "agent_log": [
                f"ReportAgent: Risk Score={risk_score}/100 ({risk_level}), "
                f"{len(vulnerabilities)} findings, "
                f"{successful_patches}/{len(patches)} patches successful"
            ],
        }

    except Exception as e:
        logger.error("Report Agent failed", error=str(e))
        import traceback
        traceback.print_exc()
        return {
            "errors": [f"ReportAgent failed: {str(e)}"],
            "current_step": "report_failed",
            "agent_log": [f"ReportAgent: FAILED - {str(e)}"],
        }


def _calculate_risk_score(vulnerabilities: list[dict]) -> int:
    """Risk score calculate karo 0-100."""
    if not vulnerabilities:
        return 0
    total = 0
    for vuln in vulnerabilities:
        severity = vuln.get("severity", "LOW")
        confidence = float(vuln.get("confidence", 0.5))
        weight = SEVERITY_WEIGHTS.get(severity, 5)
        total += weight * confidence
    return min(int(total), 100)


def _get_risk_level(score: int) -> str:
    """Risk score se risk level nikalo."""
    if score >= 75:
        return "CRITICAL"
    elif score >= 50:
        return "HIGH"
    elif score >= 25:
        return "MEDIUM"
    elif score > 0:
        return "LOW"
    else:
        return "SAFE"


def _get_risk_summary(score: int, finding_count: int) -> str:
    """Short risk summary."""
    if score == 0:
        return "No vulnerabilities detected. Repository appears secure."
    elif score < 25:
        return f"Low risk. {finding_count} minor issue(s) detected."
    elif score < 50:
        return f"Medium risk. {finding_count} vulnerability(ies) require attention."
    elif score < 75:
        return f"High risk. {finding_count} significant vulnerability(ies) detected."
    else:
        return f"Critical risk. Immediate action required - {finding_count} severe vulnerability(ies)."


def _format_findings(
    vulnerabilities: list[dict],
    patches: list[dict],
) -> list[dict]:
    """Findings ko report format mein convert karo."""
    formatted = []
    patch_by_index = {p.get("finding_id"): p for p in patches}

    for i, vuln in enumerate(vulnerabilities):
        finding_id = f"finding_{i}"
        patch = patch_by_index.get(finding_id)
        cwe_id = vuln.get("cwe_id", "")
        cwe_desc = CWE_DESCRIPTIONS.get(cwe_id, "")

        formatted.append({
            "finding_number": i + 1,
            "finding_id": finding_id,
            "vuln_type": vuln.get("vuln_type"),
            "severity": vuln.get("severity"),
            "confidence": vuln.get("confidence"),
            "file_path": vuln.get("file_path"),
            "line_start": vuln.get("line_start"),
            "line_end": vuln.get("line_end"),
            "description": vuln.get("description"),
            "evidence": vuln.get("evidence", ""),
            "cwe_id": cwe_id,
            "cwe_description": cwe_desc,
            "reasoning": vuln.get("reasoning", ""),
            "patch_available": patch is not None and patch.get("success", False),
            "patch_summary": patch.get("changes_summary", "") if patch else "",
            "unified_diff": patch.get("unified_diff", "") if patch else "",
        })

    return formatted


def _generate_executive_summary(
    risk_score: int,
    risk_level: str,
    total_findings: int,
    critical: int,
    high: int,
    medium: int,
    low: int,
    successful_patches: int,
    total_patches: int,
    repo_name: str,
) -> str:
    """Professional executive summary generate karo."""
    if total_findings == 0:
        return (
            f"Security audit of repository '{repo_name}' completed successfully. "
            f"No vulnerabilities were detected."
        )

    severity_breakdown = []
    if critical:
        severity_breakdown.append(f"{critical} critical")
    if high:
        severity_breakdown.append(f"{high} high")
    if medium:
        severity_breakdown.append(f"{medium} medium")
    if low:
        severity_breakdown.append(f"{low} low")

    breakdown_str = ", ".join(severity_breakdown)
    patch_info = ""
    if total_patches > 0:
        patch_info = (
            f" Automated patches were generated for {successful_patches} "
            f"of {total_patches} finding(s)."
        )

    return (
        f"Security audit of repository '{repo_name}' identified {total_findings} "
        f"vulnerability(ies) with an overall risk score of {risk_score}/100 ({risk_level} risk). "
        f"Findings include {breakdown_str} severity issue(s)."
        f"{patch_info} "
        f"Immediate remediation is recommended for all high and critical severity findings."
    )


def _save_report(report: AuditReport, scan_id: str) -> str:
    """Report ko file mein save karo."""
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)

    json_path = reports_dir / f"report_{scan_id[:8]}.json"
    txt_path = reports_dir / f"report_{scan_id[:8]}.txt"

    report_dict = {
        "report_id": report.report_id,
        "scan_id": report.scan_id,
        "generated_at": report.generated_at,
        "repository": {
            "name": report.repository_name,
            "path": report.repository_path,
            "language": report.language,
            "frameworks": report.frameworks_detected,
            "files_analyzed": report.files_analyzed,
        },
        "risk_assessment": {
            "score": report.risk_score,
            "level": report.risk_level,
            "summary": report.risk_summary,
        },
        "findings_summary": {
            "total": report.total_findings,
            "critical": report.critical_count,
            "high": report.high_count,
            "medium": report.medium_count,
            "low": report.low_count,
        },
        "patch_summary": {
            "total": report.total_patches,
            "successful": report.successful_patches,
            "success_rate": report.patch_success_rate,
        },
        "executive_summary": report.executive_summary,
        "findings": report.findings,
        "recommendations": report.recommendations,
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report_dict, f, indent=2)

    txt_content = _generate_text_report(report)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(txt_content)

    logger.info(
        "Reports saved",
        json=str(json_path),
        txt=str(txt_path),
    )

    return str(json_path)


def _generate_text_report(report: AuditReport) -> str:
    """Human-readable text report generate karo."""
    lines = []

    # Header
    lines.append("=" * 60)
    lines.append("      CODEAUDITAGENT SECURITY AUDIT REPORT")
    lines.append("=" * 60)
    lines.append(f"Report ID   : {report.report_id}")
    lines.append(f"Generated   : {report.generated_at}")
    lines.append(f"Repository  : {report.repository_name}")
    lines.append(f"Language    : {report.language}")
    lines.append(f"Frameworks  : {', '.join(report.frameworks_detected) or 'None detected'}")
    lines.append(f"Files Scanned: {report.files_analyzed}")
    lines.append("")

    # Risk Score Box
    lines.append("+" + "-" * 40 + "+")
    lines.append(f"|  RISK SCORE : {report.risk_score}/100 ({report.risk_level:<10})      |")
    lines.append("+" + "-" * 40 + "+")
    lines.append(f"|  CRITICAL : {report.critical_count:<5}  HIGH   : {report.high_count:<5}          |")
    lines.append(f"|  MEDIUM   : {report.medium_count:<5}  LOW    : {report.low_count:<5}          |")
    lines.append("+" + "-" * 40 + "+")
    lines.append("")

    # Executive Summary
    lines.append("EXECUTIVE SUMMARY")
    lines.append("-" * 60)
    lines.append(report.executive_summary)
    lines.append("")

    # Patch Stats
    lines.append("PATCH SUMMARY")
    lines.append("-" * 60)
    lines.append(f"Total Patches    : {report.total_patches}")
    lines.append(f"Successful       : {report.successful_patches}")
    lines.append(f"Success Rate     : {report.patch_success_rate:.0%}")
    lines.append("")

    # Findings
    lines.append("DETAILED FINDINGS")
    lines.append("=" * 60)

    if not report.findings:
        lines.append("No vulnerabilities detected.")
    else:
        for finding in report.findings:
            lines.append("")
            lines.append(
                f"Finding #{finding['finding_number']} - "
                f"{finding['vuln_type']} [{finding['severity']}]"
            )
            lines.append("-" * 60)
            lines.append(f"File         : {finding['file_path']}")
            lines.append(f"Line         : {finding['line_start']}")
            lines.append(f"Confidence   : {float(finding['confidence']):.0%}")
            lines.append(f"CWE          : {finding['cwe_id']}")
            lines.append(f"CWE Desc     : {finding['cwe_description']}")
            lines.append("")
            lines.append("Description  :")
            lines.append(f"  {finding['description']}")
            lines.append("")

            if finding.get("patch_available"):
                lines.append("[PATCH AVAILABLE]")
                diff = finding.get("unified_diff", "")
                if diff:
                    lines.append("")
                    lines.append("Unified Diff :")
                    lines.append(diff)
            else:
                lines.append("[NO PATCH AVAILABLE]")

            lines.append("")

    # Recommendations
    if report.recommendations:
        lines.append("RECOMMENDATIONS")
        lines.append("=" * 60)
        for i, rec in enumerate(report.recommendations, 1):
            lines.append(f"{i}. {rec}")
        lines.append("")

    # Footer
    lines.append("=" * 60)
    lines.append("Generated by CodeAuditAgent")
    lines.append("Detect -> Reason -> Patch -> Verify")
    lines.append("=" * 60)

    return "\n".join(lines)