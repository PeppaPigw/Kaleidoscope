"""Users API — user preferences and profile."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user_id, get_db
from app.models.user import User
from app.services.monitoring.alert_service import AlertService

router = APIRouter(prefix="/users", tags=["users"])


def _dedupe_strings(
    values: list[str] | None,
    *,
    casefold: bool = False,
) -> list[str]:
    """Strip blanks and deduplicate string arrays while preserving order."""
    if not values:
        return []

    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = str(value).strip()
        if not cleaned:
            continue
        key = cleaned.casefold() if casefold else cleaned
        if key in seen:
            continue
        seen.add(key)
        normalized.append(cleaned)
    return normalized


class ResearchFacets(BaseModel):
    """Saved fine-grained research facet preferences used for personalization."""

    domain: list[str] = Field(default_factory=list)
    task: list[str] = Field(default_factory=list)
    method: list[str] = Field(default_factory=list)
    data_object: list[str] = Field(default_factory=list)
    application: list[str] = Field(default_factory=list)
    paper_type: list[str] = Field(default_factory=list)
    evaluation_quality: list[str] = Field(default_factory=list)

    @field_validator(
        "domain",
        "task",
        "method",
        "data_object",
        "application",
        "paper_type",
        "evaluation_quality",
        mode="after",
    )
    @classmethod
    def _normalize_values(cls, values: list[str]) -> list[str]:
        return _dedupe_strings(values, casefold=True)


class UserPreferences(BaseModel):
    """User preferences schema — arbitrary JSON structure with known keys."""

    subscribed_categories: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    tracked_authors: list[str] = Field(default_factory=list)
    research_facets: ResearchFacets = Field(default_factory=ResearchFacets)
    interests_set: bool = False

    model_config = {"extra": "allow"}

    @field_validator("subscribed_categories", mode="after")
    @classmethod
    def _normalize_categories(cls, values: list[str]) -> list[str]:
        return _dedupe_strings(values)

    @field_validator("keywords", mode="after")
    @classmethod
    def _normalize_keywords(cls, values: list[str]) -> list[str]:
        return _dedupe_strings(values, casefold=True)

    @field_validator("tracked_authors", mode="after")
    @classmethod
    def _normalize_authors(cls, values: list[str]) -> list[str]:
        return _dedupe_strings(values, casefold=True)


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
    return UserPreferences.model_validate(user.preferences or {})


@router.put("/me/preferences", response_model=UserPreferences)
async def update_preferences(
    body: UserPreferences,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Replace current user's preferences."""
    user = await _get_or_create_user(db, user_id)
    user.preferences = body.model_dump()
    alert_service = AlertService(db, user_id)
    await alert_service.sync_preference_rules(
        keywords=body.keywords,
        tracked_authors=body.tracked_authors,
    )
    await db.flush()
    return user.preferences
