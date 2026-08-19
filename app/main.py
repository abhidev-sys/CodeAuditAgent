from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logger import setup_logging, get_logger
from app.core.database import check_database_connection
from app.api.router import api_router

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info(
        "CodeAuditAgent starting",
        env=settings.app_env,
        model=settings.llm_model_name,
    )
    db_ok = check_database_connection()
    if not db_ok:
        logger.warning("Database not reachable on startup")
    yield
    logger.info("CodeAuditAgent shutting down")


app = FastAPI(
    title="CodeAuditAgent",
    description="Autonomous AI Security Auditor — Detect → Reason → Patch → Verify",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ← YEH LINE SABSE IMPORTANT HAI
app.include_router(api_router)


@app.get("/health", tags=["System"])
def health_check():
    db_ok = check_database_connection()
    return {
        "status": "healthy" if db_ok else "degraded",
        "version": "0.1.0",
        "env": settings.app_env,
        "database": "connected" if db_ok else "unreachable",
    }


@app.get("/", tags=["System"])
def root():
    return {
        "project": "CodeAuditAgent",
        "tagline": "Detect → Reason → Patch → Verify",
        "docs": "/docs",
    }