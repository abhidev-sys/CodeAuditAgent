"""
Repository API endpoints.

Endpoints:
- POST /repositories — naya repository ingest karo
- GET /repositories/{repo_id} — repository details dekho
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from app.core.database import get_db, SessionLocal
from app.core.database import get_db
from app.core.logger import get_logger
from app.core.exceptions import (
    RepositoryError,
    UnsupportedLanguageError,
    RepositoryTooLargeError,
)
from app.schemas.repository import (
    RepositoryCreate,
    RepositoryResponse,
    RepositoryIngestResponse,
)
from app.repository.manager import ingest_repository
from app.repository.detector import detect_frameworks, find_entry_points
from app.models.repository import Repository

# APIRouter = FastAPI ka way to group related endpoints
router = APIRouter(prefix="/repositories", tags=["Repositories"])
logger = get_logger("api.repositories")


@router.post("/", response_model=RepositoryIngestResponse, status_code=201)
def create_repository(
    request: RepositoryCreate,
    db: Session = Depends(get_db),
):
    try:
        db_repo, index = ingest_repository(
            path=request.path,
            db=db,
            name=request.name,
            url=request.url,
        )
        
        frameworks = detect_frameworks(db_repo.path)
        entry_points = find_entry_points(db_repo.path)
        
        return RepositoryIngestResponse(
            repository=RepositoryResponse.model_validate(db_repo),
            analyzable_files=index.analyzable_files,
            frameworks=frameworks,
            entry_points=entry_points,
            message=f"Repository '{db_repo.name}' ingested successfully",
        )
        
    except UnsupportedLanguageError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RepositoryTooLargeError as e:
        raise HTTPException(status_code=413, detail=str(e))
    except RepositoryError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Unexpected error", error=str(e))
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get("/{repository_id}", response_model=RepositoryResponse)
def get_repository(
    repository_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Repository details fetch karo ID se.
    """
    repo = db.query(Repository).filter(Repository.id == repository_id).first()
    
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    return RepositoryResponse.model_validate(repo)


@router.get("/", response_model=list[RepositoryResponse])
def list_repositories(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 20,
):
    """
    Saari repositories list karo.
    """
    repos = db.query(Repository).offset(skip).limit(limit).all()
    return [RepositoryResponse.model_validate(r) for r in repos]