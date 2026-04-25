"""Universal paper resolver API."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.services.paper_resolver_service import IdentifierType, PaperResolverService

router = APIRouter(tags=["resolve"])
DbSession = Annotated[AsyncSession, Depends(get_db)]


class ResolveRequest(BaseModel):
    """Request body for resolving a paper identifier."""

    identifier: str = Field(..., min_length=1, max_length=1000)
    identifier_type: IdentifierType = "auto"
    include_external: bool = True
    candidate_limit: int = Field(default=5, ge=1, le=20)


@router.post("/resolve")
async def resolve_identifier(
    body: ResolveRequest,
    db: DbSession,
) -> dict[str, Any]:
    """Resolve local and external paper candidates for an identifier."""
    return await PaperResolverService(db).resolve(
        identifier=body.identifier,
        identifier_type=body.identifier_type,
        include_external=body.include_external,
        candidate_limit=body.candidate_limit,
    )
