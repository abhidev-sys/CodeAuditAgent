"""
LangGraph Shared State

Yeh file sabse important hai — har agent yahi state
read karta hai aur yahi update karta hai.

Sochो isko ek shared notebook ki tarah:
- Har agent kuch likhta hai
- Agla agent woh padh sakta hai
- State immutable way mein update hoti hai (TypedDict)
"""

from typing import TypedDict, Annotated
from operator import add
import uuid


class ScanState(TypedDict):
    """
    Complete scan ka state — LangGraph yeh manage karta hai.

    TypedDict kyun?
    - Type safety milti hai
    - LangGraph ko pata hota hai kya expect karna hai
    - Serialization easy hoti hai

    Annotated[list, add] kyun?
    - Multiple agents ek hi list mein items add kar sakte hain
    - State override nahi hoti — append hoti hai
    - Thread-safe behavior
    """

    # ===== INPUT =====
    # Scan ka unique ID
    scan_id: str
    # Repository ka path
    repository_path: str
    # Repository ka DB ID
    repository_id: str

    # ===== REPO INTELLIGENCE =====
    # Repository ka summary
    repo_summary: dict
    # Detected language
    language: str
    # Detected frameworks
    frameworks: list[str]
    # Entry points
    entry_points: list[str]
    # Dependencies
    dependencies: list[str]

    # ===== CODE INTELLIGENCE =====
    # AST results — file path -> result dict
    ast_results: dict
    # Data flow results
    data_flow_results: dict
    # Code chunks for LLM
    code_chunks: list[dict]
    # Static analysis findings
    static_findings: list[dict]

    # ===== VULNERABILITY DETECTION =====
    # Detected vulnerabilities
    # Annotated[list, add] = multiple agents add kar sakte hain
    vulnerabilities: Annotated[list[dict], add]

    # ===== EXPLOITABILITY =====
    # Exploitability assessments
    exploitability_results: Annotated[list[dict], add]

    # ===== PATCHES =====
    # Generated patches
    patches: Annotated[list[dict], add]

    # ===== VERIFICATION =====
    # Verification results
    verification_results: Annotated[list[dict], add]

    # ===== METADATA =====
    # Agent execution log
    agent_log: Annotated[list[str], add]
    # Errors
    errors: Annotated[list[str], add]
    # Current step
    current_step: str
    # Risk score (0-100)
    risk_score: int
    # Total token usage
    token_usage: int


def create_initial_state(
    scan_id: str,
    repository_path: str,
    repository_id: str,
) -> ScanState:
    """
    Initial state banao — scan shuru karne se pehle.

    Saare fields empty/default values se initialize karo.
    """
    return ScanState(
        scan_id=scan_id,
        repository_path=repository_path,
        repository_id=repository_id,
        repo_summary={},
        language="",
        frameworks=[],
        entry_points=[],
        dependencies=[],
        ast_results={},
        data_flow_results={},
        code_chunks=[],
        static_findings=[],
        vulnerabilities=[],
        exploitability_results=[],
        patches=[],
        verification_results=[],
        agent_log=[],
        errors=[],
        current_step="start",
        risk_score=0,
        token_usage=0,
    )