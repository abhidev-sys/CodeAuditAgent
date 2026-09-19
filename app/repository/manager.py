"""
Repository Manager — Main Entry Point

Supports:
- Local repository paths
- Public GitHub/GitLab/Bitbucket repositories

Pipeline:
Source → Resolve/Clone → Validate → Analyze → Index → Database
"""

from pathlib import Path
from sqlalchemy.orm import Session
from urllib.parse import urlparse
import subprocess
import uuid

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


# ---------------------------------------------------------
# Repository source configuration
# ---------------------------------------------------------

SUPPORTED_GIT_HOSTS = {
    "github.com",
    "www.github.com",
    "gitlab.com",
    "www.gitlab.com",
    "bitbucket.org",
    "www.bitbucket.org",
}

PROJECT_ROOT = Path(__file__).resolve().parents[2]

REPOSITORY_WORKSPACE = PROJECT_ROOT / "workspace" / "repositories"


# ---------------------------------------------------------
# URL detection
# ---------------------------------------------------------

def is_git_url(source: str) -> bool:
    """
    Check whether the supplied source is a supported Git URL.
    """

    if not source:
        return False

    try:
        parsed = urlparse(source)

        return (
            parsed.scheme in {"http", "https"}
            and parsed.hostname is not None
            and parsed.hostname.lower() in SUPPORTED_GIT_HOSTS
        )

    except Exception:
        return False


# ---------------------------------------------------------
# Git repository cloning
# ---------------------------------------------------------

def clone_repository(repository_url: str) -> Path:
    """
    Clone a remote public repository into the local workspace.

    Security:
    - Only approved Git hosting domains are accepted.
    - Credentials embedded in URLs are rejected.
    - subprocess uses argument lists, not shell=True.
    - Clone has a timeout.
    """

    if not is_git_url(repository_url):
        raise RepositoryError(
            "Unsupported repository URL. "
            "Supported hosts: GitHub, GitLab and Bitbucket."
        )

    parsed = urlparse(repository_url)

    # Never allow credentials inside repository URLs.
    if parsed.username or parsed.password:
        raise RepositoryError(
            "Repository URLs containing embedded credentials are not allowed."
        )

    REPOSITORY_WORKSPACE.mkdir(
        parents=True,
        exist_ok=True,
    )

    repository_id = uuid.uuid4().hex
    destination = REPOSITORY_WORKSPACE / repository_id

    logger.info(
        "Cloning remote repository",
        host=parsed.hostname,
        destination=str(destination),
    )

    try:
        result = subprocess.run(
            [
                "git",
                "clone",
                "--depth",
                "1",
                "--no-tags",
                repository_url,
                str(destination),
            ],
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )

    except FileNotFoundError:
        raise RepositoryError(
            "Git is not installed or is not available in PATH."
        )

    except subprocess.TimeoutExpired:
        raise RepositoryError(
            "Repository cloning timed out after 5 minutes."
        )

    except Exception as exc:
        logger.error(
            "Repository clone failed",
            error=str(exc),
        )

        raise RepositoryError(
            "Unable to clone the repository."
        )

    if result.returncode != 0:
        logger.error(
            "Git clone failed",
            return_code=result.returncode,
        )

        # Do not expose raw git output because it may contain
        # sensitive repository information.
        if destination.exists():
            import shutil
            shutil.rmtree(destination, ignore_errors=True)

        raise RepositoryError(
            "Repository cloning failed. "
            "Make sure the repository URL is valid and publicly accessible."
        )

    if not destination.exists():
        raise RepositoryError(
            "Repository was cloned but the destination directory was not created."
        )

    logger.info(
        "Repository cloned successfully",
        destination=str(destination),
    )

    return destination


# ---------------------------------------------------------
# Resolve repository source
# ---------------------------------------------------------

def resolve_repository_source(
    path: str | None,
    url: str | None,
) -> tuple[Path, str | None]:
    """
    Convert either a local path or remote Git URL
    into a local repository path.

    Returns:
        (local_repository_path, remote_url)
    """

    source = url or path

    if not source:
        raise RepositoryError(
            "Repository source is required."
        )

    # Remote repository
    if is_git_url(source):
        local_path = clone_repository(source)

        return local_path, source

    # Local repository
    local_path = Path(source).resolve()

    return local_path, url


# ---------------------------------------------------------
# Local repository validation
# ---------------------------------------------------------

def validate_repository_path(path: str | Path) -> Path:
    """
    Validate that the repository exists and is a directory.
    """

    repo_path = Path(path).resolve()

    if not repo_path.exists():
        raise RepositoryError(
            f"Path does not exist: {path}",
            details={"path": str(repo_path)},
        )

    if not repo_path.is_dir():
        raise RepositoryError(
            f"Path is not a directory: {path}",
            details={"path": str(repo_path)},
        )

    files = list(repo_path.rglob("*"))

    if not files:
        raise RepositoryError(
            f"Directory is empty: {path}",
            details={"path": str(repo_path)},
        )

    return repo_path


# ---------------------------------------------------------
# Repository size
# ---------------------------------------------------------

def check_repository_size(repo_path: Path) -> float:
    """
    Calculate repository size in MB.
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
            (
                f"Repository size {size_mb:.1f}MB exceeds "
                f"limit of {settings.max_repo_size_mb}MB"
            ),
            details={
                "size_mb": size_mb,
                "limit_mb": settings.max_repo_size_mb,
            },
        )

    return size_mb


# ---------------------------------------------------------
# Main ingestion pipeline
# ---------------------------------------------------------

def ingest_repository(
    path: str,
    db: Session,
    name: str | None = None,
    url: str | None = None,
) -> tuple[Repository, RepositoryIndex]:
    """
    Ingest a repository.

    Supports both:

        Local:
        R:\\projects\\my-repo

        Remote:
        https://github.com/user/my-repo.git

    Pipeline:

        Resolve source
            ↓
        Clone if remote
            ↓
        Validate
            ↓
        Size check
            ↓
        Language detection
            ↓
        Framework detection
            ↓
        Entry points
            ↓
        Dependencies
            ↓
        File indexing
            ↓
        Database
    """

    logger.info(
        "Starting repository ingestion",
        path=path,
        url=url,
    )

    # -----------------------------------------------------
    # Step 1: Resolve source
    # -----------------------------------------------------

    repo_path, remote_url = resolve_repository_source(
        path=path,
        url=url,
    )

    logger.info(
        "Repository source resolved",
        local_path=str(repo_path),
        remote_url=remote_url,
    )

    # -----------------------------------------------------
    # Step 2: Validate repository
    # -----------------------------------------------------

    repo_path = validate_repository_path(repo_path)

    # -----------------------------------------------------
    # Step 3: Size check
    # -----------------------------------------------------

    size_mb = check_repository_size(repo_path)

    logger.info(
        "Repository size OK",
        size_mb=f"{size_mb:.2f}MB",
    )

    # -----------------------------------------------------
    # Step 4: Detect language
    # -----------------------------------------------------

    language = detect_language(str(repo_path))

    logger.info(
        "Language detected",
        language=language,
    )

    # -----------------------------------------------------
    # Step 5: Supported language check
    # -----------------------------------------------------

    if language not in settings.supported_language_list:
        raise UnsupportedLanguageError(
            (
                f"Language '{language}' is not supported. "
                f"Supported: {settings.supported_language_list}"
            ),
            details={
                "detected": language,
                "supported": settings.supported_language_list,
            },
        )

    # -----------------------------------------------------
    # Step 6: Framework detection
    # -----------------------------------------------------

    frameworks = detect_frameworks(str(repo_path))

    # -----------------------------------------------------
    # Step 7: Entry points
    # -----------------------------------------------------

    entry_points = find_entry_points(str(repo_path))

    # -----------------------------------------------------
    # Step 8: Dependencies
    # -----------------------------------------------------

    dependencies = read_dependencies(str(repo_path))

    # -----------------------------------------------------
    # Step 9: File indexing
    # -----------------------------------------------------

    index = index_repository(str(repo_path))

    # -----------------------------------------------------
    # Step 10: Repository name
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # Step 11: Database record
    # -----------------------------------------------------

    db_repository = Repository(
        name=repo_name,
        path=str(repo_path),
        url=remote_url,
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