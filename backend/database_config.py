# backend/database_config.py
import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

# Async database URL from .env
DATABASE_URL = os.getenv("DATABASE_URL")  # e.g., postgresql+asyncpg://user:pass@localhost/dbname

# Async SQLAlchemy engine
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # set False in production
    future=True
)

# Async sessionmaker
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False
)

# Base class for models
Base = declarative_base()