from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger("database")


class Base(DeclarativeBase):
    pass


engine = create_engine(
    settings.database_url,
    echo=settings.app_env == "development",
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

# ← YAHI MISSING THA
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db():
    """FastAPI dependency — har request ke liye DB session."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def check_database_connection() -> bool:
    """Health check."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error("Database connection failed", error=str(e))
        return False


def create_all_tables():
    """Testing ke liye — seedha tables banao."""
    Base.metadata.create_all(bind=engine)