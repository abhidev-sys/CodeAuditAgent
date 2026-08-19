"""
Repository File Indexer

Kya karta hai:
- Repository ki saari files ka index banata hai
- Har file ke baare mein metadata collect karta hai
  (path, size, lines, language)
- Large files skip karta hai (LLM context limit ke liye)
- Binary files skip karta hai

Kyun zaroori hai:
- Agents ko pata hona chahiye ki repository mein kya hai
- Bina index ke LLM poori repository blindly scan karega — expensive!
- Index se targeted analysis hoti hai
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger("indexer")

# Binary files skip karo — inhe analyze nahi kar sakte
BINARY_EXTENSIONS = {
    ".pyc", ".pyo", ".pyd",    # Python compiled
    ".jpg", ".jpeg", ".png",    # Images
    ".gif", ".bmp", ".ico",
    ".pdf", ".doc", ".docx",    # Documents
    ".zip", ".tar", ".gz",      # Archives
    ".exe", ".dll", ".so",      # Executables
    ".db", ".sqlite",           # Databases
    ".lock",                    # Lock files
}

# Yeh files skip karo
SKIP_FILES = {
    ".gitignore",
    ".env",
    ".env.example",
    "package-lock.json",
    "yarn.lock",
    "poetry.lock",
    "Pipfile.lock",
}

# Yeh directories skip karo
SKIP_DIRS = {
    ".git", "__pycache__", ".venv", "venv", "env",
    "node_modules", ".pytest_cache", "dist", "build",
    ".eggs", "migrations", ".mypy_cache", ".ruff_cache",
}


@dataclass
class FileInfo:
    """
    Ek file ke baare mein saari information.
    
    dataclass automatically __init__, __repr__ banata hai
    """
    # File ka path repo root se relative
    relative_path: str
    # File ka absolute path
    absolute_path: str
    # File ka extension jaise ".py"
    extension: str
    # File ka size bytes mein
    size_bytes: int
    # File mein kitni lines hain
    line_count: int
    # Detected language
    language: str
    # Kya yeh file analyze karne layak hai?
    is_analyzable: bool


@dataclass
class RepositoryIndex:
    """
    Poori repository ka index.
    
    Agents yeh index use karenge targeted analysis ke liye.
    """
    # Total files (analyzable + non-analyzable)
    total_files: int = 0
    # Sirf analyzable files
    analyzable_files: int = 0
    # Total lines of code
    total_lines: int = 0
    # Total size bytes mein
    total_size_bytes: int = 0
    # Saari files ki list
    files: list[FileInfo] = field(default_factory=list)
    # Sirf analyzable files — agents mainly yeh use karenge
    analyzable_file_paths: list[str] = field(default_factory=list)
    # Language wise file count
    language_breakdown: dict[str, int] = field(default_factory=dict)


def index_repository(repo_path: str) -> RepositoryIndex:
    """
    Repository ki saari files ka index banao.
    
    Args:
        repo_path: Repository ka local path
        
    Returns:
        RepositoryIndex object with all file metadata
    """
    index = RepositoryIndex()
    repo = Path(repo_path)
    max_size_bytes = settings.max_file_size_kb * 1024  # KB to bytes
    
    logger.info("Starting repository indexing", path=repo_path)
    
    for root, dirs, files in os.walk(repo_path):
        # Skip directories in-place
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        
        for filename in files:
            file_path = Path(root) / filename
            
            # Skip karo agar special file hai
            if filename in SKIP_FILES:
                continue
            
            try:
                # File metadata nikalo
                size_bytes = file_path.stat().st_size
                extension = file_path.suffix.lower()
                relative_path = str(file_path.relative_to(repo))
                
                # Binary files skip karo
                if extension in BINARY_EXTENSIONS:
                    continue
                
                # Language determine karo
                from app.repository.detector import EXTENSION_MAP
                language = EXTENSION_MAP.get(extension, "other")
                
                # Kya yeh file analyze karne layak hai?
                is_analyzable = (
                    # Size limit ke andar hona chahiye
                    size_bytes <= max_size_bytes
                    # Binary nahi hona chahiye
                    and extension not in BINARY_EXTENSIONS
                    # Supported language honi chahiye
                    and language in settings.supported_language_list
                )
                
                # Lines count karo — sirf analyzable files ke liye
                line_count = 0
                if is_analyzable:
                    try:
                        content = file_path.read_text(
                            encoding="utf-8", errors="ignore"
                        )
                        line_count = len(content.splitlines())
                    except Exception:
                        is_analyzable = False
                
                # FileInfo object banao
                file_info = FileInfo(
                    relative_path=relative_path,
                    absolute_path=str(file_path),
                    extension=extension,
                    size_bytes=size_bytes,
                    line_count=line_count,
                    language=language,
                    is_analyzable=is_analyzable,
                )
                
                # Index update karo
                index.files.append(file_info)
                index.total_files += 1
                index.total_size_bytes += size_bytes
                
                if is_analyzable:
                    index.analyzable_files += 1
                    index.total_lines += line_count
                    index.analyzable_file_paths.append(relative_path)
                    
                    # Language breakdown update karo
                    index.language_breakdown[language] = (
                        index.language_breakdown.get(language, 0) + 1
                    )
                    
            except Exception as e:
                # Ek file fail ho toh skip karo
                logger.warning(
                    "Could not index file",
                    file=str(file_path),
                    error=str(e)
                )
                continue
    
    logger.info(
        "Repository indexing complete",
        total_files=index.total_files,
        analyzable_files=index.analyzable_files,
        total_lines=index.total_lines,
    )
    
    return index