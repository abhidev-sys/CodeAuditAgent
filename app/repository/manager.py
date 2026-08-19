"""
Repository Manager — Main Entry Point

Kya karta hai:
- User ke diye hue path ko validate karta hai
- Language detect karta hai
- Framework detect karta hai
- File index banata hai
- Sab information database mein save karta hai
- Repository object return karta hai

Yeh sabse pehla step hai har scan mein.
"""

from pathlib import Path
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logger import get_logger
from app.core.exceptions import (
    RepositoryError,
    UnsupportedLanguageError,
    RepositoryTooLargeError,
)
from app.models.repository import Repository
from app.repository.detector import (
    detect_language,
    detect_frameworks,
    find_entry_points,
    read_dependencies,
)
from app.repository.indexer import index_repository, RepositoryIndex

logger = get_logger("repository_manager")


def validate_repository_path(path: str) -> Path:
    """
    Check karo ki path valid hai.
    
    Validations:
    1. Path exist karta hai?
    2. Path ek directory hai?
    3. Path ke andar Python files hain?
    
    Args:
        path: User ka diya hua path
        
    Returns:
        Validated Path object
        
    Raises:
        RepositoryError: Agar path invalid hai
    """
    repo_path = Path(path).resolve()  # Absolute path banao
    
    # Check 1: Exist karta hai?
    if not repo_path.exists():
        raise RepositoryError(
            f"Path does not exist: {path}",
            details={"path": str(repo_path)}
        )
    
    # Check 2: Directory hai?
    if not repo_path.is_dir():
        raise RepositoryError(
            f"Path is not a directory: {path}",
            details={"path": str(repo_path)}
        )
    
    # Check 3: Koi file hai andar?
    files = list(repo_path.rglob("*"))
    if not files:
        raise RepositoryError(
            f"Directory is empty: {path}",
            details={"path": str(repo_path)}
        )
    
    return repo_path


def check_repository_size(repo_path: Path) -> float:
    """
    Repository ka total size MB mein calculate karo.
    
    Args:
        repo_path: Validated repository path
        
    Returns:
        Size in MB
        
    Raises:
        RepositoryTooLargeError: Agar size limit se zyada hai
    """
    total_size = 0
    for f in repo_path.rglob("*"):
        if f.is_file():
            try:
                total_size += f.stat().st_size
            except Exception:
                continue
    
    size_mb = total_size / (1024 * 1024)
    
    if size_mb > settings.max_repo_size_mb:
        raise RepositoryTooLargeError(
            f"Repository size {size_mb:.1f}MB exceeds limit of {settings.max_repo_size_mb}MB",
            details={"size_mb": size_mb, "limit_mb": settings.max_repo_size_mb}
        )
    
    return size_mb


def ingest_repository(
    path: str,
    db: Session,
    name: str | None = None,
    url: str | None = None,
) -> tuple[Repository, RepositoryIndex]:
    """
    Repository ko ingest karo — validate, analyze, aur database mein save karo.
    
    Yeh function poori repository ingestion pipeline run karta hai:
    1. Path validate karo
    2. Size check karo
    3. Language detect karo
    4. Supported language check karo
    5. Framework detect karo
    6. File index banao
    7. Database mein save karo
    
    Args:
        path: Repository ka local path
        db: Database session
        name: Optional custom name (default: folder ka naam)
        url: Optional Git URL
        
    Returns:
        Tuple of (Repository DB object, RepositoryIndex)
        
    Raises:
        RepositoryError: Path invalid hai
        UnsupportedLanguageError: Language supported nahi
        RepositoryTooLargeError: Repository bahut badi hai
    """
    logger.info("Starting repository ingestion", path=path)
    
    # Step 1: Path validate karo
    repo_path = validate_repository_path(path)
    
    # Step 2: Size check karo
    size_mb = check_repository_size(repo_path)
    logger.info("Repository size OK", size_mb=f"{size_mb:.2f}MB")
    
    # Step 3: Language detect karo
    language = detect_language(str(repo_path))
    
    # Step 4: Supported language check karo
    if language not in settings.supported_language_list:
        raise UnsupportedLanguageError(
            f"Language '{language}' is not supported. Supported: {settings.supported_language_list}",
            details={"detected": language, "supported": settings.supported_language_list}
        )
    
    # Step 5: Frameworks detect karo
    frameworks = detect_frameworks(str(repo_path))
    
    # Step 6: Entry points dhundho
    entry_points = find_entry_points(str(repo_path))
    
    # Step 7: Dependencies padho
    dependencies = read_dependencies(str(repo_path))
    
    # Step 8: File index banao
    index = index_repository(str(repo_path))
    
    # Step 9: Repository naam set karo
    repo_name = name or repo_path.name
    
    logger.info(
        "Repository analysis complete",
        name=repo_name,
        language=language,
        frameworks=frameworks,
        total_files=index.total_files,
        analyzable_files=index.analyzable_files,
        total_lines=index.total_lines,
    )
    
    # Step 10: Database mein save karo
    db_repository = Repository(
        name=repo_name,
        path=str(repo_path),
        url=url,
        language=language,
        total_files=index.analyzable_files,
        total_lines=index.total_lines,
    )
    
    db.add(db_repository)
    db.flush()
    db.refresh(db_repository)
    
    logger.info(
        "Repository saved to database",
        repository_id=str(db_repository.id),
        name=repo_name,
    )
    
    return db_repository, index