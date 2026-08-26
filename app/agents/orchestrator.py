"""
LangGraph Orchestrator — Complete Pipeline
START → repo_intel → vuln_detection → patch_generation → report → END
"""

from langgraph.graph import StateGraph, START, END
from app.agents.state import ScanState, create_initial_state
from app.agents.repo_intel_agent import repo_intel_node
from app.agents.vuln_detection_agent import vuln_detection_node
from app.agents.patch_generation_agent import patch_generation_node
from app.agents.report_agent import report_node
from app.core.logger import get_logger

logger = get_logger("orchestrator")


def should_run_vuln_detection(state: ScanState) -> str:
    if state.get("static_findings"):
        return "vuln_detection"
    logger.info("No static findings — going to report")
    return "report"


def should_run_patch_generation(state: ScanState) -> str:
    if state.get("vulnerabilities"):
        return "patch_generation"
    logger.info("No vulnerabilities — going to report")
    return "report"


def build_scan_graph() -> StateGraph:
    """
    Complete LangGraph pipeline.

    Flow:
    START
      ↓
    repo_intel
      ↓ (has findings?)
    vuln_detection
      ↓ (has vulns?)
    patch_generation
      ↓
    report
      ↓
    END
    """
    graph = StateGraph(ScanState)

    # Nodes
    graph.add_node("repo_intel", repo_intel_node)
    graph.add_node("vuln_detection", vuln_detection_node)
    graph.add_node("patch_generation", patch_generation_node)
    graph.add_node("report", report_node)

    # Edges
    graph.add_edge(START, "repo_intel")

    graph.add_conditional_edges(
        "repo_intel",
        should_run_vuln_detection,
        {
            "vuln_detection": "vuln_detection",
            "report": "report",
        }
    )

    graph.add_conditional_edges(
        "vuln_detection",
        should_run_patch_generation,
        {
            "patch_generation": "patch_generation",
            "report": "report",
        }
    )

    graph.add_edge("patch_generation", "report")
    graph.add_edge("report", END)

    return graph


def run_scan(
    repository_path: str,
    repository_id: str,
    scan_id: str,
) -> ScanState:
    """Complete scan pipeline run karo."""
    logger.info("Starting scan", scan_id=scan_id, path=repository_path)

    graph = build_scan_graph()
    compiled = graph.compile()

    initial_state = create_initial_state(
        scan_id=scan_id,
        repository_path=repository_path,
        repository_id=repository_id,
    )

    try:
        final_state = compiled.invoke(initial_state)
        logger.info(
            "Scan complete",
            scan_id=scan_id,
            vulnerabilities=len(final_state.get("vulnerabilities", [])),
            patches=len(final_state.get("patches", [])),
            risk_score=final_state.get("risk_score", 0),
        )
        return final_state

    except Exception as e:
        logger.error("Scan failed", scan_id=scan_id, error=str(e))
        raise