from fastapi import APIRouter
from app.api.repositories import router as repositories_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(repositories_router)