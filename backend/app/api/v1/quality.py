"""Quality API — metadata scoring, reproducibility, and quality reports."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.services.quality_service import QualityService

router = APIRouter(prefix="/quality", tags=["quality"])


def _raise_not_found_if_error(result: dict) -> None:
    error = result.get("error")
    if error:
        raise HTTPException(status_code=404, detail=error)


@router.get("/papers/{paper_id}/metadata-score")
async def get_metadata_score(
    paper_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Return the metadata completeness score for a paper."""
    svc = QualityService(db)
    result = await svc.get_metadata_score(str(paper_id))
    _raise_not_found_if_error(result)
    return result


@router.get("/papers/{paper_id}/reproducibility")
async def get_reproducibility(
    paper_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Return reproducibility signals for a paper."""
    svc = QualityService(db)
    result = await svc.get_reproducibility(str(paper_id))
    _raise_not_found_if_error(result)
    return result


@router.get("/papers/{paper_id}/report")
async def get_quality_report(
    paper_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Return the combined quality report for a paper."""
    svc = QualityService(db)
    result = await svc.get_quality_report(str(paper_id))
    _raise_not_found_if_error(result.get("metadata_score", {}))
    _raise_not_found_if_error(result.get("reproducibility", {}))
    return result
