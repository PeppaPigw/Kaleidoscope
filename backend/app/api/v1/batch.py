"""Standard controlled batch API."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user_id, get_db
from app.services.batch_service import SUPPORTED_BATCH_OPERATIONS, BatchService

router = APIRouter(tags=["batch"])
DbSession = Annotated[AsyncSession, Depends(get_db)]
UserId = Annotated[str, Depends(get_current_user_id)]


class BatchCall(BaseModel):
    """Single operation in a standard batch request."""

    id: str | None = Field(default=None, max_length=100)
    operation: str = Field(..., min_length=1, max_length=100)
    arguments: dict[str, Any] = Field(default_factory=dict)


class BatchRequest(BaseModel):
    """Request body for executing independent agent-safe operations."""

    calls: list[BatchCall] = Field(..., min_length=1, max_length=20)


@router.post("/batch")
async def execute_batch(
    body: BatchRequest,
    db: DbSession,
    user_id: UserId,
) -> dict[str, Any]:
    """Execute up to 20 independent safe operations and return ordered results."""
    payload = [call.model_dump() for call in body.calls]
    result = await BatchService(db, user_id).execute(payload)
    result["supported_operations"] = sorted(SUPPORTED_BATCH_OPERATIONS)
    return result
