"""
Vulnerability Detection Agent — Agent 2

Responsibility:
- Static findings + AST evidence + Data flow combine karna
- LLM se verify karna ki finding real hai ya false positive
- Confidence score assign karna
- CWE ID assign karna
- Structured Finding output banana

Philosophy:
- Static analysis FIRST (fast, no cost)
- LLM SECOND (only for suspicious candidates)
- Evidence-based reasoning — LLM ko proof chahiye
"""

from pydantic import BaseModel, Field
from app.agents.state import ScanState
from app.llm.factory import get_llm
from app.core.logger import get_logger
import json

logger = get_logger("vuln_detection_agent")


class VulnerabilityFinding(BaseModel):
    """
    Structured vulnerability finding.
    Pydantic se LLM output validate hoti hai.
    """
    vuln_type: str = Field(
        description="SQLI, XSS, SECRETS, SSRF, or DESERIALIZATION"
    )
    severity: str = Field(
        description="CRITICAL, HIGH, MEDIUM, or LOW"
    )
    confidence: float = Field(
        description="0.0 to 1.0 — how confident are you?",
        ge=0.0, le=1.0
    )
    file_path: str = Field(description="Affected file path")
    line_start: int = Field(description="Starting line number")
    line_end: int = Field(description="Ending line number")
    description: str = Field(description="Clear explanation of the vulnerability")
    cwe_id: str = Field(description="CWE ID like CWE-89")
    evidence: str = Field(description="Code evidence supporting this finding")
    is_false_positive: bool = Field(
        description="Is this likely a false positive?"
    )
    reasoning: str = Field(description="Your step-by-step reasoning")


def vuln_detection_node(state: ScanState) -> dict:
    """
    LangGraph node — Vulnerability Detection.

    Strategy:
    1. Static findings ko candidates banao
    2. Data flow evidence add karo
    3. Code chunk nikalo
    4. LLM se verify karo
    5. Structured findings return karo

    Args:
        state: Current scan state

    Returns:
        Dict with vulnerabilities list
    """
    scan_id = state["scan_id"]
    static_findings = state.get("static_findings", [])
    data_flow_results = state.get("data_flow_results", {})
    code_chunks = state.get("code_chunks", [])

    logger.info(
        "Vuln Detection Agent starting",
        scan_id=scan_id,
        static_findings=len(static_findings),
    )

    if not static_findings:
        logger.info("No static findings — skipping LLM analysis")
        return {
            "vulnerabilities": [],
            "current_step": "vuln_detection_complete",
            "agent_log": ["VulnDetectionAgent: No static findings to analyze"],
        }

    llm = get_llm(temperature=0.1)
    vulnerabilities = []

    # Har static finding ke liye LLM verify karo
    for finding in static_findings:
        try:
            vuln = _analyze_finding_with_llm(
                finding=finding,
                data_flow_results=data_flow_results,
                code_chunks=code_chunks,
                llm=llm,
                scan_id=scan_id,
            )

            if vuln and not vuln.get("is_false_positive"):
                vulnerabilities.append(vuln)
                logger.info(
                    "Vulnerability confirmed",
                    type=vuln["vuln_type"],
                    file=vuln["file_path"],
                    line=vuln["line_start"],
                    confidence=vuln["confidence"],
                )

        except Exception as e:
            logger.error(
                "Finding analysis failed",
                error=str(e),
                finding=finding.get("file_path"),
            )
            continue

    logger.info(
        "Vuln Detection Agent complete",
        scan_id=scan_id,
        confirmed=len(vulnerabilities),
        total_checked=len(static_findings),
    )

    return {
        "vulnerabilities": vulnerabilities,
        "current_step": "vuln_detection_complete",
        "agent_log": [
            f"VulnDetectionAgent: {len(vulnerabilities)} confirmed "
            f"from {len(static_findings)} candidates"
        ],
    }


def _analyze_finding_with_llm(
    finding: dict,
    data_flow_results: dict,
    code_chunks: list[dict],
    llm,
    scan_id: str,
) -> dict | None:
    """
    LLM se ek finding verify karo.

    Strategy:
    1. Relevant code chunk nikalo
    2. Data flow evidence nikalo
    3. LLM ko structured prompt do
    4. Structured output parse karo
    """

    file_path = finding.get("file_path", "")
    line_start = finding.get("line_start", 0)
    vuln_type = finding.get("vuln_type", "")

    # Relevant code chunk nikalo
    relevant_chunk = _get_relevant_chunk(
        code_chunks, file_path, line_start
    )

    # Data flow evidence nikalo
    df_evidence = _get_data_flow_evidence(
        data_flow_results, file_path, vuln_type
    )

    # Prompt banao
    prompt = _build_analysis_prompt(
        finding=finding,
        code_chunk=relevant_chunk,
        df_evidence=df_evidence,
    )

    try:
        # LLM call karo
        from langchain_core.messages import HumanMessage, SystemMessage

        messages = [
            SystemMessage(content=_get_system_prompt()),
            HumanMessage(content=prompt),
        ]

        response = llm.invoke(messages)
        response_text = response.content

        # JSON parse karo
        result = _parse_llm_response(response_text, finding)
        return result

    except Exception as e:
        logger.error("LLM analysis failed", error=str(e))
        # LLM fail hone pe static finding as-is return karo
        return {
            "vuln_type": finding.get("vuln_type"),
            "severity": finding.get("severity"),
            "confidence": finding.get("confidence", 0.5),
            "file_path": file_path,
            "line_start": line_start,
            "line_end": finding.get("line_end", line_start),
            "description": finding.get("description"),
            "cwe_id": finding.get("cwe_id", ""),
            "evidence": finding.get("code_snippet", ""),
            "is_false_positive": False,
            "reasoning": "Static analysis finding — LLM verification failed",
        }


def _get_relevant_chunk(
    code_chunks: list[dict],
    file_path: str,
    line_num: int,
) -> str:
    """File aur line ke liye relevant code chunk nikalo."""

    # Pehle suspicious chunks check karo
    for chunk in code_chunks:
        if (chunk.get("file_path") == file_path
                and chunk.get("is_suspicious")
                and chunk.get("start_line", 0) <= line_num <= chunk.get("end_line", 0)):
            return chunk.get("content", "")

    # Phir koi bhi matching chunk
    for chunk in code_chunks:
        if chunk.get("file_path") == file_path:
            return chunk.get("content", "")

    return "Code chunk not available"


def _get_data_flow_evidence(
    data_flow_results: dict,
    file_path: str,
    vuln_type: str,
) -> str:
    """Data flow evidence nikalo."""
    df = data_flow_results.get(file_path, {})
    flows = df.get("taint_flows", [])

    relevant_flows = [
        f for f in flows
        if f.get("vuln_type") == vuln_type
    ]

    if not relevant_flows:
        return "No data flow evidence available"

    evidence_parts = []
    for flow in relevant_flows[:3]:  # Max 3 flows
        evidence_parts.append(
            f"Taint flow: {flow.get('source')} (line {flow.get('source_line')}) "
            f"→ {flow.get('sink')} (line {flow.get('sink_line')}) "
            f"via variable '{flow.get('tainted_variable')}'"
        )

    return "\n".join(evidence_parts)


def _get_system_prompt() -> str:
    """System prompt for vulnerability analysis."""
    return """You are an expert security engineer analyzing Python code for vulnerabilities.

Your job is to verify whether a reported vulnerability is real or a false positive.

RULES:
1. Be precise — false positives waste time
2. Base your analysis on the actual code provided
3. Consider the data flow evidence
4. Assign confidence based on evidence strength
5. Always respond in valid JSON format

VULNERABILITY TYPES:
- SQLI: SQL injection via string concatenation/formatting
- XSS: Cross-site scripting via unescaped user input
- SECRETS: Hardcoded passwords, API keys, tokens
- SSRF: Server-side request forgery via user-controlled URLs
- DESERIALIZATION: Unsafe pickle/yaml/marshal usage

SEVERITY LEVELS:
- CRITICAL: Immediate exploitation possible, high impact
- HIGH: Easily exploitable
- MEDIUM: Requires specific conditions
- LOW: Difficult to exploit"""


def _build_analysis_prompt(
    finding: dict,
    code_chunk: str,
    df_evidence: str,
) -> str:
    """Analysis prompt banao."""
    return f"""Analyze this potential security vulnerability:

REPORTED FINDING:
- Type: {finding.get('vuln_type')}
- File: {finding.get('file_path')}
- Line: {finding.get('line_start')}
- Tool: {finding.get('tool')}
- Description: {finding.get('description')}
- Code: {finding.get('code_snippet', '')}

DATA FLOW EVIDENCE:
{df_evidence}

CODE CONTEXT:
{code_chunk}

Respond ONLY with this JSON (no markdown, no explanation outside JSON):
{{
    "vuln_type": "SQLI|XSS|SECRETS|SSRF|DESERIALIZATION",
    "severity": "CRITICAL|HIGH|MEDIUM|LOW",
    "confidence": 0.0-1.0,
    "file_path": "{finding.get('file_path')}",
    "line_start": {finding.get('line_start')},
    "line_end": {finding.get('line_end', finding.get('line_start'))},
    "description": "clear explanation",
    "cwe_id": "CWE-XX",
    "evidence": "specific code evidence",
    "is_false_positive": true/false,
    "reasoning": "step by step reasoning"
}}"""


def _parse_llm_response(response_text: str, fallback_finding: dict) -> dict:
    """LLM response parse karo — JSON extract karo."""
    try:
        # JSON block extract karo
        text = response_text.strip()

        # Markdown code blocks remove karo
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        result = json.loads(text)
        return result

    except json.JSONDecodeError:
        logger.warning("LLM returned invalid JSON — using static finding")
        return {
            "vuln_type": fallback_finding.get("vuln_type"),
            "severity": fallback_finding.get("severity"),
            "confidence": fallback_finding.get("confidence", 0.5),
            "file_path": fallback_finding.get("file_path"),
            "line_start": fallback_finding.get("line_start"),
            "line_end": fallback_finding.get("line_end"),
            "description": fallback_finding.get("description"),
            "cwe_id": fallback_finding.get("cwe_id", ""),
            "evidence": fallback_finding.get("code_snippet", ""),
            "is_false_positive": False,
            "reasoning": "Static analysis finding",
        }