"""
Code Chunker — LLM ke liye smart code pieces banata hai

Kyun zaroori hai?
- LLM ka context window limited hai
- Poori file ek saath nahi daal sakte
- Smart chunking = relevant code hi LLM ko milta hai
- Cost kam hoti hai — unnecessary tokens nahi jaate

Strategy:
- Function-based chunking (best approach)
- Suspicious area ke aas paas extra context
- Overlap rakho taaki context na toote
"""

from dataclasses import dataclass, field
from pathlib import Path
from app.analysis.ast_analyzer import ASTAnalysisResult
from app.core.logger import get_logger

logger = get_logger("code_chunker")

# LLM ke liye maximum lines per chunk
MAX_LINES_PER_CHUNK = 50
# Context lines — suspicious area ke upar neeche kitni lines
CONTEXT_LINES = 5


@dataclass
class CodeChunk:
    """
    Ek code chunk — LLM ko yeh diya jayega analysis ke liye.
    """
    # Chunk ka unique ID
    chunk_id: str
    # Kaun si file se aaya
    file_path: str
    # Content
    content: str
    # Start aur end line numbers
    start_line: int
    end_line: int
    # Yeh chunk kyun important hai?
    chunk_type: str  # "function", "suspicious", "full_file"
    # Kya yeh chunk suspicious hai?
    is_suspicious: bool = False
    # Metadata
    metadata: dict = field(default_factory=dict)


def create_chunks(
    file_path: str,
    ast_result: ASTAnalysisResult,
    source_code: str,
) -> list[CodeChunk]:
    """
    File ke smart chunks banao.

    Strategy:
    1. Pehle suspicious areas ke chunks banao (highest priority)
    2. Phir functions ke chunks banao
    3. Agar file chhoti hai toh poori file ek chunk

    Args:
        file_path: Source file path
        ast_result: AST analysis result
        source_code: File ka source code

    Returns:
        List of CodeChunk objects
    """
    chunks = []
    lines = source_code.splitlines()
    total_lines = len(lines)

    # Agar file bahut chhoti hai — ek hi chunk
    if total_lines <= MAX_LINES_PER_CHUNK:
        chunk = CodeChunk(
            chunk_id=f"{Path(file_path).stem}_full",
            file_path=file_path,
            content=source_code,
            start_line=1,
            end_line=total_lines,
            chunk_type="full_file",
            is_suspicious=len(ast_result.suspicious_nodes) > 0,
            metadata={"reason": "Small file — full content"},
        )
        chunks.append(chunk)
        logger.info("Created full file chunk", file=file_path)
        return chunks

    # Suspicious areas ke chunks — highest priority
    suspicious_chunks = _create_suspicious_chunks(
        file_path, ast_result, lines
    )
    chunks.extend(suspicious_chunks)

    # Function chunks
    function_chunks = _create_function_chunks(
        file_path, ast_result, lines
    )
    chunks.extend(function_chunks)

    # Duplicates remove karo
    chunks = _deduplicate_chunks(chunks)

    logger.info(
        "Code chunking complete",
        file=file_path,
        total_chunks=len(chunks),
        suspicious_chunks=len(suspicious_chunks),
    )

    return chunks


def _create_suspicious_chunks(
    file_path: str,
    ast_result: ASTAnalysisResult,
    lines: list[str],
) -> list[CodeChunk]:
    """Suspicious nodes ke around chunks banao."""
    chunks = []

    for i, node in enumerate(ast_result.suspicious_nodes):
        line_num = node.get("line", 1)

        # Context ke saath lines nikalo
        start = max(0, line_num - CONTEXT_LINES - 1)
        end = min(len(lines), line_num + CONTEXT_LINES)

        chunk_lines = lines[start:end]
        content = "\n".join(
            f"{start + j + 1}: {line}"
            for j, line in enumerate(chunk_lines)
        )

        chunk = CodeChunk(
            chunk_id=f"{Path(file_path).stem}_suspicious_{i}",
            file_path=file_path,
            content=content,
            start_line=start + 1,
            end_line=end,
            chunk_type="suspicious",
            is_suspicious=True,
            metadata={
                "reason": node.get("reason", "Suspicious code"),
                "suspicious_line": line_num,
                "node_type": node.get("type", "unknown"),
            },
        )
        chunks.append(chunk)

    return chunks


def _create_function_chunks(
    file_path: str,
    ast_result: ASTAnalysisResult,
    lines: list[str],
) -> list[CodeChunk]:
    """Har function ka ek chunk banao."""
    chunks = []

    for func in ast_result.functions:
        # Function lines nikalo
        start_idx = func.start_line - 1
        end_idx = min(func.end_line, len(lines))

        func_lines = lines[start_idx:end_idx]

        # Agar function bahut bada hai toh truncate karo
        if len(func_lines) > MAX_LINES_PER_CHUNK:
            func_lines = func_lines[:MAX_LINES_PER_CHUNK]
            end_idx = start_idx + MAX_LINES_PER_CHUNK

        content = "\n".join(
            f"{start_idx + j + 1}: {line}"
            for j, line in enumerate(func_lines)
        )

        # Kya yeh function suspicious hai?
        is_suspicious = any(
            node.get("line", 0) >= func.start_line
            and node.get("line", 0) <= func.end_line
            for node in ast_result.suspicious_nodes
        )

        chunk = CodeChunk(
            chunk_id=f"{Path(file_path).stem}_func_{func.name}",
            file_path=file_path,
            content=content,
            start_line=func.start_line,
            end_line=end_idx,
            chunk_type="function",
            is_suspicious=is_suspicious,
            metadata={
                "function_name": func.name,
                "parameters": func.parameters,
                "has_request_param": func.has_request_param,
            },
        )
        chunks.append(chunk)

    return chunks


def _deduplicate_chunks(chunks: list[CodeChunk]) -> list[CodeChunk]:
    """Overlapping chunks remove karo."""
    seen_ranges = []
    unique_chunks = []

    for chunk in chunks:
        range_key = (chunk.file_path, chunk.start_line, chunk.end_line)
        if range_key not in seen_ranges:
            seen_ranges.append(range_key)
            unique_chunks.append(chunk)

    return unique_chunks