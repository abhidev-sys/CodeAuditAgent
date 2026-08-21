"""
Static Analysis Engine

Kya karta hai:
- Bandit se Python security issues scan karta hai
- Semgrep se custom patterns check karta hai
- Dono results merge karta hai
- Duplicate findings remove karta hai

Kyun dono tools?
- Bandit = broad coverage, fast
- Semgrep = precise custom rules
- Combined = best of both worlds
"""

import json
import subprocess
import tempfile
import os
from dataclasses import dataclass, field
from pathlib import Path
from app.core.logger import get_logger

logger = get_logger("static_analyzer")


@dataclass
class StaticFinding:
    """
    Static analysis se mila ek finding.
    Baad mein LLM isse verify karega.
    """
    # Tool jisne yeh dhundha
    tool: str                    # "bandit", "semgrep", "custom"
    # Vulnerability type
    vuln_type: str               # "SQLI", "XSS", "SECRETS", etc.
    # Severity
    severity: str                # "CRITICAL", "HIGH", "MEDIUM", "LOW"
    # File aur line
    file_path: str
    line_start: int
    line_end: int
    # Code snippet
    code_snippet: str
    # Description
    description: str
    # CWE ID
    cwe_id: str = ""
    # Confidence from static tool
    confidence: float = 0.5
    # Tool-specific metadata
    metadata: dict = field(default_factory=dict)


@dataclass
class StaticAnalysisReport:
    """Complete static analysis report for a repository."""
    repository_path: str
    findings: list[StaticFinding] = field(default_factory=list)
    # Tool-wise counts
    bandit_count: int = 0
    semgrep_count: int = 0
    custom_count: int = 0
    # Severity breakdown
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    # Scan success?
    bandit_success: bool = False
    semgrep_success: bool = False
    error: str = ""


def run_static_analysis(repository_path: str) -> StaticAnalysisReport:
    """
    Complete static analysis run karo.

    Steps:
    1. Bandit run karo
    2. Semgrep run karo (agar available ho)
    3. Custom patterns check karo
    4. Results merge karo
    5. Severity count karo

    Args:
        repository_path: Repository ka local path

    Returns:
        StaticAnalysisReport with all findings
    """
    report = StaticAnalysisReport(repository_path=repository_path)

    logger.info("Starting static analysis", path=repository_path)

    # Step 1: Bandit
    bandit_findings = _run_bandit(repository_path)
    report.findings.extend(bandit_findings)
    report.bandit_count = len(bandit_findings)
    report.bandit_success = True
    logger.info("Bandit complete", findings=len(bandit_findings))

    # Step 2: Semgrep (optional — skip if not installed)
    try:
        semgrep_findings = _run_semgrep(repository_path)
        report.findings.extend(semgrep_findings)
        report.semgrep_count = len(semgrep_findings)
        report.semgrep_success = True
        logger.info("Semgrep complete", findings=len(semgrep_findings))
    except Exception as e:
        logger.warning("Semgrep skipped", error=str(e))

    # Step 3: Custom patterns
    custom_findings = _run_custom_patterns(repository_path)
    report.findings.extend(custom_findings)
    report.custom_count = len(custom_findings)
    logger.info("Custom patterns complete", findings=len(custom_findings))

    # Step 4: Deduplicate
    report.findings = _deduplicate_findings(report.findings)

    # Step 5: Severity counts
    for f in report.findings:
        if f.severity == "CRITICAL":
            report.critical_count += 1
        elif f.severity == "HIGH":
            report.high_count += 1
        elif f.severity == "MEDIUM":
            report.medium_count += 1
        else:
            report.low_count += 1

    logger.info(
        "Static analysis complete",
        total=len(report.findings),
        critical=report.critical_count,
        high=report.high_count,
        medium=report.medium_count,
        low=report.low_count,
    )

    return report


def _run_bandit(repository_path: str) -> list[StaticFinding]:
    """
    Bandit security scanner run karo.

    Bandit kya karta hai:
    - Python code mein common security issues scan karta hai
    - AST-based analysis use karta hai
    - CWE IDs assign karta hai
    - JSON output deta hai (easy to parse)
    """
    findings = []

    try:
        # Bandit command — JSON output format
        cmd = [
            "bandit",
            "-r",                    # Recursive scan
            repository_path,
            "-f", "json",            # JSON format
            "-q",                    # Quiet mode
            "--exit-zero",           # Exit 0 even if findings found
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )

        if not result.stdout:
            logger.warning("Bandit returned no output")
            return findings

        # JSON parse karo
        data = json.loads(result.stdout)
        results = data.get("results", [])

        for item in results:
            finding = _parse_bandit_result(item, repository_path)
            if finding:
                findings.append(finding)

    except subprocess.TimeoutExpired:
        logger.error("Bandit timed out")
    except json.JSONDecodeError as e:
        logger.error("Bandit JSON parse failed", error=str(e))
    except FileNotFoundError:
        logger.error("Bandit not found — install with: pip install bandit")
    except Exception as e:
        logger.error("Bandit failed", error=str(e))

    return findings


def _parse_bandit_result(item: dict, repo_path: str) -> StaticFinding | None:
    """Bandit ka ek result parse karo."""
    try:
        # Severity map karo
        severity_map = {
            "HIGH": "HIGH",
            "MEDIUM": "MEDIUM",
            "LOW": "LOW",
        }
        severity = severity_map.get(
            item.get("issue_severity", "LOW"), "LOW"
        )

        # Confidence map karo
        confidence_map = {
            "HIGH": 0.85,
            "MEDIUM": 0.65,
            "LOW": 0.45,
        }
        confidence = confidence_map.get(
            item.get("issue_confidence", "LOW"), 0.45
        )

        # Vulnerability type determine karo
        test_id = item.get("test_id", "")
        test_name = item.get("test_name", "")
        vuln_type = _map_bandit_to_vuln_type(test_id, test_name)

        # File path relative banao
        file_path = item.get("filename", "")
        try:
            file_path = str(Path(file_path).relative_to(repo_path))
        except ValueError:
            pass

        return StaticFinding(
            tool="bandit",
            vuln_type=vuln_type,
            severity=severity,
            file_path=file_path,
            line_start=item.get("line_number", 0),
            line_end=item.get("line_number", 0),
            code_snippet=item.get("code", "")[:300],
            description=item.get("issue_text", ""),
            cwe_id=item.get("issue_cwe", {}).get("id", ""),
            confidence=confidence,
            metadata={
                "test_id": test_id,
                "test_name": test_name,
                "more_info": item.get("more_info", ""),
            },
        )

    except Exception as e:
        logger.warning("Failed to parse bandit result", error=str(e))
        return None


def _map_bandit_to_vuln_type(test_id: str, test_name: str) -> str:
    """Bandit test ID ko hamara vulnerability type mein convert karo."""
    mappings = {
        "B608": "SQLI",           # SQL injection
        "B703": "XSS",            # Django XSS
        "B501": "SECRETS",        # Hardcoded password
        "B106": "SECRETS",        # Hardcoded password func arg
        "B107": "SECRETS",        # Hardcoded password default
        "B105": "SECRETS",        # Hardcoded password string
        "B301": "DESERIALIZATION", # Pickle
        "B302": "DESERIALIZATION", # Marshal
        "B303": "DESERIALIZATION", # MD5 weak hash
        "B310": "SSRF",           # URL open
        "B311": "SSRF",           # Random not crypto
        "B602": "COMMAND_INJECTION", # Subprocess shell=True
        "B603": "COMMAND_INJECTION", # Subprocess without shell
        "B605": "COMMAND_INJECTION", # os.system
        "B201": "XSS",            # Flask debug=True
    }

    vuln = mappings.get(test_id)
    if vuln:
        return vuln

    # Test name se guess karo
    name_lower = test_name.lower()
    if "sql" in name_lower:
        return "SQLI"
    elif "xss" in name_lower or "cross" in name_lower:
        return "XSS"
    elif "secret" in name_lower or "password" in name_lower or "hardcoded" in name_lower:
        return "SECRETS"
    elif "pickle" in name_lower or "deserializ" in name_lower:
        return "DESERIALIZATION"
    elif "ssrf" in name_lower or "request" in name_lower:
        return "SSRF"
    elif "subprocess" in name_lower or "shell" in name_lower:
        return "COMMAND_INJECTION"

    return "GENERAL"


def _run_semgrep(repository_path: str) -> list[StaticFinding]:
    """
    Semgrep run karo custom rules ke saath.

    Semgrep kya karta hai:
    - AST-level pattern matching
    - Custom YAML rules support karta hai
    - False positives kam hote hain
    - Multiple languages support
    """
    findings = []

    # Custom rules directory
    rules_dir = Path(__file__).parent / "rules"

    if not rules_dir.exists():
        logger.warning("Semgrep rules directory not found")
        return findings

    try:
        cmd = [
            "semgrep",
            "--config", str(rules_dir),
            repository_path,
            "--json",
            "--quiet",
            "--no-git-ignore",
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.stdout:
            data = json.loads(result.stdout)
            for item in data.get("results", []):
                finding = _parse_semgrep_result(item, repository_path)
                if finding:
                    findings.append(finding)

    except FileNotFoundError:
        raise Exception("Semgrep not installed")
    except Exception as e:
        raise Exception(f"Semgrep failed: {e}")

    return findings


def _parse_semgrep_result(item: dict, repo_path: str) -> StaticFinding | None:
    """Semgrep ka ek result parse karo."""
    try:
        file_path = item.get("path", "")
        try:
            file_path = str(Path(file_path).relative_to(repo_path))
        except ValueError:
            pass

        metadata = item.get("extra", {}).get("metadata", {})
        severity = metadata.get("severity", "MEDIUM").upper()
        vuln_type = metadata.get("vuln_type", "GENERAL")
        cwe = metadata.get("cwe", "")

        return StaticFinding(
            tool="semgrep",
            vuln_type=vuln_type,
            severity=severity,
            file_path=file_path,
            line_start=item.get("start", {}).get("line", 0),
            line_end=item.get("end", {}).get("line", 0),
            code_snippet=item.get("extra", {}).get("lines", "")[:300],
            description=item.get("extra", {}).get("message", ""),
            cwe_id=cwe,
            confidence=0.75,
            metadata={"rule_id": item.get("check_id", "")},
        )

    except Exception as e:
        logger.warning("Failed to parse semgrep result", error=str(e))
        return None


def _run_custom_patterns(repository_path: str) -> list[StaticFinding]:
    """
    Hamare custom patterns run karo.

    Yeh patterns specifically hamari 5 vulnerability types ke liye hain:
    - SQL Injection
    - XSS
    - Hardcoded Secrets
    - SSRF
    - Insecure Deserialization
    """
    findings = []
    repo = Path(repository_path)

    # Sirf Python files scan karo
    python_files = list(repo.rglob("*.py"))

    for file_path in python_files:
        # Skip virtual env aur migrations
        parts = file_path.parts
        if any(p in parts for p in ["venv", ".venv", "migrations", "__pycache__"]):
            continue

        try:
            source = file_path.read_text(encoding="utf-8", errors="ignore")
            lines = source.splitlines()

            file_findings = _check_custom_patterns(
                str(file_path), lines, repository_path
            )
            findings.extend(file_findings)

        except Exception as e:
            logger.warning("Custom pattern check failed", file=str(file_path), error=str(e))

    return findings


def _check_custom_patterns(
    file_path: str,
    lines: list[str],
    repo_path: str,
) -> list[StaticFinding]:
    """Ek file mein custom patterns check karo."""
    findings = []

    try:
        rel_path = str(Path(file_path).relative_to(repo_path))
    except ValueError:
        rel_path = file_path

    for line_num, line in enumerate(lines, 1):
        stripped = line.strip()

        # Skip comments
        if stripped.startswith("#"):
            continue

        # 1. SQL Injection patterns
        sqli_finding = _check_sqli_pattern(stripped, line_num, rel_path)
        if sqli_finding:
            findings.append(sqli_finding)

        # 2. Hardcoded Secrets
        secret_finding = _check_secrets_pattern(stripped, line_num, rel_path)
        if secret_finding:
            findings.append(secret_finding)

        # 3. SSRF patterns
        ssrf_finding = _check_ssrf_pattern(stripped, line_num, rel_path)
        if ssrf_finding:
            findings.append(ssrf_finding)

        # 4. Insecure Deserialization
        deser_finding = _check_deserialization_pattern(stripped, line_num, rel_path)
        if deser_finding:
            findings.append(deser_finding)

    return findings


def _check_sqli_pattern(line: str, line_num: int, file_path: str) -> StaticFinding | None:
    """SQL Injection patterns check karo."""

    # Pattern 1: String concatenation in SQL query
    sql_keywords = ["select ", "insert ", "update ", "delete ", "where "]
    has_sql = any(kw in line.lower() for kw in sql_keywords)
    has_concat = "+" in line or "%" in line or ".format(" in line or "f'" in line or 'f"' in line

    if has_sql and has_concat:
        return StaticFinding(
            tool="custom",
            vuln_type="SQLI",
            severity="HIGH",
            file_path=file_path,
            line_start=line_num,
            line_end=line_num,
            code_snippet=line[:200],
            description="Potential SQL injection: SQL query with string formatting",
            cwe_id="CWE-89",
            confidence=0.75,
        )

    return None


def _check_secrets_pattern(line: str, line_num: int, file_path: str) -> StaticFinding | None:
    """Hardcoded secrets check karo."""
    import re

    # Secret variable names
    secret_vars = [
        "password", "passwd", "secret", "api_key", "apikey",
        "token", "auth_token", "access_token", "private_key",
        "aws_secret", "db_password",
    ]

    line_lower = line.lower()

    for secret_var in secret_vars:
        if secret_var in line_lower and "=" in line:
            # Check karo ki actual string value hai (not a variable reference)
            # Pattern: secret_key = "actual_value"
            pattern = rf'{secret_var}\s*=\s*["\'][^"\'{{}}]+["\']'
            if re.search(pattern, line_lower):
                # Skip placeholder values
                skip_values = [
                    "your_", "example", "placeholder", "changeme",
                    "xxx", "***", "<", ">", "none", "null", ""
                ]
                if not any(skip in line_lower for skip in skip_values):
                    return StaticFinding(
                        tool="custom",
                        vuln_type="SECRETS",
                        severity="CRITICAL",
                        file_path=file_path,
                        line_start=line_num,
                        line_end=line_num,
                        code_snippet=line[:200],
                        description=f"Hardcoded secret detected: {secret_var}",
                        cwe_id="CWE-798",
                        confidence=0.80,
                    )

    return None


def _check_ssrf_pattern(line: str, line_num: int, file_path: str) -> StaticFinding | None:
    """SSRF patterns check karo."""

    # SSRF indicators
    ssrf_patterns = [
        "requests.get(",
        "requests.post(",
        "urllib.request.urlopen(",
        "httpx.get(",
        "httpx.post(",
    ]

    for pattern in ssrf_patterns:
        if pattern in line:
            # Kya URL user input se aa rahi hai?
            user_input_indicators = [
                "request.args", "request.form",
                "request.json", "params[", "data[",
            ]
            # Simple check — LLM deeper verify karega
            return StaticFinding(
                tool="custom",
                vuln_type="SSRF",
                severity="MEDIUM",
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                code_snippet=line[:200],
                description="Potential SSRF: HTTP request — verify URL source",
                cwe_id="CWE-918",
                confidence=0.55,
            )

    return None


def _check_deserialization_pattern(
    line: str, line_num: int, file_path: str
) -> StaticFinding | None:
    """Insecure deserialization patterns check karo."""

    deser_patterns = [
        "pickle.loads(",
        "pickle.load(",
        "marshal.loads(",
        "yaml.load(",        # yaml.safe_load() safe hai
        "shelve.open(",
    ]

    for pattern in deser_patterns:
        if pattern in line:
            # yaml.load() check — safe_load safe hai
            if "yaml.load(" in pattern and "safe_load" in line:
                continue

            return StaticFinding(
                tool="custom",
                vuln_type="DESERIALIZATION",
                severity="HIGH",
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                code_snippet=line[:200],
                description=f"Insecure deserialization: {pattern}",
                cwe_id="CWE-502",
                confidence=0.85,
            )

    return None


def _deduplicate_findings(findings: list[StaticFinding]) -> list[StaticFinding]:
    """
    Duplicate findings remove karo.

    Same file + same line + same vuln_type = duplicate
    """
    seen = set()
    unique = []

    for f in findings:
        key = (f.file_path, f.line_start, f.vuln_type)
        if key not in seen:
            seen.add(key)
            unique.append(f)

    removed = len(findings) - len(unique)
    if removed > 0:
        logger.info("Deduplicated findings", removed=removed)

    return unique