"""
Repository Intelligence Agent — Agent 1

Responsibility:
- Repository ka structure samajhna
- Language, frameworks, entry points identify karna
- Security-relevant patterns note karna
- Baaki agents ke liye context prepare karna

Yeh agent sirf programmatic analysis karta hai —
LLM call sirf summary banane ke liye hota hai.
"""

from pathlib import Path
from app.agents.state import ScanState
from app.analysis.ast_analyzer import analyze_file
from app.analysis.data_flow import analyze_data_flow
from app.analysis.code_chunker import create_chunks
from app.analysis.symbol_extractor import extract_repository_symbols
from app.repository.detector import (
    detect_language,
    detect_frameworks,
    find_entry_points,
    read_dependencies,
)
from app.repository.indexer import index_repository
from app.security.static_analyzer import run_static_analysis
from app.core.logger import get_logger

logger = get_logger("repo_intel_agent")


def repo_intel_node(state: ScanState) -> dict:
    """
    LangGraph node — Repository Intelligence.

    Kya karta hai:
    1. Repository index banata hai
    2. Language + frameworks detect karta hai
    3. AST analysis karta hai har file pe
    4. Data flow analyze karta hai
    5. Code chunks banata hai
    6. Static analysis run karta hai
    7. Summary state mein save karta hai

    Args:
        state: Current scan state

    Returns:
        Dict with updated state fields
    """
    repo_path = state["repository_path"]
    scan_id = state["scan_id"]

    logger.info(
        "Repo Intel Agent starting",
        scan_id=scan_id,
        path=repo_path,
    )

    try:
        # Step 1: Repository index banao
        index = index_repository(repo_path)

        # Step 2: Language + frameworks
        language = detect_language(repo_path)
        frameworks = detect_frameworks(repo_path)
        entry_points = find_entry_points(repo_path)
        dependencies = read_dependencies(repo_path)

        # Step 3: AST + Data Flow analysis
        ast_results = {}
        data_flow_results = {}
        all_chunks = []

        for file_path in index.analyzable_file_paths:
            abs_path = str(Path(repo_path) / file_path)

            # AST analyze karo
            ast_result = analyze_file(abs_path)
            ast_results[file_path] = {
                "functions": [
                    {
                        "name": f.name,
                        "start_line": f.start_line,
                        "end_line": f.end_line,
                        "parameters": f.parameters,
                        "has_request_param": f.has_request_param,
                    }
                    for f in ast_result.functions
                ],
                "imports": [
                    {
                        "module": i.module,
                        "is_sensitive": i.is_sensitive,
                        "line": i.line,
                    }
                    for i in ast_result.imports
                ],
                "suspicious_nodes": ast_result.suspicious_nodes,
                "string_literals": ast_result.string_literals,
                "parse_success": ast_result.parse_success,
            }

            # Data flow analyze karo
            try:
                source_code = Path(abs_path).read_text(
                    encoding="utf-8", errors="ignore"
                )
                df_result = analyze_data_flow(ast_result, source_code)
                data_flow_results[file_path] = {
                    "taint_flows": [
                        {
                            "vuln_type": f.vuln_type,
                            "source": f.source,
                            "source_line": f.source_line,
                            "tainted_variable": f.tainted_variable,
                            "sink": f.sink,
                            "sink_line": f.sink_line,
                            "confidence": f.confidence,
                            "evidence": f.evidence,
                        }
                        for f in df_result.taint_flows
                    ],
                }

                # Code chunks banao
                chunks = create_chunks(abs_path, ast_result, source_code)
                for chunk in chunks:
                    all_chunks.append({
                        "chunk_id": chunk.chunk_id,
                        "file_path": file_path,
                        "content": chunk.content,
                        "start_line": chunk.start_line,
                        "end_line": chunk.end_line,
                        "chunk_type": chunk.chunk_type,
                        "is_suspicious": chunk.is_suspicious,
                        "metadata": chunk.metadata,
                    })

            except Exception as e:
                logger.warning(
                    "Data flow analysis failed",
                    file=file_path,
                    error=str(e),
                )

        # Step 4: Static analysis
        static_report = run_static_analysis(repo_path)
        static_findings = [
            {
                "tool": f.tool,
                "vuln_type": f.vuln_type,
                "severity": f.severity,
                "file_path": f.file_path,
                "line_start": f.line_start,
                "line_end": f.line_end,
                "code_snippet": f.code_snippet,
                "description": f.description,
                "cwe_id": f.cwe_id,
                "confidence": f.confidence,
            }
            for f in static_report.findings
        ]

        # Step 5: Repo summary banao
        repo_summary = {
            "total_files": index.total_files,
            "analyzable_files": index.analyzable_files,
            "total_lines": index.total_lines,
            "language_breakdown": index.language_breakdown,
            "suspicious_files": [
                fp for fp, ar in ast_results.items()
                if ar.get("suspicious_nodes")
            ],
            "sensitive_imports": [
                {"file": fp, "module": imp["module"], "line": imp["line"]}
                for fp, ar in ast_results.items()
                for imp in ar.get("imports", [])
                if imp.get("is_sensitive")
            ],
            "static_findings_count": len(static_findings),
            "taint_flows_count": sum(
                len(df.get("taint_flows", []))
                for df in data_flow_results.values()
            ),
        }

        logger.info(
            "Repo Intel Agent complete",
            scan_id=scan_id,
            files=index.analyzable_files,
            static_findings=len(static_findings),
            chunks=len(all_chunks),
        )

        return {
            "language": language,
            "frameworks": frameworks,
            "entry_points": entry_points,
            "dependencies": dependencies,
            "ast_results": ast_results,
            "data_flow_results": data_flow_results,
            "code_chunks": all_chunks,
            "static_findings": static_findings,
            "repo_summary": repo_summary,
            "current_step": "repo_intel_complete",
            "agent_log": [
                f"RepoIntelAgent: Analyzed {index.analyzable_files} files, "
                f"found {len(static_findings)} static findings, "
                f"{len(all_chunks)} code chunks"
            ],
        }

    except Exception as e:
        logger.error("Repo Intel Agent failed", error=str(e))
        import traceback
        return {
            "errors": [f"RepoIntelAgent failed: {str(e)}"],
            "current_step": "repo_intel_failed",
            "agent_log": [f"RepoIntelAgent: FAILED — {str(e)}"],
        }