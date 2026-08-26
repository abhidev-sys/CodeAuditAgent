"""
LangGraph Orchestrator — Updated with Patch Generation
"""

from langgraph.graph import StateGraph, START, END
from app.agents.state import ScanState, create_initial_state
from app.agents.repo_intel_agent import repo_intel_node
from app.agents.vuln_detection_agent import vuln_detection_node
from app.agents.patch_generation_agent import patch_generation_node
from app.core.logger import get_logger

logger = get_logger("orchestrator")


def should_run_vuln_detection(state: ScanState) -> str:
    """Static findings hain toh vuln detection chalao."""
    if state.get("static_findings"):
        return "vuln_detection"
    logger.info("No static findings — skipping to end")
    return END


def should_run_patch_generation(state: ScanState) -> str:
    """Confirmed vulnerabilities hain toh patch generation chalao."""
    if state.get("vulnerabilities"):
        return "patch_generation"
    logger.info("No vulnerabilities — skipping patch generation")
    return END


def build_scan_graph() -> StateGraph:
    """
    Updated LangGraph scan graph.

    Flow:
    START → repo_intel → vuln_detection → patch_generation → END
    """
    graph = StateGraph(ScanState)

    # Nodes add karo
    graph.add_node("repo_intel", repo_intel_node)
    graph.add_node("vuln_detection", vuln_detection_node)
    graph.add_node("patch_generation", patch_generation_node)

    # Edges
    graph.add_edge(START, "repo_intel")

    # Conditional: repo_intel → vuln_detection ya END
    graph.add_conditional_edges(
        "repo_intel",
        should_run_vuln_detection,
        {
            "vuln_detection": "vuln_detection",
            END: END,
        }
    )

    # Conditional: vuln_detection → patch_generation ya END
    graph.add_conditional_edges(
        "vuln_detection",
        should_run_patch_generation,
        {
            "patch_generation": "patch_generation",
            END: END,
        }
    )

    # patch_generation → END
    graph.add_edge("patch_generation", END)

    return graph


def run_scan(
    repository_path: str,
    repository_id: str,
    scan_id: str,
) -> ScanState:
    """Complete scan run karo."""
    logger.info(
        "Starting scan",
        scan_id=scan_id,
        path=repository_path,
    )

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
            errors=len(final_state.get("errors", [])),
        )
        return final_state

    except Exception as e:
        logger.error("Scan failed", scan_id=scan_id, error=str(e))
        raise