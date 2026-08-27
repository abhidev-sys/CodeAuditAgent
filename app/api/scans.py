"""
Scan API endpoints.

Endpoints:
- POST /scans          — naya scan start karo
- GET  /scans/{id}     — scan status dekho
- GET  /scans          — saare scans list karo
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.core.logger import get_logger
from app.schemas.scan import ScanCreate, ScanResponse, ScanStatusResponse
from app.services.scan_service import create_scan, get_scan
from app.models.scan import Scan

router = APIRouter(prefix="/scans", tags=["Scans"])
logger = get_logger("api.scans")


@router.post("/", response_model=ScanResponse, status_code=202)
def start_scan(
    request: ScanCreate,
    db: Session = Depends(get_db),
):
    """
    Naya security scan start karo.

    - Repository ID chahiye
    - Scan background mein run hoga
    - 202 Accepted — matlab scan shuru ho gaya
    - Status check karne ke liye GET /scans/{id} use karo
    """
    logger.info(
        "Scan requested",
        repository_id=str(request.repository_id),
    )

    try:
        scan = create_scan(
            db=db,
            repository_id=str(request.repository_id),
        )
        return ScanResponse.model_validate(scan)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Scan creation failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{scan_id}", response_model=ScanStatusResponse)
def get_scan_status(
    scan_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Scan ka current status fetch karo.

    Status values:
    - PENDING   — abhi shuru nahi hua
    - RUNNING   — chal raha hai
    - COMPLETED — khatam ho gaya
    - FAILED    — kuch error aaya
    """
    scan = get_scan(db, str(scan_id))

    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    messages = {
        "PENDING": "Scan is queued and will start shortly",
        "RUNNING": "Scan is currently running — agents are analyzing your code",
        "COMPLETED": f"Scan completed — Risk Score: {scan.risk_score}/100",
        "FAILED": f"Scan failed: {scan.error_message}",
    }

    return ScanStatusResponse(
        id=scan.id,
        status=scan.status,
        risk_score=scan.risk_score,
        started_at=scan.started_at,
        completed_at=scan.completed_at,
        error_message=scan.error_message,
        message=messages.get(scan.status, "Unknown status"),
    )


@router.get("/", response_model=list[ScanResponse])
def list_scans(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 20,
):
    """Saare scans list karo."""
    scans = db.query(Scan).offset(skip).limit(limit).all()
    return [ScanResponse.model_validate(s) for s in scans]