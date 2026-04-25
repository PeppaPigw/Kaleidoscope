"""Database engine, session factory, and dependency injection."""

from collections.abc import AsyncGenerator

from fastapi import Request
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings

# Create async engine with connection pooling
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)

# Session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yields an async DB session, auto-closes on exit."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_current_user_id(request: Request) -> str:
    """
    FastAPI dependency: extract user ID from API-key middleware or JWT.

    Falls back to DEFAULT_USER_ID in single-user / no-auth mode.
    Set KALEIDOSCOPE_JWT_SECRET env var to enable real auth.
    """
    from fastapi import HTTPException

    from app.auth import JWT_SECRET, decode_access_token
    from app.models.collection import DEFAULT_USER_ID

    state_user_id = getattr(request.state, "user_id", None)
    if state_user_id:
        return str(state_user_id)

    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[len("Bearer ") :]
        user_id = decode_access_token(token)
        if user_id:
            return user_id
        if JWT_SECRET:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
    if JWT_SECRET:
        raise HTTPException(status_code=401, detail="Authentication required")
    return DEFAULT_USER_ID
