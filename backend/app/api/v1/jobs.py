"""Async job lifecycle API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.services.job_service import JobService

router = APIRouter(prefix="/jobs", tags=["jobs"])


class JobCancelRequest(BaseModel):
    """Request body for cancelling a queued or running job."""

    terminate: bool = False
    signal: str = Field(default="SIGTERM", min_length=1, max_length=20)


@router.get("")
async def list_jobs(
    entity_id: str | None = Query(default=None, max_length=100),
) -> dict[str, Any]:
    """List known jobs for an entity when durable tracking is available."""
    return JobService().list_jobs(entity_id=entity_id)


@router.get("/{job_id}")
async def get_job(
    job_id: str,
    include_traceback: bool = Query(default=False),
) -> dict[str, Any]:
    """Return status, result, and error metadata for a job."""
    return JobService().get_job(job_id, include_traceback=include_traceback)


@router.post("/{job_id}/cancel")
async def cancel_job(
    job_id: str,
    body: JobCancelRequest | None = None,
) -> dict[str, Any]:
    """Request cancellation for a queued/running job."""
    payload = body or JobCancelRequest()
    return JobService().cancel_job(
        job_id,
        terminate=payload.terminate,
        signal=payload.signal,
    )
