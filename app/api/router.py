"""Main API router — saare sub-routers yahan register hote hain."""

from fastapi import APIRouter
from app.api.repositories import router as repositories_router
from app.api.scans import router as scans_router
from app.api.findings import router as findings_router
from app.api.reports import router as reports_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(repositories_router)
api_router.include_router(scans_router)
api_router.include_router(findings_router)
api_router.include_router(reports_router)