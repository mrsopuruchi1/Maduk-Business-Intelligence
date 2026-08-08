# backend/database.py

import os
from typing import AsyncGenerator
from dotenv import load_dotenv

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy.orm import declarative_base

# ----------------------------
# LOAD ENV VARIABLES
# ----------------------------
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in environment variables")

# ----------------------------
# ENGINE SETUP (OPTIMIZED)
# ----------------------------
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    pool_size=10,          # handles concurrency
    max_overflow=20,       # burst traffic
    pool_pre_ping=True     # avoids stale connections
)

# ----------------------------
# SESSION SETUP
# ----------------------------
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# ----------------------------
# BASE MODEL
# ----------------------------
Base = declarative_base()

# ----------------------------
# IMPORT ALL MODELS (VERY IMPORTANT)
# ----------------------------
# This ensures SQLAlchemy registers relationships
from backend.models.user import User
from backend.models.tenant import Tenant
from backend.models.user_tenant import UserTenant
from backend.models.subscription import Subscription


# ----------------------------
# INIT DB (CREATE TABLES)
# ----------------------------
async def init_db():
    """
    Initialize database and create all tables.
    Call this on app startup.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# ----------------------------
# DB SESSION DEPENDENCY
# ----------------------------
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Provides a database session to FastAPI routes.
    Ensures proper cleanup after request.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()