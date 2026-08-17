"""
Async PostgreSQL connection using SQLAlchemy 2.0.

WHY async?
- FastAPI is async-native
- Async DB = more concurrent scans without blocking
- SQLAlchemy 2.0 async is production standard

WHY not ORM for everything?
- ORM for CRUD operations
- Raw SQL for complex queries

INTERVIEW ANGLE:
"Why use async SQLAlchemy instead of synchronous?"
→ Non-blocking I/O: while waiting for DB, server can handle other requests.
"""

from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings
from app.core.logger import get_logger


logger = get_logger("database")


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


engine = create_async_engine(
    settings.database_url,
    echo=settings.app_env == "development",
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)


AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency: provides a DB session per request.
    Always closes the session after request completes.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def check_database_connection() -> bool:
    """Health check: verify DB is reachable."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))

        logger.info("Database connection successful")
        return True

    except Exception as e:
        logger.error("Database connection failed", error=str(e))
        return False