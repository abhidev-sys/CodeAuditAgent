"""
LangGraph Orchestrator — Main Graph Definition

Yeh file poore agent pipeline ko define karti hai.

Graph structure:
START → repo_intel → vuln_detection → END (MVP)

Advanced version mein:
START → repo_intel → vuln_detection → exploitability
      → patch_generation → verification → report → END
"""

from langgraph.graph import StateGraph, START, END
from app.agents.state import ScanState, create_initial_state
from app.agents.repo_intel_agent import repo_intel_node
from app.agents.vuln_detection_agent import vuln_detection_node
from app.core.logger import get_logger

logger = get_logger("orchestrator")


def should_run_vuln_detection(state: ScanState) -> str:
    """
    Conditional routing:
    - Agar static findings hain → vuln_detection chalao
    - Nahi toh directly end karo
    """
    if state.get("static_findings"):
        return "vuln_detection"
    else:
        logger.info("No static findings — skipping vuln detection")
        return END


def build_scan_graph() -> StateGraph:
    """
    LangGraph scan graph banao.

    Graph nodes aur edges define karta hai.
    Yeh ek state machine hai jahan:
    - Nodes = agents/functions
    - Edges = transitions between agents
    - Conditional edges = routing logic
    """
    # Graph create karo with our state type
    graph = StateGraph(ScanState)

    # Nodes add karo
    graph.add_node("repo_intel", repo_intel_node)
    graph.add_node("vuln_detection", vuln_detection_node)

    # Edges define karo
    # START → repo_intel (hamesha)
    graph.add_edge(START, "repo_intel")

    # repo_intel → vuln_detection ya END (conditional)
    graph.add_conditional_edges(
        "repo_intel",
        should_run_vuln_detection,
        {
            "vuln_detection": "vuln_detection",
            END: END,
        }
    )

    # vuln_detection → END
    graph.add_edge("vuln_detection", END)

    return graph


def run_scan(
    repository_path: str,
    repository_id: str,
    scan_id: str,
) -> ScanState:
    """
    Complete scan run karo.

    Args:
        repository_path: Repository ka local path
        repository_id: DB mein repository ka ID
        scan_id: Current scan ka ID

    Returns:
        Final ScanState with all results
    """
    logger.info(
        "Starting scan",
        scan_id=scan_id,
        path=repository_path,
    )

    # Graph compile karo
    graph = build_scan_graph()
    compiled = graph.compile()

    # Initial state banao
    initial_state = create_initial_state(
        scan_id=scan_id,
        repository_path=repository_path,
        repository_id=repository_id,
    )

    # Graph run karo
    try:
        final_state = compiled.invoke(initial_state)
        logger.info(
            "Scan complete",
            scan_id=scan_id,
            vulnerabilities=len(final_state.get("vulnerabilities", [])),
            errors=len(final_state.get("errors", [])),
        )
        return final_state

    except Exception as e:
        logger.error("Scan failed", scan_id=scan_id, error=str(e))
        raise