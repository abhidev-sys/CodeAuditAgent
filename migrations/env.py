# Python ke system path ko modify karne ke liye
import sys

# File aur folder paths handle karne ke liye
from pathlib import Path

# Logging configuration ke liye
from logging.config import fileConfig

# SQLAlchemy se database engine configuration
from sqlalchemy import engine_from_config, pool

# Alembic ka main context object
from alembic import context


# ---------------------------------------------------------
# PROJECT ROOT PATH
# ---------------------------------------------------------

# __file__ = current env.py file
#
# __file__ ka path:
# R:\codeauditagent\migrations\env.py
#
# .resolve() = absolute path banata hai
# .parent = migrations folder
# .parent.parent = project root
#
# Result:
# R:\codeauditagent
BASE_DIR = Path(__file__).resolve().parent.parent


# Project root ko Python ke import path mein add karo
#
# Iske baad Python:
# from app.core.config import settings
#
# ko successfully find kar payega.
sys.path.insert(0, str(BASE_DIR))


# ---------------------------------------------------------
# APPLICATION IMPORTS
# ---------------------------------------------------------

# Hamare project ki configuration
from app.core.config import settings

# SQLAlchemy ka Base class
# Iske metadata mein hamare saare database tables registered honge
from app.core.database import Base

# Saare models import karo
#
# Iska purpose:
# Repository
# Scan
# Finding
# Patch
# Verification
# Report
#
# in sabko SQLAlchemy ke Base.metadata mein register karna hai.
import app.models


# ---------------------------------------------------------
# ALEMBIC CONFIGURATION
# ---------------------------------------------------------

# Alembic ka configuration object
config = context.config


# Agar alembic.ini mein logging configuration available hai
# toh usko load karo.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# ---------------------------------------------------------
# DATABASE METADATA
# ---------------------------------------------------------

# Alembic ko batate hain ki hamare database models
# ka metadata yahan available hai.
#
# Alembic isi metadata ko PostgreSQL ke existing schema
# ke saath compare karega.
target_metadata = Base.metadata


# ---------------------------------------------------------
# OFFLINE MIGRATION
# ---------------------------------------------------------

def run_migrations_offline() -> None:
    """
    Offline mode mein Alembic actual database se connect nahi karta.

    Is mode mein migration SQL generate ki ja sakti hai.
    """

    # alembic.ini se database URL read karo
    url = config.get_main_option("sqlalchemy.url")

    # Alembic ko migration configuration do
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    # Migration transaction start karo
    with context.begin_transaction():

        # Migration execute/generate karo
        context.run_migrations()


# ---------------------------------------------------------
# ONLINE MIGRATION
# ---------------------------------------------------------

def run_migrations_online() -> None:
    """
    Normal migration mode.

    Is mode mein Alembic actual PostgreSQL database
    se connection establish karta hai.
    """

    # alembic.ini ki SQLAlchemy settings se
    # database engine configuration create karo
    connectable = engine_from_config(
        config.get_section(
            config.config_ini_section,
            {}
        ),

        # Sirf sqlalchemy. se start hone wali settings use karo
        prefix="sqlalchemy.",

        # Migration ke liye connection pool maintain
        # karne ki zarurat nahi hai
        poolclass=pool.NullPool,
    )

    # PostgreSQL se connection establish karo
    with connectable.connect() as connection:

        # Alembic ko current database connection
        # aur hamare models ka metadata provide karo
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        # Migration transaction ke andar run karo
        with context.begin_transaction():

            # Actual migration execute karo
            context.run_migrations()


# ---------------------------------------------------------
# MIGRATION MODE
# ---------------------------------------------------------

# Check karo Alembic offline mode mein hai ya online mode mein
if context.is_offline_mode():

    # Offline migration run karo
    run_migrations_offline()

else:

    # Normal online migration run karo
    run_migrations_online()