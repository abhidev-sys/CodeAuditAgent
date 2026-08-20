"""
Symbol Extractor — Repository ka symbol table banata hai

Kya karta hai:
- Saare functions aur classes ka map banata hai
- Kaun sa function kaun se function ko call karta hai
- Global variables track karta hai
- Agents ko context deta hai
"""

from dataclasses import dataclass, field
from app.analysis.ast_analyzer import analyze_file, ASTAnalysisResult
from app.repository.indexer import RepositoryIndex
from app.core.logger import get_logger

logger = get_logger("symbol_extractor")


@dataclass
class RepositorySymbols:
    """
    Poori repository ka symbol table.
    """
    # file_path -> list of function names
    functions_by_file: dict[str, list[str]] = field(default_factory=dict)
    # file_path -> AST result
    ast_results: dict[str, ASTAnalysisResult] = field(default_factory=dict)
    # Saare suspicious nodes across all files
    all_suspicious_nodes: list[dict] = field(default_factory=list)
    # Sensitive imports across all files
    sensitive_imports: list[dict] = field(default_factory=list)
    # Total files analyzed
    total_files_analyzed: int = 0
    # Total suspicious nodes
    total_suspicious: int = 0


def extract_repository_symbols(index: RepositoryIndex) -> RepositorySymbols:
    """
    Repository ki saari files ka symbol table banao.

    Args:
        index: Repository file index

    Returns:
        RepositorySymbols with complete analysis
    """
    symbols = RepositorySymbols()

    logger.info(
        "Starting symbol extraction",
        total_files=index.analyzable_files,
    )

    for file_path in index.analyzable_file_paths:
        try:
            # AST analysis karo
            ast_result = analyze_file(file_path)
            symbols.ast_results[file_path] = ast_result

            # Functions track karo
            func_names = [f.name for f in ast_result.functions]
            symbols.functions_by_file[file_path] = func_names

            # Suspicious nodes collect karo
            for node in ast_result.suspicious_nodes:
                node["file_path"] = file_path
                symbols.all_suspicious_nodes.append(node)

            # Sensitive imports collect karo
            for imp in ast_result.imports:
                if imp.is_sensitive:
                    symbols.sensitive_imports.append({
                        "file": file_path,
                        "module": imp.module,
                        "line": imp.line,
                    })

            symbols.total_files_analyzed += 1
            symbols.total_suspicious += len(ast_result.suspicious_nodes)

        except Exception as e:
            logger.error(
                "Symbol extraction failed for file",
                file=file_path,
                error=str(e),
            )
            continue

    logger.info(
        "Symbol extraction complete",
        files_analyzed=symbols.total_files_analyzed,
        total_suspicious=symbols.total_suspicious,
        sensitive_imports=len(symbols.sensitive_imports),
    )

    return symbols