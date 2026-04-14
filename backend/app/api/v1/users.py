"""Users API — user preferences and profile."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user_id
from app.models.user import User

router = APIRouter(prefix="/users", tags=["users"])


class UserPreferences(BaseModel):
    """User preferences schema — arbitrary JSON structure with known keys."""

    subscribed_categories: list[str] = []
    keywords: list[str] = []
    tracked_authors: list[str] = []
    interests_set: bool = False

    model_config = {"extra": "allow"}


async def _get_or_create_user(db: AsyncSession, user_id: str) -> User:
    """Fetch the default user row, creating it if it doesn't exist yet."""
    import uuid

    from app.models.collection import DEFAULT_USER_ID

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        # Create the default user row on first access
        user = User(
            id=uuid.UUID(DEFAULT_USER_ID),
            email="admin@kaleidoscope.local",
            username="admin",
            display_name="Admin",
            preferences={},
        )
        db.add(user)
        await db.flush()
    return user


@router.get("/me/preferences", response_model=UserPreferences)
async def get_preferences(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Return current user's preferences."""
    user = await _get_or_create_user(db, user_id)
    return user.preferences or {}


@router.put("/me/preferences", response_model=UserPreferences)
async def update_preferences(
    body: UserPreferences,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Replace current user's preferences."""
    user = await _get_or_create_user(db, user_id)
    user.preferences = body.model_dump()
    await db.flush()
    return user.preferences
