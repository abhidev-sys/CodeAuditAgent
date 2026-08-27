"""
Scan Service — Business logic for scan operations.

Yeh layer API aur agents ke beech mein hai.
Database operations + agent pipeline coordination yahan hoti hai.
"""

import uuid
import threading
import json
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session

from app.models.scan import Scan
from app.models.finding import Finding
from app.models.patch import Patch
from app.models.report import Report
from app.models.repository import Repository
from app.agents.orchestrator import run_scan
from app.core.logger import get_logger

logger = get_logger("scan_service")


def create_scan(
    db: Session,
    repository_id: str,
) -> Scan:
    """
    Naya scan create karo aur background mein run karo.

    Steps:
    1. Repository exist karta hai check karo
    2. Scan DB record banao (PENDING status)
    3. Background thread mein scan run karo
    4. Scan object return karo

    Args:
        db: Database session
        repository_id: Repository UUID

    Returns:
        Scan DB object
    """
    # Repository check karo
    repo = db.query(Repository).filter(
        Repository.id == repository_id
    ).first()

    if not repo:
        raise ValueError(f"Repository not found: {repository_id}")

    # Scan record banao
    scan_id = str(uuid.uuid4())
    scan = Scan(
        id=scan_id,
        repository_id=repository_id,
        status="PENDING",
        model_used="openai/gpt-oss-120b",
        created_at=datetime.now(),
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)

    logger.info(
        "Scan created",
        scan_id=scan_id,
        repository_id=str(repository_id),
    )

    # Background thread mein run karo
    thread = threading.Thread(
        target=_run_scan_background,
        args=(scan_id, str(repo.path), str(repository_id)),
        daemon=True,
    )
    thread.start()

    return scan


def _run_scan_background(
    scan_id: str,
    repository_path: str,
    repository_id: str,
) -> None:
    """
    Background mein scan run karo.

    Yeh function ek alag thread mein chalta hai taaki
    API request block na ho.

    Steps:
    1. Scan status RUNNING karo
    2. Agent pipeline run karo
    3. Results database mein save karo
    4. Scan status COMPLETED karo
    """
    from app.core.database import SessionLocal

    db = SessionLocal()

    try:
        # Status update karo
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        if not scan:
            logger.error("Scan not found in background", scan_id=scan_id)
            return

        scan.status = "RUNNING"
        scan.started_at = datetime.now()
        db.commit()

        logger.info("Scan running in background", scan_id=scan_id)

        # Agent pipeline run karo
        result = run_scan(
            repository_path=repository_path,
            repository_id=repository_id,
            scan_id=scan_id,
        )

        # Results save karo
        _save_results_to_db(
            db=db,
            scan_id=scan_id,
            result=result,
        )

        # Scan complete karo
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        scan.status = "COMPLETED"
        scan.completed_at = datetime.now()
        scan.risk_score = result.get("risk_score", 0)
        scan.token_usage = result.get("token_usage", 0)
        db.commit()

        logger.info(
            "Scan completed",
            scan_id=scan_id,
            risk_score=result.get("risk_score", 0),
            vulnerabilities=len(result.get("vulnerabilities", [])),
        )

    except Exception as e:
        logger.error(
            "Scan failed in background",
            scan_id=scan_id,
            error=str(e),
        )
        import traceback
        traceback.print_exc()

        # Scan failed mark karo
        try:
            scan = db.query(Scan).filter(Scan.id == scan_id).first()
            if scan:
                scan.status = "FAILED"
                scan.error_message = str(e)
                scan.completed_at = datetime.now()
                db.commit()
        except Exception as inner_e:
            logger.error("Failed to update scan status", error=str(inner_e))

    finally:
        db.close()


def _save_results_to_db(
    db: Session,
    scan_id: str,
    result: dict,
) -> None:
    """Scan results database mein save karo."""

    vulnerabilities = result.get("vulnerabilities", [])
    patches = result.get("patches", [])

    # Findings save karo
    finding_id_map = {}  # finding_index -> db finding id

    for i, vuln in enumerate(vulnerabilities):
        finding = Finding(
            scan_id=scan_id,
            vuln_type=vuln.get("vuln_type", "GENERAL"),
            severity=vuln.get("severity", "MEDIUM"),
            confidence=vuln.get("confidence", 0.5),
            file_path=vuln.get("file_path", ""),
            line_start=vuln.get("line_start"),
            line_end=vuln.get("line_end"),
            code_snippet=str(vuln.get("evidence", ""))[:500],
            cwe_id=vuln.get("cwe_id", ""),
            description=vuln.get("description", ""),
            evidence={
                "reasoning": vuln.get("reasoning", ""),
                "evidence": vuln.get("evidence", ""),
            },
            exploitability="TRUE_POSITIVE",
            status="OPEN",
        )
        db.add(finding)
        db.flush()
        finding_id_map[f"finding_{i}"] = str(finding.id)

    db.commit()

    # Patches save karo
    for patch_data in patches:
        finding_key = patch_data.get("finding_id", "")
        finding_db_id = finding_id_map.get(finding_key)

        if not finding_db_id:
            continue

        patch = Patch(
            finding_id=finding_db_id,
            unified_diff=patch_data.get("unified_diff", ""),
            explanation=patch_data.get("explanation", ""),
            confidence=patch_data.get("confidence", 0.5),
            status="GENERATED" if patch_data.get("success") else "FAILED",
        )
        db.add(patch)

    db.commit()

    # Report save karo
    report_file = Path(f"reports/report_{scan_id[:8]}.json")
    summary = {}

    if report_file.exists():
        try:
            with open(report_file, encoding="utf-8") as f:
                summary = json.load(f)
        except Exception:
            pass

    report = Report(
        scan_id=scan_id,
        summary=summary,
        report_path=str(report_file),
    )
    db.add(report)
    db.commit()

    logger.info(
        "Results saved to DB",
        scan_id=scan_id,
        findings=len(vulnerabilities),
        patches=len(patches),
    )


def get_scan(db: Session, scan_id: str) -> Scan | None:
    """Scan by ID fetch karo."""
    return db.query(Scan).filter(Scan.id == scan_id).first()


def get_findings(db: Session, scan_id: str) -> list[Finding]:
    """Scan ke saare findings fetch karo."""
    return db.query(Finding).filter(
        Finding.scan_id == scan_id
    ).order_by(Finding.created_at).all()


def get_report(db: Session, scan_id: str) -> Report | None:
    """Scan ka report fetch karo."""
    return db.query(Report).filter(
        Report.scan_id == scan_id
    ).first()