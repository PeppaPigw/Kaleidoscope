"""API key management endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user_id, get_db
from app.services.api_key_service import VALID_API_SCOPES, APIKeyService

router = APIRouter(prefix="/api-keys", tags=["api-keys"])
DbSession = Annotated[AsyncSession, Depends(get_db)]
UserId = Annotated[str, Depends(get_current_user_id)]


class APIKeyCreateRequest(BaseModel):
    """Request body for creating an external API key."""

    name: str = Field(..., min_length=1, max_length=255)
    scopes: list[str] = Field(default_factory=list, max_length=20)
    expires_at: datetime | None = None
    description: str | None = Field(default=None, max_length=2000)


@router.post("")
async def create_api_key(
    body: APIKeyCreateRequest,
    db: DbSession,
    user_id: UserId,
) -> dict[str, Any]:
    """Create an API key and return the raw secret once."""
    try:
        return await APIKeyService(db, user_id).create_key(
            name=body.name,
            scopes=body.scopes,
            expires_at=body.expires_at,
            description=body.description,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("")
async def list_api_keys(
    db: DbSession,
    user_id: UserId,
    include_revoked: bool = Query(default=False),
) -> dict[str, Any]:
    """List API keys without exposing raw secrets."""
    keys = await APIKeyService(db, user_id).list_keys(include_revoked=include_revoked)
    return {"keys": keys, "total": len(keys), "valid_scopes": sorted(VALID_API_SCOPES)}


@router.delete("/{key_id}")
async def revoke_api_key(
    key_id: str,
    db: DbSession,
    user_id: UserId,
) -> dict[str, Any]:
    """Revoke an API key by ID."""
    key = await APIKeyService(db, user_id).revoke_key(key_id)
    if key is None:
        raise HTTPException(status_code=404, detail="API key not found")
    return {"revoked": True, "key": key}
