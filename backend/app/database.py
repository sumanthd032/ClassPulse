"""
Async SQLAlchemy engine and session factory.

All database I/O uses asyncpg under the hood so FastAPI routes never block
the event loop.
"""
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from app.config import settings

# ---------------------------------------------------------------------------
# Engine
# pool_pre_ping=True: validate connections before checkout (handles stale ones)
# ---------------------------------------------------------------------------
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,        # Set to True only for query-level debugging
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# ---------------------------------------------------------------------------
# Session factory
# expire_on_commit=False: prevents "DetachedInstanceError" in async code
# ---------------------------------------------------------------------------
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# All ORM models inherit from this Base.
Base = declarative_base()


async def get_db() -> AsyncSession:
    """
    FastAPI dependency that yields a database session.
    The session is automatically closed when the request completes.
    """
    async with AsyncSessionLocal() as session:
        yield session
