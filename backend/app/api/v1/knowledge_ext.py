"""Extended knowledge API — quizzes, glossary views, and retraction stats."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.services.analysis.knowledge_service_ext import KnowledgeExtService

router = APIRouter(prefix="/knowledge/ext", tags=["knowledge"])


def _raise_not_found_if_error(result: dict) -> None:
    error = result.get("error")
    if error:
        raise HTTPException(status_code=404, detail=error)


@router.get("/papers/{paper_id}/quiz")
async def generate_quiz(
    paper_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Generate a small quiz from a paper."""
    svc = KnowledgeExtService(db)
    result = await svc.generate_quiz(str(paper_id))
    _raise_not_found_if_error(result)
    return result


@router.get("/papers/{paper_id}/glossary")
async def get_glossary(
    paper_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Return glossary terms associated with a paper."""
    svc = KnowledgeExtService(db)
    result = await svc.get_glossary(str(paper_id))
    _raise_not_found_if_error(result)
    return result


@router.get("/retraction-stats")
async def get_retraction_stats(
    min_year: int = Query(2000, ge=1900),
    db: AsyncSession = Depends(get_db),
):
    """Return retraction statistics starting from the given year."""
    svc = KnowledgeExtService(db)
    return await svc.get_retraction_stats(min_year=min_year)
